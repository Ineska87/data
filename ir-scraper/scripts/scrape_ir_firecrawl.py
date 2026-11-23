#!/usr/bin/env python3
"""
Skrypt do scrapowania list raportów bieżących (ESPI) oraz raportów okresowych
ze stron relacji inwestorskich (IR) wybranych spółek giełdowych przy użyciu Firecrawl.

Wersja 3.0 - jawna pętla paginacji (scrape_url per strona)
"""

import argparse
from collections import Counter
import json
import os
import random
import sys
import time
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from itertools import count
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from firecrawl_cache import FirecrawlCache, UnbilledFetchError, canonical_url, read_legacy_pages

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parents[1] / "scripts"))
from data_paths import DATA_ROOT, load_study_scope
from espi_identity import classify_report, deduplicate_reports, url_identity


# ============================================================
# KONFIGURACJA SPÓŁEK
# ============================================================
COMPANIES: Dict[str, Dict[str, Any]] = {
    "orlen": {
        "ticker": "PKN",
        "nazwa": "ORLEN S.A.",
        "raporty_biezace": {
            "url": "https://www.orlen.pl/pl/relacje-inwestorskie/raporty-i-publikacje/raporty-biezace",
            "page_param": "page",
            "page_start": 1,
        },
        "raporty_okresowe": {
            "url": "https://www.orlen.pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania",
            "page_param": None,
        },
    },
    "pge": {
        "ticker": "PGE",
        "nazwa": "PGE Polska Grupa Energetyczna S.A.",
        "raporty_biezace": {
            "url": "https://www.gkpge.pl/dla-inwestorow/raporty-biezace",
            "page_param": "page",
            "page_start": 1,
        },
        "raporty_okresowe": {
            "url": "https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe",
            "page_param": None,
        },
    },
    "zepak": {
        "ticker": "ZEP",
        "nazwa": "ZE PAK S.A.",
        "raporty_biezace": {
            "url": "https://ri.zepak.com.pl/pl/raporty/raporty-biezace.html",
            "page_param": "y",
            "page_start": 2026,
            "page_step": -1,
            "sub_page_template": "https://ri.zepak.com.pl/pl/raporty/raporty-biezace/{sub}.html?y={year}",
        },
        "raporty_okresowe": {
            "url": "https://ri.zepak.com.pl/pl/raporty/raporty-okresowe.html",
            "page_param": "y",
            "page_start": 2026,
            "page_step": -1,
            "sub_page_template": "https://ri.zepak.com.pl/pl/raporty/raporty-okresowe/{sub}.html?y={year}",
        },
    },
    "enea": {
        "ticker": "ENA",
        "nazwa": "ENEA S.A.",
        "raporty_biezace": {
            "url": "https://ir.enea.pl/lista-raportow/kategoria/3611/raporty-bie-ce?pageLimit=10",
            "page_param": "offset",
            "page_start": 0,
            "page_step": 10,
        },
        "raporty_okresowe": {
            "url": "https://ir.enea.pl/lista-raportow/kategoria/3612/raporty-okresowe?pageLimit=10",
            "page_param": "offset",
            "page_start": 0,
            "page_step": 10,
        },
    },
    "tauron": {
        "ticker": "TPE",
        "nazwa": "TAURON Polska Energia S.A.",
        "raporty_biezace": {
            "url": "https://www.tauron.pl/tauron/relacje-inwestorskie/raporty-biezace?pageSize=15",
            "page_param": "pageNumber",
            "page_start": 1,
        },
        "raporty_okresowe": {
            "url": "https://www.tauron.pl/tauron/relacje-inwestorskie/raporty-okresowe?pageSize=15",
            "page_param": "pageNumber",
            "page_start": 1,
        },
    },
    "bogdanka": {
        "ticker": "LWB",
        "nazwa": "Lubelski Węgiel Bogdanka S.A.",
        "raporty_biezace": {
            "url": "https://www.bankier.pl/gielda/notowania/akcje/BOGDANKA/komunikaty/{page}?source=3",
            "page_param": "page",
            "page_start": 1,
        },
        "raporty_okresowe": {
            "url": "https://www.bankier.pl/gielda/notowania/akcje/BOGDANKA/komunikaty/{page}?source=3",
            "page_param": "page",
            "page_start": 1,
        },
    },
    "unimot": {
        "ticker": "UNT",
        "nazwa": "UNIMOT S.A.",
        "raporty_biezace": {
            "url": "https://www.unimot.pl/relacje-inwestorskie/raporty-i-strategia/raporty-biezace",
            "page_param": "page",
            "page_start": 1,
        },
        "raporty_okresowe": {
            "url": "https://www.unimot.pl/relacje-inwestorskie/raporty-i-strategia/raporty-okresowe",
            "page_param": None,
        },
    },
    "jsw": {
        "ticker": "JSW",
        "nazwa": "JSW S.A.",
        "raporty_biezace": {
            "url_template": "https://www.jsw.pl/relacje-inwestorskie/raporty-gieldowe/raporty-biezace/raporty-biezace-{year}",
            "follow_next": True,
            "year_start": 2026,
            "year_end": 2011,
            "max_sub_pages": 15,
        },
        "raporty_okresowe": {
            "url": "https://www.jsw.pl/relacje-inwestorskie/raporty-gieldowe/raporty-okresowe",
            "page_param": None,
        },
    },
}


def get_api_key() -> str:
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        print("BŁĄD: Brak klucza API Firecrawl. Ustaw FIRECRAWL_API_KEY w .env", file=sys.stderr)
        sys.exit(1)
    return api_key


def make_absolute_url(base: str, url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    return url if url.startswith(("http://", "https://")) else urljoin(base, url)


def normalize_reports(reports: List[Dict[str, Any]], base_url: str) -> List[Dict[str, Any]]:
    normalized = []
    for r in reports:
        if not isinstance(r, dict):
            continue
        item = {
            "numer": (r.get("numer") or "").strip(),
            "data": (r.get("data") or "").strip(),
            "godzina": (r.get("godzina") or "").strip(),
            "tytul": (r.get("tytul") or r.get("title") or "").strip(),
            "url": make_absolute_url(base_url, r.get("url") or r.get("link")),
        }
        if item["tytul"]:
            normalized.append(item)
    return normalized


def deduplicate(reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return deduplicate_reports(reports)


def build_page_url(base_url: str, page: int, page_param: str) -> str:
    if "{page}" in base_url:
        return base_url.replace("{page}", str(page))
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{page_param}={page}"


def retry_delay(error, attempt):
    response = getattr(error, "response", None)
    value = response.headers.get("Retry-After", "").strip() if response is not None else ""
    if value.isdecimal():
        return int(value)
    if value:
        try:
            when = parsedate_to_datetime(value)
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            return max(0, (when - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            pass
    return 2 ** (attempt + 1) + random.random()


class ScrapeSession:
    """Read saved pages first and open a paid client only for permitted misses."""

    def __init__(self, cache, env_file, max_uncached, delay, *, proxy="basic"):
        self.cache = cache
        self.env_file = env_file
        self.max_uncached = max_uncached
        self.delay = delay
        self.proxy = proxy
        self.api_requests = 0
        self.requested_urls = 0
        self.confirmed_credits = 0
        self.uncertain_charge = False
        self.cache_hits = 0
        self.client = None

    def read(self, url):
        cached = self.cache.get(url)
        if cached is not None:
            self.cache_hits += 1
            return cached
        if self.max_uncached is not None and self.requested_urls >= self.max_uncached:
            raise RuntimeError(f"Limit nowych zapytań osiągnięty. Brak strony w cache: {url}")
        if not self.client:
            from dotenv import load_dotenv
            from firecrawl import Firecrawl

            load_dotenv(dotenv_path=self.env_file, override=False)
            self.client = Firecrawl(api_key=get_api_key(), timeout=90, max_retries=0)
        result, hit = self.cache.get_or_fetch(url, self.fetch)
        self.cache_hits += int(hit)
        return result

    def fetch(self, url):
        from firecrawl.v2.utils.error_handler import BadRequestError, PaymentRequiredError, RateLimitError, UnauthorizedError
        from requests.exceptions import ConnectTimeout

        if self.api_requests:
            time.sleep(self.delay)
        self.requested_urls += 1
        max_attempts = 5
        for attempt in range(max_attempts):
            self.api_requests += 1
            try:
                result = self.client.scrape(url, formats=["markdown", "html"], parsers=[], proxy=self.proxy)
            except (RateLimitError, ConnectTimeout) as error:
                if attempt == max_attempts - 1:
                    raise UnbilledFetchError(f"Firecrawl nie przyjął {url} po {max_attempts} próbach.") from error
                wait = retry_delay(error, attempt)
                print(f"Firecrawl wznawia za {wait:.1f} s ({attempt + 2}/{max_attempts}) dla {url}.", file=sys.stderr)
                try:
                    time.sleep(wait)
                except KeyboardInterrupt as interrupted:
                    raise UnbilledFetchError(f"Anulowano ponowienie dla {url}.") from interrupted
            except (BadRequestError, UnauthorizedError, PaymentRequiredError) as error:
                raise UnbilledFetchError(str(error)) from error
            except BaseException:
                self.uncertain_charge = True
                raise
            else:
                break

        credits = getattr(result.metadata, "credits_used", None)
        credits = 1 if credits is None else credits
        self.confirmed_credits += credits
        return {
            "markdown": result.markdown or "",
            "html": result.html or "",
            "provenance": {
                "source": "Firecrawl",
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "credits_used": credits,
                "http_status": getattr(result.metadata, "status_code", None),
                "source_url": getattr(result.metadata, "source_url", None),
                "resolved_url": getattr(result.metadata, "url", None),
            },
        }

    def usage_summary(self):
        credits = f"{self.confirmed_credits} kredytów"
        if self.uncertain_charge:
            credits = f"co najmniej {credits} (jedno żądanie bez potwierdzenia rozliczenia)"
        return f"{self.api_requests} prób API, {credits}, {self.cache_hits} odczytów cache"


def scrape_page(app: ScrapeSession, url: str, *, ticker: str, report_type: str, reparse_archive=False):
    from espi_listings import parse_archive_page
    from standard_listings import parse_standard_listing

    payload = app.read(url)
    status = payload.get("provenance", {}).get("http_status")
    if status is not None and status >= 400:
        raise RuntimeError(f"Emitent zwrócił HTTP {status} dla {url}. Odpowiedź jest zapisana w cache.")
    markdown = payload.get("markdown", "")
    if report_type == "biezace" and "raporty" in payload:
        data = payload
        if reparse_archive and markdown:
            data = {**payload, "raporty": parse_archive_page(ticker, url, markdown) or payload["raporty"]}
    else:
        data = parse_standard_listing(url, payload, ticker, report_type)
    return (data["raporty"], markdown, data.get("total_pages"),
            data.get("total_sub_pages"), data.get("next_page_url"))


def scrape_with_pagination(
    app: Any,
    base_url: str,
    page_param: str,
    page_start: int,
    max_pages: Optional[int],
    delay: float = 1.5,
    page_step: int = 1,
    sub_page_template: Optional[str] = None,
    *,
    ticker: str,
    report_type: str,
) -> Dict[str, Any]:
    """Scrapuje kolejne strony paginacji do limitu lub końca wyników."""
    all_reports: List[Dict] = []
    all_markdown: List[str] = []
    sources: List[str] = []
    total_pages_detected: Optional[int] = None

    try:
        visited_batches = set()
        for i in range(max_pages) if max_pages is not None else count():
            page_value = page_start + i * page_step
            if i > 0:
                time.sleep(delay)

            url = build_page_url(base_url, page_value, page_param)
            limit = total_pages_detected or max_pages
            print(f"  → Strona {i + 1}/{limit}: {url}")

            page_reports, page_md, detected, sub_pages, _ = scrape_page(app, url, ticker=ticker, report_type=report_type)

            # wyświetl wykrytą liczbę stron (tylko informacyjnie, nie używaj do zatrzymania)
            if page_step == 1 and detected is not None and detected > (i + 1) and total_pages_detected is None:
                total_pages_detected = detected
                print(f"  ℹ Wykryto ~{total_pages_detected} stron (informacyjnie)")

            if not page_reports:
                print(f"  ⚠ Brak raportów na stronie {i + 1} — zatrzymuję pętlę")
                break
            signature = tuple((r.get("numer"), r.get("data"), r.get("url")) for r in page_reports)
            if signature in visited_batches:
                print(f"  Koniec paginacji, strona {i + 1} powtórzyła znaną listę.")
                break
            visited_batches.add(signature)

            # obsługa podstron (np. ZE PAK: raporty-biezace/2.html?y=2020)
            if sub_page_template and sub_pages and sub_pages > 1:
                print(f"  ℹ Wykryto {sub_pages} podstron dla wartości {page_value}")
                for sp in range(2, sub_pages + 1):
                    time.sleep(delay)
                    sub_url = sub_page_template.format(sub=sp, year=page_value)
                    print(f"    → Podstrona {sp}/{sub_pages}: {sub_url}")
                    sp_reports, sp_md, _, _, _ = scrape_page(app, sub_url, ticker=ticker, report_type=report_type)
                    page_reports = [*page_reports, *sp_reports]
                    if sp_md:
                        page_md += f"\n\n### Podstrona {sp}\n\n" + sp_md
                    sources.append(sub_url)

            all_reports.extend(page_reports)
            if page_md:
                all_markdown.append(f"## Źródło strony: {url}\n\n{page_md}")
            sources.append(url)

    except KeyboardInterrupt:
        raise SystemExit("Przerwano pobieranie. Zapisane już strony pozostają w cache.")

    normalized = normalize_reports(all_reports, base_url)
    unique = deduplicate(normalized)

    return {
        "reports": unique,
        "markdown": "\n\n---\n\n".join(all_markdown),
        "sources": sources,
        "pages_scraped": len(sources),
        "total_pages_detected": total_pages_detected,
        "removed_duplicates": len(normalized) - len(unique),
    }


def scrape_single_page(app: Any, url: str, *, ticker: str, report_type: str) -> Dict[str, Any]:
    """Scrapuje jedną stronę bez paginacji."""
    print(f"  → Scrapowanie: {url}")
    reports, markdown, _, _, _ = scrape_page(app, url, ticker=ticker, report_type=report_type)
    normalized = normalize_reports(reports, url)
    return {
        "reports": normalized,
        "markdown": markdown,
        "sources": [url],
        "pages_scraped": 1,
        "total_pages_detected": None,
        "removed_duplicates": 0,
    }


def scrape_years_follow_next(
    app: Any,
    url_template: str,
    year_start: int,
    year_end: int,
    max_sub_pages: int = 15,
    delay: float = 1.5,
    *,
    ticker: str,
    report_type: str,
) -> Dict[str, Any]:
    """Scrapuje strony z rokiem w URL (np. JSW), śledząc next_page_url dla podstron.

    Używane gdy URL paginacji zawiera dynamiczny cHash lub inne nieznane parametry,
    które można pobrać tylko ze strony — nie z szablonu.
    """
    all_reports: List[Dict] = []
    all_markdown: List[str] = []
    sources: List[str] = []

    try:
        for year in range(year_start, year_end - 1, -1):
            year_url = url_template.format(year=year)
            print(f"  → Rok {year}: {year_url}")
            current_url: Optional[str] = year_url
            sub_page = 1
            year_reports: List[Dict] = []
            visited_urls: set = {year_url}

            while current_url and sub_page <= max_sub_pages:
                if sub_page > 1:
                    time.sleep(delay)
                page_reports, page_md, _, _, next_page_url = scrape_page(
                    app, current_url, ticker=ticker, report_type=report_type,
                )

                if not page_reports and sub_page == 1:
                    print(f"    ⚠ Brak raportów dla roku {year} — pomijam rok")
                    break

                year_reports.extend(page_reports)
                if page_md:
                    all_markdown.append(f"## {year} — strona {sub_page}: {current_url}\n\n{page_md}")
                sources.append(current_url)
                print(f"    ✓ Strona {sub_page}: {len(page_reports)} raportów (łącznie w roku: {len(year_reports)})")

                # zatrzymaj gdy brak następnej strony lub URL już odwiedzony (pętla)
                if next_page_url and next_page_url not in visited_urls:
                    visited_urls.add(next_page_url)
                    current_url = next_page_url
                    print(f"    → Następna strona: {current_url}")
                else:
                    if next_page_url and next_page_url in visited_urls:
                        print(f"    ⚠ next_page_url już odwiedzony — koniec roku {year}")
                    current_url = None
                sub_page += 1

            all_reports.extend(year_reports)
            print(f"  ✓ Rok {year} zakończony: {len(year_reports)} raportów")

    except KeyboardInterrupt:
        raise SystemExit("Przerwano pobieranie. Zapisane już strony pozostają w cache.")

    base = url_template.split("{")[0]
    normalized = normalize_reports(all_reports, base)
    unique = deduplicate(normalized)
    return {
        "reports": unique,
        "markdown": "\n\n---\n\n".join(all_markdown),
        "sources": sources,
        "pages_scraped": len(sources),
        "total_pages_detected": None,
        "removed_duplicates": len(normalized) - len(unique),
    }


def save_json(data: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ Zapisano JSON: {path}")


def save_markdown(content: str, metadata: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sources = metadata.get("zrodla", [])
    sources_str = ", ".join(sources) if isinstance(sources, list) else sources
    header = (
        f"# Raporty - {metadata.get('spolka')}\n"
        f"Źródła: {sources_str}\n"
        f"Data scrapowania: {metadata.get('data_scrapowania')}\n"
        f"Liczba raportów (unikalnych): {metadata.get('liczba_raportow', 0)}\n"
        f"Stron scrapowanych: {metadata.get('liczba_stron', 0)}\n"
        f"\n---\n\n"
    )
    with path.open("w", encoding="utf-8") as f:
        f.write(header + content)
    print(f"  ✓ Zapisano Markdown: {path}")


def generate_summary_table(reports: List[Dict[str, Any]]) -> str:
    if not reports:
        return "Brak raportów.\n"
    lines = ["| Lp. | Numer | Data | Godzina | Tytuł | Link |", "|-----|-------|------|---------|-------|------|"]
    for i, r in enumerate(reports, 1):
        url = r.get("url") or ""
        link = f"[link]({url})" if url else "-"
        lines.append(f"| {i} | {r.get('numer', '-')} | {r.get('data', '-')} | {r.get('godzina', '-')} | {r.get('tytul', '')} | {link} |")
    return "\n".join(lines) + "\n"


def legacy_pages(data_root, ticker):
    """Pair a dated JSON snapshot with the matching per-page historical export."""
    from espi_listings import ARCHIVE_STEMS

    folder = data_root / "raw" / "espi"
    if ticker == "LWB":
        candidates = data_root / "raw" / "context" / "espi" / ticker
        stem = "bogdanka_biezace_20260625_164542"
    else:
        candidates = folder / ticker
        stem = ARCHIVE_STEMS[ticker]
    markdown = folder / "archivemd_backup" / f"{stem}.md"
    if not markdown.is_file():
        return {}
    for snapshot in sorted(candidates.glob("*.json")):
        try:
            return read_legacy_pages(snapshot, markdown)
        except (KeyError, ValueError):
            continue
    raise RuntimeError(f"Nie znaleziono JSON odpowiadającego archiwum {markdown.name}.")


def study_plan(tickers, start, end, cache, archived=None):
    from espi_listings import load_archived_pages

    plans = {}
    for ticker in tickers:
        pages = load_archived_pages(DATA_ROOT, ticker, start, end)
        if not pages:
            raise RuntimeError(f"Brak zweryfikowanych adresów list dla {ticker}.")
        urls = dict.fromkeys(map(canonical_url, pages))
        outside_cache = [url for url in urls if cache.get(url) is None]
        reusable = [url for url in outside_cache if url in (archived or {}).get(ticker, {})]
        missing = [url for url in outside_cache if url not in set(reusable)]
        plans[ticker] = (urls, missing)
        print(f"{ticker} {start}–{end}: {len(urls)} stron, {len(urls) - len(outside_cache)} w cache, "
              f"{len(reusable)} do odzyskania lokalnie, {len(missing)} do pobrania.")
        for url in missing:
            print(f"  poza cache: {url}")
    print(f"Razem poza cache: {len({url for _, missing in plans.values() for url in missing})}.")
    return plans


def archive_keys(rows, start, end):
    return {
        (classify_report(row["numer"], row["tytul"]).report_number, row["data"], url_identity(row["url"]))
        for row in rows if start <= date.fromisoformat(row["data"]) <= end
    }


def export_study(tickers, start, end, app, output_dir, verify_public, output_format):
    from espi_listings import PUBLIC_LISTINGS, load_public_pages

    completed = []
    plans = study_plan(tickers, start, end, app.cache)
    for ticker, (urls, _) in plans.items():
        rows = []
        markdown_pages = []
        for url in urls:
            parsed, markdown, _, _, _ = scrape_page(
                app, url, ticker=ticker, report_type="biezace", reparse_archive=True,
            )
            if not parsed:
                raise RuntimeError(f"Brak rozpoznawalnych rekordów ze strony {url}.")
            rows.extend(row for row in parsed if start <= date.fromisoformat(row["data"]) <= end)
            if output_format in {"md", "both"} and markdown:
                markdown_pages.append(f"## Źródło strony: {url}\n\n{markdown}")
        unique = deduplicate(rows)
        counts = Counter(date.fromisoformat(row["data"]).year for row in unique)
        if set(counts) != set(range(start.year, end.year + 1)):
            raise RuntimeError(f"Zrzut {ticker} nie pokrywa każdego roku w zakresie: {dict(counts)}.")
        verification = {}
        if verify_public and ticker in PUBLIC_LISTINGS:
            public = load_public_pages(ticker, start, end)
            public_keys = archive_keys((row for page in public.values() for row in page["reports"]), start, end)
            archive = archive_keys(unique, start, end)
            if public_keys != archive:
                raise RuntimeError(f"{ticker}: wykaz publiczny różni się od cache. "
                                   f"Tylko publiczny: {len(public_keys - archive)}, tylko archiwalny: {len(archive - public_keys)}.")
            verification = {"kind": "direct_issuer_html", "pages": list(public),
                            "matching_disclosures": len(public_keys)}
            print(f"{ticker}: {len(public_keys)} rekordów zgodnych z {len(public)} aktualnymi stronami emitenta.")
            for url, page in public.items():
                if app.cache.get(url) is None:
                    app.cache.put(url, {"raporty": page["reports"], "markdown": "",
                                        "provenance": {"source": "issuer_html"}})
        completed.append((ticker, urls, unique, counts, verification, markdown_pages))

    captured_at = datetime.now(timezone.utc)
    batch = captured_at.strftime("%Y%m%dT%H%M%S%fZ")
    for ticker, urls, reports, counts, verification, markdown_pages in completed:
        target = (output_dir or DATA_ROOT / "staging" / "espi") / ticker / f"{ticker.lower()}_espi_{batch}"
        key, company = next((key, company) for key, company in COMPANIES.items() if company["ticker"] == ticker)
        metadata = {
            "spolka": company["nazwa"], "spolka_key": key, "ticker": ticker, "typ": "biezace",
            "zrodla": list(urls), "data_scrapowania": captured_at.isoformat(),
            "source_kind": "issuer_listing_reparse",
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "coverage_verification": verification,
            "liczba_stron": len(urls), "liczba_raportow": len(reports),
            "reports_by_year": dict(sorted(counts.items())), "raporty": reports,
        }
        if output_format in {"json", "both"}:
            save_json(metadata, target.with_suffix(".json"))
        if output_format in {"md", "both"}:
            target.parent.mkdir(parents=True, exist_ok=True)
            content = generate_summary_table(reports) + "\n\n" + "\n\n---\n\n".join(markdown_pages)
            save_markdown(content, metadata, target.with_suffix(".md"))


def main():
    parser = argparse.ArgumentParser(description="Scrapuj raporty IR spółek giełdowych")
    parser.add_argument("--spolka", choices=list(COMPANIES.keys()), default="orlen")
    parser.add_argument("--typ", choices=["biezace", "okresowe"], default="biezace")
    parser.add_argument("--format", choices=["json", "md", "both"], help="Domyślnie JSON w trybie badania")
    parser.add_argument("--max-pages", type=int, help="Opcjonalny limit dla pojedynczego archiwum poza trybem badania")
    parser.add_argument("--delay", type=float, default=1.5, help="Opóźnienie między stronami w sekundach")
    parser.add_argument("--output-dir", type=Path, help="Domyślnie data/staging/<rodzaj>/<ticker>")
    parser.add_argument("--env-file", type=Path, default=DATA_ROOT.parent / ".env")
    parser.add_argument("--study", action="store_true", help="ESPI sześciu emitentów i lata z study_scope.json")
    parser.add_argument("--seed-cache", action="store_true", help="Zaimportuj zachowane odpowiedzi do cache i zakończ bez API")
    parser.add_argument("--dry-run", action="store_true", help="Pokaż adresy poza cache bez zapytań Firecrawl")
    parser.add_argument("--cache-dir", type=Path, default=DATA_ROOT / "raw" / "firecrawl_cache")
    parser.add_argument("--max-uncached", type=int, help="Limit nowych URL-i w Firecrawl, 0 oznacza tylko cache")
    parser.add_argument("--verify-public", action="store_true", help="Porównaj z publicznym HTML emitenta tam, gdzie jest parser")
    args = parser.parse_args()
    if args.max_pages is not None and args.max_pages < 1:
        parser.error("--max-pages musi być dodatnie.")
    if args.max_uncached is not None and args.max_uncached < 0:
        parser.error("--max-uncached musi być nieujemne.")
    if args.delay < 0:
        parser.error("--delay musi być nieujemne.")
    if args.dry_run and args.seed_cache:
        parser.error("Użyj osobno --seed-cache oraz --dry-run.")
    cache = FirecrawlCache(args.cache_dir)
    scope = load_study_scope()
    selected_ticker = COMPANIES[args.spolka]["ticker"]
    use_study = args.study or (args.typ == "biezace" and args.max_pages is None and selected_ticker in scope["tickers"])
    if args.verify_public and (not use_study or args.seed_cache or args.dry_run):
        parser.error("--verify-public dotyczy zapisu zrzutów badania.")
    if use_study:
        if args.typ != "biezace" or args.max_pages is not None:
            parser.error("Tryb --study obejmuje całe ESPI z lat określonych w study_scope.json.")
        start = date.fromisoformat(scope["period"]["start"])
        end = date.fromisoformat(scope["period"]["end"])
        tickers = scope["tickers"] if args.study else [selected_ticker]
        archived = {ticker: legacy_pages(DATA_ROOT, ticker) for ticker in tickers}
        if args.dry_run:
            study_plan(tickers, start, end, cache, archived)
            print("Firecrawl: 0 zapytań, 0 kredytów.")
            return
        for ticker, pages in archived.items():
            count_seeded = sum(cache.put(url, payload) for url, payload in pages.items())
            if args.seed_cache or count_seeded:
                print(f"{ticker}: {count_seeded} nowych wpisów cache z {len(pages)} stron archiwalnych.")
        if args.seed_cache:
            print("Firecrawl: 0 zapytań, 0 kredytów.")
            return
        app = ScrapeSession(cache, args.env_file, args.max_uncached, args.delay)
        try:
            export_study(tickers, start, end, app, args.output_dir, args.verify_public, args.format or "json")
        finally:
            print(f"Firecrawl: {app.usage_summary()}.")
        return
    if args.seed_cache:
        parser.error("Dodaj --study, aby zaimportować sześć archiwów.")

    cfg = COMPANIES[args.spolka]
    typ_cfg = cfg.get(f"raporty_{args.typ}")

    if not typ_cfg:
        print(f"BŁĄD: Brak konfiguracji dla typu '{args.typ}' i spółki '{args.spolka}'")
        sys.exit(1)

    url_template: Optional[str] = typ_cfg.get("url_template")
    follow_next: bool = typ_cfg.get("follow_next", False)
    base_url: str = typ_cfg.get("url", url_template or "")
    page_param: Optional[str] = typ_cfg.get("page_param")
    page_start: int = typ_cfg.get("page_start", 1)
    page_step: int = typ_cfg.get("page_step", 1)
    sub_page_template: Optional[str] = typ_cfg.get("sub_page_template")

    if args.dry_run:
        if not page_param and not follow_next:
            print(f"{base_url}: {int(cache.get(base_url) is None)} stron poza cache.")
        else:
            print("Liczba stron poza cache zależy od nawigacji wybranego archiwum. Dla sześciu badanych emitentów użyj --study.")
        print("Firecrawl: 0 zapytań, 0 kredytów.")
        return
    if selected_ticker == "LWB" or (args.typ == "biezace" and selected_ticker in scope["tickers"]):
        for url, payload in legacy_pages(DATA_ROOT, selected_ticker).items():
            cache.put(url, payload)

    print("=" * 70)
    print(f"Scrapowanie: {cfg['nazwa']}")
    print(f"Typ: {args.typ}")
    if url_template and follow_next:
        year_start = typ_cfg.get("year_start", 2026)
        year_end = typ_cfg.get("year_end", 2011)
        max_sub = typ_cfg.get("max_sub_pages", 15)
        print(f"Tryb: lata {year_start}→{year_end}, next_page_url, max {max_sub} podstron/rok")
        print(f"Szablon URL: {url_template}")
    else:
        print(f"URL: {base_url}")
        print(f"Paginacja: {'?' + page_param + '=N' if page_param else 'brak'} | Krok: {page_step} | Limit stron: {args.max_pages}")
    print("=" * 70)

    app = ScrapeSession(cache, args.env_file, args.max_uncached, args.delay)

    try:
        if url_template and follow_next:
            result = scrape_years_follow_next(
                app, url_template, year_start, year_end, max_sub, args.delay,
                ticker=selected_ticker, report_type=args.typ,
            )
        elif page_param:
            result = scrape_with_pagination(
                app, base_url, page_param, page_start, args.max_pages, args.delay, page_step, sub_page_template,
                ticker=selected_ticker, report_type=args.typ,
            )
        else:
            result = scrape_single_page(app, base_url, ticker=selected_ticker, report_type=args.typ)
    finally:
        print(f"Firecrawl: {app.usage_summary()}.")

    reports = result["reports"]
    scraped_at = datetime.now(timezone.utc)
    timestamp = scraped_at.strftime("%Y%m%dT%H%M%S%fZ")

    base_meta = {
        "spolka": cfg["nazwa"],
        "spolka_key": args.spolka,
        "ticker": cfg["ticker"],
        "typ": args.typ,
        "zrodla": result["sources"],
        "data_scrapowania": scraped_at.isoformat(),
        "liczba_stron": result["pages_scraped"],
        "total_pages_detected": result["total_pages_detected"],
        "liczba_raportow_przed_unikalnymi": len(reports) + result["removed_duplicates"],
        "liczba_raportow": len(reports),
        "usuniete_duplikaty": result["removed_duplicates"],
    }

    category = "espi" if args.typ == "biezace" else "periodic_links"
    out_dir = args.output_dir or DATA_ROOT / "staging" / category / cfg["ticker"]

    out_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"{args.spolka}_{args.typ}_{timestamp}"

    output_format = args.format or "both"
    if output_format in ("json", "both"):
        save_json({**base_meta, "raporty": reports}, out_dir / f"{base_name}.json")

    if output_format in ("md", "both"):
        table = generate_summary_table(reports)
        save_markdown(
            table + "\n\n## Oryginalna treść stron (markdown z Firecrawl)\n\n" + result["markdown"],
            base_meta,
            out_dir / f"{base_name}.md",
        )

    print("\n" + "-" * 70)
    print("PODSUMOWANIE")
    print(f"  Spółka:              {cfg['nazwa']}")
    print(f"  Stron scrapowanych:  {result['pages_scraped']}")
    if result["total_pages_detected"]:
        print(f"  Wszystkich stron:    {result['total_pages_detected']}")
    print(f"  Raportów (brutto):   {len(reports) + result['removed_duplicates']}")
    print(f"  Usuniętych duplik.:  {result['removed_duplicates']}")
    print(f"  Raportów (netto):    {len(reports)}")
    print("-" * 70)


if __name__ == "__main__":
    sys.stdout.reconfigure(errors="backslashreplace")
    main()
