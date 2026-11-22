#!/usr/bin/env python3
"""Download ENA investor presentations + remaining ZEP/JSW decks."""

from __future__ import annotations

import json
import re
import ssl
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from data_paths import DATA_ROOT
from urllib.parse import urljoin, unquote, quote

BASE = DATA_ROOT / "raw" / "reports"
CTX = ssl.create_default_context()
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
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


def fetch(url: str) -> bytes:
    parts = urllib.parse.urlsplit(url)
    path = quote(unquote(parts.path), safe="/:@&%=+$,;~*-_.()")
    url2 = urllib.parse.urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))
    req = urllib.request.Request(url2, headers=HEADERS)
    with urllib.request.urlopen(req, context=CTX, timeout=180) as r:
        return r.read()


def links_on(url: str) -> list[tuple[str, str]]:
    html = fetch(url).decode("utf-8", errors="replace")
    p = LinkExtractor()
    p.feed(html)
    return [(urljoin(url, h), re.sub(r"\s+", " ", t).strip()) for h, t in p.links]


def save(ticker: str, name: str, url: str) -> dict:
    out = BASE / ticker
    out.mkdir(parents=True, exist_ok=True)
    path = out / name
    if path.exists() and path.stat().st_size > 40_000 and path.read_bytes()[:4] == b"%PDF":
        return {"file": name, "url": url, "status": "skip", "bytes": path.stat().st_size}
    try:
        data = fetch(url)
        if not data.startswith(b"%PDF"):
            if b"%PDF" in data[:2048]:
                data = data[data.find(b"%PDF") :]
            else:
                return {"file": name, "url": url, "status": "fail", "error": f"not pdf {data[:40]!r}"}
        if len(data) < 30_000:
            return {"file": name, "url": url, "status": "fail", "error": f"too small {len(data)}"}
        path.write_bytes(data)
        return {"file": name, "url": url, "status": "ok", "bytes": len(data)}
    except Exception as e:
        return {"file": name, "url": url, "status": "fail", "error": str(e)}


def classify_period(blob: str) -> tuple[int | None, str | None]:
    b = blob.lower()
    y = None
    for m in re.finditer(r"(202[0-6])", b):
        y = int(m.group(1))
    if y and y > 2025:
        # presentation for 2026 Q1 etc - skip or keep if user wants - skip for thesis window
        if y == 2026:
            return None, None
    period = None
    if re.search(r"q3|iii|3q|9m|9\s*mies|three quarters|3 quarters", b):
        period = "Q3"
    elif re.search(r"h1|hy|1h|1p|półrocz|polrocz|6m|half.?year|first half|1st half|2q", b):
        period = "H1"
    elif re.search(r"q1|1q|i\s*kw|first quarter|1st quarter", b):
        period = "Q1"
    elif re.search(r"fy|q4|4q|full.?year|annual|rok\s*20|year\s*20|roczne|za\s*rok", b):
        period = "Q4"
    return y, period


def collect_ena() -> list[dict]:
    print("=== ENA investor presentations ===")
    pages = [
        "https://ir.enea.pl/en/investor-presentations",
        "https://ir.enea.pl/prezentacje-inwestorskie",
        "https://ir.enea.pl/en/investor-presentations?from=2020-01-01T00:00:00Z&to=2026-12-31T23:59:59Z",
        "https://ir.enea.pl/en/investor-presentations?pageLimit=100",
    ]
    found = {}
    for page in pages:
        try:
            ls = links_on(page)
            print(f" page {page} links={len(ls)}")
        except Exception as e:
            print(" ERR", page, e)
            continue
        for full, text in ls:
            b = (full + " " + text).lower()
            if not any(x in b for x in (".pdf", "cdn-netpr", "mediakit", "attachment", "download")):
                continue
            if "prezent" not in b and "presentation" not in b and "results" not in b and "wyniki" not in b:
                # still accept result PDFs from investor presentations section
                if "result" not in b and "wyniki" not in b:
                    continue
            y, p = classify_period(full + " " + text)
            if not y or not p or y < 2020 or y > 2025:
                continue
            # prefer PL
            score = 10
            if "wyniki" in b or "_pl" in b or "/pl" in b:
                score += 5
            if "prezent" in b or "presentation" in b:
                score += 10
            key = (y, p)
            if key not in found or score > found[key][0]:
                found[key] = (score, full, text)
                print(f"  + {y} {p}: {text[:70]}")
    return found


def collect_jsw() -> list[dict]:
    print("\n=== JSW ===")
    pages = [
        "https://www.jsw.pl/relacje-inwestorskie",
        "https://www.jsw.pl/relacje-inwestorskie/raporty-gieldowe",
    ]
    # try common presentation listing patterns
    for y in range(2020, 2026):
        pages.append(f"https://www.jsw.pl/relacje-inwestorskie/raporty-gieldowe/raporty-okresowe/raporty-okresowe-{y}")
    found = {}
    for page in pages:
        try:
            ls = links_on(page)
        except Exception as e:
            print(" ERR", e)
            continue
        for full, text in ls:
            b = (full + " " + text).lower()
            if "prezent" not in b and "presentation" not in full.lower():
                continue
            if not any(x in b for x in (".pdf", "fileadmin", "download")):
                continue
            y, p = classify_period(full + " " + text)
            if not y:
                m = re.search(r"/(202[0-5])/", full)
                if m:
                    y = int(m.group(1))
            if not y or not p or y < 2020 or y > 2025:
                continue
            found[(y, p)] = (10, full, text)
            print(f"  + {y} {p}: {text[:70]}")
    return found


def collect_zep_old() -> dict:
    print("\n=== ZEP 2020-2022 ===")
    found = {}
    try:
        ls = links_on("https://ri.zepak.com.pl/pl/prezentacje.html")
        print(" prezentacje links", len(ls))
        for full, text in ls:
            if ".pdf" not in full.lower():
                continue
            if full.startswith("/"):
                full = "https://ri.zepak.com.pl" + full
            # normalize upload paths
            m = re.search(r"(/upload/(?:files|aggregate)/[^?\s]+\.pdf)", full, re.I)
            if m:
                full = "https://ri.zepak.com.pl" + m.group(1) if m.group(1).startswith("/") else m.group(1)
                if not full.startswith("http"):
                    full = "https://ri.zepak.com.pl" + m.group(1)
            y, p = classify_period(full + " " + text)
            if not y or not p or y < 2020 or y > 2025:
                continue
            found[(y, p)] = (10, full, text)
            print(f"  + {y} {p}: {Path_name(full)}")
    except Exception as e:
        print(" ERR", e)
    # also try year filter on prezentacje if exists
    return found


def Path_name(u: str) -> str:
    return unquote(u.split("/")[-1])[:70]


def main() -> None:
    results = []

    ena = collect_ena()
    for (y, p), (_, url, text) in sorted(ena.items()):
        name = f"ENA_{y}_{p}_prezentacja.pdf"
        print(f"… {name}")
        r = save("ENA", name, url)
        print(f"  {r['status']} {r.get('bytes') or r.get('error')}")
        results.append({"ticker": "ENA", **r})
        time.sleep(0.3)

    jsw = collect_jsw()
    for (y, p), (_, url, text) in sorted(jsw.items()):
        name = f"JSW_{y}_{p}_prezentacja.pdf"
        print(f"… {name}")
        r = save("JSW", name, url.split("?")[0])
        print(f"  {r['status']} {r.get('bytes') or r.get('error')}")
        results.append({"ticker": "JSW", **r})
        time.sleep(0.3)

    zep = collect_zep_old()
    for (y, p), (_, url, text) in sorted(zep.items()):
        name = f"ZEP_{y}_{p}_prezentacja.pdf"
        print(f"… {name}")
        r = save("ZEP", name, url)
        print(f"  {r['status']} {r.get('bytes') or r.get('error')}")
        results.append({"ticker": "ZEP", **r})
        time.sleep(0.25)

    # UNT 2024/2025 Q1 Q4 if on centrum - try more pages
    print("\n=== UNT 2024-25 Q1/Q4 ===")
    try:
        ls = links_on("https://www.unimot.pl/relacje-inwestorskie/materialy-informacyjne/centrum-wynikowe")
        for full, text in ls:
            b = (full + " " + text).lower()
            if "prezent" not in b:
                continue
            y, p = classify_period(b)
            if not y or not p or y < 2024:
                continue
            name = f"UNT_{y}_{p}_prezentacja.pdf"
            print(f"… {name}")
            r = save("UNT", name, full)
            print(f"  {r['status']} {r.get('bytes') or r.get('error')}")
            results.append({"ticker": "UNT", **r})
            time.sleep(0.25)
    except Exception as e:
        print("UNT ERR", e)

    man = BASE / "manifest_presentations_ena_jsw_zep.json"
    ok = sum(1 for x in results if x["status"] in ("ok", "skip"))
    fail = sum(1 for x in results if x["status"] == "fail")
    man.write_text(
        json.dumps(
            {
                "downloaded_at": datetime.now(timezone.utc).isoformat(),
                "n_ok": ok,
                "n_fail": fail,
                "files": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nOK/skip={ok} fail={fail} total={len(results)}")


if __name__ == "__main__":
    main()
