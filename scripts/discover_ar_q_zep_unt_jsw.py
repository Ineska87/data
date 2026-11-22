#!/usr/bin/env python3
"""Discover AR + Q/H1 report links for ZEP, UNT, JSW (2020-2025)."""

from __future__ import annotations

import json
import re
import ssl
import urllib.request
from html.parser import HTMLParser

from data_paths import DATA_ROOT
from urllib.parse import urljoin, unquote

CTX = ssl.create_default_context()
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pl-PL,pl;q=0.9",
}
OUT = DATA_ROOT / "metadata" / "download_manifests" / "_zep_unt_jsw_url_list.json"


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


def fetch(url: str, timeout: int = 90) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=CTX, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def links_on(url: str) -> list[tuple[str, str]]:
    html = fetch(url)
    p = LinkExtractor()
    p.feed(html)
    return [(urljoin(url, h), re.sub(r"\s+", " ", t).strip()) for h, t in p.links]


def year_in(s: str) -> int | None:
    m = re.search(r"(20(?:2[0-5]|1[9]))", s)
    return int(m.group(1)) if m else None


def classify_period(text: str, url: str) -> str | None:
    blob = (text + " " + url).lower()
    # annual
    if any(
        k in blob
        for k in (
            "raport roczny",
            "raport-roczny",
            "skonsolidowany raport roczny",
            "skonsolidowane sprawozdanie finansowe",
            "za rok",
            "roczny za",
            "annual",
            "/roczny",
            "r_sprawozdanie",
            "rr-",
            "srr",
        )
    ):
        # exclude if clearly quarter
        if not any(k in blob for k in ("kwartal", "półrocz", "polrocz", "q1", "q3", "hy", "i kwart", "iii")):
            # "za rok 2024" annual
            if re.search(r"za\s+rok|raport\s+roczny|roczny\s+za|/roczny|rr\s|srr", blob):
                return "AR"
    if any(k in blob for k in ("i półrocz", "i polrocz", "półroczny", "polroczny", "hy", "h1", "1h", "psr", "za i półrocze", "za i polrocze", "pierwsze półrocze")):
        return "H1"
    if any(k in blob for k in ("iii kwart", "3 kwart", "q3", "qsr 3", "qsr-3", "9 miesi", "za iii")):
        return "Q3"
    if any(k in blob for k in ("i kwart", "1 kwart", "q1", "qsr 1", "qsr-1", "3 miesi", "za i kwart")):
        return "Q1"
    if "roczny" in blob and "kwartal" not in blob and "półrocz" not in blob and "polrocz" not in blob:
        return "AR"
    return None


def is_pdfish(url: str) -> bool:
    u = url.lower()
    return any(x in u for x in (".pdf", ".zip", ".7z", "upload/files", "download", "media/", "fileadmin"))


# ---------- ZEP ----------
def discover_zep() -> list[dict]:
    print("\n########## ZEP ##########")
    base = "https://ri.zepak.com.pl/pl/raporty/raporty-okresowe.html"
    files: list[dict] = []
    try:
        top = links_on(base)
    except Exception as e:
        print("ZEP hub ERR", e)
        return files
    print(f"hub links: {len(top)}")
    # collect year/detail pages + direct PDFs
    detail_pages = []
    for full, text in top:
        y = year_in(full + " " + text)
        if y and 2020 <= y <= 2025:
            if full.endswith(".html") or "raporty-okresowe" in full:
                detail_pages.append((y, full, text))
            if is_pdfish(full) or full.lower().endswith(".pdf"):
                print(f"  direct [{text[:70]}] {full[:120]}")
    # also try year index if any
    # scrape all detail pages for 2020-2025
    # listing page may have rows linking to individual report pages
    seen_pages = set()
    for y, full, text in detail_pages:
        if full in seen_pages:
            continue
        # only report pages, not filters
        if "raporty-okresowe.html" == full.rstrip("/").split("/")[-1]:
            continue
        seen_pages.add(full)
        print(f"  page {y}: {full}")
        try:
            ls = links_on(full)
        except Exception as e:
            print("   ERR", e)
            continue
        for furl, ftext in ls:
            if not (is_pdfish(furl) or ".pdf" in furl.lower() or "/upload/" in furl.lower()):
                continue
            period = classify_period(ftext + " " + text, furl)
            # refine AR from parent page title
            parent_l = text.lower()
            if "roczny" in parent_l and period is None:
                period = "AR"
            if "kwartal" in parent_l and "i " in parent_l and period is None:
                period = "Q1"
            kind = "other"
            tl = (ftext + " " + furl).lower()
            if any(k in tl for k in ("skonsolidowan", "ssf", "gk", "grupy")) and any(
                k in tl for k in ("sprawozdanie finans", "raport finans", "skonsolidowany raport", ".pdf")
            ):
                kind = "sprawozdanie"
            elif "zarząd" in tl or "zarzad" in tl or "zarzadu" in tl:
                kind = "sprawozdanie-zarzadu"
            elif "prezentac" in tl:
                kind = "prezentacja"
            elif "skonsolidowan" in tl or "sprawozdanie" in tl or "raport" in tl:
                kind = "sprawozdanie"
            if period is None:
                period = classify_period(text, full) or "UNK"
            print(f"    [{period}/{kind}] {ftext[:60]} -> {furl[-80:]}")
            files.append(
                {
                    "ticker": "ZEP",
                    "year": y,
                    "period": period,
                    "kind": kind,
                    "file": None,
                    "url": furl.split("?")[0],
                    "note": ftext[:120],
                    "page": full,
                    "status": "raw",
                }
            )
    # also parse hub for direct PDF upload links with year
    for full, text in top:
        if "/upload/" in full or full.lower().endswith(".pdf"):
            y = year_in(full + " " + text)
            if not y or y < 2020 or y > 2025:
                continue
            period = classify_period(text, full) or "UNK"
            files.append(
                {
                    "ticker": "ZEP",
                    "year": y,
                    "period": period,
                    "kind": "sprawozdanie",
                    "file": None,
                    "url": full.split("?")[0],
                    "note": text[:120],
                    "page": base,
                    "status": "raw",
                }
            )
    return files


# ---------- UNT ----------
def discover_unt() -> list[dict]:
    print("\n########## UNT ##########")
    pages = [
        "https://www.unimot.pl/relacje-inwestorskie/raporty-i-strategia/raporty-okresowe",
        "https://www.unimot.pl/relacje-inwestorskie/materialy-informacyjne/centrum-wynikowe",
    ]
    # may have pagination
    for i in range(2, 8):
        pages.append(f"https://www.unimot.pl/relacje-inwestorskie/raporty-i-strategia/raporty-okresowe?page={i}")
    files: list[dict] = []
    seen = set()
    for page in pages:
        print(f"  page {page}")
        try:
            ls = links_on(page)
        except Exception as e:
            print("  ERR", e)
            continue
        for full, text in ls:
            if full in seen:
                continue
            if not (is_pdfish(full) or "/media/" in full or ".pdf" in full.lower() or "download" in full.lower()):
                # sometimes report is intermediate page
                if "raport" in (full + text).lower() and "aktualnosci" not in full:
                    pass
                else:
                    continue
            y = year_in(full + " " + text)
            if not y or y < 2020 or y > 2025:
                continue
            seen.add(full)
            period = classify_period(text, full) or "UNK"
            kind = "sprawozdanie"
            tl = (text + " " + full).lower()
            if "prezentac" in tl:
                kind = "prezentacja"
            elif "zarząd" in tl or "zarzad" in tl:
                kind = "sprawozdanie-zarzadu"
            print(f"    [{y} {period}/{kind}] {text[:60]} -> {full[-90:]}")
            files.append(
                {
                    "ticker": "UNT",
                    "year": y,
                    "period": period,
                    "kind": kind,
                    "file": None,
                    "url": full.split("?")[0] if ".pdf" in full.lower() else full,
                    "note": text[:120],
                    "page": page,
                    "status": "raw",
                }
            )
    return files


# ---------- JSW ----------
def discover_jsw() -> list[dict]:
    print("\n########## JSW ##########")
    files: list[dict] = []
    for y in range(2020, 2026):
        url = f"https://www.jsw.pl/relacje-inwestorskie/raporty-gieldowe/raporty-okresowe/raporty-okresowe-{y}"
        print(f"  year {y}: {url}")
        try:
            ls = links_on(url)
        except Exception as e:
            print("  ERR", e)
            continue
        # JSW often links to detail pages then files; also direct fileadmin
        subpages = []
        for full, text in ls:
            blob = (full + " " + text).lower()
            if any(
                k in blob
                for k in (
                    "skonsolidowany",
                    "roczny",
                    "kwartal",
                    "półrocz",
                    "polrocz",
                    "sprawozdanie",
                    "fileadmin",
                    ".pdf",
                    "raport",
                )
            ):
                if full.lower().endswith((".pdf", ".zip", ".7z")) or "fileadmin" in full or "download" in full:
                    period = classify_period(text, full)
                    if period is None:
                        if "roczny" in blob:
                            period = "AR"
                        elif "9 mies" in blob or "iii" in blob:
                            period = "Q3"
                        elif "półrocz" in blob or "polrocz" in blob or "6 mies" in blob:
                            period = "H1"
                        elif "3 mies" in blob or "i kwart" in blob:
                            period = "Q1"
                        else:
                            period = "UNK"
                    kind = "sprawozdanie"
                    if "prezentac" in blob:
                        kind = "prezentacja"
                    elif "zarząd" in blob or "zarzad" in blob:
                        kind = "sprawozdanie-zarzadu"
                    print(f"    [{period}/{kind}] {text[:70]}")
                    files.append(
                        {
                            "ticker": "JSW",
                            "year": y,
                            "period": period or "UNK",
                            "kind": kind,
                            "file": None,
                            "url": full.split("?")[0],
                            "note": text[:120],
                            "page": url,
                            "status": "raw",
                        }
                    )
                elif "raporty-okresowe" in full or "raport" in full:
                    subpages.append((full, text))
        # follow a few subpages (consolidated annual etc.)
        for full, text in subpages[:30]:
            if full == url:
                continue
            if not any(k in (full + text).lower() for k in ("skonsolid", "roczny", "kwartal", "półrocz", "polrocz", "raport")):
                continue
            try:
                sub = links_on(full)
            except Exception:
                continue
            for furl, ftext in sub:
                if not (furl.lower().endswith((".pdf", ".zip")) or "fileadmin" in furl or "download" in furl.lower()):
                    continue
                period = classify_period(ftext + " " + text, furl)
                if period is None:
                    period = classify_period(text, full) or "UNK"
                kind = "sprawozdanie"
                bl = (ftext + furl).lower()
                if "prezentac" in bl:
                    kind = "prezentacja"
                elif "zarzad" in bl or "zarząd" in bl:
                    kind = "sprawozdanie-zarzadu"
                print(f"    sub [{period}/{kind}] {ftext[:60]}")
                files.append(
                    {
                        "ticker": "JSW",
                        "year": y,
                        "period": period,
                        "kind": kind,
                        "file": None,
                        "url": furl.split("?")[0],
                        "note": ftext[:120],
                        "page": full,
                        "status": "raw",
                    }
                )
    return files


def assign_filenames(rows: list[dict]) -> list[dict]:
    """Pick best report per ticker/year/period and assign names."""
    # group
    from collections import defaultdict

    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        if r.get("period") == "UNK" or not r.get("url"):
            continue
        # only keep main report kinds for download priority
        groups[(r["ticker"], r["year"], r["period"])].append(r)

    out: list[dict] = []
    for key, items in sorted(groups.items()):
        ticker, year, period = key
        # score items
        def score(r: dict) -> int:
            note = (r.get("note") or "").lower()
            url = (r.get("url") or "").lower()
            kind = r.get("kind") or ""
            s = 0
            if kind == "sprawozdanie":
                s += 20
            if kind == "sprawozdanie-zarzadu":
                s += 12
            if kind == "prezentacja":
                s += 8
            if "skonsolid" in note or "skonsolid" in url or "gk" in note:
                s += 15
            if "jednostkow" in note or "jednostkow" in url:
                s -= 10
            if period == "AR" and ("roczny" in note or "roczny" in url or "za rok" in note):
                s += 10
            if ".pdf" in url:
                s += 5
            if ".zip" in url or ".7z" in url:
                s += 3
            if "prezentac" in note:
                s += 2 if kind == "prezentacja" else -5
            return s

        items_sorted = sorted(items, key=score, reverse=True)
        # pick best sprawozdanie
        best_report = next((i for i in items_sorted if i.get("kind") == "sprawozdanie" or "skonsolid" in (i.get("note") or "").lower()), items_sorted[0])
        # presentation if any
        best_pres = next((i for i in items_sorted if i.get("kind") == "prezentacja"), None)
        best_sz = next((i for i in items_sorted if i.get("kind") == "sprawozdanie-zarzadu"), None)

        def make(r: dict, kind_suffix: str) -> dict:
            if period == "AR":
                fname = f"{ticker}_{year}_AR_{kind_suffix}.pdf"
            else:
                fname = f"{ticker}_{year}_{period}_{kind_suffix}.pdf"
            # fix extension if zip
            if r["url"].lower().endswith(".zip"):
                fname = fname.replace(".pdf", ".zip")
            elif r["url"].lower().endswith(".7z"):
                fname = fname.replace(".pdf", ".7z")
            return {
                "ticker": ticker,
                "year": year,
                "period": period,
                "file": fname,
                "url": r["url"],
                "note": r.get("note"),
                "page": r.get("page"),
                "status": "ready",
            }

        # for AR: prefer skonsolidowany as _skonsolidowany
        if period == "AR":
            out.append(make(best_report, "skonsolidowany" if "skonsolid" in (best_report.get("note") or best_report.get("url") or "").lower() or best_report.get("kind") == "sprawozdanie" else "sprawozdanie"))
            # rename first AR to skonsolidowany always if report
            out[-1]["file"] = f"{ticker}_{year}_AR_skonsolidowany" + (".zip" if out[-1]["url"].lower().endswith(".zip") else ".pdf")
            if best_sz:
                out.append(make(best_sz, "sprawozdanie-zarzadu"))
            if best_pres:
                out.append(make(best_pres, "prezentacja"))
        else:
            out.append(make(best_report, "sprawozdanie"))
            if best_pres and ticker in ("ZEP", "JSW", "UNT"):
                out.append(make(best_pres, "prezentacja"))
            if best_sz and period == "H1":
                out.append(make(best_sz, "sprawozdanie-zarzadu"))
    return out


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    raw: list[dict] = []
    raw.extend(discover_zep())
    raw.extend(discover_unt())
    raw.extend(discover_jsw())
    ready = assign_filenames(raw)
    payload = {"raw_count": len(raw), "ready_count": len(ready), "ready": ready, "raw": raw}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nReady: {len(ready)} (raw {len(raw)}) -> {OUT}")
    for r in ready:
        print(f"  {r['file']}")


if __name__ == "__main__":
    main()
