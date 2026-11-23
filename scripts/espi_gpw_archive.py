"""Match thesis disclosures to the official GPW public archive."""

import argparse
import json
import re
import sys
import time
import unicodedata
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit

import requests
from lxml import html
from lxml.etree import ParserError

from data_paths import DATA_ROOT, EVENTS, METADATA
from espi_identity import classify_report
from espi_investment_evidence import EVIDENCE, csv_rows, jsonl, write_jsonl, write_text


BASE_URL = "https://www.gpw.pl/"
LISTING = urljoin(BASE_URL, "komunikaty")
ISIN_FIXES = {"ZEP": "PLZEPAK00012"}
ROW_STAMP = re.compile(
    r"(?P<date>\d{2}-\d{2}-\d{4})\s+(?P<time>\d{2}:\d{2}:\d{2})\s*\|\s*"
    r"Bieżący\s*\|\s*ESPI(?:\s*\|\s*(?P<number>\d{1,4}\s*/\s*\d{4}(?:\s*/?\s*K\d*)?))?",
    re.I,
)


def issuer_isins():
    payload = json.loads((METADATA / "companies.json").read_text(encoding="utf-8-sig"))
    return {**{row["ticker"]: row["isin"] for row in payload["companies"]}, **ISIN_FIXES}


def normalize_title(value):
    return " ".join(re.findall(r"\w+", unicodedata.normalize("NFKC", value or "").casefold()))


def content_text(element):
    return " ".join(" ".join(element.itertext()).split())


def parse_listing(body, isin):
    page = html.fromstring(body)
    by_id = {}
    for link in page.xpath('//a[contains(@href, "geru_id=")]'):
        card = next((node for node in link.iterancestors("li")), None)
        if card is None:
            continue
        text = content_text(card)
        stamp = ROW_STAMP.search(text)
        if not stamp or f"({isin})" not in text:
            continue
        url = urljoin(BASE_URL, link.attrib["href"])
        parsed = urlsplit(url)
        if parsed.hostname != "www.gpw.pl" or parsed.path != "/komunikat":
            continue
        fields = parse_qs(parsed.query)
        item_id = fields.get("geru_id", [""])[0]
        if not item_id.isdecimal():
            continue
        published = datetime.strptime(stamp["date"], "%d-%m-%Y").date().isoformat()
        title = fields.get("title", [""])[0]
        number = classify_report(stamp["number"] or "", title).report_number
        by_id[item_id] = {
            "archive_url": urljoin(BASE_URL, f"komunikat?geru_id={item_id}"),
            "archive_title": title,
            "publication_date": published,
            "publication_time": stamp["time"][:5],
            "publication_time_exact": stamp["time"],
            "report_number": number,
        }
    return list(by_id.values())


def request_text(url, *, params=None):
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, timeout=(8, 30))
            response.raise_for_status()
            response.encoding = "utf-8"
            return response.text
        except requests.RequestException as exc:
            code = exc.response.status_code if exc.response is not None else None
            if attempt == 2 or (code is not None and code not in {429, 500, 502, 503, 504}):
                raise
            header = exc.response.headers.get("Retry-After", "") if exc.response is not None else ""
            time.sleep(int(header) if header.isdecimal() else 2 ** attempt)


def get_listing(ticker, isin, output_dir, *, requested_date=None, limit=100, offset=0):
    suffix = requested_date or "all"
    path = output_dir / "gpw_archive" / ticker / f"{suffix}_{limit}_{offset}.html"
    if path.is_file():
        return parse_listing(path.read_text(encoding="utf-8"), isin)
    params = {
        "searchText": isin,
        "limit": limit,
        "offset": offset,
        "categoryRaports[]": "ESPI",
        "typeRaports[]": "RB",
    }
    if requested_date:
        params["date"] = requested_date
    body = request_text(LISTING, params=params)
    rows = parse_listing(body, isin)
    if rows or "Brak wpisów" in body:
        write_text(path, body)
    return rows


def get_history(ticker, isin, earliest, output_dir, batch_size):
    rows = []
    urls = set()
    offset = 0
    while True:
        batch = get_listing(ticker, isin, output_dir, limit=batch_size, offset=offset)
        fresh = [row for row in batch if row["archive_url"] not in urls]
        if not fresh:
            break
        rows.extend(fresh)
        urls.update(row["archive_url"] for row in fresh)
        if min(row["publication_date"] for row in fresh) < earliest:
            break
        offset += batch_size
        time.sleep(0.2)
    return rows


def match_date(row):
    return row.get("publication_date") or row.get("event_date") or row.get("data_pub") or ""


def match_candidates(subject, matches):
    number = classify_report(subject.get("report_number") or "").report_number
    related = [record for record in matches if (not number or record["report_number"] == number)]
    title = normalize_title(subject.get("title") or subject.get("tytul"))
    if number and len(related) == 1:
        return {**related[0], "match_rule": "issuer_date_number"}
    exact = [record for record in related if title and normalize_title(record["archive_title"]) == title]
    if exact and len({item["publication_time_exact"] for item in exact}) == 1:
        return {**min(exact, key=lambda item: item["archive_url"]), "match_rule": "issuer_date_number_title",
                "archive_aliases": [item["archive_url"] for item in exact]}
    if not related and number and title:
        ordinal = number.split("/")[0]
        aliases = [record for record in matches if normalize_title(record["archive_title"]) == title
                   and record["report_number"].split("/")[0] == ordinal]
        if len(aliases) == 1:
            return {**aliases[0], "match_rule": "issuer_date_title_same_ordinal"}
    return None


def adjacent_day(subject, observations):
    number = classify_report(subject.get("report_number") or "").report_number
    title = normalize_title(subject.get("title") or subject.get("tytul"))
    if not number or not title:
        return None
    matches = [row for row in observations if row["report_number"] == number
               and normalize_title(row["archive_title"]) == title]
    if len(matches) != 1:
        return None
    original = date.fromisoformat(match_date(subject))
    observed = date.fromisoformat(matches[0]["publication_date"])
    return {**matches[0], "match_rule": "issuer_adjacent_day_number_title"} if abs((observed - original).days) == 1 else None


def match_ticker(ticker, isin, queue, output_dir, batch_size, date_fallback):
    days = []
    for row in queue:
        try:
            days.append(date.fromisoformat(match_date(row)).isoformat())
        except ValueError:
            continue
    if not days:
        return []
    historical = get_history(ticker, isin, min(days), output_dir, batch_size)
    by_date = defaultdict(list)
    for item in historical:
        by_date[item["publication_date"]].append(item)
    first_attempted = set()
    matched = []
    for row in queue:
        day = match_date(row)
        item = match_candidates(row, by_date[day])
        if item is None and date_fallback and day in days and day not in first_attempted:
            first_attempted.add(day)
            dated = get_listing(ticker, isin, output_dir, requested_date=day, limit=25)
            previous = {x["archive_url"] for x in by_date[day]}
            by_date[day].extend(entry for entry in dated if entry["publication_date"] == day and entry["archive_url"] not in previous)
            item = match_candidates(row, by_date[day])
        if item is None and day in days and not by_date[day]:
            item = adjacent_day(row, historical)
        if item:
            matched.append({**item, "event_id": row["event_id"], "ticker": ticker,
                            "event_date": day, "reported_number": row.get("report_number") or "",
                            "time_source_url": item["archive_url"]})
    print(f"GPW {ticker}: {len(matched)}/{len(queue)} dopasowań, {len(historical)} wpisów indeksu.", flush=True)
    return matched


def parse_archive_detail(body, item):
    scraper = str(DATA_ROOT / "ir-scraper" / "scripts")
    if scraper not in sys.path:
        sys.path.insert(0, scraper)
    from espi_detail_parse import PDF_ONLY, extract_references, parse_detail

    url = item["archive_url"]
    page = html.fromstring(body)
    metadata = page.xpath('//span[contains(concat(" ", normalize-space(@class), " "), " date ")]')
    stamp = next((match for tag in metadata if (match := ROW_STAMP.search(content_text(tag)))), None)
    record = {**item, "source_url": url, "text": "", "attachments": [], "report_links": []}
    if not stamp or stamp["time"] != item["publication_time_exact"]:
        return {**record, "status": "unrecognized_gpw"}
    actual_date = datetime.strptime(stamp["date"], "%d-%m-%Y").date().isoformat()
    if actual_date != item["publication_date"]:
        return {**record, "status": "unrecognized_gpw"}
    parsed = parse_detail(url, {"html": body}, item["ticker"], item["report_number"], actual_date)
    content_marker = page.xpath(
        '//div[contains(concat(" ", normalize-space(@class), " "), " report-data ")]'
        '//tr[./td[normalize-space(.)="Treść raportu:" or normalize-space(.)="Treść raportu"]]'
    )
    if content_marker:
        paragraphs = []
        for section in content_marker[0].itersiblings():
            text = content_text(section)
            if re.match(r"^(?:Załączniki|Plik Opis|PODPISY|MESSAGE\b)", text, re.IGNORECASE):
                break
            if text:
                paragraphs.append(text)
        original = "\n\n".join(paragraphs)
        if len(original) >= 40 and parsed["status"] != "pdf_required" and not (
            parsed["attachments"] and len(original) < 300 and PDF_ONLY.search(original)
        ):
            parsed.update(
                text=original, status="ok",
                reference_numbers=extract_references(original, item.get("reported_number") or item["report_number"]),
            )
    return {**record, **parsed, "publication_date": actual_date, "publication_date_source": "source",
            "publication_time": item["publication_time"], "time_source_url": url}


def get_archive_detail(item, output_dir):
    archive_id = parse_qs(urlsplit(item["archive_url"]).query)["geru_id"][0]
    raw = output_dir / "gpw_archive" / "reports" / archive_id[:2] / f"{archive_id}.html"
    try:
        if raw.is_file():
            body = raw.read_text(encoding="utf-8")
        else:
            body = request_text(item["archive_url"])
            write_text(raw, body)
        record = parse_archive_detail(body, item)
        if record["status"] == "pdf_required" and record.get("document_url"):
            from scrape_espi_details import read_report_pdf, report_pdf_path

            try:
                path = report_pdf_path(record, output_dir, download=True)
                read_report_pdf(record, path, output_dir)
            except (requests.RequestException, OSError, ValueError, RuntimeError) as exc:
                record["pdf_error"] = str(exc)
        return record
    except (requests.RequestException, OSError, ValueError, ParserError) as exc:
        return {**item, "source_url": item["archive_url"], "status": "archive_error", "error": str(exc)}


def write_bodies(matches, output_dir, details_path, selected, limit, reparse, body_output=None):
    detailed = {row["event_id"] for row in jsonl(details_path)
                if row.get("status") == "ok" and row.get("text")} if details_path and details_path.is_file() else set()
    path = body_output or output_dir / "gpw_reports.jsonl"
    old = {row["event_id"]: row for row in jsonl(path)} if path.is_file() else {}
    pending = [row for row in matches if row["event_id"] not in detailed
               and (not selected or row["event_id"] in selected)
               and (reparse or old.get(row["event_id"], {}).get("status") != "ok")][:limit]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for index, item in enumerate(pool.map(lambda row: get_archive_detail(row, output_dir), pending), 1):
            old[item["event_id"]] = item
            if index % 25 == 0:
                write_jsonl(path, old.values())
                print(f"GPW szczegóły {index}/{len(pending)}.", flush=True)
    write_jsonl(path, old.values())
    print(f"GPW treści: {sum(row.get('status') == 'ok' for row in old.values())}/{len(old)}.", flush=True)


def include_verified_clocks(matches, output_dir):
    checked = output_dir / "verified_clock_overrides.jsonl"
    if not checked.is_file():
        return matches
    all_records = {row["event_id"]: row for row in matches}
    for row in jsonl(checked):
        if row.get("archive_url") and row.get("publication_time_exact"):
            all_records[row["event_id"]] = row
    return list(all_records.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=EVIDENCE)
    parser.add_argument("--extra", type=Path, help="Additional earlier disclosures in JSONL")
    parser.add_argument("--batch-size", default=250, type=int)
    parser.add_argument("--date-fallback", action="store_true", help="Query the exact date for missing history matches")
    parser.add_argument("--fetch-bodies", action="store_true", help="Download details from the corresponding official GPW links")
    parser.add_argument("--details", type=Path, help="Skip entries with a complete body already recorded in this JSONL")
    parser.add_argument("--body-id", action="append", help="Restrict retrieval to selected event IDs")
    parser.add_argument("--body-output", type=Path, help="Write matched body records to this JSONL instead")
    parser.add_argument("--body-limit", type=int, help="Maximum number of archive details to retrieve this run")
    parser.add_argument("--reparse", action="store_true", help="Reparse existing GPW detail snapshots")
    parser.add_argument("--use-existing-matches", action="store_true", help="Use the locally generated index verbatim")
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    match_index = args.output_dir / "archive_matches.jsonl"
    if args.use_existing_matches:
        if not args.fetch_bodies:
            parser.error("--use-existing-matches requires --fetch-bodies")
        matches = include_verified_clocks(jsonl(match_index), args.output_dir)
        write_bodies(matches, args.output_dir, args.details, set(args.body_id or ()),
                     args.body_limit, args.reparse, args.body_output)
        return
    all_rows = csv_rows(EVENTS / "espi_review_queue.csv")
    if args.extra:
        seen = {row["event_id"] for row in all_rows}
        all_rows.extend(row for row in jsonl(args.extra) if row["event_id"] not in seen)
    by_ticker = defaultdict(list)
    for row in all_rows:
        by_ticker[row["ticker"]].append(row)
    isins = issuer_isins()
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks = [pool.submit(
            match_ticker, ticker, isins[ticker], rows, args.output_dir, args.batch_size, args.date_fallback,
        ) for ticker, rows in by_ticker.items() if ticker in isins]
        matches = [row for task in tasks for row in task.result()]
    write_jsonl(match_index, matches)
    print(f"GPW razem: {len(matches)}/{len(all_rows)} dopasowań.", flush=True)
    if args.fetch_bodies:
        write_bodies(include_verified_clocks(matches, args.output_dir), args.output_dir, args.details, set(args.body_id or ()),
                     args.body_limit, args.reparse, args.body_output)


if __name__ == "__main__":
    main()
