"""Acquire ESPI source pages and materialize the locally parsed evidence."""

import argparse
import csv
import hashlib
import json
import os
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import local
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from firecrawl_cache import FirecrawlCache, UncertainFetchError, canonical_url, replace_with_retry
from scrape_ir_firecrawl import DATA_ROOT, ScrapeSession, get_api_key

from data_paths import EVENTS, RAW


EVIDENCE = RAW / "espi" / "detail_evidence"
BUDGET = 2500


def write_evidence(path, text):
    write_bytes(path, text.encode("utf-8"))


def write_bytes(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(dir=path.parent, delete=False) as file:
            temporary = Path(file.name)
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        replace_with_retry(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def read_rows(queue, supplementary):
    with queue.open(encoding="utf-8-sig", newline="") as stream:
        rows = {row["event_id"]: row for row in csv.DictReader(stream)}
    for manifest in supplementary:
        with manifest.open(encoding="utf-8-sig") as stream:
            for line in stream:
                if line.strip():
                    item = json.loads(line)
                    existing = rows.setdefault(item["event_id"], item)
                    if item.get("referenced_by"):
                        existing["referenced_by"] = item["referenced_by"]
    return list(rows.values())


def plan_urls(rows, cache, evidence_dir):
    queue = {}
    for row in rows:
        url = row.get("url")
        if url:
            queue.setdefault(canonical_url(url), row["ticker"])
    supported_by_archive = set()
    existing_index = evidence_dir / "reports.jsonl"
    if existing_index.is_file():
        with existing_index.open(encoding="utf-8-sig") as stream:
            for line in stream:
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("status") == "ok" and row.get("text", "").strip() and row.get("url") and row.get("text_source_url"):
                    supported_by_archive.add(canonical_url(row["url"]))
    cached, missing, pending, archived = [], [], [], []
    for url in queue:
        try:
            available = cache.get(url) is not None
        except UncertainFetchError:
            target = archived if url in supported_by_archive else pending
        else:
            target = cached if available else archived if url in supported_by_archive else missing
        target.append(url)
    counts = {kind: Counter(queue[url] for url in urls) for kind, urls in
              (("cache", cached), ("archiwum lokalne", archived), ("do pobrania", missing), ("oczekujące", pending))}
    for ticker in dict.fromkeys(queue.values()):
        print(f"{ticker}: " + ", ".join(f"{kind} {totals[ticker]}" for kind, totals in counts.items()))
    print(f"Pozycje: {len(rows)}. Unikalne URL-e: {len(queue)}. "
          f"Do pobrania poza cache i archiwum: {len(missing)}. Oczekujące: {len(pending)}.", flush=True)
    return missing


def account_balance(api_key):
    if not api_key:
        return None
    request = Request(
        "https://api.firecrawl.dev/v2/team/credit-usage",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    try:
        with urlopen(request, timeout=20) as response:
            data = json.load(response)["data"]
        return {key: data[key] for key in ("remainingCredits", "billingPeriodStart", "billingPeriodEnd")}
    except (URLError, TimeoutError, ValueError, KeyError) as error:
        print(f"Nie udało się odczytać salda Firecrawl ({type(error).__name__}).", file=sys.stderr)
        return None


def download_pages(urls, cache, output_dir, workers):
    if not urls:
        print("Firecrawl: 0 zapytań i 0 kredytów.", flush=True)
        return
    from dotenv import load_dotenv

    env_file = DATA_ROOT.parent / ".env"
    load_dotenv(dotenv_path=env_file, override=False, encoding="utf-8-sig")
    key = get_api_key()
    before = account_balance(key)
    if before and before["remainingCredits"] < len(urls):
        raise SystemExit("Liczba stron przewyższa dostępne saldo Firecrawl.")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    worker_state = local()
    totals = Counter()
    failures = []

    def run_one(url):
        if not hasattr(worker_state, "session"):
            worker_state.session = ScrapeSession(cache, env_file, None, 0, proxy="auto")
        app = worker_state.session
        before_attempts, before_credits = app.api_requests, app.confirmed_credits
        app.uncertain_charge = False
        failure = None
        try:
            app.read(url)
        except Exception as error:
            failure = {"url": url, "error_type": type(error).__name__, "detail": str(error),
                       "possibly_charged": app.uncertain_charge}
        return app.api_requests - before_attempts, app.confirmed_credits - before_credits, failure

    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(run_one, url) for url in urls]
            for completed, future in enumerate(as_completed(futures), 1):
                attempts, credits, failure = future.result()
                totals.update(attempts=attempts, confirmed_credits=credits, finished=1)
                if failure:
                    failures.append(failure)
                    if len(failures) <= 10:
                        print(f"Problem z pobraniem {failure['url']} ({failure['error_type']}).", flush=True)
                if completed % 25 == 0 or completed == len(urls):
                    print(f"Pobrano lub sprawdzono {completed}/{len(urls)}, "
                          f"{totals['confirmed_credits']} potwierdzonych kredytów, {len(failures)} błędów.", flush=True)
    finally:
        after = account_balance(key)
        compatible = before and after and all(before[field] == after[field] for field in
                                              ("billingPeriodStart", "billingPeriodEnd"))
        usage = {
            "planned_urls": len(urls), **totals, "account_before": before, "account_after": after,
            "account_delta": before["remainingCredits"] - after["remainingCredits"] if compatible else None,
            "failed": failures,
        }
        write_evidence(output_dir / "firecrawl_runs" / f"{run_id}.json",
                       json.dumps(usage, ensure_ascii=False, indent=2) + "\n")
        print(f"Firecrawl: {totals['attempts']} prób, {totals['confirmed_credits']} potwierdzonych kredytów, "
              f"różnica salda {usage['account_delta']}, błędów {len(failures)}.", flush=True)


def report_pdf_path(row, output_dir, download):
    import requests

    url = row["document_url"]
    digest = hashlib.sha256(canonical_url(url).encode()).hexdigest()
    path = output_dir / "source_pdfs" / f"{digest}.pdf"
    if not path.is_file() and download:
        limit = 50 * 1024 * 1024
        data = bytearray()
        with requests.get(url, timeout=30, stream=True) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=64 * 1024):
                data.extend(chunk)
                if len(data) > limit:
                    raise ValueError("Źródłowy raport PDF przekracza dopuszczalny rozmiar.")
        if not data.startswith(b"%PDF-"):
            raise ValueError("Link do raportu nie zwrócił poprawnego PDF o obsługiwanym rozmiarze.")
        write_bytes(path, data)
    return path


def read_report_pdf(row, path, output_dir):
    import pymupdf

    data = path.read_bytes()
    with pymupdf.open(stream=data, filetype="pdf") as document:
        text = "\n\n".join(page.get_text(sort=True).strip() for page in document).strip()
    row.update(
        source_pdf=str(path.relative_to(output_dir)),
        source_pdf_sha256=hashlib.sha256(data).hexdigest(),
        text=text,
        status="ok" if text else "scan_without_text",
    )
    return row


def supplement_details(row, fallbacks):
    original_links = {field: row.get(field, []) for field in ("attachments", "report_links")}
    matches = [other for other in fallbacks
               if other.get("publication_date") == row["event_date"] and other.get("status") == "ok"]
    primary = next((other for other in matches if other.get("text")), {})
    primary_url = primary.get("source_url") or primary.get("url") or ""
    primary_is_gpw = urlsplit(primary_url).hostname in {"gpw.pl", "www.gpw.pl"}
    if primary and (row.get("status") != "ok" or primary_is_gpw):
        row.update({key: value for key, value in primary.items() if key not in {
            "event_id", "ticker", "report_number", "title", "url", "event_date", "referenced_by",
        }})
        row["text_source_url"] = primary_url
    clock = next((other for other in matches if other.get("publication_time") and other.get("time_source_url")), {})
    if clock:
        for field in ("publication_time", "publication_time_exact", "time_source_url", "time_source_kind"):
            if clock.get(field):
                row[field] = clock[field]
    for field in ("attachments", "report_links"):
        sources = original_links[field] + [source for item in [row, *matches] for source in item.get(field, []) or []]
        if sources:
            row[field] = list({source["url"]: source for source in sources if source.get("url")}.values())
    return row


def extract_reports(rows, cache, output_dir, workers, download_pdfs):
    from espi_detail_parse import parse_detail

    parsed_rows = []
    fallbacks = {}
    for path in (
        output_dir / "verified_clock_overrides.jsonl", output_dir / "archive_matches.jsonl",
        output_dir / "gpw_reports.jsonl", output_dir / "manual_gpw_reports.jsonl",
        output_dir / "gpw_prior_reports.jsonl", output_dir / "issuer_candidate_reports.jsonl",
        output_dir / "pap_mediaroom_reports.jsonl",
    ):
        if path.is_file():
            with path.open(encoding="utf-8-sig") as stream:
                for line in stream:
                    if line.strip():
                        item = json.loads(line)
                        if path.name in {"archive_matches.jsonl", "verified_clock_overrides.jsonl"}:
                            item.update(status="ok", time_source_kind="gpw_espi_archive")
                        fallbacks.setdefault(item["event_id"], []).append(item)
    for row in rows:
        base = {field: row.get(field, "") for field in
                ("event_id", "ticker", "report_number", "title", "url", "event_date", "referenced_by")}
        url = base["url"]
        try:
            payload = cache.get(url) if url else None
            detail = (parse_detail(url, payload, base["ticker"], base["report_number"], base["event_date"])
                      if payload else {"status": "missing_cache"})
        except UncertainFetchError as error:
            detail = {"status": "pending_download", "error": str(error)}
        except ValueError as error:
            detail = {"status": "parse_error", "error": str(error)}
        if detail.get("text", "").strip() and not detail.get("status"):
            detail["status"] = "ok"
        if detail.get("status") == "ok":
            detail["text_source_url"] = url
        detail["catalog_time"] = row.get("event_time", "")
        detail["catalog_time_url"] = row.get("publication_time_source_url") or row.get("time_source_url") or url
        parsed_rows.append({**base, **detail})
    def locate_pdf(row):
        if row.get("document_url") and row.get("status") == "pdf_required":
            try:
                return report_pdf_path(row, output_dir, download_pdfs)
            except (OSError, ValueError, RuntimeError) as error:
                row["pdf_error"] = str(error)
        return None

    with ThreadPoolExecutor(max_workers=workers) as pool:
        paths = list(pool.map(locate_pdf, parsed_rows))
    for row, path in zip(parsed_rows, paths, strict=True):
        if path and path.is_file():
            try:
                read_report_pdf(row, path, output_dir)
            except (OSError, ValueError, RuntimeError) as error:
                row["pdf_error"] = str(error)
        supplement_details(row, fallbacks.get(row["event_id"], []))
        if not row.get("publication_time") and row["catalog_time"] and row.get("status") == "ok":
            row["publication_time"] = row["catalog_time"]
            row["time_source_url"] = row["catalog_time_url"]
            row["time_source_kind"] = "espi_catalog_issuer_listing"
    write_evidence(
        output_dir / "reports.jsonl",
        "\n".join(json.dumps(row, ensure_ascii=False) for row in parsed_rows) + "\n",
    )
    print("Stan treści ESPI", dict(Counter(row.get("status", "unknown") for row in parsed_rows)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--queue", type=Path, default=EVENTS / "espi_review_queue.csv")
    parser.add_argument("--supplementary", type=Path, nargs="*", default=[])
    parser.add_argument("--output-dir", type=Path, default=EVIDENCE)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--batch", action="store_true", help="Użyj standardowego Firecrawl batch_scrape.")
    parser.add_argument("--resume-batch", type=Path, help="Odbierz wyniki z dziennika już wysłanych partii.")
    parser.add_argument("--download-report-pdfs", action="store_true", help="Pobierz źródłowe PDF-y emitentów bez Firecrawl.")
    parser.add_argument("--max-uncached", type=int, default=BUDGET)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--fetch-only", action="store_true")
    mode.add_argument("--parse-only", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.workers <= 50 or args.max_uncached < 0:
        parser.error("--workers musi wynosić 1–50, a --max-uncached musi być nieujemne.")
    rows = read_rows(args.queue, args.supplementary)
    cache = FirecrawlCache(RAW / "firecrawl_cache")
    if not args.parse_only:
        missing = plan_urls(rows, cache, args.output_dir)
        if args.dry_run:
            return
        if len(missing) > args.max_uncached:
            raise SystemExit(f"Plan {len(missing)} URL-i przekracza limit {args.max_uncached}.")
        if args.resume_batch or (missing and args.batch):
            from dotenv import load_dotenv
            from firecrawl_detail_batch import run_batch

            load_dotenv(dotenv_path=DATA_ROOT.parent / ".env", override=False, encoding="utf-8-sig")
            run_batch(missing, cache, get_api_key(), args.output_dir, write_evidence, resume=args.resume_batch)
        else:
            download_pages(missing, cache, args.output_dir, args.workers)
    if not args.fetch_only:
        extract_reports(rows, cache, args.output_dir, args.workers, args.download_report_pdfs)


if __name__ == "__main__":
    sys.stdout.reconfigure(errors="backslashreplace")
    main()
