#!/usr/bin/env python3
"""Build download list for PGE/TPE/ENA quarterly + semi-annual reports 2020-2025.

Priority files:
  - consolidated financial report (sprawozdanie / raport finansowy)
  - for TPE: skonsolidowane sprawozdanie (ashx)
  - for ENA: PDF attachments from QSr / PSr pages
Optional: presentation (if easily found on same page)
"""

from __future__ import annotations

import json
import re
import ssl
import urllib.request
from html.parser import HTMLParser

from data_paths import DATA_ROOT
from urllib.parse import urljoin

CTX = ssl.create_default_context()
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pl-PL,pl;q=0.9",
}
OUT = DATA_ROOT / "metadata" / "download_manifests" / "_quarters_url_list.json"


class LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self._href = href
                self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._text).strip()))
            self._href = None


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=CTX, timeout=90) as r:
        return r.read().decode("utf-8", errors="replace")


def links_on(url: str) -> list[tuple[str, str]]:
    html = fetch(url)
    p = LinkExtractor()
    p.feed(html)
    out = []
    for href, text in p.links:
        full = urljoin(url, href)
        out.append((full, text))
    return out


def clean_url(u: str) -> str:
    # strip query for stable naming
    return u.split("?")[0]


def pick_pge(links: list[tuple[str, str]], year: int, period: str) -> list[tuple[str, str, str]]:
    """Return (filename, url, note) candidates for PGE period page."""
    found: list[tuple[str, str, str]] = []
    for full, text in links:
        t = re.sub(r"\s+", " ", text).lower()
        u = full.lower()
        if "content/download" not in u:
            continue
        if not (u.endswith(".pdf") or ".pdf" in u):
            continue
        # financial report
        if (
            "raport finansowy" in t
            or "kwartalny raport" in t
            or "półroczny raport" in t
            or "polroczny raport" in t
            or re.search(r"\d_pge_gk_(q1|q3|hy)_", u)
            or "raport_finansowy" in u
        ) and "prezentac" not in t and "szacunk" not in t and "zaproszenie" not in t and "niezbędnik" not in t and "analyst" not in t:
            fname = f"PGE_{year}_{period}_sprawozdanie.pdf"
            found.append((fname, clean_url(full), text[:120]))
        elif "prezentacja inwestorska" in t or (
            "prezentacja" in t and "wyniki" in t and "szacunk" not in t and "konferenc" not in t
        ):
            fname = f"PGE_{year}_{period}_prezentacja.pdf"
            found.append((fname, clean_url(full), text[:120]))
    # dedupe by filename keep first
    seen = set()
    out = []
    for f, u, n in found:
        if f in seen:
            continue
        seen.add(f)
        out.append((f, u, n))
    return out


def pge_pages() -> list[tuple[int, str, str]]:
    """(year, period, hub_url)"""
    rows = []
    for y in range(2020, 2026):
        # Q1
        rows.append((y, "Q1", f"https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/skonsolidowany-raport-kwartalny-za-i-kwartal-{y}-r"))
        # H1 — URL variants
        if y == 2020:
            h1 = "https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/skonsolidowany-raport-kwartalny-za-i-polrocze-2020-r"
        elif y == 2021:
            h1 = "https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/skonsolidowany-raport-polroczny-za-i-polrocze-2021-r"
        else:
            h1 = f"https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/skonsolidowany-raport-za-i-polrocze-{y}-r"
        rows.append((y, "H1", h1))
        # Q3
        rows.append((y, "Q3", f"https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/skonsolidowany-raport-kwartalny-za-iii-kwartal-{y}-r"))
    return rows


# Tauron: predictable ashx paths from earlier discovery
def tpe_files() -> list[tuple[str, str, str, str]]:
    """(ticker, filename, url, note)"""
    files = []
    # Known patterns from IR page 2020-2025
    # Prefer skonsolidowane sprawozdanie for Q1/Q3; for H1 prefer skonsolidowane sprawozdanie or rozszerzony
    known = {
        # 2025
        ("2025", "Q1"): "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2025/i-kwartal/tauron-pe-skonsolidowane-sprawozdanie-fin-za-i-kw-2025-r.ashx",
        ("2025", "H1"): "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2025/i-polrocze/skonsolidowane-sprawozdanie-finansowe-gk-tpe-za-i-polrocze-2025.ashx",
        ("2025", "Q3"): "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2025/iii-kwartal/skonsolidowane-sprawozdanie-finansowe-za-iii-kwartal-2025-r.ashx",
        # 2024
        ("2024", "Q1"): "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2024/i-kwartal/tauron-pe-skonsolidowane-sprawozdanie-fin-za-i-kw-2024-r.ashx",
        ("2024", "H1"): "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2024/i-polrocze/skonsolidowane-sprawozdanie-finansowe-grupy-kapitalowej-tauron-za-i-polrocze-2024.ashx",
        ("2024", "Q3"): "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2024/iii-kwartal/tauron-pe-skonsolidowane-sprawozdanie-finansowe-za-iii-kwartal-2024-r.ashx",
        # 2023
        ("2023", "Q1"): "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2023/i-kwartal/skonsolidowane-sprawozdanie-finansowe-za-i-kwartal-2023-r.ashx",
        ("2023", "H1"): "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2023/i-polrocze/skonsolidowane-sprawozdanie-finansowe-gk-tpe-za-i-polr-2023.ashx",
        ("2023", "Q3"): "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2023/iii-kwartal/skonsolidowane-sprawozdanie-finansowe-za-iii-kwartal-2023-r.ashx",
        # 2022
        ("2022", "Q1"): "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2022/i-kwartal/tauron_skonsolidowany_raport_za_i_kwartal_2022.ashx",
        ("2022", "H1"): "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2022/i-polrocze/rozszerzony_skonsolidowany_raport_polroczny_za_i_polrocze_2022.ashx",
        ("2022", "Q3"): "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2022/iii-kwartal/rozszerzony_skonsolidowany_raport_kwartalny_za_iii_kwartal_2022_r.ashx",
        # 2021
        ("2021", "Q1"): "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2021/i-kwartal/rozszerzony_skonsolidowany_raport_kwartalny_za_i_kwartal_2021_r.ashx",
        ("2021", "H1"): "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2021/i-polrocze/rozszerzony_skonsolidowany_raport_polroczny_za_i_polrocze_2021_r.ashx",
        ("2021", "Q3"): "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2021/iii-kwartal/rozszerzony_skonsolidowany_raport_kwartalny_za_iii_kwartal_2021_r.ashx",
        # 2020
        ("2020", "Q1"): "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2020/i-kwartal/rozszerzony_skonsolidowany_raport_kwartalny_za_i_kwartal_2020_r.ashx",
        ("2020", "H1"): "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2020/i-polrocze/rozszerzony_skonsolidowany_raport_polroczny_za_i_polrocze_2020_r.ashx",
        ("2020", "Q3"): "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2020/iii-kwartal/rozszerzony_skonsolidowany_raport_kwartalny_za_iii_kwartal_2020_r.ashx",
    }
    for (year, period), url in known.items():
        files.append(("TPE", f"TPE_{year}_{period}_sprawozdanie.pdf", url, "ashx IR"))
    return files


def enea_period_pages() -> list[tuple[int, str, str]]:
    """Scrape listing and return (year, period, page_url)."""
    listing = "https://ir.enea.pl/lista-raportow/kategoria/3612/raporty-okresowe?pageLimit=100"
    html = fetch(listing)
    p = LinkExtractor()
    p.feed(html)
    rows = []
    for href, text in p.links:
        full = urljoin(listing, href)
        t = re.sub(r"\s+", " ", text)
        tl = t.lower()
        # match QSr / PSr
        m_year = re.search(r"(20\d{2})", t)
        if not m_year:
            m_year = re.search(r"(20\d{2})", full)
        if not m_year:
            continue
        year = int(m_year.group(1))
        if year < 2020 or year > 2025:
            continue
        period = None
        if "półrocz" in tl or "polrocz" in tl or "/psr" in full.lower() or "psr-" in full.lower() or "psr " in tl:
            period = "H1"
        elif re.search(r"qsr\s*1|qsr-1|/qsr-1|i kwartał|1\s*/\s*20|qsr 1", tl + full.lower()) or "qsr-1" in full.lower() or "1-202" in full.lower():
            # Q1
            if "3" not in tl.split("kwartał")[0][-5:] if "kwartał" in tl else True:
                if "iii" in tl or "3 /" in tl or "qsr 3" in tl or "qsr-3" in full.lower():
                    period = "Q3"
                elif "1 /" in tl or "qsr 1" in tl or "qsr-1" in full.lower() or "i kwartał" in tl or "1-202" in full:
                    period = "Q1"
        if "qsr-3" in full.lower() or "qsr 3" in tl or "iii kwartał" in tl or "3 / 20" in tl:
            period = "Q3"
        if "qsr-1" in full.lower() or re.search(r"qsr\s*1\s*/", tl) or "1 / 20" in tl:
            if period != "Q3":
                period = "Q1"
        if "psr" in full.lower() or "półroczny" in tl or "polroczny" in tl:
            period = "H1"
        # refine with URL slug
        slug = full.lower()
        if "qsr-1" in slug or "qsr-1-" in slug or "kwartalny-qsr-1" in slug:
            period = "Q1"
        if "qsr-3" in slug or "kwartalny-qsr-3" in slug:
            period = "Q3"
        if "psr" in slug and "qsr" not in slug:
            period = "H1"
        if period and ("skonsolidowany-raport" in slug or "qsr" in slug or "psr" in slug):
            rows.append((year, period, full))
    # dedupe year+period keep first
    seen = set()
    out = []
    for y, p, u in rows:
        key = (y, p)
        if key in seen:
            continue
        seen.add(key)
        out.append((y, p, u))
    return sorted(out, key=lambda x: (x[0], {"Q1": 1, "H1": 2, "Q3": 3}.get(x[1], 9)))


def pick_enea(links: list[tuple[str, str]], year: int, period: str) -> list[tuple[str, str, str]]:
    found = []
    for full, text in links:
        t = re.sub(r"\s+", " ", text).lower()
        if "cdn-netpr" not in full and not full.lower().endswith(".pdf"):
            continue
        if not (".pdf" in full.lower() or full.lower().endswith(".pdf")):
            continue
        # consolidated financial
        if (
            "skonsolidowane sprawozdanie" in t
            or "sprawozdanie finansowe gk" in t
            or "sprawozdanie_finansowe" in full.lower()
            or "skonsolidowane_sprawozdanie" in full.lower()
            or "pozostale_informacje" in full.lower()
            or "pozostałe informacje" in t
            or "rozszerzonego skonsolidowanego" in t
        ):
            # prefer actual SSF over "pozostałe informacje"
            if "pozosta" in t or "pozostale" in full.lower():
                fname = f"ENA_{year}_{period}_pozostale.pdf"
            else:
                fname = f"ENA_{year}_{period}_sprawozdanie.pdf"
            found.append((fname, full, text[:120]))
        elif "prezentac" in t:
            found.append((f"ENA_{year}_{period}_prezentacja.pdf", full, text[:120]))
        elif "sprawozdanie zarządu" in t or "sprawozdanie zarzadu" in t or "sprawozdanie_zarzadu" in full.lower():
            found.append((f"ENA_{year}_{period}_sprawozdanie-zarzadu.pdf", full, text[:120]))
    # prefer SSF first; if only pozostałe and no ssf, keep
    seen = set()
    out = []
    for f, u, n in found:
        if f in seen:
            continue
        seen.add(f)
        out.append((f, u, n))
    # if we have both ssf and pozostale, drop pozostale for space? keep both optional - drop pozostale
    out = [x for x in out if "_pozostale" not in x[0] or not any(y[0].endswith("_sprawozdanie.pdf") for y in out)]
    return out


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    files: list[dict] = []

    print("=== PGE pages ===")
    for year, period, url in pge_pages():
        print(f"  {year} {period} {url}")
        try:
            ls = links_on(url)
        except Exception as e:
            print(f"    ERR {e}")
            files.append(
                {
                    "ticker": "PGE",
                    "year": year,
                    "period": period,
                    "file": f"PGE_{year}_{period}_sprawozdanie.pdf",
                    "url": None,
                    "status": "page_fail",
                    "error": str(e),
                    "page": url,
                }
            )
            continue
        picks = pick_pge(ls, year, period)
        if not picks:
            print("    NO PICK")
            files.append(
                {
                    "ticker": "PGE",
                    "year": year,
                    "period": period,
                    "file": f"PGE_{year}_{period}_sprawozdanie.pdf",
                    "url": None,
                    "status": "no_link",
                    "page": url,
                }
            )
        for fname, furl, note in picks:
            print(f"    + {fname} <- {furl[:80]} | {note[:50]}")
            files.append(
                {
                    "ticker": "PGE",
                    "year": year,
                    "period": period,
                    "file": fname,
                    "url": furl,
                    "status": "ready",
                    "note": note,
                    "page": url,
                }
            )

    print("\n=== TPE known ashx ===")
    for ticker, fname, url, note in tpe_files():
        year = int(fname.split("_")[1])
        period = fname.split("_")[2]
        print(f"  + {fname}")
        files.append(
            {
                "ticker": ticker,
                "year": year,
                "period": period,
                "file": fname,
                "url": url,
                "status": "ready",
                "note": note,
            }
        )

    print("\n=== ENA listing + pages ===")
    try:
        enea_pages = enea_period_pages()
        print(f"  found {len(enea_pages)} period pages")
        for y, p, u in enea_pages:
            print(f"  {y} {p} {u}")
    except Exception as e:
        print("ENA listing ERR", e)
        enea_pages = []

    for year, period, url in enea_pages:
        try:
            ls = links_on(url)
        except Exception as e:
            print(f"    ERR {e}")
            files.append(
                {
                    "ticker": "ENA",
                    "year": year,
                    "period": period,
                    "file": f"ENA_{year}_{period}_sprawozdanie.pdf",
                    "url": None,
                    "status": "page_fail",
                    "error": str(e),
                    "page": url,
                }
            )
            continue
        picks = pick_enea(ls, year, period)
        if not picks:
            print(f"    NO PICK {year} {period}")
            # dump pdf candidates
            for full, text in ls:
                if ".pdf" in full.lower() or "cdn-netpr" in full:
                    print(f"      cand [{text[:60]}] {full[:100]}")
            files.append(
                {
                    "ticker": "ENA",
                    "year": year,
                    "period": period,
                    "file": f"ENA_{year}_{period}_sprawozdanie.pdf",
                    "url": None,
                    "status": "no_link",
                    "page": url,
                }
            )
        for fname, furl, note in picks:
            # only keep main sprawozdanie (+ optional zarzad for H1 if small set)
            if not fname.endswith("_sprawozdanie.pdf") and not fname.endswith("_prezentacja.pdf"):
                # keep zarzad only for H1
                if not (period == "H1" and "zarzadu" in fname):
                    continue
            print(f"    + {fname}")
            files.append(
                {
                    "ticker": "ENA",
                    "year": year,
                    "period": period,
                    "file": fname,
                    "url": furl,
                    "status": "ready",
                    "note": note,
                    "page": url,
                }
            )

    OUT.write_text(json.dumps(files, ensure_ascii=False, indent=2), encoding="utf-8")
    ready = [f for f in files if f.get("status") == "ready" and f.get("url")]
    print(f"\nReady downloads: {len(ready)} / total entries {len(files)}")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
