#!/usr/bin/env python3
"""Fix failed TPE URLs + download ZEP/ENA/JSW presentation packs."""

from __future__ import annotations

import json
import re
import ssl
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin, unquote, quote

from data_paths import DATA_ROOT

BASE = DATA_ROOT / "raw" / "reports"
CTX = ssl.create_default_context()
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
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
    # encode non-ascii path segments
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
        if len(data) < 20_000:
            return {"file": name, "url": url, "status": "fail", "error": f"too small {len(data)}"}
        path.write_bytes(data)
        return {"file": name, "url": url, "status": "ok", "bytes": len(data)}
    except Exception as e:
        return {"file": name, "url": url, "status": "fail", "error": str(e)}


def fix_tpe() -> list[dict]:
    print("=== TPE fix + missing ===")
    # re-scrape prezentacje page for exact hrefs
    page = "https://www.tauron.pl/tauron/relacje-inwestorskie/prezentacje"
    ls = links_on(page)
    results = []
    mapping = {}
    for full, text in ls:
        if "prezentacje" not in full.lower() and "prezent" not in (full + text).lower():
            continue
        if not any(x in full.lower() for x in (".ashx", ".pdf", "offer-documents")):
            continue
        tl = text.lower() + " " + full.lower()
        y = None
        m = re.search(r"(202[0-5])", tl)
        if m:
            y = int(m.group(1))
        if not y:
            continue
        period = None
        if "iii" in tl or "3q" in tl or "q3" in tl:
            period = "Q3"
        elif "i półrocz" in tl or "i polrocz" in tl or "h1" in tl or "1h" in tl or "hy" in tl:
            period = "H1"
        elif "i kwart" in tl or "1q" in tl or "q1" in tl:
            period = "Q1"
        elif "za 20" in tl or "roczny" in tl or "4q" in tl or "q4" in tl or "rok" in tl:
            period = "Q4"
        if not period:
            continue
        mapping[(y, period)] = full
        print(f"  map {y} {period}: {full}")

    # also known wyniki.tauron.pl annual 2025
    mapping.setdefault((2025, "Q4"), "https://wyniki.tauron.pl/Roczny2025_Tauron.pdf")

    for (y, p), url in sorted(mapping.items()):
        name = f"TPE_{y}_{p}_prezentacja.pdf"
        print(f"… {name}")
        r = save("TPE", name, url)
        print(f"  {r['status']} {r.get('bytes') or r.get('error')}")
        results.append(r)
        time.sleep(0.25)
    return results


def fix_zep() -> list[dict]:
    print("\n=== ZEP aggregate + files ===")
    # known aggregate URLs from IR search + scrape prezentacje page
    known = [
        ("ZEP_2025_Q4_prezentacja.pdf", "https://ri.zepak.com.pl/upload/files/ZE_PAK_2025_final_PL.pdf"),
        ("ZEP_2025_Q3_prezentacja.pdf", "https://ri.zepak.com.pl/upload/aggregate/ZEPAK_2025-3Q_PREZENTACJA.pdf"),
        ("ZEP_2025_H1_prezentacja.pdf", "https://ri.zepak.com.pl/upload/aggregate/ZEPAK_2025-6M_PREZENTACJA_publikacja.pdf"),
        ("ZEP_2025_Q1_prezentacja.pdf", "https://ri.zepak.com.pl/upload/aggregate/ZEPAK_2025-1Q_PREZENTACJA.pdf"),
        ("ZEP_2024_Q4_prezentacja.pdf", "https://ri.zepak.com.pl/upload/aggregate/ZEPAK_2024-R_PREZENTACJA.pdf"),
        ("ZEP_2024_Q3_prezentacja.pdf", "https://ri.zepak.com.pl/upload/aggregate/ZEPAK_2024-3Q_PREZENTACJA_final.pdf"),
        ("ZEP_2024_H1_prezentacja.pdf", "https://ri.zepak.com.pl/upload/aggregate/ZEPAK_2024-6M_PREZENTACJA_final.pdf"),
        ("ZEP_2024_Q1_prezentacja.pdf", "https://ri.zepak.com.pl/upload/aggregate/ZEPAK_2024-1Q_PREZENTACJA.pdf"),
        ("ZEP_2023_Q4_prezentacja.pdf", "https://ri.zepak.com.pl/upload/aggregate/ZEPAK_2023-R_PREZENTACJA_06_05_2024_fin.pdf"),
        ("ZEP_2023_Q3_prezentacja.pdf", "https://ri.zepak.com.pl/upload/aggregate/ZEPAK_2023-3Q_PREZENTACJA.pdf"),
        ("ZEP_2023_H1_prezentacja.pdf", "https://ri.zepak.com.pl/upload/aggregate/ZEPAK_2023-1P_PREZENTACJA_final.pdf"),
        ("ZEP_2023_Q1_prezentacja.pdf", "https://ri.zepak.com.pl/upload/aggregate/ZEPAK_2023-1Q_PREZENTACJA.pdf"),
    ]
    # scrape prezentacje page for more (2020-2022)
    try:
        ls = links_on("https://ri.zepak.com.pl/pl/prezentacje.html")
        for full, text in ls:
            if ".pdf" not in full.lower():
                continue
            # normalize
            if "/upload/" in full:
                # keep as is but prefer absolute
                if full.startswith("/"):
                    full = "https://ri.zepak.com.pl" + full
            b = (full + " " + text).lower()
            y = None
            m = re.search(r"(202[0-5])", b)
            if m:
                y = int(m.group(1))
            if not y:
                continue
            period = None
            if "3q" in b or "iii" in b or "9m" in b:
                period = "Q3"
            elif "6m" in b or "1p" in b or "1h" in b or "półrocz" in b or "polrocz" in b:
                period = "H1"
            elif "1q" in b or "i kw" in b:
                period = "Q1"
            elif "-r_" in b or "roczne" in b or "wyniki 20" in b or "fy" in b or "4q" in b:
                period = "Q4"
            if not period:
                continue
            name = f"ZEP_{y}_{period}_prezentacja.pdf"
            if not any(n == name for n, _ in known):
                known.append((name, full.split("?")[0]))
    except Exception as e:
        print(" scrape ERR", e)

    results = []
    for name, url in known:
        print(f"… {name}")
        r = save("ZEP", name, url)
        print(f"  {r['status']} {r.get('bytes') or r.get('error')}")
        results.append(r)
        time.sleep(0.25)
    return results


def fix_ena() -> list[dict]:
    print("\n=== ENA ===")
    results = []
    pages = [
        "https://ir.enea.pl/",
        "https://ir.enea.pl/centrum-pobierania-plikow",
        "https://media.enea.pl/",
        "https://www.enea.pl/relacje-inwestorskie",
        "https://ir.enea.pl/lista-raportow",
    ]
    # try map
    found = []
    for page in pages:
        try:
            ls = links_on(page)
        except Exception as e:
            print(" ERR", page, e)
            continue
        for full, text in ls:
            b = (full + " " + text).lower()
            if "prezent" not in b and "presentation" not in b and "wyniki" not in b:
                continue
            if not any(x in b for x in (".pdf", "cdn-netpr", "download", "mediakit")):
                continue
            if "strateg" in b and "prezent" not in b:
                continue
            y = None
            m = re.search(r"(202[0-5])", b)
            if m:
                y = int(m.group(1))
            if not y:
                continue
            period = None
            if re.search(r"q3|iii\s*kw|3q|9\s*mies", b):
                period = "Q3"
            elif re.search(r"h1|hy|półrocz|polrocz|1h|6\s*mies", b):
                period = "H1"
            elif re.search(r"q1|i\s*kw|1q", b):
                period = "Q1"
            elif re.search(r"q4|fy|roczne|za\s*rok|4q|annual", b):
                period = "Q4"
            if not period:
                continue
            if "prezent" not in b and "presentation" not in b:
                continue
            found.append((y, period, full, text))
            print(f"  found {y} {period}: {text[:50]} {full[:80]}")

    # dedupe
    best = {}
    for y, p, url, text in found:
        key = (y, p)
        if key not in best:
            best[key] = (url, text)

    for (y, p), (url, text) in sorted(best.items()):
        name = f"ENA_{y}_{p}_prezentacja.pdf"
        print(f"… {name}")
        r = save("ENA", name, url)
        print(f"  {r['status']} {r.get('bytes') or r.get('error')}")
        results.append(r)
        time.sleep(0.3)
    return results


def fix_jsw() -> list[dict]:
    print("\n=== JSW ===")
    results = []
    pages = [
        "https://www.jsw.pl/relacje-inwestorskie",
        "https://www.jsw.pl/relacje-inwestorskie/raporty-gieldowe",
        "https://www.jsw.pl/relacje-inwestorskie/akcje-i-akcjonariat",
    ]
    # year pages often have presentation links
    for y in range(2020, 2026):
        pages.append(
            f"https://www.jsw.pl/relacje-inwestorskie/raporty-gieldowe/raporty-okresowe/raporty-okresowe-{y}"
        )

    found = []
    for page in pages:
        try:
            ls = links_on(page)
        except Exception as e:
            print(" ERR", page[-50:], e)
            continue
        for full, text in ls:
            b = (full + " " + text).lower()
            if "prezent" not in b and "presentation" not in b:
                # also "wyniki" pdf in fileadmin presentations folder
                if "prezent" not in full.lower() and "presentation" not in full.lower():
                    continue
            if not any(x in b for x in (".pdf", "fileadmin", "download")):
                continue
            y = None
            m = re.search(r"(202[0-5])", b)
            if m:
                y = int(m.group(1))
            if not y:
                m = re.search(r"/(202[0-5])/", full)
                if m:
                    y = int(m.group(1))
            if not y or y < 2020 or y > 2025:
                continue
            period = None
            if re.search(r"3q|q3|iii|9m|9_m", b):
                period = "Q3"
            elif re.search(r"1h|h1|hy|6m|polrocz|półrocz|1p", b):
                period = "H1"
            elif re.search(r"1q|q1|iq", b):
                period = "Q1"
            elif re.search(r"4q|q4|fy|1y|roczne|annual|rok", b):
                period = "Q4"
            if not period:
                continue
            found.append((y, period, full, text))
            print(f"  found {y} {period}: {text[:60]}")

    best = {}
    for y, p, url, text in found:
        key = (y, p)
        # prefer higher score
        score = 10
        bl = (url + text).lower()
        if "prezent" in bl:
            score += 20
        if "wyniki" in bl:
            score += 5
        if key not in best or score > best[key][0]:
            best[key] = (score, url, text)

    for (y, p), (_, url, text) in sorted(best.items()):
        name = f"JSW_{y}_{p}_prezentacja.pdf"
        print(f"… {name}")
        r = save("JSW", name, url.split("?")[0])
        print(f"  {r['status']} {r.get('bytes') or r.get('error')}")
        results.append(r)
        time.sleep(0.3)
    return results


def unt_presentation_period(url: str, title: str) -> tuple[int, str] | None:
    filename = unquote(urllib.parse.urlsplit(url).path).rsplit("/", 1)[-1].casefold()
    # Release dates in filenames often belong to the following fiscal year.
    filename = re.sub(r"^20\d{2}[-_.]\d{2}[-_.]\d{2}[-_. ]*", "", filename)
    text = re.sub(r"[_\s]+", "-", f"{filename} {title.casefold()}")
    quarterly = re.search(r"(?<!\w)([1234]q|q[1234]|1h|h1)[- ]*(20\d{2}|\d{2})(?!\d)", text)
    if quarterly:
        code, year_text = quarterly.groups()
        periods = {"1q": "Q1", "q1": "Q1", "2q": "H1", "q2": "H1", "1h": "H1", "h1": "H1",
                   "3q": "Q3", "q3": "Q3", "4q": "Q4", "q4": "Q4"}
        return int(year_text) + (2000 if len(year_text) == 2 else 0), periods[code]
    fiscal = re.search(r"(20\d{2})-?fy\b", text)
    if fiscal:
        return int(fiscal.group(1)), "Q4"
    year = re.search(r"za-(20\d{2})(?!\d)", text) or re.search(r"(?<!\d)(20\d{2})(?!\d)", text)
    if not year:
        return None
    for period, pattern in (
        ("Q3", r"3q|q3|iii"),
        ("H1", r"1h|h1|hy|2q|q2|półrocz|polrocz"),
        ("Q1", r"1q|q1"),
        ("Q4", r"fy|4q|q4|roczne|za-20\d{2}"),
    ):
        if re.search(pattern, text):
            return int(year.group(1)), period
    return None


def fill_unt_more() -> list[dict]:
    print("\n=== UNT remaining ===")
    # scrape centrum for all prezentacja links
    results = []
    page = "https://www.unimot.pl/relacje-inwestorskie/materialy-informacyjne/centrum-wynikowe"
    try:
        ls = links_on(page)
    except Exception as e:
        print("ERR", e)
        return results
    found = {}
    for full, text in ls:
        b = (full + " " + text).lower()
        if "prezent" not in b:
            continue
        if "/media/" not in full:
            continue
        parsed = unt_presentation_period(full, text)
        if parsed is None:
            continue
        y, period = parsed
        if not 2020 <= y <= 2025:
            continue
        found[(y, period)] = full
        print(f"  {y} {period}: {full[-70:]}")

    for (y, p), url in sorted(found.items()):
        name = f"UNT_{y}_{p}_prezentacja.pdf"
        print(f"… {name}")
        r = save("UNT", name, url)
        print(f"  {r['status']} {r.get('bytes') or r.get('error')}")
        results.append(r)
        time.sleep(0.25)
    return results


def main() -> None:
    all_r = []
    all_r.extend(fix_tpe())
    all_r.extend(fix_zep())
    all_r.extend(fix_ena())
    all_r.extend(fix_jsw())
    all_r.extend(fill_unt_more())

    man = BASE / "manifest_presentations_fixup.json"
    ok = sum(1 for x in all_r if x["status"] in ("ok", "skip"))
    fail = sum(1 for x in all_r if x["status"] == "fail")
    man.write_text(
        json.dumps(
            {
                "downloaded_at": datetime.now(timezone.utc).isoformat(),
                "n_ok": ok,
                "n_fail": fail,
                "files": all_r,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nOK/skip={ok} fail={fail} total={len(all_r)}")
    print("Manifest", man)


if __name__ == "__main__":
    main()
