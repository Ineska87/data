"""Recover missing ESPI content from the public PAP MediaRoom issuer indexes."""

import argparse
import json
import re
import time
import unicodedata
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

from espi_detail_parse import REPORT, format_report, parse_detail, parse_stamp, tidy
from firecrawl_cache import FirecrawlCache
from scrape_espi_details import EVIDENCE, EVENTS, RAW, read_report_pdf, read_rows, report_pdf_path, write_evidence


PAP = "https://pap-mediaroom.pl"
ISSUER_INDEXES = {"PKN": (9810,), "PGE": (15377, 9996), "ENA": (11185,), "TPE": (10049,),
                  "ZEP": (10156,), "UNT": (12505,)}
HEADING_NUMBER = re.compile(rf"\(({REPORT})\)", re.I)


def public_source(url, cache):
    if cached := cache.get(url):
        return cached
    for attempt in range(3):
        try:
            request = Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "text/html"})
            with urlopen(request, timeout=25) as response:
                final = response.geturl()
                if urlsplit(final).hostname != urlsplit(PAP).hostname:
                    raise ValueError(f"Nieoczekiwane przekierowanie PAP: {final}")
                payload = {
                    "html": response.read().decode("utf-8", "replace"),
                    "provenance": {
                        "source": "pap_mediaroom",
                        "http_status": response.status,
                        "captured_at": datetime.now(timezone.utc).isoformat(),
                    },
                }
            cache.put(url, payload)
            return payload
        except HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise
            delay = (exc.headers.get("Retry-After") or "").strip()
            time.sleep(int(delay) if delay.isdecimal() else 2 ** attempt)
        except (URLError, TimeoutError, ConnectionError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Nie udało się pobrać {url}.")


def parse_index(url, html):
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    dates = []
    for card in soup.select(".newsList .node--view-mode-list-of-articles"):
        heading = card.select_one("h3.title")
        link = heading.find_parent("a", href=True) if heading else None
        stamp = card.select_one("li.date")
        origin = card.select_one("li.source a")
        day, clock = parse_stamp(stamp.get_text(" ", strip=True)) if stamp else ("", "")
        if day:
            dates.append(day)
        title = tidy(heading.get_text(" ", strip=True)) if heading else ""
        number = HEADING_NUMBER.search(title)
        if not (link and day and origin and origin.get_text(strip=True) == "ESPI" and number):
            continue
        rows.append({
            "number": format_report(number[1]),
            "title": title[number.end():].strip(),
            "url": urljoin(url, link["href"]),
            "mirror_date": day,
            "mirror_time": clock,
        })
    next_page = soup.select_one("a[rel~=next][href]")
    return rows, dates, urljoin(url, next_page["href"]) if next_page else None


def index_issuer(term, earliest, cache):
    url = f"{PAP}/taxonomy/term/{term}"
    pages = set()
    indexes = []
    while url and url not in pages:
        rows, dates, next_page = parse_index(url, public_source(url, cache)["html"])
        if not dates:
            raise ValueError(f"Brak rozpoznawalnych dat na stronie indeksu {url}.")
        pages.add(url)
        indexes.extend(rows)
        if max(dates) < earliest:
            break
        url = next_page
    print(f"PAP MediaRoom, indeks {term}: {len(pages)} stron, {len(indexes)} raportów.", flush=True)
    return indexes


def normal_title(text):
    folded = unicodedata.normalize("NFKD", text.casefold()).replace("ł", "l")
    return " ".join(re.findall(r"\w+", "".join(c for c in folded if not unicodedata.combining(c))))


def row_candidates(row, index):
    day = date.fromisoformat(row["event_date"])
    number = format_report(row["report_number"])
    title = normal_title(row.get("title", ""))
    previous = index.get(number, ())
    if number.endswith("/K"):
        previous = [*previous, *index.get(number[:-2], ())]
    for entry in previous:
        similarity = SequenceMatcher(None, title, normal_title(entry["title"]), autojunk=False).ratio()
        lag = (date.fromisoformat(entry["mirror_date"]) - day).days
        if (lag == 0 and similarity >= 0.62) or (lag == 1 and similarity >= 0.90):
            clock = int(entry["mirror_time"].replace(":", "") or "2400")
            yield (entry["number"] == number, -lag, similarity, -clock), entry


def recover(row, entry, cache, output_dir, download_pdfs):
    url = entry["url"]
    result = {
        **row, "issuer_url": row["url"], "url": url, "source_url": url, "source_kind": "pap_mediaroom_espi_relay",
        "mirror_date": entry["mirror_date"], "mirror_time": entry["mirror_time"],
    }
    try:
        payload = public_source(url, cache)
        detail = parse_detail(url, payload, row["ticker"], row["report_number"], row["event_date"])
        result.update(detail)
        # The portal's displayed clock belongs to its republication, not the ESPI transmission.
        result.update(publication_time="", time_source_url="", publication_date=row["event_date"],
                      publication_date_source="catalog")
        if result["status"] == "pdf_required" and result.get("document_url"):
            path = report_pdf_path(result, output_dir, download_pdfs)
            if path.is_file():
                result["_local_pdf"] = path
    except (OSError, RuntimeError, ValueError) as error:
        result.update(status="fallback_failed", error=str(error))
    return result


def index_rows(selected, cache, workers):
    by_term = {}
    for row in selected:
        for term in ISSUER_INDEXES.get(row["ticker"], ()):
            earliest = (date.fromisoformat(row["event_date"]) - timedelta(days=2)).isoformat()
            by_term[term] = min(by_term.get(term, earliest), earliest)
    def checked(term):
        try:
            return term, index_issuer(term, by_term[term], cache)
        except (OSError, RuntimeError, ValueError) as error:
            print(f"Problem z indeksem PAP {term}: {error}", flush=True)
            return term, []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        indexes = dict(pool.map(checked, by_term))
    by_ticker = {}
    for ticker, terms in ISSUER_INDEXES.items():
        joined = defaultdict(list)
        seen = set()
        for term in terms:
            for entry in indexes.get(term, ()):
                if entry["url"] not in seen:
                    joined[entry["number"]].append(entry)
                    seen.add(entry["url"])
        by_ticker[ticker] = joined
    return by_ticker


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, default=EVENTS / "espi_review_queue.csv")
    parser.add_argument("--supplementary", type=Path, nargs="*", default=[])
    parser.add_argument("--reports", type=Path, help="Ogranicz pobieranie do raportów bez odczytanej treści w tym pliku JSONL")
    parser.add_argument("--tickers", nargs="+", choices=tuple(ISSUER_INDEXES), default=list(ISSUER_INDEXES))
    parser.add_argument("--output-dir", type=Path, default=EVIDENCE)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--index-only", action="store_true")
    parser.add_argument("--download-report-pdfs", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.workers <= 10:
        parser.error("--workers musi być w zakresie 1–10.")

    cache = FirecrawlCache(RAW / "firecrawl_cache")
    selected = [row for row in read_rows(args.queue, args.supplementary)
                if row.get("ticker") in args.tickers and row.get("event_date") and row.get("report_number")]
    if args.reports:
        with args.reports.open(encoding="utf-8-sig") as stream:
            available = {row["event_id"] for line in stream if line.strip() and (row := json.loads(line))
                         and row.get("status") == "ok" and row.get("text", "").strip()}
        selected = [row for row in selected if row["event_id"] not in available]
    index = index_rows(selected, cache, args.workers)
    matched = [
        (row, max(options, key=lambda option: option[0])[1])
        for row in selected if (options := list(row_candidates(row, index[row["ticker"]])))
    ]
    print(f"PAP MediaRoom: dopasowano {len(matched)} z {len(selected)} komunikatów.", flush=True)
    if args.index_only:
        return
    fields = ("event_id", "ticker", "report_number", "title", "url", "event_date", "referenced_by")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(
            lambda item: recover({key: item[0].get(key, "") for key in fields}, item[1],
                                 cache, args.output_dir, args.download_report_pdfs),
            matched,
        ))
    for row in rows:
        if path := row.pop("_local_pdf", None):
            try:
                read_report_pdf(row, path, args.output_dir)
            except (OSError, RuntimeError, ValueError) as error:
                row["pdf_error"] = str(error)
    write_evidence(
        args.output_dir / "pap_mediaroom_reports.jsonl",
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
    )
    print("Stan zapasowych treści PAP", dict(Counter(row["status"] for row in rows)), flush=True)


if __name__ == "__main__":
    main()
