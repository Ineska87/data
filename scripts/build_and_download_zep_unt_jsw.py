#!/usr/bin/env python3
"""Build URL list + download AR and Q1/H1/Q3 for ZEP, UNT, JSW (2020-2025)."""

from __future__ import annotations

import json
import re
import ssl
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser

from data_paths import DATA_ROOT
from urllib.parse import urljoin, unquote

BASE = DATA_ROOT / "raw" / "reports"
CTX = ssl.create_default_context()
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
}


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


def fetch(url: str, timeout: int = 90) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=CTX, timeout=timeout) as r:
        return r.read()


def fetch_html(url: str) -> str:
    return fetch(url).decode("utf-8", errors="replace")


def links_on(url: str) -> list[tuple[str, str]]:
    html = fetch_html(url)
    p = LinkExtractor()
    p.feed(html)
    out = []
    for h, t in p.links:
        full = urljoin(url, h)
        text = re.sub(r"\s+", " ", t).strip()
        out.append((full, text))
    return out


def clean(url: str) -> str:
    return url.split("?")[0]


# ===================== ZEP =====================
def discover_zep() -> list[dict]:
    print("\n=== ZEP ===")
    files: list[dict] = []
    # year filter pages list report detail pages
    for y in range(2020, 2026):
        hub = f"https://ri.zepak.com.pl/pl/raporty/raporty-okresowe.html?y={y}"
        print(f" year hub {y}")
        try:
            ls = links_on(hub)
        except Exception as e:
            print("  hub ERR", e)
            continue
        detail = []
        for full, text in ls:
            if "/raporty/raporty-okresowe/" in full and full.endswith(".html"):
                # skip year filter self
                if "raporty-okresowe.html" in full:
                    continue
                detail.append((full, text))
        print(f"  detail pages: {len(detail)}")
        for page, ptitle in detail:
            # classify period from title
            tl = ptitle.lower() + " " + page.lower()
            if "platnosci" in tl or "płatności" in tl or "platnosci" in page.lower():
                continue
            if "roczny" in tl or "za-20" in page or re.search(r"za-\d{4}-rok", page):
                period = "AR"
            elif "polrocz" in tl or "półrocz" in tl or "polrocze" in page or "polrocze" in tl:
                period = "H1"
            elif "iii" in tl or "3-kwart" in page or "iii-kwart" in page:
                period = "Q3"
            elif "i-kwart" in page or "i kwart" in tl or "1-kwart" in page:
                period = "Q1"
            else:
                # try from title
                if "kwartal" in tl:
                    period = "Q3" if "iii" in tl or "3" in tl else "Q1"
                else:
                    period = "UNK"
            if period == "UNK":
                print(f"  skip UNK {ptitle[:70]}")
                continue
            try:
                pls = links_on(page)
            except Exception as e:
                print(f"  page ERR {page}: {e}")
                continue
            # pick consolidated PDF / SZ PDF
            for furl, ftext in pls:
                u = furl.lower()
                if not (u.endswith(".pdf") or "/upload/files/" in u and u.endswith(".pdf")):
                    # also accept relative upload pdf
                    if ".pdf" not in u:
                        continue
                note = (ftext + " " + unquote(furl)).lower()
                # skip payments, RN, oswiadczenie alone, audit only if not main
                if any(k in note for k in ("platnosci", "płatności", "oswiadczenie", "oświadczenie", "ocena_rn", "atestacja")):
                    if "sprawozdanie_finansowe" not in note and "skonsolidowane" not in note:
                        continue
                kind = None
                if "skonsolidowane_sprawozdanie" in note or "skonsolidowane sprawozdanie" in note or "gk_zepak" in note and "sprawozdanie_finansowe" in note:
                    kind = "skonsolidowany"
                elif "sprawozdanie_finansowe" in note or "sprawozdanie finansowe" in note:
                    # jednostkowe vs skonsolidowane
                    if "skonsolid" in note or "gk" in note:
                        kind = "skonsolidowany"
                    else:
                        # for interim, jednostkowe often not wanted; still for AR keep skonsolid first
                        kind = "jednostkowy"
                elif "zarzadu" in note or "zarządu" in note or "sprawozdanie_zarzadu" in note:
                    kind = "sprawozdanie-zarzadu"
                elif "prezentac" in note:
                    kind = "prezentacja"
                elif period != "AR" and (".pdf" in u) and ("raport" in note or "kwartal" in note or "polrocz" in note):
                    kind = "sprawozdanie"
                if not kind:
                    # fallback: skonsolidowany report page + pdf
                    if period == "AR" and "skonsolidowany-raport-roczny" in page and furl.endswith(".pdf"):
                        if "finansowe" in note or "skonsolidowane" in note:
                            kind = "skonsolidowany"
                        elif "zarzadu" in note:
                            kind = "sprawozdanie-zarzadu"
                    elif period != "AR" and furl.endswith(".pdf") and "skonsolid" in page:
                        kind = "sprawozdanie"
                if not kind:
                    continue
                print(f"  + {y} {period} {kind}: {unquote(furl).split('/')[-1][:70]}")
                files.append(
                    {
                        "ticker": "ZEP",
                        "year": y,
                        "period": period,
                        "kind": kind,
                        "url": clean(furl),
                        "note": ftext[:120] or unquote(furl).split("/")[-1],
                        "page": page,
                    }
                )
    return files


# ===================== UNT =====================
def discover_unt() -> list[dict]:
    print("\n=== UNT ===")
    files: list[dict] = []
    pages = ["https://www.unimot.pl/relacje-inwestorskie/raporty-i-strategia/raporty-okresowe"]
    for i in range(2, 10):
        pages.append(f"https://www.unimot.pl/relacje-inwestorskie/raporty-i-strategia/raporty-okresowe?page={i}")
    seen = set()
    for page in pages:
        print(" page", page)
        try:
            ls = links_on(page)
        except Exception as e:
            print(" ERR", e)
            continue
        for full, text in ls:
            if "/media/" not in full and "download" not in full.lower():
                continue
            if full in seen:
                continue
            # only binary-ish
            low = (full + " " + text).lower()
            if not any(x in low for x in (".pdf", ".zip", "download")):
                continue
            if any(x in low for x in (".xades", ".xhtml", "biegłego", "bieglego", "sbr", "atestacji", "przeglądu", "przegladu", "szr_")):
                # keep SZR only if needed - skip sustainability and audit
                if "sprawozdanie_zarzadu" not in low and "zarzadu" not in low:
                    continue
            if ".xhtml" in low or ".xades" in low:
                if ".pdf" not in low:
                    continue
            # year
            y = None
            for m in re.finditer(r"(202[0-5])", unquote(full) + " " + text):
                y = int(m.group(1))
            if not y:
                continue
            # period
            period = None
            if re.search(r"1q20|q1.?20|1q_20|kwartalny_1q|1q202|q1_202|/1q", low) or "1q20" in low:
                period = "Q1"
            if re.search(r"3q20|q3.?20|3q_20|kwartalny_3q|3q202|q3_202|/3q", low) or "3q20" in low:
                period = "Q3"
            if re.search(r"hy20|h1.?20|hy_20|hy202|i półrocz|i polrocz|półroczn|polroczn|1h20", low) or "hy20" in low:
                period = "H1"
            if period is None:
                # annual: skonsolidowane ... za 202X, unt-202X-12-31
                if re.search(r"12-31|za 202[0-5]|_202[0-5]_12|roczny|annual", low) and not re.search(r"[13]q|hy|kwartal|półrocz|polrocz", low):
                    if "skonsolid" in low or "ssf" in low or "gk unimot" in low or "gk_unimot" in low:
                        period = "AR"
                    elif "zarzadu" in low or "zarządu" in low:
                        period = "AR"
            if period is None:
                continue
            kind = "sprawozdanie"
            if "zarzadu" in low or "zarządu" in low:
                kind = "sprawozdanie-zarzadu"
            elif "prezentac" in low:
                kind = "prezentacja"
            elif period == "AR" and ("skonsolid" in low or "ssf" in low or "gk" in low):
                kind = "skonsolidowany"
            elif period == "AR" and "jednostkow" in low:
                kind = "jednostkowy"
            elif "skonsolid" in low:
                kind = "sprawozdanie"
            elif "jednostkow" in low:
                kind = "jednostkowy"
            # skip pure jednostkowe for interim if we have skonsolid
            seen.add(full)
            url = full if "?" in full and "download" in full else clean(full)
            # prefer keeping query for unimot media sometimes needed - use full with ?v=1 ok
            files.append(
                {
                    "ticker": "UNT",
                    "year": y,
                    "period": period,
                    "kind": kind,
                    "url": full,  # keep full media download URL
                    "note": text[:120],
                    "page": page,
                }
            )
            print(f"  + {y} {period} {kind}: {text[:50]}")
    return files


# ===================== JSW =====================
def discover_jsw() -> list[dict]:
    print("\n=== JSW ===")
    files: list[dict] = []
    for y in range(2020, 2026):
        url = f"https://www.jsw.pl/relacje-inwestorskie/raporty-gieldowe/raporty-okresowe/raporty-okresowe-{y}"
        print(f" year {y}")
        try:
            ls = links_on(url)
        except Exception as e:
            print(" ERR", e)
            continue
        for full, text in ls:
            tl = (text + " " + full).lower()
            # only file links
            if not any(x in full.lower() for x in (".pdf", ".zip", "fileadmin", "download", "tx_news", "file")):
                # jsw often uses /fileadmin/ or path with pdf
                if not re.search(r"\.(pdf|zip)(\?|$)", full.lower()):
                    continue
            # skip junk
            if any(k in tl for k in ("csr 201", "mineral expert", "wardell", "resource base", "raport csr")):
                continue
            period = None
            kind = "sprawozdanie"
            # AR
            if "skonsolidowane sprawozdanie finansowe gk" in tl or "skonsolidowany raport roczny" in tl:
                period = "AR"
                kind = "skonsolidowany"
            elif "sprawozdanie finansowe jsw" in tl and "śródroczne" not in tl and "skrocone" not in tl and "skrócone" not in tl:
                if "za 20" in tl or f"za {y}" in tl:
                    period = "AR"
                    kind = "jednostkowy"
            elif "sprawozdanie zarządu" in tl or "sprawozdanie zarzadu" in tl:
                if "śródroczne" in tl or "okres 6" in tl or "półrocz" in tl or "polrocz" in tl:
                    period = "H1"
                    kind = "sprawozdanie-zarzadu"
                elif "za 20" in tl or f"{y}" in tl and "miesiąc" not in tl:
                    period = "AR"
                    kind = "sprawozdanie-zarzadu"
            # quarters
            if "9 miesiąc" in tl or "9 miesi" in tl or "okres 9" in tl:
                period = "Q3"
                if "skonsolidowane" in tl:
                    kind = "sprawozdanie"
                elif "jednostkow" in tl:
                    kind = "jednostkowy"
                elif "pozostałe" in tl or "pozostale" in tl:
                    kind = "pozostale"
                else:
                    kind = "sprawozdanie"
            elif "6 miesiąc" in tl or "6 miesi" in tl or "okres 6" in tl or "półrocz" in tl or "polrocz" in tl:
                period = "H1"
                if "zarząd" in tl or "zarzad" in tl:
                    kind = "sprawozdanie-zarzadu"
                elif "skonsolidowane" in tl:
                    kind = "sprawozdanie"
                elif "jednostkow" in tl:
                    kind = "jednostkowy"
            elif "3 miesiąc" in tl or "3 miesi" in tl or "okres 3" in tl:
                period = "Q1"
                if "skonsolidowane" in tl:
                    kind = "sprawozdanie"
                elif "jednostkow" in tl:
                    kind = "jednostkowy"
                elif "pozostałe" in tl or "pozostale" in tl:
                    kind = "pozostale"
            if period is None:
                continue
            # only want consolidated main reports (+ SZ for AR/H1)
            if kind in ("jednostkowy", "pozostale"):
                continue
            if kind == "sprawozdanie" and "wybrane dane" in tl:
                continue
            if "biegł" in tl or "biegle" in tl or "rewident" in tl:
                continue
            if "odmowy" in tl or "stanowisko zarządu jsw" in tl:
                continue
            files.append(
                {
                    "ticker": "JSW",
                    "year": y,
                    "period": period,
                    "kind": kind,
                    "url": clean(full),
                    "note": text[:140],
                    "page": url,
                }
            )
            print(f"  + {period}/{kind}: {text[:70]}")
    return files


def pick_ready(raw: list[dict]) -> list[dict]:
    """Select best file per ticker/year/period/kind group for download."""
    # For each (ticker, year, period) pick primary report + optional SZ
    by: dict[tuple, list[dict]] = defaultdict(list)
    for r in raw:
        by[(r["ticker"], r["year"], r["period"])].append(r)

    ready = []
    for (ticker, year, period), items in sorted(by.items()):
        def score(r: dict) -> int:
            k = r.get("kind") or ""
            n = (r.get("note") or "").lower()
            u = (r.get("url") or "").lower()
            s = 0
            if k in ("skonsolidowany", "sprawozdanie"):
                s += 30
            if k == "sprawozdanie-zarzadu":
                s += 20
            if k == "prezentacja":
                s += 10
            if "skonsolid" in n or "skonsolid" in u or "gk" in n:
                s += 15
            if "jednostkow" in n:
                s -= 20
            if u.endswith(".pdf"):
                s += 8
            if u.endswith(".zip"):
                s += 5
            if "platnosci" in n or "płatności" in n:
                s -= 50
            return s

        items = sorted(items, key=score, reverse=True)
        # primary
        primary = next(
            (
                i
                for i in items
                if i.get("kind") in ("skonsolidowany", "sprawozdanie")
            ),
            items[0],
        )
        sz = next((i for i in items if i.get("kind") == "sprawozdanie-zarzadu"), None)
        pres = next((i for i in items if i.get("kind") == "prezentacja"), None)

        def fname(r: dict, suffix: str) -> str:
            ext = ".pdf"
            ul = r["url"].lower()
            if ul.endswith(".zip") or ".zip" in ul.split("?")[0]:
                ext = ".zip"
            if period == "AR":
                return f"{ticker}_{year}_AR_{suffix}{ext}"
            return f"{ticker}_{year}_{period}_{suffix}{ext}"

        if period == "AR":
            ready.append(
                {
                    **primary,
                    "file": fname(primary, "skonsolidowany"),
                    "status": "ready",
                }
            )
            if sz:
                ready.append({**sz, "file": fname(sz, "sprawozdanie-zarzadu"), "status": "ready"})
            if pres:
                ready.append({**pres, "file": fname(pres, "prezentacja"), "status": "ready"})
        else:
            ready.append(
                {
                    **primary,
                    "file": fname(primary, "sprawozdanie"),
                    "status": "ready",
                }
            )
            if sz and period == "H1":
                ready.append({**sz, "file": fname(sz, "sprawozdanie-zarzadu"), "status": "ready"})
            if pres:
                ready.append({**pres, "file": fname(pres, "prezentacja"), "status": "ready"})
    # dedupe by file name keep highest score url
    by_file: dict[str, dict] = {}
    for r in ready:
        f = r["file"]
        if f not in by_file:
            by_file[f] = r
    return list(by_file.values())


def download_one(ticker: str, name: str, url: str, retries: int = 4) -> dict:
    out_dir = BASE / ticker
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    if path.exists() and path.stat().st_size > 20_000:
        return {
            "ticker": ticker,
            "file": name,
            "url": url,
            "status": "skip_exists",
            "bytes": path.stat().st_size,
        }
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            data = fetch(url, timeout=240)
            if len(data) < 10_000:
                raise ValueError(f"too_small {len(data)}")
            head = data[:10]
            if head.lstrip().startswith(b"<") or head.lstrip().startswith(b"<!DOC"):
                # might still be ok for rare cases - reject html
                if b"%PDF" not in data[:1024] and not data.startswith(b"PK"):
                    raise ValueError("got HTML")
            path.write_bytes(data)
            return {
                "ticker": ticker,
                "file": name,
                "url": url,
                "status": "ok",
                "bytes": len(data),
            }
        except Exception as e:
            last_err = e
            time.sleep(1.2 * attempt)
    return {"ticker": ticker, "file": name, "url": url, "status": "fail", "error": str(last_err)}


def main() -> None:
    raw: list[dict] = []
    raw.extend(discover_zep())
    raw.extend(discover_unt())
    raw.extend(discover_jsw())
    ready = pick_ready(raw)
    print(f"\nReady downloads: {len(ready)} (from {len(raw)} raw)")
    for r in sorted(ready, key=lambda x: (x["ticker"], x["year"], x["period"], x["file"])):
        print(f"  {r['file']} <- {r['url'][:90]}")

    list_path = DATA_ROOT / "metadata" / "download_manifests" / "_zep_unt_jsw_ready.json"
    list_path.parent.mkdir(parents=True, exist_ok=True)
    list_path.write_text(json.dumps(ready, ensure_ascii=False, indent=2), encoding="utf-8")

    results = []
    for r in ready:
        print(f"… {r['ticker']}/{r['file']}")
        out = download_one(r["ticker"], r["file"], r["url"])
        results.append(out)
        if out["status"] == "ok":
            print(f"  OK {out['bytes']:,}")
        elif out["status"] == "skip_exists":
            print(f"  SKIP {out['bytes']:,}")
        else:
            print(f"  FAIL {out.get('error')}")
        time.sleep(0.35)

    manifest = {
        "scope": "AR + Q1/H1/Q3 ZEP/UNT/JSW 2020-2025",
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "n_ok": sum(1 for x in results if x["status"] in ("ok", "skip_exists")),
        "n_fail": sum(1 for x in results if x["status"] == "fail"),
        "files": results,
    }
    man = BASE / "manifest_ar_q_zep_unt_jsw.json"
    man.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nManifest {man}")
    print(f"OK/skip={manifest['n_ok']} fail={manifest['n_fail']} / {len(results)}")
    if manifest["n_fail"]:
        print("Failures:")
        for x in results:
            if x["status"] == "fail":
                print(f"  - {x['file']}: {x.get('error')} | {x.get('url')}")


if __name__ == "__main__":
    main()
