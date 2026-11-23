"""Find investment reports and retain the disclosure sources used for review."""

import argparse
import csv
import hashlib
import json
import re
import time
import unicodedata
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit

import requests
from urllib.request import Request, urlopen

from data_paths import DATA_ROOT, EVENTS, METADATA, RAW
from espi_identity import classify_report, url_identity


EVIDENCE = RAW / "espi" / "detail_evidence"
CASE_NUMBERS = {"27/2021", "30/2023", "2/2024", "56/2024", "64/2024", "12/2025"}

PROJECT = (
    r"\binwestycj\w*|\binwestycyjn\w*|\bcapex\b|\bolefin\w*|\bnowa chemi\w*|"
    r"\b(?:farm\w*|park\w*) (?:wiatrow\w*|fotowoltaiczn\w*|solarn\w*)|"
    r"\b(?:budow\w*|rozbudow\w*|przebudow\w*|modernizacj\w*) (?:bloku|elektrowni|ciepłowni|instalacji|"
    r"sieci|przyłącza|magazynu|rafinerii|zakładu|kompleksu|terminalu|gazociągu|kopalni)|"
    r"\b(?:projek\w*|program\w*) (?:budow\w*|rozbudow\w*|przebudow\w*|modernizacj\w*|"
    r"offshore|onshore|wiatrow\w*|fotowoltaiczn\w*|jądrow\w*)"
)
ASSET = (
    r"\b(?:aktyw\w*|środk\w* trwał\w*) w budowie\b|\b(?:nieukończon\w*|niedokończon\w*) inwestycj\w*|"
    r"\bnakład\w* (?:poniesion\w* )?na budowę\b"
)
RULES = {
    "start": (
        r"\b(?:rozpoczę\w*|rusz\w*|start\w*|zatwierdz\w*|zaakceptow\w*)|"
        r"\b(?:decyzj\w*|decyduj\w*|zdecydow\w*|zgod\w*) (?:o |na |w sprawie )?(?:budow\w*|rozbudow\w*|"
        r"modernizacj\w*|rozpoczę\w*|realizacj\w*|przystąp\w*|uruchom\w*)|"
        r"\b(?:rozpocz\w*|przystąpi\w*) (?:do )?(?:realizacj\w*|budow\w*|rozbudow\w*|"
        r"modernizacj\w*|prac\w*)|\b(?:ostateczn\w* decyzj\w* inwestycyjn\w*|fid)\b",
        PROJECT,
    ),
    "revision": (
        r"\b(?:zmian\w*|zmien\w*|aktualiz\w*|rewizj\w*|zwiększ\w*|obniż\w*|wzrost\w*|przekrocz\w*|"
        r"przesuni\w*|opóźn\w*|odrocze\w*|wydłuż\w*|przedłuż\w*)",
        r"\b(?:capex|harmonogram\w*|budżet\w*|nakład\w* inwestycyjn\w*|koszt\w* (?:całkowit\w* )?"
        r"(?:inwestycj\w*|projektu|budowy|realizacji)|(?:termin\w*|dat\w*) (?:zakończeni\w*|"
        r"uruchomieni\w*|oddani\w*|realizacji)|zakres\w* (?:projektu|inwestycji))\b",
    ),
    "execution_contract": (
        r"\b(?:zawar\w*|zawier\w*|podpisa\w*|podpisy\w*|wybór|wybra\w*|udzieli\w*|udzielen\w*|"
        r"przyzna\w*|aneks\w*)",
        r"\b(?:umow\w*|kontrakt\w*|zamówieni\w*) (?:epc\w*|na (?:budow\w*|rozbudow\w*|przebudow\w*|"
        r"modernizacj\w*|realizacj\w*|zaprojektowani\w*|wykonani\w*)|wykonawcz\w*|inwestycyjn\w*)|"
        r"\b(?:generaln\w* wykonawc\w*|formu[łl]\w* epc\w*|kontrakt\w* epc\w*)",
    ),
    "impairment_under_construction": (
        r"\b(?:odpis\w* aktualiz\w*|utrat\w* wartości|test\w* na utrat\w* wartości)\b",
        ASSET + r"|\bolefin\w*|\bnowa chemi\w*|\belektrowni\w* ostrołęk\w*",
    ),
    "suspension": (
        r"\b(?:wstrzym\w*|zaniech\w*|zawiesz\w*|zawiesze\w*|zatrzyma\w*|przerwa\w*|"
        r"rezygn\w*|odstąp\w*|definitywn\w* zakończ\w*|niekontynu\w*|nierentown\w*)",
        PROJECT,
    ),
}
RULES = {name: tuple(re.compile(source, re.I) for source in sources) for name, sources in RULES.items()}
PROJECT_RE = re.compile(PROJECT, re.I)
CONSTRUCTION_AMENDMENT = re.compile(
    r"\b(?:zmieniają\w*|zmian\w*|aneks\w*)(?:\s+\w+){0,3}\s+(?:umow\w*|kontrakt\w*)"
    r"\s+(?:na|dotycząc\w*)(?:\s+\w+){0,3}\s+(?:budow\w*|rozbudow\w*|"
    r"przebudow\w*|wykonani\w*|modernizacj\w*)",
    re.I,
)
REVISED_ESTIMATE = re.compile(
    r"\b(?:aktualn\w*|now\w*|zrewidowan\w*)\s+(?:szacun\w*|prognoz\w*|koszt\w*|"
    r"harmonogram\w*|termin\w*)(?=[^!?]{0,130}\b(?:20\d{2}|\d+[,.]?\d*\s*(?:mln|mld|PLN|zł))\b)",
    re.I,
)
REPORTING_SCHEDULE = re.compile(
    r"\b(?:harmonogram\w*|termin\w*)\s+(?:publikac\w*|przekaz\w*|waln\w* zgromadzen\w*)",
    re.I,
)
REPORT_REFERENCE = re.compile(
    r"\b(?:raport\w*\s+(?:bieżąc\w*|espi)|raport\w*\s+nr\.?|patrz\s+także)\s*"
    r"(?:(?:ESPI|spółk\w*|emitent\w*)\s+)?(?:nr\.?\s*)?(?=\d\s*[/\d])",
    re.I,
)
REFERENCE_NUMBER = re.compile(r"\b\d{1,4}\s*/\s*(?:19|20)\d{2}(?:\s*/\s*K\d*)?\b", re.I)
NUMBER_SEGMENT = re.compile(
    r"(?:\s+(?:i|oraz|a także|nr)\s+|[,;]\s*|\s+z\s+(?:dnia\s+)?\d{1,2}[ .-])",
    re.I,
)


def jsonl(path):
    with path.open(encoding="utf-8-sig") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def replace_file(source, destination):
    for delay in (0.025, 0.05, 0.1, 0.2, 0.4):
        try:
            source.replace(destination)
            return
        except PermissionError:
            time.sleep(delay)
    source.replace(destination)


def write_text(path, contents):
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        temp = Path(stream.name)
        stream.write(contents)
    try:
        replace_file(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def write_jsonl(path, rows):
    write_text(path, "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def normalize(text):
    return " ".join(unicodedata.normalize("NFKC", text or "").split())


def distinct(matches):
    return list(dict.fromkeys(matches))


def screen(text):
    """Return the first locally grounded evidence for each candidate criterion."""
    text = normalize(text)
    found = {}
    for category, (action_pattern, project_pattern) in RULES.items():
        for action in action_pattern.finditer(text):
            context_start = max(0, action.start() - 105)
            context_end = min(len(text), action.end() + 165)
            context = text[context_start:context_end]
            if category == "revision" and REPORTING_SCHEDULE.search(context) and not PROJECT_RE.search(context):
                continue
            if project_pattern.search(context):
                found[category] = context
                break
    if "revision" not in found and (amendment := CONSTRUCTION_AMENDMENT.search(text)):
        if revised := REVISED_ESTIMATE.search(text, amendment.end()):
            found["revision"] = (
                text[max(0, amendment.start() - 65):amendment.end() + 80]
                + " […] " + text[revised.start():revised.end() + 125]
            )
    return found


def review_candidate(row):
    forced = row["ticker"] == "PKN" and row.get("report_number") in CASE_NUMBERS
    body_available = row.get("status") == "ok" and bool(normalize(row.get("text")))
    title = screen(row.get("title"))
    body = screen(row.get("text")) if body_available else {}
    return {
        "event_id": row["event_id"],
        "ticker": row["ticker"],
        "report_number": row.get("report_number", ""),
        "title": row.get("title", ""),
        "url": row.get("url", ""),
        "event_date": row.get("event_date", ""),
        "publication_date": row.get("publication_date", ""),
        "publication_time": row.get("publication_time", ""),
        "time_source_url": row.get("time_source_url", ""),
        "detail_status": row.get("status", ""),
        "mandatory_olefiny": forced,
        "has_full_text": body_available,
        "title_evidence": title,
        "full_text_evidence": body,
        "detected_only_in_full_text": bool(body and not title),
    }


def past_date(row):
    return row.get("publication_date") or row.get("event_date") or row.get("data_pub") or ""


def disclosure_number(value):
    return classify_report(value or "").report_number


def earlier(source, target):
    first, second = past_date(source), past_date(target)
    if not first or not second:
        return False
    if second != first:
        return second < first
    a, b = (disclosure_number(row.get("report_number")).split("/") for row in (source, target))
    return len(a) >= 2 and len(b) >= 2 and a[1] == b[1] and int(b[0]) < int(a[0])


def report_reference_numbers(text, *, project_related):
    for mention in REPORT_REFERENCE.finditer(text):
        tail = text[mention.end():mention.end() + 230]
        prefix_end = mention.start() - 160
        evidence = text[max(0, prefix_end):mention.end() + min(180, len(tail))]
        if not project_related and not PROJECT_RE.search(evidence):
            continue
        previous = 0
        for number in REFERENCE_NUMBER.finditer(tail):
            separator = tail[previous:number.start()]
            if previous == 0 and separator.strip():
                break
            if previous and not NUMBER_SEGMENT.match(separator):
                break
            if len(separator) > 65:
                break
            yield disclosure_number(number[0]), evidence
            previous = number.end()


def catalog_reference_set(source, candidate, by_number, by_url, manual):
    source_url = source.get("url") or ""
    source_number = disclosure_number(source.get("report_number"))
    source_year = past_date(source)[:4]
    ticker = source["ticker"]
    linked = {}
    unresolved = {}
    for link in source.get("report_links") or ():
        item = link if isinstance(link, dict) else {"url": link}
        url = item.get("url") or ""
        target = by_url.get((ticker, url_identity(url))) if url else None
        if target and earlier(source, target):
            linked[target["event_id"]] = (target, "link w treści raportu", item.get("title") or url)

    project_related = candidate["mandatory_olefiny"]
    body = normalize(source.get("text")) if candidate["has_full_text"] else ""
    for number, evidence in report_reference_numbers(body, project_related=project_related):
        if not number or number == source_number:
            continue
        matches = [row for row in by_number[(ticker, number)] if earlier(source, row)]
        if len(matches) == 1:
            target = matches[0]
            linked.setdefault(target["event_id"], (target, "numer raportu przywołany w treści", evidence))
        elif (len(matches) > 1
              or (source_year and number.split("/")[1] <= source_year and not by_number[(ticker, number)])):
            unresolved[number] = evidence

    if (url := manual.get("previous_plan_url")) and url_identity(url) != url_identity(source_url):
        target = by_url.get((ticker, url_identity(url))) or {
            "event_id": f"{ticker}_reference_{hashlib.sha256(url.encode()).hexdigest()[:16]}",
            "ticker": ticker, "report_number": "", "tytul": "", "url": url,
            "data_pub": manual.get("previous_plan_date"),
        }
        linked[target["event_id"]] = (target, "plan bazowy z rejestru ręcznej weryfikacji", url)
    return linked, unresolved


def references(candidates, details, catalog, reviews):
    by_number = defaultdict(list)
    by_url = {}
    for row in catalog:
        if row.get("catalog_issue"):
            continue
        if number := disclosure_number(row["report_number"]):
            by_number[(row["ticker"], number)].append(row)
        if row["url"]:
            by_url[(row["ticker"], url_identity(row["url"]))] = row

    plans = {}
    missing = []
    for candidate in candidates:
        source = details[candidate["event_id"]]
        linked, unresolved = catalog_reference_set(
            source, candidate, by_number, by_url, reviews.get(source["event_id"], {}),
        )
        for key, (target, kind, excerpt) in linked.items():
            plan = plans.setdefault(key, {
                "event_id": key, "ticker": source["ticker"], "report_number": target.get("report_number", ""),
                "title": target.get("tytul", ""), "url": target["url"], "event_date": past_date(target),
                "referenced_by": [], "evidence": [],
            })
            plan["referenced_by"].append(source["event_id"])
            plan["evidence"].append({"event_id": source["event_id"], "kind": kind, "excerpt": excerpt})
        for number, excerpt in unresolved.items():
            missing.append({"event_id": source["event_id"], "ticker": source["ticker"],
                            "report_number": number, "evidence": excerpt})
    return list(plans.values()), missing


def existing_pdfs(details=(), evidence_dir=EVIDENCE):
    """Reuse a local PDF only where its source URL is recorded."""
    sources = {}
    for manifest in sorted((RAW / "reports").rglob("*manifest*.json")):
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        lists = payload.values() if isinstance(payload, dict) else (payload,)
        for items in lists:
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                url = item.get("url") or item.get("source_url")
                filename = item.get("file") or item.get("path") or item.get("local_file") or item.get("filename")
                if not isinstance(url, str) or not isinstance(filename, str):
                    continue
                for candidate in (manifest.parent / filename, DATA_ROOT / filename, RAW / filename):
                    path = candidate.resolve()
                    if path.is_relative_to(RAW) and path.suffix.lower() == ".pdf" and path.is_file():
                        if valid_pdf(path):
                            sources.setdefault(url_identity(url), path)
                        break
    for row in details:
        if row.get("source_pdf") and row.get("document_url"):
            path = (evidence_dir / row["source_pdf"]).resolve()
            if path.is_relative_to(RAW) and path.is_file() and valid_pdf(path):
                sources.setdefault(url_identity(row["document_url"]), path)
    return sources


def valid_pdf(path):
    with path.open("rb") as stream:
        if b"%PDF-" not in stream.read(1024):
            return False
        stream.seek(-min(2048, path.stat().st_size), 2)
        return b"%%EOF" in stream.read()


def attachment_inventory(candidates, details):
    assets = {}
    for candidate in candidates:
        row = details[candidate["event_id"]]
        for raw_link in row.get("attachments") or ():
            item = raw_link if isinstance(raw_link, dict) else {"url": raw_link}
            url = item.get("url") or ""
            parsed = urlsplit(url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                continue
            key = url_identity(url)
            asset = assets.setdefault(key, {"url": url, "titles": [], "event_ids": []})
            if title := item.get("title"):
                if title not in asset["titles"]:
                    asset["titles"].append(title)
            if row["event_id"] not in asset["event_ids"]:
                asset["event_ids"].append(row["event_id"])
    return assets


def retrieve_pdf(url, destination):
    temporary = None
    try:
        with requests.get(url, timeout=(10, 35), stream=True) as response:
            response.raise_for_status()
            chunks = response.iter_content(chunk_size=65536)
            first = next(chunks, b"")
            if b"%PDF-" not in first[:1024]:
                raise ValueError(f"odpowiedź nie jest PDF ({response.headers.get('Content-Type', '')})")
            destination.parent.mkdir(parents=True, exist_ok=True)
            with NamedTemporaryFile("wb", dir=destination.parent, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(first)
                for chunk in chunks:
                    stream.write(chunk)
            if not valid_pdf(temporary):
                raise ValueError("niepełny PDF")
            replace_file(temporary, destination)
            return response.url
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def process_attachment(task, output, local, download):
    key, asset = task
    digest = hashlib.sha256(key.encode()).hexdigest()
    target = output / "attachments" / digest[:2] / f"{digest}.pdf"
    if target.is_file() and valid_pdf(target):
        status, path = "cached", target
    elif key in local:
        status, path = "reused_existing", local[key]
    elif download:
        for attempt in range(3):
            try:
                final = retrieve_pdf(asset["url"], target)
                status, path = "downloaded", target
                asset["resolved_url"] = final
                break
            except (requests.RequestException, OSError, ValueError) as exc:
                response = exc.response if isinstance(exc, requests.RequestException) else None
                repeat = (isinstance(exc, (requests.ConnectionError, requests.Timeout))
                          or response is not None and response.status_code in {429, 500, 502, 503, 504})
                if not repeat or attempt == 2:
                    return {**asset, "status": "failed", "error": str(exc)}
                header = response.headers.get("Retry-After", "") if response is not None else ""
                time.sleep(float(header) if header.isdecimal() else 2 ** (attempt + 1))
    else:
        return {**asset, "status": "planned"}
    file_display = path.relative_to(DATA_ROOT).as_posix() if path.is_relative_to(DATA_ROOT) else str(path)
    return {**asset, "status": status, "file": file_display, "bytes": path.stat().st_size}


def summarize(all_rows, candidates, publications, plans, pending, unresolved):
    good_rows = [row for row in all_rows if row["has_full_text"]]
    return {
        "screened": len(all_rows),
        "full_text_available": len(good_rows),
        "full_text_unavailable": len(all_rows) - len(good_rows),
        "title_candidates_all": sum(bool(row["title_evidence"]) for row in all_rows),
        "title_candidates_comparable": sum(bool(row["title_evidence"]) for row in good_rows),
        "full_text_candidates": sum(bool(row["full_text_evidence"]) for row in good_rows),
        "additional_full_text_candidates": sum(row["detected_only_in_full_text"] for row in good_rows),
        "union_candidates": len(candidates),
        "mandatory_olefiny_in_queue": sum(row["mandatory_olefiny"] for row in candidates),
        "candidate_verified_time": sum(bool(row["publication_time"] and row["time_source_url"]) for row in candidates),
        "unique_referenced_disclosures": len(plans),
        "prior_reports_to_retrieve": len(pending),
        "unresolved_reference_mentions": len(unresolved),
        "attachments_by_status": dict(Counter(item["status"] for item in publications)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--details", type=Path, default=EVIDENCE / "reports.jsonl")
    parser.add_argument("--output-dir", type=Path, default=EVIDENCE)
    parser.add_argument("--download", action="store_true", help="Download PDF attachments directly from their source")
    args = parser.parse_args()
    input_rows = jsonl(args.details)
    queue = {row["event_id"] for row in csv_rows(EVENTS / "espi_review_queue.csv")}
    details = {row["event_id"]: row for row in input_rows}
    if len(details) != len(input_rows):
        raise ValueError("Pojawiły się powtórzone event_id w indeksie treści ESPI.")
    if missing_queue := queue - details.keys():
        raise ValueError(f"Brak wierszy indeksu dla {len(missing_queue)} komunikatów z kolejki ESPI.")
    all_rows = [review_candidate(row) for row in input_rows if row["event_id"] in queue]
    candidates = [row for row in all_rows if row["title_evidence"] or row["full_text_evidence"] or row["mandatory_olefiny"]]
    plans, unresolved = references(
        candidates, details, csv_rows(EVENTS / "espi_catalog.csv"),
        {row["event_id"]: row for row in csv_rows(METADATA / "espi_review.csv")},
    )
    pending = [row for row in plans if row["url"] and details.get(row["event_id"], {}).get("status") != "ok"]
    attachments = attachment_inventory(candidates, details)
    local = existing_pdfs(input_rows, args.details.parent)
    write_jsonl(args.output_dir / "investment_candidates.jsonl", candidates)
    write_jsonl(args.output_dir / "prior_reports.jsonl", pending)
    write_jsonl(args.output_dir / "prior_report_links.jsonl", plans)
    write_jsonl(args.output_dir / "unresolved_references.jsonl", unresolved)
    with ThreadPoolExecutor(max_workers=5) as pool:
        publications = list(pool.map(
            lambda task: process_attachment(task, args.output_dir, local, args.download), attachments.items(),
        ))
    write_jsonl(args.output_dir / "attachments.jsonl", publications)
    summary = summarize(all_rows, candidates, publications, plans, pending, unresolved)
    write_text(args.output_dir / "investment_evidence_summary.json", json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
