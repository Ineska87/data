#!/usr/bin/env python3
"""Fix ZEP downloads: correct upload base URL + period from filename."""

from __future__ import annotations

import json
import re
import ssl
import time
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

from data_paths import DATA_ROOT
from urllib.parse import urljoin, unquote

BASE = DATA_ROOT / "raw" / "reports" / "ZEP"
CTX = ssl.create_default_context()
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Referer": "https://ri.zepak.com.pl/pl/raporty/raporty-okresowe.html",
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
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=CTX, timeout=180) as r:
        return r.read()


def links_on(url: str) -> list[tuple[str, str]]:
    html = fetch(url).decode("utf-8", errors="replace")
    p = LinkExtractor()
    p.feed(html)
    return [(urljoin(url, h), re.sub(r"\s+", " ", t).strip()) for h, t in p.links]


def to_upload_url(url: str) -> str:
    """Map any path containing /upload/files/NAME to https://ri.zepak.com.pl/upload/files/NAME."""
    u = url.split("?")[0]
    m = re.search(r"/upload/files/([^/]+\.pdf)$", u, re.I)
    if m:
        return f"https://ri.zepak.com.pl/upload/files/{m.group(1)}"
    if u.startswith("https://ri.zepak.com.pl/upload/files/"):
        return u
    # bare filename
    if u.lower().endswith(".pdf") and "/" not in u:
        return f"https://ri.zepak.com.pl/upload/files/{u}"
    return u


def classify_file(name: str) -> tuple[int, str, str] | None:
    """Return (year, period, kind) from filename."""
    n = unquote(name)
    nl = n.lower()
    # skip junk
    if any(k in nl for k in ("platnosci", "płatności", "oswiadczenie", "oświadczenie", "badania", "komitet", "pozostae", "pozostale", "atestacja")):
        return None
    # year from pattern ZEPAK_YYYY or zepak_YYYY or ZEP_YYYY
    ym = re.search(r"(?:zepak|zep)[_\-]?(\d{4})", nl)
    if not ym:
        ym = re.search(r"(\d{4})[_\-]?(?:r|1p|1q|3q|1h)", nl)
    if not ym:
        return None
    year = int(ym.group(1))
    if year < 2019 or year > 2025:
        return None

    kind = "sprawozdanie"
    if "zarzadu" in nl or "zarządu" in nl:
        kind = "sprawozdanie-zarzadu"
    elif "skonsolidowane" in nl or "skonsolidowany" in nl:
        kind = "skonsolidowany"
    elif "sprawozdanie_finansowe" in nl or "sprawozdanie-finansowe" in nl:
        kind = "skonsolidowany"  # often named without skonsolid when on AR page; prefer if R

    # period: 1Q, 3Q, 1P/H1, R annual
    if re.search(r"[_\-]1q|[_\-]iq|i_kwart|i-kwart", nl) or "1q_" in nl or "-1q_" in nl:
        period = "Q1"
    elif re.search(r"[_\-]3q|[_\-]iiiq|iii_kwart|iii-kwart", nl) or "3q_" in nl or "-3q_" in nl:
        period = "Q3"
    elif re.search(r"[_\-]1p|[_\-]1h|polrocz|półrocz|i_polrocze|i-polrocze", nl) or "1p_" in nl or "-1p_" in nl or "_1p_" in nl:
        period = "H1"
    elif re.search(r"[_\-]r[_\-]|[_\-]r\.|_r_|-r_|/r_|yyyy-r", nl) or re.search(r"\d{4}-r_|\d{4}_r_|\d{4}-r\.|\d{4}_r\.", nl) or re.search(r"\d{4}-r_|\d{4}_r_|\d{4}-r-|\d{4}_r-", nl):
        period = "AR"
    elif re.search(r"\d{4}-r|\d{4}_r", nl):
        period = "AR"
    else:
        # 2020-R style
        if re.search(r"\d{4}-r_|\d{4}_r_|\d{4}-r\.|\d{4}_r\.|\d{4}-r[_\-]", nl):
            period = "AR"
        else:
            return None

    # map report year: filename year is the fiscal year
    if year == 2019:
        return None  # out of range for 2020-2025 sample unless we want it
    if year > 2025:
        return None

    if kind == "sprawozdanie" and period == "AR":
        kind = "skonsolidowany"
    return year, period, kind


def discover() -> list[dict]:
    files: list[dict] = []
    seen_urls: set[str] = set()
    for hub_y in range(2020, 2027):
        hub = f"https://ri.zepak.com.pl/pl/raporty/raporty-okresowe.html?y={hub_y}"
        try:
            ls = links_on(hub)
        except Exception as e:
            print("hub ERR", hub_y, e)
            continue
        detail = [u for u, t in ls if "/raporty/raporty-okresowe/" in u and u.endswith(".html") and "raporty-okresowe.html" not in u]
        # also direct pdfs on hub
        for full, text in ls:
            if ".pdf" in full.lower():
                detail.append(full)  # type ignore - will handle below
        pages = []
        for item in detail:
            if isinstance(item, str) and item.endswith(".html"):
                pages.append(item)
            elif isinstance(item, str) and item.lower().endswith(".pdf"):
                pages.append(item)

        for page in pages:
            if page.lower().endswith(".pdf"):
                candidates = [(page, Path(unquote(page)).name)]
            else:
                try:
                    pls = links_on(page)
                except Exception as e:
                    print(" page ERR", page, e)
                    continue
                candidates = [(f, t) for f, t in pls if ".pdf" in f.lower()]

            for furl, ftext in candidates:
                name = unquote(furl).split("/")[-1]
                if not name.lower().endswith(".pdf"):
                    continue
                cls = classify_file(name)
                if not cls:
                    # try text
                    cls = classify_file(ftext + " " + name)
                if not cls:
                    continue
                year, period, kind = cls
                if year < 2020 or year > 2025:
                    continue
                url = to_upload_url(furl)
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                files.append(
                    {
                        "year": year,
                        "period": period,
                        "kind": kind,
                        "url": url,
                        "name": name,
                        "note": ftext[:100],
                    }
                )
                print(f"  found {year} {period} {kind}: {name[:60]}")
    return files


def pick(files: list[dict]) -> list[dict]:
    from collections import defaultdict

    by = defaultdict(list)
    for f in files:
        by[(f["year"], f["period"])].append(f)
    ready = []
    for (year, period), items in sorted(by.items()):
        def score(r):
            s = 0
            n = r["name"].lower()
            k = r["kind"]
            if k == "skonsolidowany":
                s += 30
            if k == "sprawozdanie-zarzadu":
                s += 20
            if k == "sprawozdanie":
                s += 25
            if "skonsolidowane" in n:
                s += 15
            if "rozszerzony" in n:
                s += 10
            if "pozost" in n:
                s -= 40
            if "oswiad" in n or "oświad" in n:
                s -= 40
            if "badania" in n:
                s -= 40
            # prefer matching period token in name
            if period == "AR" and re.search(r"\d{4}-r|\d{4}_r", n):
                s += 20
            if period == "H1" and ("1p" in n or "1h" in n):
                s += 20
            if period == "Q1" and "1q" in n:
                s += 20
            if period == "Q3" and "3q" in n:
                s += 20
            return s

        items = sorted(items, key=score, reverse=True)
        primary = next(
            (i for i in items if i["kind"] in ("skonsolidowany", "sprawozdanie")),
            items[0],
        )
        sz = next((i for i in items if i["kind"] == "sprawozdanie-zarzadu"), None)
        if period == "AR":
            ready.append(
                {
                    "file": f"ZEP_{year}_AR_skonsolidowany.pdf",
                    "url": primary["url"],
                    "year": year,
                    "period": period,
                }
            )
            if sz:
                ready.append(
                    {
                        "file": f"ZEP_{year}_AR_sprawozdanie-zarzadu.pdf",
                        "url": sz["url"],
                        "year": year,
                        "period": period,
                    }
                )
        else:
            ready.append(
                {
                    "file": f"ZEP_{year}_{period}_sprawozdanie.pdf",
                    "url": primary["url"],
                    "year": year,
                    "period": period,
                }
            )
            if sz and period == "H1":
                ready.append(
                    {
                        "file": f"ZEP_{year}_H1_sprawozdanie-zarzadu.pdf",
                        "url": sz["url"],
                        "year": year,
                        "period": period,
                    }
                )
    # dedupe
    out = {}
    for r in ready:
        out[r["file"]] = r
    return list(out.values())


def download(url: str, path: Path) -> tuple[str, int, str | None]:
    if path.exists() and path.stat().st_size > 50_000:
        # re-check if PDF
        head = path.read_bytes()[:5]
        if head.startswith(b"%PDF"):
            return "skip_exists", path.stat().st_size, None
        path.unlink()
    last = None
    for attempt in range(1, 5):
        try:
            data = fetch(url)
            if not data.startswith(b"%PDF"):
                # try alternate path variants
                raise ValueError(f"not PDF head={data[:40]!r}")
            path.write_bytes(data)
            return "ok", len(data), None
        except Exception as e:
            last = str(e)
            time.sleep(1.2 * attempt)
    return "fail", 0, last


def main() -> None:
    BASE.mkdir(parents=True, exist_ok=True)
    # remove failed HTML stubs
    for p in BASE.glob("ZEP_*.pdf"):
        try:
            h = p.read_bytes()[:20]
            if h.lstrip().startswith(b"<") or not h.startswith(b"%PDF"):
                print("remove bad", p.name)
                p.unlink()
        except Exception:
            pass

    print("Discover ZEP…")
    raw = discover()
    ready = pick(raw)
    print(f"Ready {len(ready)}")
    results = []
    for r in sorted(ready, key=lambda x: (x["year"], x["period"], x["file"])):
        path = BASE / r["file"]
        print(f"… {r['file']}")
        print(f"   {r['url']}")
        status, nbytes, err = download(r["url"], path)
        results.append({**r, "status": status, "bytes": nbytes, "error": err})
        print(f"   {status} {nbytes} {err or ''}")
        time.sleep(0.3)

    man_path = DATA_ROOT / "raw" / "reports" / "manifest_zep_fixed.json"
    man_path.write_text(
        json.dumps(
            {
                "downloaded_at": datetime.now(timezone.utc).isoformat(),
                "n_ok": sum(1 for x in results if x["status"] in ("ok", "skip_exists")),
                "n_fail": sum(1 for x in results if x["status"] == "fail"),
                "files": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("Manifest", man_path)
    print("OK", sum(1 for x in results if x["status"] in ("ok", "skip_exists")), "fail", sum(1 for x in results if x["status"] == "fail"))


if __name__ == "__main__":
    main()
