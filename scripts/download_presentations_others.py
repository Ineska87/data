#!/usr/bin/env python3
"""Download earnings/investor presentations for TPE, ENA, ZEP, UNT, JSW (2020-2025)."""

from __future__ import annotations

import json
import re
import ssl
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

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

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self._href = href
                self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._text).strip()))
            self._href = None


def fetch(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=CTX, timeout=timeout) as r:
        return r.read()


def links_on(url: str) -> list[tuple[str, str]]:
    html = fetch(url).decode("utf-8", errors="replace")
    p = LinkExtractor()
    p.feed(html)
    return [(urljoin(url, h), re.sub(r"\s+", " ", t).strip()) for h, t in p.links]


def year_period(blob: str) -> tuple[int | None, str | None]:
    b = blob.lower()
    year = None
    for m in re.finditer(r"(202[0-5])", b):
        year = int(m.group(1))
    period = None
    if re.search(r"\bq4\b|iv\s*kw|4q|fy\b|rok\s*20|za\s*rok|annual|full.?year|wyniki\s*roczne|za\s*202", b):
        # annual often with year
        if re.search(r"\bq4\b|iv\s*kw|4q|fy|full.?year|wyniki\s*(za\s*)?rok|raport\s*roczny.*prezent|prezent.*roczny|za\s*rok\s*202", b):
            period = "Q4"
    if re.search(r"\bq3\b|iii\s*kw|3q|9\s*mies", b):
        period = "Q3"
    if re.search(r"\bh1\b|\bhy\b|1h|i\s*p[oó][łl]rocz|p[oó][łl]rocz|6\s*mies|1p\b", b):
        period = "H1"
    if re.search(r"\bq1\b|i\s*kw|1q|3\s*mies", b) and period is None:
        period = "Q1"
    if period is None and re.search(r"\bq4\b|iv\s*kw|4q|fy\b|full.?year", b):
        period = "Q4"
    return year, period


def is_presentation(url: str, text: str) -> bool:
    b = (url + " " + text).lower()
    if any(k in b for k in (".xades", ".xhtml", "webcast", "mp4", "youtube", "transkrypt", "transcript")):
        return False
    if not any(k in b for k in (".pdf", ".ashx", "download", "prezent", "presentation", "investor", "wyniki")):
        return False
    # positive
    if any(
        k in b
        for k in (
            "prezentac",
            "presentation",
            "investor presentation",
            "wyniki finansowe",
            "earnings",
            "deck",
            "ir-presentation",
            "prezentacja-wyniki",
            "prezentacja_wyniki",
            "prezentacja-inwestorska",
        )
    ):
        return True
    # Tauron ashx with prezent in path
    if "prezent" in b and (".pdf" in b or ".ashx" in b):
        return True
    return False


def score_pres(url: str, text: str) -> int:
    b = (url + " " + text).lower()
    s = 0
    if "prezentac" in b:
        s += 20
    if "wyniki" in b:
        s += 10
    if "inwestorsk" in b or "investor" in b:
        s += 8
    if "konferenc" in b:
        s += 5
    if "factsheet" in b or "one-pager" in b or "onepager" in b:
        s -= 15
    if "szacunk" in b or "estimate" in b:
        s -= 5
    if ".pdf" in b:
        s += 5
    if "esg" in b and "wyniki" not in b:
        s -= 10
    if "strateg" in b and "wyniki" not in b:
        s -= 8
    return s


# ---------- collectors ----------

def collect_tpe() -> list[dict]:
    print("\n=== TPE ===")
    out = []
    pages = [
        "https://www.tauron.pl/tauron/relacje-inwestorskie/prezentacje",
        "https://www.tauron.pl/tauron/relacje-inwestorskie",
    ]
    for page in pages:
        try:
            ls = links_on(page)
        except Exception as e:
            print(" ERR", e)
            continue
        for full, text in ls:
            if not is_presentation(full, text) and "prezent" not in (full + text).lower():
                continue
            if not any(x in full.lower() for x in (".pdf", ".ashx", "offer-documents", "media")):
                continue
            y, p = year_period(full + " " + text)
            if not y or y < 2020 or y > 2025:
                # try path year
                m = re.search(r"/(\d{4})/", full)
                if m:
                    y = int(m.group(1))
            if not y or y < 2020 or y > 2025:
                continue
            if not p:
                # filename heuristics
                fl = full.lower()
                if "4q" in fl or "q4" in fl or "fy" in fl:
                    p = "Q4"
                elif "3q" in fl or "q3" in fl:
                    p = "Q3"
                elif "1h" in fl or "h1" in fl or "hy" in fl or "polrocz" in fl:
                    p = "H1"
                elif "1q" in fl or "q1" in fl:
                    p = "Q1"
            if not p:
                continue
            out.append(
                {
                    "ticker": "TPE",
                    "year": y,
                    "period": p,
                    "url": full.split("?")[0] if ".ashx" in full else full,
                    "note": text[:120],
                    "score": score_pres(full, text),
                    "page": page,
                }
            )
            print(f"  + {y} {p}: {text[:60]}")
    return out


def collect_ena() -> list[dict]:
    print("\n=== ENA ===")
    out = []
    pages = [
        "https://ir.enea.pl/",
        "https://ir.enea.pl/prezentacje",
        "https://ir.enea.pl/wyniki-finansowe",
        "https://ir.enea.pl/centrum-pobierania-plikow",
        "https://media.enea.pl/",
    ]
    # also search year result pages if exist
    for y in range(2020, 2026):
        pages.append(f"https://ir.enea.pl/wyniki/{y}")
        pages.append(f"https://ir.enea.pl/prezentacje/{y}")
    for page in pages:
        try:
            ls = links_on(page)
        except Exception as e:
            print(" ERR", page, e)
            continue
        for full, text in ls:
            b = (full + " " + text).lower()
            if "cdn-netpr" not in full and ".pdf" not in b and "download" not in b and "prezent" not in b:
                continue
            if not (is_presentation(full, text) or "prezent" in b):
                continue
            y, p = year_period(full + " " + text)
            if not y or y < 2020 or y > 2025 or not p:
                continue
            out.append(
                {
                    "ticker": "ENA",
                    "year": y,
                    "period": p,
                    "url": full,
                    "note": text[:120],
                    "score": score_pres(full, text),
                    "page": page,
                }
            )
            print(f"  + {y} {p}: {text[:60]}")
    return out


def collect_zep() -> list[dict]:
    print("\n=== ZEP ===")
    out = []
    pages = [
        "https://ri.zepak.com.pl/pl/prezentacje.html",
        "https://ri.zepak.com.pl/pl/",
    ]
    for page in pages:
        try:
            ls = links_on(page)
        except Exception as e:
            print(" ERR", e)
            continue
        for full, text in ls:
            b = (full + " " + text).lower()
            if ".pdf" not in b and "upload" not in b:
                continue
            if not (is_presentation(full, text) or "prezent" in b or "wyniki" in b):
                continue
            # normalize upload url
            m = re.search(r"/upload/files/([^/?]+\.pdf)", full, re.I)
            if m:
                full = f"https://ri.zepak.com.pl/upload/files/{m.group(1)}"
            elif "/pl/raporty/" in full and "/upload/files/" in full:
                m2 = re.search(r"/upload/files/([^/?]+\.pdf)", full, re.I)
                if m2:
                    full = f"https://ri.zepak.com.pl/upload/files/{m2.group(1)}"
            y, p = year_period(full + " " + text)
            if not y:
                m = re.search(r"(202[0-5])", unquote(full))
                if m:
                    y = int(m.group(1))
            if not y or y < 2020 or y > 2025:
                continue
            if not p:
                fl = full.lower()
                if "4q" in fl or "q4" in fl or "fy" in fl or "roczne" in fl or "-r_" in fl:
                    p = "Q4"
                elif "3q" in fl or "q3" in fl:
                    p = "Q3"
                elif "1h" in fl or "h1" in fl or "1p" in fl or "polrocz" in fl:
                    p = "H1"
                elif "1q" in fl or "q1" in fl:
                    p = "Q1"
            if not p:
                continue
            out.append(
                {
                    "ticker": "ZEP",
                    "year": y,
                    "period": p,
                    "url": full.split("?")[0],
                    "note": text[:120],
                    "score": score_pres(full, text),
                    "page": page,
                }
            )
            print(f"  + {y} {p}: {text[:60] or Path(unquote(full)).name[:60]}")
    return out


def collect_unt() -> list[dict]:
    print("\n=== UNT ===")
    out = []
    pages = [
        "https://www.unimot.pl/relacje-inwestorskie/materialy-informacyjne/centrum-wynikowe",
        "https://www.unimot.pl/relacje-inwestorskie/raporty-i-strategia/raporty-okresowe",
        "https://www.unimot.pl/relacje-inwestorskie",
    ]
    for page in pages:
        try:
            ls = links_on(page)
        except Exception as e:
            print(" ERR", e)
            continue
        for full, text in ls:
            b = (full + " " + text).lower()
            if "prezent" not in b and "presentation" not in b:
                continue
            if "/media/" not in full:
                continue
            y, p = year_period(full + " " + text)
            if not y or y < 2020 or y > 2025 or not p:
                continue
            out.append(
                {
                    "ticker": "UNT",
                    "year": y,
                    "period": p,
                    "url": full,
                    "note": text[:120],
                    "score": score_pres(full, text),
                    "page": page,
                }
            )
            print(f"  + {y} {p}: {text[:60]}")
    return out


def collect_jsw() -> list[dict]:
    print("\n=== JSW ===")
    out = []
    pages = [
        "https://www.jsw.pl/relacje-inwestorskie/raporty-gieldowe/prezentacje",
        "https://www.jsw.pl/relacje-inwestorskie/prezentacje",
        "https://www.jsw.pl/relacje-inwestorskie",
    ]
    for y in range(2020, 2026):
        pages.append(
            f"https://www.jsw.pl/relacje-inwestorskie/raporty-gieldowe/raporty-okresowe/raporty-okresowe-{y}"
        )
        pages.append(f"https://www.jsw.pl/relacje-inwestorskie/raporty-gieldowe/prezentacje/{y}")
    for page in pages:
        try:
            ls = links_on(page)
        except Exception as e:
            print(" ERR", page[-40:], e)
            continue
        for full, text in ls:
            b = (full + " " + text).lower()
            if not (is_presentation(full, text) or "prezent" in b):
                continue
            if not any(x in b for x in (".pdf", "fileadmin", "download", "prezent")):
                continue
            y, p = year_period(full + " " + text)
            if not y:
                m = re.search(r"/(202[0-5])/", full)
                if m:
                    y = int(m.group(1))
            if not y or y < 2020 or y > 2025:
                continue
            if not p:
                fl = full.lower()
                if "4q" in fl or "q4" in fl or "fy" in fl or "1y" in fl or "roczne" in fl:
                    p = "Q4"
                elif "3q" in fl or "q3" in fl:
                    p = "Q3"
                elif "1h" in fl or "h1" in fl or "hy" in fl:
                    p = "H1"
                elif "1q" in fl or "q1" in fl:
                    p = "Q1"
            if not p:
                continue
            out.append(
                {
                    "ticker": "JSW",
                    "year": y,
                    "period": p,
                    "url": full.split("?")[0],
                    "note": text[:120],
                    "score": score_pres(full, text),
                    "page": page,
                }
            )
            print(f"  + {y} {p}: {text[:60]}")
    return out


def pick_best(items: list[dict]) -> list[dict]:
    by: dict[tuple, list[dict]] = defaultdict(list)
    for it in items:
        by[(it["ticker"], it["year"], it["period"])].append(it)
    ready = []
    for key, group in sorted(by.items()):
        ticker, year, period = key
        best = sorted(group, key=lambda x: x.get("score", 0), reverse=True)[0]
        fname = f"{ticker}_{year}_{period}_prezentacja.pdf"
        ready.append({**best, "file": fname, "status": "ready"})
    return ready


def download_one(ticker: str, name: str, url: str) -> dict:
    out_dir = BASE / ticker
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    if path.exists() and path.stat().st_size > 40_000:
        head = path.read_bytes()[:5]
        if head.startswith(b"%PDF"):
            return {"ticker": ticker, "file": name, "url": url, "status": "skip_exists", "bytes": path.stat().st_size}
    last = None
    for attempt in range(1, 4):
        try:
            data = fetch(url, timeout=180)
            if len(data) < 20_000:
                raise ValueError(f"too_small {len(data)}")
            if not data.startswith(b"%PDF"):
                # ashx may still be pdf
                if b"%PDF" in data[:1024]:
                    data = data[data.find(b"%PDF") :]
                else:
                    raise ValueError(f"not PDF head={data[:40]!r}")
            path.write_bytes(data)
            return {"ticker": ticker, "file": name, "url": url, "status": "ok", "bytes": len(data)}
        except Exception as e:
            last = e
            time.sleep(1.0 * attempt)
    return {"ticker": ticker, "file": name, "url": url, "status": "fail", "error": str(last)}


def main() -> None:
    raw: list[dict] = []
    raw.extend(collect_tpe())
    raw.extend(collect_ena())
    raw.extend(collect_zep())
    raw.extend(collect_unt())
    raw.extend(collect_jsw())

    ready = pick_best(raw)
    print(f"\nReady unique presentations: {len(ready)} (raw {len(raw)})")
    for r in ready:
        print(f"  {r['file']} score={r.get('score')} <- {r['url'][:90]}")

    list_path = DATA_ROOT / "metadata" / "download_manifests" / "_presentations_ready.json"
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
        "scope": "Prezentacje wynikowe TPE/ENA/ZEP/UNT/JSW 2020-2025",
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "n_ok": sum(1 for x in results if x["status"] in ("ok", "skip_exists")),
        "n_fail": sum(1 for x in results if x["status"] == "fail"),
        "files": results,
    }
    man = BASE / "manifest_presentations_others.json"
    man.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nManifest {man}")
    print(f"OK/skip={manifest['n_ok']} fail={manifest['n_fail']} / {len(results)}")
    if manifest["n_fail"]:
        print("Failures:")
        for x in results:
            if x["status"] == "fail":
                print(f"  - {x['file']}: {x.get('error')}")


if __name__ == "__main__":
    main()
