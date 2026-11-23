"""Standard Firecrawl batch transport with resumable URL locks and local persistence."""

import json
import time
from datetime import datetime, timezone
from urllib.parse import urlencode, urljoin, urlsplit

import requests

from firecrawl_cache import canonical_url


BASE_URL = "https://api.firecrawl.dev"
ENDPOINT = BASE_URL + "/v2/batch/scrape"


def request(session, method, url, **kwargs):
    for attempt in range(6):
        try:
            response = session.request(method, url, timeout=40, **kwargs)
        except (requests.Timeout, requests.ConnectionError):
            if method == "POST" or attempt == 5:
                raise
        else:
            if response.ok:
                return response.json()
            if response.status_code == 429:
                wait = response.headers.get("Retry-After")
                if wait and wait.isdecimal():
                    time.sleep(int(wait))
            elif method == "GET" and response.status_code in {500, 502, 503, 504}:
                pass
            else:
                response.raise_for_status()
            if attempt == 5:
                response.raise_for_status()
        time.sleep(min(2 ** attempt, 20))
    raise RuntimeError("Firecrawl nie odpowiedział po sześciu próbach.")


def result_payload(document, job_id):
    metadata = document.get("metadata") or {}
    return {
        "markdown": document.get("markdown") or "",
        "html": document.get("html") or "",
        "provenance": {
            "source": "Firecrawl",
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "batch_id": job_id,
            "credits_used": metadata.get("creditsUsed"),
            "http_status": metadata.get("statusCode"),
            "source_url": metadata.get("sourceURL"),
            "resolved_url": metadata.get("url"),
        },
    }


def save_status(cache, session, job, status_url):
    first = None
    visited = set()
    reserved = set(job["urls"])
    done = set(job["saved"])
    while status_url:
        url = urljoin(BASE_URL, status_url)
        if urlsplit(url).netloc != urlsplit(BASE_URL).netloc:
            raise ValueError(f"Zewnętrzny adres stanu partii Firecrawl: {url}")
        if url in visited:
            break
        visited.add(url)
        status = request(session, "GET", url)
        first = first or status
        documents = status.get("data") or []
        for document in documents:
            metadata = document.get("metadata") or {}
            source = metadata.get("sourceURL") or metadata.get("url")
            if not source:
                continue
            key = canonical_url(source)
            if key in reserved and key not in done:
                if cache.finish_batch(key, job["reservation"], result_payload(document, job["id"])):
                    job["saved"].append(key)
                    done.add(key)
                elif cache.get(key) is not None:
                    job["saved"].append(key)
                    done.add(key)
        if not documents:
            break
        status_url = status.get("next")
    return first


def run_batch(urls, cache, api_key, output_dir, write_evidence, *, resume=None):
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {api_key}"})
    if resume:
        journal = json.loads(resume.read_text(encoding="utf-8"))
        run_id, jobs, output = journal["id"], journal["jobs"], resume
        for job in jobs:
            for url in job["urls"]:
                try:
                    saved = cache.get(url)
                except RuntimeError:
                    continue
                if saved and saved.get("provenance", {}).get("batch_id") == job.get("id") and url not in job["saved"]:
                    job["saved"].append(url)
    else:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        output = output_dir / "firecrawl_runs" / f"{run_id}_batch.json"
        jobs = []
        for offset in range(0, len(urls), 250):
            reservation = f"{run_id}:{offset}"
            reserved = cache.reserve_batch(urls[offset:offset + 250], reservation)
            if reserved:
                jobs.append({"reservation": reservation, "urls": reserved, "saved": [], "status": "reserved"})

    def checkpoint():
        write_evidence(output, json.dumps({"id": run_id, "jobs": jobs}, ensure_ascii=False, indent=2) + "\n")

    checkpoint()
    for job in (job for job in jobs if job["status"] == "reserved"):
        job["status"] = "submitting"
        checkpoint()
        try:
            result = request(
                session, "POST", ENDPOINT, json={
                    "urls": job["urls"], "formats": ["markdown", "html"], "parsers": [],
                    "onlyMainContent": False, "proxy": "auto",
                },
            )
        except requests.HTTPError as error:
            status = error.response.status_code
            if status in {400, 401, 402, 403, 422, 429}:
                for url in job["urls"]:
                    cache.finish_batch(url, job["reservation"])
                job.update(status="rejected", http_status=status)
            else:
                job.update(status="submission_uncertain", http_status=status)
            print(f"Firecrawl partia {len(job['urls'])} URL-i: HTTP {status}.", flush=True)
        except (requests.RequestException, ValueError) as error:
            job.update(status="submission_uncertain", error=type(error).__name__)
        else:
            job.update(id=result["id"], status="pending")
            print(f"Firecrawl przyjął partię {len(job['urls'])} URL-i ({job['id']}).", flush=True)
        checkpoint()

    terminal = {"completed", "failed", "cancelled"}
    active = [job for job in jobs if job.get("id") and job["status"] not in terminal]
    while active:
        for job in active:
            try:
                query = urlencode({"skip": len(job["saved"]), "limit": 40})
                status = save_status(cache, session, job, f"{ENDPOINT}/{job['id']}?{query}")
            except (requests.RequestException, ValueError) as error:
                print(f"Firecrawl, odczyt stanu {job['id']}: {type(error).__name__}.", flush=True)
                continue
            job["status"] = status["status"]
            job["credits_used"] = status.get("creditsUsed")
            job["completed"] = status.get("completed")
            if job["status"] in terminal:
                if len(job["saved"]) < (job["completed"] or 0):
                    try:
                        save_status(cache, session, job, f"{ENDPOINT}/{job['id']}?limit=40")
                    except (requests.RequestException, ValueError) as error:
                        job["status"] = "retry_download"
                        job["error"] = type(error).__name__
                        continue
                remaining = set(job["urls"]) - set(job["saved"])
                if remaining:
                    try:
                        errors = request(session, "GET", f"{ENDPOINT}/{job['id']}/errors").get("errors") or []
                        for error in errors:
                            source = error.get("url")
                            if source and (url := canonical_url(source)) in remaining:
                                cache.finish_batch(url, job["reservation"])
                        job["errors"] = errors
                    except (requests.RequestException, ValueError):
                        pass
            checkpoint()
        active = [job for job in active if job["status"] not in terminal]
        print(
            f"Firecrawl batch: {sum(len(job['saved']) for job in jobs)}/{sum(len(job['urls']) for job in jobs)} stron w cache, "
            f"{len(active)} partii w toku.", flush=True,
        )
        if active:
            time.sleep(10)
    print(f"Firecrawl batch rozliczenie: {sum(job.get('credits_used') or 0 for job in jobs)} kredytów wg statusów.", flush=True)
