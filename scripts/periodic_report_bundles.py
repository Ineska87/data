"""Inventory periodic reports and archive the source files required by ESPI events."""

import argparse
import csv
import hashlib
import json
import os
import re
import time
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

import requests

from data_paths import DATA_ROOT, EVENTS, METADATA, RAW


REPORTS = RAW / "reports"
ARCHIVE = REPORTS / "publication_archive"
EVIDENCE = RAW / "espi" / "detail_evidence"
TICKERS = ("PKN", "PGE", "TPE", "ENA", "ZEP", "UNT")
PERIODS = ("Q1", "H1", "Q3", "AR")
WARSAW = ZoneInfo("Europe/Warsaw")
FILE_NAME = re.compile(r"^([A-Z]+)_(20\d{2})_(Q1|H1|Q3|AR)_(.+)\.(pdf|zip|7z|xhtml)$")


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def read_publications(path):
    if path.suffix.lower() != ".jsonl":
        return read_csv(path)
    with path.open(encoding="utf-8-sig") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def replace(source, destination):
    for delay in (0.1, 0.3, 0.8, 1.5):
        try:
            source.replace(destination)
            return
        except PermissionError:
            time.sleep(delay)
    source.replace(destination)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def recognized_file(path, file_type):
    with path.open("rb") as stream:
        prefix = stream.read(4096)
        if file_type == "pdf":
            stream.seek(-min(4096, path.stat().st_size), 2)
            return b"%PDF-" in prefix[:1024] and b"%%EOF" in stream.read()
    if file_type == "zip":
        return zipfile.is_zipfile(path)
    if file_type == "7z":
        return prefix.startswith(b"7z\xbc\xaf\x27\x1c")
    return b"<html" in prefix.lower() and b"http://www.w3.org/1999/xhtml" in prefix.lower()


def inventory():
    present = defaultdict(list)
    invalid = []
    for ticker in TICKERS:
        for path in sorted((REPORTS / ticker).rglob("*")):
            if not path.is_file() or not (match := FILE_NAME.fullmatch(path.name)):
                continue
            name_ticker, year, period, kind, file_type = match.groups()
            if name_ticker != ticker or not re.search(r"sprawozdanie|skonsolidowan|raport|pakiet", kind):
                continue
            if recognized_file(path, file_type):
                present[f"{ticker}-{year}-{period}"].append(path.relative_to(DATA_ROOT).as_posix())
            else:
                invalid.append(path.relative_to(DATA_ROOT).as_posix())
    return present, invalid


def persist_download(response, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    digest = hashlib.sha256()
    try:
        with NamedTemporaryFile("wb", dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                stream.write(chunk)
                digest.update(chunk)
            stream.flush()
            os.fsync(stream.fileno())
        if not recognized_file(temporary, target.suffix[1:]):
            raise ValueError(f"Nieprawidłowy format odpowiedzi dla {target.name}")
        if target.suffix == ".zip":
            with zipfile.ZipFile(temporary) as archive:
                if not archive.namelist() or archive.testzip() is not None:
                    raise ValueError(f"Uszkodzone archiwum dla {target.name}")
        replace(temporary, target)
        return digest.hexdigest()
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def fetch_file(url, target):
    for attempt in range(3):
        try:
            with requests.get(url, timeout=(15, 60), stream=True) as response:
                response.raise_for_status()
                return persist_download(response, target), response.url
        except requests.RequestException as error:
            response = error.response
            if attempt == 2 or (response is not None and response.status_code not in {429, 500, 502, 503, 504}):
                raise
            retry = response.headers.get("Retry-After", "") if response is not None else ""
            time.sleep(int(retry) if retry.isdigit() else 2 ** attempt)


def download_plan(plan, receipt, dry_run):
    desired = json.loads(plan.read_text(encoding="utf-8-sig"))
    history = json.loads(receipt.read_text(encoding="utf-8-sig")) if receipt.is_file() else {}
    entries = history.get("files", {})
    failures = []
    for item in desired:
        match = FILE_NAME.fullmatch(item["filename"])
        if (not match or Path(item["filename"]).name != item["filename"]
                or match[1] not in TICKERS or item["report_id"] != "-".join(match.groups()[:3])):
            raise ValueError(f"Niepoprawna nazwa raportu: {item['filename']}")
        if urlsplit(item["url"]).scheme != "https":
            raise ValueError(f"Źródło raportu musi prowadzić do HTTPS: {item['url']}")
        target = REPORTS / match[1] / item["filename"]
        key = target.relative_to(DATA_ROOT).as_posix()
        if target.is_file():
            if not recognized_file(target, match[5]):
                raise ValueError(f"Plik istnieje, ale wymaga ręcznego sprawdzenia: {key}")
            print(f"Lokalny: {key}")
            if not dry_run and key not in entries:
                with target.open("rb") as stream:
                    checksum = hashlib.file_digest(stream, "sha256").hexdigest()
                entries[key] = {**item, "bytes": target.stat().st_size, "sha256": checksum, "status": "already_local"}
            continue
        print(f"Do pobrania: {key}", flush=True)
        if dry_run:
            continue
        try:
            checksum, resolved = fetch_file(item["url"], target)
        except (OSError, ValueError) as error:
            failures.append(f"{key} ({error})")
            continue
        entries[key] = {
            **item, "resolved_url": resolved, "bytes": target.stat().st_size, "sha256": checksum, "status": "downloaded",
        }
        write_json(receipt, {"firecrawl_credits": 0, "files": entries})
    if not dry_run:
        write_json(receipt, {"firecrawl_credits": 0, "files": entries})
    print("Firecrawl: 0 kredytów.")
    if failures:
        raise SystemExit("Nie pobrano: " + ", ".join(failures))


def local_timestamp(value, day):
    if not value:
        return None
    if "T" in value or " " in value:
        stamp = datetime.fromisoformat(value)
    else:
        stamp = datetime.fromisoformat(f"{day}T{value}")
    return stamp.astimezone(WARSAW) if stamp.tzinfo else stamp.replace(tzinfo=WARSAW)


def event_rows():
    with (EVIDENCE / "investment_candidates.jsonl").open(encoding="utf-8") as stream:
        candidates = {row["event_id"]: row for line in stream if line.strip() and (row := json.loads(line))}
    approved = {
        row["event_id"] for row in read_csv(METADATA / "espi_review.csv") if row["review_status"] == "include"
    }
    source = {row["event_id"]: row for row in read_csv(EVENTS / "espi_review_queue.csv")}
    for event_id in sorted(candidates.keys() | approved):
        row = source[event_id]
        yield {
            "event_id": event_id, "ticker": row["ticker"], "event_date": row["event_date"],
            "event_time": row["publication_time"], "approved": event_id in approved,
        }


def select_basis(event, reports):
    day = date.fromisoformat(event["event_date"])
    event_timestamp = local_timestamp(event["event_time"], day)
    earlier = []
    uncertain = []
    same_day_later = []
    for report in reports:
        published = date.fromisoformat(report["publication_date"])
        timestamp = local_timestamp(report.get("published_at") or report.get("publication_time"), published)
        if published < day or (published == day and timestamp and event_timestamp and timestamp < event_timestamp):
            earlier.append((published, timestamp, report))
        elif published == day and not (timestamp and event_timestamp):
            uncertain.append(report["report_id"])
        elif published == day:
            same_day_later.append(report["report_id"])
    if not earlier:
        return {}, uncertain, same_day_later
    latest_date = max(row[0] for row in earlier)
    same_day = [(stamp, report) for published, stamp, report in earlier if published == latest_date]
    if len(same_day) == 1:
        return same_day[0][1], uncertain, same_day_later
    known = [stamp for stamp, _ in same_day if stamp is not None]
    if len(known) == len(same_day) and len(set(known)) == len(same_day):
        return max(same_day, key=lambda pair: pair[0])[1], uncertain, same_day_later
    return {}, uncertain + [report["report_id"] for _, report in same_day], same_day_later


def build_reference_list(publication_file, output):
    by_issuer = defaultdict(list)
    for row in read_publications(publication_file):
        ticker, _, period = row["report_id"].split("-")
        if ticker in TICKERS and period in PERIODS and row.get("publication_date"):
            by_issuer[ticker].append(row)
    present, invalid = inventory()
    rows = []
    for event in event_rows():
        report, ambiguity, same_day_later = select_basis(event, by_issuer[event["ticker"]])
        report_id = report.get("report_id", "")
        rows.append({
            **event, "reference_report_id": report_id,
            "report_publication_date": report.get("publication_date", ""),
            "report_published_at": report.get("published_at", ""),
            "report_source_url": report.get("source_url", ""),
            "local_files": " | ".join(present.get(report_id, [])),
            "ambiguous_report_ids": " | ".join(ambiguity),
            "same_day_reports_at_or_after_event": " | ".join(same_day_later),
            "status": "publication_order_unconfirmed" if ambiguity else (
                "local" if report_id in present else "missing_package" if report_id else "no_earlier_report"
            ),
        })
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    missing = [f"{ticker}-{year}-{period}" for ticker in TICKERS for year in range(2020, 2026)
               for period in PERIODS if f"{ticker}-{year}-{period}" not in present]
    print(f"Zdarzenia: {len(rows)}. Wynik: {dict(Counter(row['status'] for row in rows))}.")
    print(f"Luki fizyczne 2020–2025: {missing}. Niepoprawne pliki: {invalid}.")
    print("Punkty odniesienia z 2019:", dict(Counter(
        row["reference_report_id"] for row in rows if "-2019-" in row["reference_report_id"]
    )))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--receipt", type=Path, default=REPORTS / "manifest_stage3_bundles.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--publications", type=Path)
    parser.add_argument("--reference-output", type=Path, default=ARCHIVE / "event_periodic_references.csv")
    args = parser.parse_args()
    if not (args.plan or args.publications):
        parser.error("Podaj --plan lub --publications.")
    if args.plan:
        download_plan(args.plan, args.receipt, args.dry_run)
    if args.publications:
        build_reference_list(args.publications, args.reference_output)


if __name__ == "__main__":
    main()
