#!/usr/bin/env python3
"""
Skrypt do scrapowania list raportów bieżących (ESPI) oraz raportów okresowych
ze stron relacji inwestorskich (IR) wybranych spółek giełdowych przy użyciu Firecrawl.

Wersja 3.0 - jawna pętla paginacji (scrape_url per strona)
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

from dotenv import load_dotenv

from firecrawl import Firecrawl
from firecrawl.v2.types import JsonFormat

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parents[1] / "scripts"))
from data_paths import DATA_ROOT


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


REPORT_EXTRACTION_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "raporty": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "numer": {"type": "string"},
                    "data": {"type": "string"},
                    "godzina": {"type": "string"},
                    "tytul": {"type": "string"},
                    "url": {"type": "string"},
                },
                "required": ["tytul"],
            },
        },
        "total_pages": {
            "type": "integer",
            "description": "Ostatni numer strony widoczny w głównej nawigacji paginacji",
        },
        "total_sub_pages": {
            "type": "integer",
            "description": "Liczba podstron w ramach bieżącej listy (np. nawigacja '1 2' na dole = 2)",
        },
        "next_page_url": {
            "type": "string",
            "description": "Pełny URL następnej strony (link '2', '>', 'następna', 'dalej' w nawigacji) — tylko jeśli istnieje kolejna strona",
        },
    },
    "required": ["raporty"],
}

SCRAPE_PROMPT = (
    "Wyodrębnij WSZYSTKIE widoczne raporty (bieżące lub okresowe) z tej strony. "
    "Dla każdego raportu wyciągnij: numer (np. 'RB nr 29/2026'), datę (DD.MM.YYYY), "
    "godzinę publikacji (HH:MM, jeśli widoczna na stronie), tytuł oraz link (pełny URL). "
    "Wyciągnij też całkowitą liczbę stron paginacji (total_pages) — "
    "to jest największy numer strony widoczny w głównej nawigacji. "
    "Jeśli na dole strony widoczna jest dodatkowa nawigacja z numerami podstron "
    "(np. '1 2' lub '« 1 2 »'), podaj total_sub_pages jako największy widoczny numer. "
    "Jeśli w paginacji istnieje link do następnej strony (np. '>', '2', 'następna', 'dalej'), "
    "podaj jego pełny URL jako next_page_url."
)


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
    seen: set = set()
    unique = []
    for r in reports:
        key = r.get("url") or r.get("tytul")
        if key and key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def build_page_url(base_url: str, page: int, page_param: str) -> str:
    if "{page}" in base_url:
        return base_url.replace("{page}", str(page))
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{page_param}={page}"


def scrape_page(app: Any, url: str) -> Tuple[List[Dict], str, Optional[int], Optional[int], Optional[str]]:
    """Scrapuje pojedynczą stronę. Zwraca (raporty, markdown, total_pages, total_sub_pages, next_page_url)."""
    result = app.scrape_url(
        url,
        formats=[
            "markdown",
            JsonFormat(
                type="json",
                schema=REPORT_EXTRACTION_SCHEMA,
                prompt=SCRAPE_PROMPT,
            ),
        ],
    )
    json_data = result.json or {}
    reports = json_data.get("raporty", []) if isinstance(json_data, dict) else []
    total_pages = json_data.get("total_pages") if isinstance(json_data, dict) else None
    total_sub_pages = json_data.get("total_sub_pages") if isinstance(json_data, dict) else None
    next_page_url = json_data.get("next_page_url") if isinstance(json_data, dict) else None
    markdown = result.markdown or ""
    return reports, markdown, total_pages, total_sub_pages, next_page_url


def scrape_with_pagination(
    app: Any,
    base_url: str,
    page_param: str,
    page_start: int,
    max_pages: int,
    delay: float = 1.5,
    page_step: int = 1,
    sub_page_template: Optional[str] = None,
) -> Dict[str, Any]:
    """Scrapuje kolejne strony paginacji do limitu lub końca wyników."""
    all_reports: List[Dict] = []
    all_markdown: List[str] = []
    sources: List[str] = []
    total_pages_detected: Optional[int] = None

    try:
        for i in range(max_pages):
            page_value = page_start + i * page_step
            if i > 0:
                time.sleep(delay)

            url = build_page_url(base_url, page_value, page_param)
            limit = total_pages_detected or max_pages
            print(f"  → Strona {i + 1}/{limit}: {url}")

            try:
                page_reports, page_md, detected, sub_pages, _ = scrape_page(app, url)
            except Exception as e:
                print(f"  ✗ Błąd na stronie {i + 1}: {e} — pomijam stronę")
                continue

            # wyświetl wykrytą liczbę stron (tylko informacyjnie, nie używaj do zatrzymania)
            if page_step == 1 and detected is not None and detected > (i + 1) and total_pages_detected is None:
                total_pages_detected = detected
                print(f"  ℹ Wykryto ~{total_pages_detected} stron (informacyjnie)")

            if not page_reports:
                print(f"  ⚠ Brak raportów na stronie {i + 1} — zatrzymuję pętlę")
                break

            # obsługa podstron (np. ZE PAK: raporty-biezace/2.html?y=2020)
            if sub_page_template and sub_pages and sub_pages > 1:
                print(f"  ℹ Wykryto {sub_pages} podstron dla wartości {page_value}")
                for sp in range(2, sub_pages + 1):
                    time.sleep(delay)
                    sub_url = sub_page_template.format(sub=sp, year=page_value)
                    print(f"    → Podstrona {sp}/{sub_pages}: {sub_url}")
                    try:
                        sp_reports, sp_md, _, _, _ = scrape_page(app, sub_url)
                        page_reports.extend(sp_reports)
                        if sp_md:
                            page_md += f"\n\n### Podstrona {sp}\n\n" + sp_md
                        sources.append(sub_url)
                    except Exception as e:
                        print(f"    ✗ Błąd podstrony {sp}: {e}")

            all_reports.extend(page_reports)
            if page_md:
                all_markdown.append(f"## Źródło strony: {url}\n\n{page_md}")
            sources.append(url)

    except KeyboardInterrupt:
        print(f"\n  ⚠ Przerwano przez użytkownika po {len(sources)} stronach — zapisuję zebrane dane...")

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


def scrape_single_page(app: Any, url: str) -> Dict[str, Any]:
    """Scrapuje jedną stronę bez paginacji."""
    print(f"  → Scrapowanie: {url}")
    reports, markdown, _, _, _ = scrape_page(app, url)
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
                try:
                    page_reports, page_md, _, _, next_page_url = scrape_page(app, current_url)
                except Exception as e:
                    print(f"    ✗ Błąd (strona {sub_page}): {e} — pomijam")
                    break

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
        print(f"\n  ⚠ Przerwano — zapisuję zebrane dane ({len(sources)} stron)...")

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


def main():
    parser = argparse.ArgumentParser(description="Scrapuj raporty IR spółek giełdowych")
    parser.add_argument("--spolka", choices=list(COMPANIES.keys()), default="orlen")
    parser.add_argument("--typ", choices=["biezace", "okresowe"], default="biezace")
    parser.add_argument("--format", choices=["json", "md", "both"], default="both")
    parser.add_argument("--max-pages", type=int, default=10, help="Maksymalna liczba stron do scrapowania")
    parser.add_argument("--delay", type=float, default=1.5, help="Opóźnienie między stronami w sekundach")
    parser.add_argument("--output-dir", type=Path, help="Domyślnie data/staging/<rodzaj>/<ticker>")
    parser.add_argument("--env-file", type=Path, default=SCRIPT_DIR.parents[2] / ".env")
    args = parser.parse_args()

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

    load_dotenv(dotenv_path=args.env_file, override=False)
    api_key = get_api_key()
    app = Firecrawl(api_key=api_key)

    if url_template and follow_next:
        result = scrape_years_follow_next(
            app, url_template,
            typ_cfg.get("year_start", 2026),
            typ_cfg.get("year_end", 2011),
            typ_cfg.get("max_sub_pages", 15),
            args.delay,
        )
    elif page_param:
        result = scrape_with_pagination(app, base_url, page_param, page_start, args.max_pages, args.delay, page_step, sub_page_template)
    else:
        result = scrape_single_page(app, base_url)

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

    if args.format in ("json", "both"):
        save_json({**base_meta, "raporty": reports}, out_dir / f"{base_name}.json")

    if args.format in ("md", "both"):
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
