"""Archive and classify the official GPW publication records for financial reports."""

import argparse
import csv
import io
import json
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit
from zoneinfo import ZoneInfo

from lxml import html

from data_paths import RAW
from espi_gpw_archive import BASE_URL, LISTING, content_text, issuer_isins, request_text
from espi_investment_evidence import write_jsonl, write_text


ARCHIVE = RAW / "reports" / "publication_archive"
TICKERS = ("PKN", "PGE", "TPE", "ENA", "ZEP", "UNT", "JSW")
STAMP = re.compile(
    r"(?P<date>\d{2}-\d{2}-\d{4})\s+(?P<time>\d{2}:\d{2}:\d{2})\s*\|\s*"
    r"(?:(?P<category>Kwartalny|Półroczny|Roczny|Okresowy|Bieżący)\s*\|\s*)?ESPI"
    r"(?:\s*\|\s*(?P<ordinal>\d*)\s*/\s*(?P<year>20\d{2}))?",
    re.I,
)
DETAIL_STAMP = re.compile(
    r"(?P<date>\d{2}-\d{2}-\d{4})\s+(?P<time>\d{2}:\d{2}:\d{2})\s*\|"
    r"(?:\s*[^|]+\|)?\s*ESPI\b",
    re.I,
)
FORM = re.compile(
    r"^(?P<prefix>Skonsolidowany\s+)?Raport\s+(?P<category>kwartalny|półroczny|roczny)"
    r"(?:\s+(?P<suffix>skonsolidowany))?\s+(?P<code>(?:SA-)?[PQRS]{1,4})\b",
    re.I,
)
PERIOD_END = re.compile(r"(?:obejmując\w*\s+okres\s+od|okres\s+od)\s+20\d{2}-\d{2}-\d{2}\s+do\s+(20\d{2})-(\d{2})-\d{2}", re.I)
QUARTER = re.compile(r"(?:^|\s)([1-4])\s+kwartał\s+roku\s+obrotowego\s+(20\d{2})", re.I)
YEAR = re.compile(r"\b(?:za|za półrocze)\s+rok(?:u)?\s+obrotow\w*\s+(20\d{2})\b", re.I)
TIMEZONE = ZoneInfo("Europe/Warsaw")


def cache_page(path, url, params=None):
    if path.is_file():
        return path.read_text(encoding="utf-8")
    body = request_text(url, params=params)
    write_text(path, body)
    return body


def list_filings(ticker, isin, start, archive, limit=250):
    observed = set()
    filings = {}
    offset = 0
    while True:
        params = {"searchText": isin, "limit": limit, "offset": offset, "categoryRaports[]": "ESPI"}
        path = archive / "gpw" / "listings" / ticker / f"{offset}_{limit}.html"
        body = cache_page(path, LISTING, params)
        page = html.fromstring(body)
        ids = {}
        days = []
        for link in page.xpath('//a[contains(@href, "geru_id=")]'):
            card = next((node for node in link.iterancestors("li")), None)
            if card is None:
                continue
            visible = content_text(card)
            if f"({isin})" not in visible:
                continue
            day_match = re.match(r"\d{2}-\d{2}-\d{4}", visible)
            if not day_match:
                continue
            day = datetime.strptime(day_match[0], "%d-%m-%Y").date()
            url = urljoin(BASE_URL, link.get("href"))
            query = parse_qs(urlsplit(url).query)
            geru_id = query.get("geru_id", [""])[0]
            if not geru_id.isdecimal():
                continue
            ids[geru_id] = day
            stamp = STAMP.match(visible)
            if not stamp:
                continue
            if stamp["category"] == "Bieżący" and (stamp["ordinal"] or not stamp["year"] or query.get("title")):
                continue
            filed = datetime.strptime(f"{stamp['date']} {stamp['time']}", "%d-%m-%Y %H:%M:%S")
            filed = filed.replace(tzinfo=TIMEZONE)
            filings[geru_id] = {
                "ticker": ticker, "isin": isin, "gpw_id": geru_id, "listing_category": stamp["category"] or "",
                "listing_fiscal_year": stamp["year"] or "", "publication_date": filed.date().isoformat(),
                "publication_time": filed.time().isoformat(), "published_at": filed.isoformat(),
                "listed_title": query.get("title", [""])[0],
                "source_url": urljoin(BASE_URL, f"komunikat?geru_id={geru_id}"),
                "listing_url": LISTING + "?" + urlencode(params),
            }
        for geru_id, day in ids.items():
            if geru_id not in observed:
                days.append(day)
        if not days or min(days).year < start:
            break
        observed.update(ids)
        offset += limit
    print(f"GPW {ticker}: {len(filings)} okresowych pozycji; strony do offsetu {offset}.", flush=True)
    return [r for r in filings.values() if int(r["publication_date"][:4]) >= start]


def attachments(section, url):
    results = {}
    for link in section.xpath('.//a[contains(@href,"attachment/")]'):
        href = urljoin(url, link.get("href"))
        if urlsplit(href).netloc == urlsplit(BASE_URL).netloc:
            results.setdefault(href, content_text(link))
    return [{"url": url, "name": title} for url, title in results.items()]


def parse_detail(filing, body):
    page = html.fromstring(body)
    sections = page.xpath('//div[contains(concat(" ",normalize-space(@class)," ")," report-data ")]')
    if not sections:
        return {**filing, "status": "no_detail"}
    section = sections[0]
    detail_stamp = next((DETAIL_STAMP.search(content_text(node)) for node in page.xpath(
        '//span[contains(concat(" ",normalize-space(@class)," ")," date ")]')
                         if DETAIL_STAMP.search(content_text(node))), None)
    if (
        not detail_stamp
        or detail_stamp["time"] != filing["publication_time"]
        or datetime.strptime(detail_stamp["date"], "%d-%m-%Y").date().isoformat() != filing["publication_date"]
    ):
        return {**filing, "status": "timestamp_mismatch"}
    rows = section.xpath(".//tr[not(.//tr)]")
    lines = [content_text(node) for node in rows]
    year = filing["listing_fiscal_year"]
    heading = next((m for line in lines[:90] if (m := FORM.match(line))), None)
    form = heading["code"].upper() if heading else ""
    category = heading["category"].casefold() if heading else ""
    quarter = next((m for line in lines[:90] if (m := QUARTER.search(line))), None)
    end = next((m for line in lines[:90] if (m := PERIOD_END.search(line))), None)
    year_match = next((m for line in lines[:90] if (m := YEAR.search(line))), None)
    if category == "kwartalny" and quarter:
        period, year = f"Q{quarter[1]}", quarter[2]
    elif category == "kwartalny" and end and end[2] in ("03", "06", "09", "12"):
        period, year = f"Q{int(end[2]) // 3}", end[1]
    elif category == "półroczny":
        period = "H1"
        year = end[1] if end else year_match[1] if year_match else year
    elif category == "roczny":
        period = "AR"
        year = end[1] if end else year_match[1] if year_match else year
    else:
        period = ""
    corrected = filing["listed_title"].casefold().startswith("korekta") or any(
        line.casefold() == "skorygowany" and row.xpath(".//input[@checked]")
        for row, line in zip(rows[:45], lines[:45], strict=True)
    )
    files = attachments(section, filing["source_url"])
    return {**filing, "status": "identified" if period and year else "unknown_period",
            "form": form, "fiscal_year": int(year) if year else None, "period": period,
            "consolidated": bool(heading and (
                heading["prefix"] or heading["suffix"] or form in ("SA-QS", "SA-PS", "SA-RS", "QSR", "PSR", "SRR")
            )),
            "corrected": corrected, "attachments": files}


def archive_detail(filing, archive):
    target = archive / "gpw" / "details" / filing["ticker"] / f"{filing['gpw_id']}.html"
    try:
        return parse_detail(filing, cache_page(target, filing["source_url"]))
    except (OSError, ValueError) as error:
        return {**filing, "status": "download_error", "error": str(error)}


def select_original(details, start, end):
    groups = defaultdict(list)
    for filing in details:
        if filing["status"] == "identified" and start <= filing["fiscal_year"] <= end:
            groups[filing["ticker"], filing["fiscal_year"], filing["period"]].append(filing)
    selected = []
    for (ticker, year, period), variants in sorted(groups.items()):
        scope = [r for r in variants if r["consolidated"]] or variants
        initial = [r for r in scope if not r["corrected"]] or scope
        candidate = min(initial, key=lambda r: r["published_at"])
        selected.append({"report_id": f"{ticker}-{year}-{period}", **candidate,
                         "alternative_gpw_ids": [r["gpw_id"] for r in variants if r is not candidate]})
    return selected


def write_registry(path, rows):
    columns = ("report_id", "publication_date", "published_at", "source_url")
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    write_text(path, out.getvalue())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    parser.add_argument("--start", type=int, default=2019)
    parser.add_argument("--end", type=int, default=2026)
    parser.add_argument("--tickers", nargs="+", choices=TICKERS, default=TICKERS)
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()
    isins = issuer_isins()
    with ThreadPoolExecutor(min(len(args.tickers), args.workers)) as pool:
        filings = [row for group in pool.map(
            lambda ticker: list_filings(ticker, isins[ticker], args.start, args.archive),
            args.tickers) for row in group]
    write_jsonl(args.archive / "gpw_listings.jsonl", filings)
    with ThreadPoolExecutor(args.workers) as pool:
        details = list(pool.map(lambda filing: archive_detail(filing, args.archive), filings))
    write_jsonl(args.archive / "gpw_periodic_details.jsonl", details)
    selected = select_original(details, args.start, args.end)
    write_jsonl(args.archive / "gpw_periodic_publications.jsonl", selected)
    write_registry(args.archive / "periodic_publications.csv", selected)
    print(f"GPW: {len(selected)} wydań, {len(details)} wpisów źródłowych.", flush=True)


if __name__ == "__main__":
    main()
