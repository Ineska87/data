#!/usr/bin/env python3
"""Find and download missing UNT quarterly reports (Q1/Q3 gaps)."""

from __future__ import annotations

import re
import ssl
import time
import urllib.request
from html.parser import HTMLParser
from data_paths import DATA_ROOT
from urllib.parse import urljoin, unquote

BASE = DATA_ROOT / "raw" / "reports" / "UNT"
CTX = ssl.create_default_context()
H = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pl-PL,pl;q=0.9",
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
    req = urllib.request.Request(url, headers=H)
    with urllib.request.urlopen(req, context=CTX, timeout=120) as r:
        return r.read()


def links_on(url: str) -> list[tuple[str, str]]:
    html = fetch(url).decode("utf-8", errors="replace")
    p = LinkExtractor()
    p.feed(html)
    return [(urljoin(url, h), re.sub(r"\s+", " ", t).strip()) for h, t in p.links]


def classify(url: str, text: str) -> tuple[int, str, str] | None:
    blob = (unquote(url) + " " + text).lower()
    if "/media/" not in url and "download" not in url.lower():
        return None
    if any(k in blob for k in (".xades", "biegłego", "bieglego", "sbr", "przegląd", "przeglad", "atestacji")):
        return None
    if not any(k in blob for k in (".pdf", ".zip", "download")):
        return None

    # period
    period = None
    if re.search(r"1q\s*20|1q20|i\s*kw|iq20|q1.?20|za-i-kw|za_i_kw|/1q|kwartalny_1q|1-kw", blob):
        period = "Q1"
    if re.search(r"3q\s*20|3q20|iii\s*kw|iiiq|q3.?20|za-iii|za_iii|/3q|kwartalny_3q|3-kw|iii kw", blob):
        period = "Q3"
    if re.search(r"hy\s*20|hy20|1h\s*20|półrocz|polrocz|1p20|i\s*półrocz|i\s*polrocz", blob):
        period = "H1"
    if period is None:
        return None

    # year — prefer year next to period token
    year = None
    for pat in (
        r"(?:1q|3q|q1|q3|hy|1h|i\s*kw|iii\s*kw|polrocz\w*|półrocz\w*)[^\d]{0,6}(202[0-5])",
        r"(202[0-5])[^\d]{0,6}(?:1q|3q|q1|q3|hy|1h)",
        r"(202[0-5])",
    ):
        m = re.search(pat, blob)
        if m:
            year = int(m.group(1))
            break
    if not year or year < 2020 or year > 2025:
        return None

    kind = "sprawozdanie"
    if "zarzadu" in blob or "zarządu" in blob or "szd" in blob:
        kind = "sprawozdanie-zarzadu"
    elif "jednostkow" in blob or "jsf" in blob:
        kind = "jednostkowy"
    elif "prezentac" in blob:
        kind = "prezentacja"
    elif "skonsolid" in blob or "ssf" in blob or "gk unimot" in blob or "gk_unimot" in blob or "raport" in blob:
        kind = "sprawozdanie"

    return year, period, kind


def main() -> None:
    BASE.mkdir(parents=True, exist_ok=True)
    pages = ["https://www.unimot.pl/relacje-inwestorskie/raporty-i-strategia/raporty-okresowe"]
    for i in range(2, 12):
        pages.append(
            f"https://www.unimot.pl/relacje-inwestorskie/raporty-i-strategia/raporty-okresowe?page={i}"
        )
    # also centrum wynikowe
    pages.append("https://www.unimot.pl/relacje-inwestorskie/materialy-informacyjne/centrum-wynikowe")

    found: dict[tuple[int, str], list[tuple[str, str, str]]] = {}
    for page in pages:
        print("PAGE", page)
        try:
            ls = links_on(page)
        except Exception as e:
            print("  ERR", e)
            continue
        n = 0
        for full, text in ls:
            cls = classify(full, text)
            if not cls:
                continue
            year, period, kind = cls
            if kind == "jednostkowy":
                continue
            found.setdefault((year, period), []).append((kind, full, text))
            n += 1
        print(f"  matches {n}")

    # target gaps
    want = [
        (2020, "Q1"),
        (2020, "Q3"),
        (2022, "Q1"),
        (2022, "Q3"),
        (2023, "Q1"),
        # also fill any other missing among 2020-2025 Q1/Q3
        (2020, "H1"),
        (2022, "H1"),
        (2023, "Q3"),
        (2023, "H1"),
        (2024, "Q1"),
        (2024, "Q3"),
        (2025, "Q1"),
        (2025, "Q3"),
        (2021, "Q1"),
        (2021, "Q3"),
        (2021, "H1"),
        (2022, "H1"),
    ]

    print("\nAll found periods:")
    for k in sorted(found):
        print(f"  {k}: {len(found[k])} links")
        for kind, url, text in found[k][:3]:
            print(f"    [{kind}] {text[:60]} | {url[-80:]}")

    # download missing
    results = []
    for year, period in sorted(set(want) | set(found.keys())):
        if year < 2020 or year > 2025:
            continue
        if period not in ("Q1", "Q3", "H1"):
            continue
        items = found.get((year, period), [])
        if not items:
            print(f"MISSING on IR: {year} {period}")
            results.append((year, period, "not_on_page", None))
            continue
        # prefer skonsolidowane sprawozdanie / raport
        def score(item):
            kind, url, text = item
            b = (url + text).lower()
            s = 0
            if kind == "sprawozdanie":
                s += 20
            if "skonsolid" in b or "ssf" in b:
                s += 15
            if kind == "sprawozdanie-zarzadu":
                s += 5
            if ".pdf" in b:
                s += 5
            if "prezentac" in b:
                s -= 10
            return s

        items = sorted(items, key=score, reverse=True)
        best = items[0]
        kind, url, text = best
        fname = f"UNT_{year}_{period}_sprawozdanie.pdf"
        if kind == "sprawozdanie-zarzadu" and not any(i[0] == "sprawozdanie" for i in items):
            fname = f"UNT_{year}_{period}_sprawozdanie-zarzadu.pdf"
        else:
            # pick first non-zarzad if available
            for k2, u2, t2 in items:
                if k2 == "sprawozdanie":
                    kind, url, text = k2, u2, t2
                    fname = f"UNT_{year}_{period}_sprawozdanie.pdf"
                    break

        path = BASE / fname
        if path.exists() and path.stat().st_size > 30_000:
            head = path.read_bytes()[:4]
            if head.startswith(b"%PDF") or head.startswith(b"PK"):
                print(f"SKIP exists {fname} ({path.stat().st_size})")
                results.append((year, period, "skip", fname))
                continue

        print(f"GET {fname}")
        print(f"  {url}")
        try:
            data = fetch(url)
            if len(data) < 15_000:
                raise ValueError(f"too small {len(data)}")
            if not (data.startswith(b"%PDF") or data.startswith(b"PK")):
                raise ValueError(f"not binary {data[:30]!r}")
            if data.startswith(b"PK"):
                fname = fname.replace(".pdf", ".zip")
                path = BASE / fname
            path.write_bytes(data)
            print(f"  OK {len(data):,}")
            results.append((year, period, "ok", fname))
            time.sleep(0.4)
        except Exception as e:
            print(f"  FAIL {e}")
            results.append((year, period, f"fail:{e}", url))

    print("\n=== SUMMARY ===")
    for r in results:
        print(r)


if __name__ == "__main__":
    main()
