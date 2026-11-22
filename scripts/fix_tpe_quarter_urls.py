#!/usr/bin/env python3
"""Refresh TPE quarter URLs from IR page into _quarters_url_list.json."""

from __future__ import annotations

import json
import re
import ssl
import urllib.request
from html.parser import HTMLParser

from data_paths import DATA_ROOT
from urllib.parse import urljoin

CTX = ssl.create_default_context()
UA = {"User-Agent": "Mozilla/5.0"}
LIST = DATA_ROOT / "metadata" / "download_manifests" / "_quarters_url_list.json"


class L(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.h = None
        self.t: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.h = href
                self.t = []

    def handle_data(self, d):
        if self.h is not None:
            self.t.append(d)

    def handle_endtag(self, tag):
        if tag == "a" and self.h is not None:
            self.links.append((self.h, " ".join(self.t).strip()))
            self.h = None


def period_from_url(full: str) -> str | None:
    u = full.lower()
    # order matters: iii before i
    if "/iii-kwartal/" in u or "/iii_kwartal/" in u or "iii-kwartal" in u or "iii_kwartal" in u:
        return "Q3"
    if "/i-polrocze/" in u or "/i_polrocze/" in u or "i-polrocze" in u or "i_polrocze" in u:
        return "H1"
    if "/i-kwartal/" in u or "/i_kwartal/" in u or "i-kwartal" in u or "i_kwartal" in u:
        return "Q1"
    return None


def is_main_report(text: str, full: str) -> bool:
    t = text.lower()
    u = full.lower()
    if any(
        k in t
        for k in (
            "wybrane",
            "biegł",
            "bieglego",
            "oświadczenie",
            "oswiadczenie",
            "jednostkow",
            "płatności",
            "platnosci",
            "zarządu",
            "zarzadu",
        )
    ):
        return False
    if "roczny" in t and "kwartal" not in t and "półrocz" not in t and "polrocz" not in t:
        return False
    keys = (
        "skonsolidowane sprawozdanie",
        "skonsolidowany raport",
        "rozszerzony skonsolidowany",
        "skonsolidowane-sprawozdanie",
        "skonsolidowany_raport",
        "skonsolidowany-raport",
        "rozszerzony_skonsolidowany",
        "skons_raport",
        "skons-raport",
    )
    return any(k in t or k in u for k in keys)


def score(url: str, text: str) -> int:
    """Higher = better main financial report."""
    u = url.lower()
    t = text.lower()
    s = 0
    if "skonsolidowane-sprawozdanie" in u or "skonsolidowane sprawozdanie" in t:
        s += 10
    if "rozszerzony" in u or "rozszerzony" in t:
        s += 5
    if "skons_raport" in u or "skons-raport" in u or "skonsolidowany_raport" in u:
        s += 8
    if "fin-za" in u or "finansowe" in u:
        s += 2
    return s


def main() -> None:
    url = "https://www.tauron.pl/tauron/relacje-inwestorskie/raporty-okresowe"
    req = urllib.request.Request(url, headers=UA)
    html = urllib.request.urlopen(req, context=CTX, timeout=90).read().decode("utf-8", errors="replace")
    p = L()
    p.feed(html)

    candidates: dict[tuple[int, str], list[tuple[int, str, str]]] = {}
    for href, text in p.links:
        full = urljoin(url, href)
        if "offer-documents" not in full.lower() and "raporty-okresowe" not in full.lower():
            continue
        ym = re.search(r"/(\d{4})/", full)
        if not ym:
            continue
        year = int(ym.group(1))
        if year < 2020 or year > 2025:
            continue
        period = period_from_url(full)
        if not period:
            continue
        if not is_main_report(text, full):
            continue
        candidates.setdefault((year, period), []).append((score(full, text), full, text))

    mapping: dict[tuple[int, str], str] = {}
    print("TPE candidates (best):")
    for key in sorted(candidates):
        cands = sorted(candidates[key], key=lambda x: -x[0])
        best = cands[0]
        mapping[key] = best[1]
        print(f"  {key}: score={best[0]} {best[1]}")
        for s, u, t in cands[1:3]:
            print(f"      alt score={s} {u}")

    data = json.loads(LIST.read_text(encoding="utf-8"))
    updated = 0
    for row in data:
        if row.get("ticker") != "TPE":
            continue
        key = (int(row["year"]), row["period"])
        if key in mapping:
            if row.get("url") != mapping[key]:
                print(f"UPDATE {row['file']}")
                print(f"   was: {row.get('url')}")
                print(f"   now: {mapping[key]}")
                row["url"] = mapping[key]
                row["note"] = "from IR scrape v2"
                updated += 1
        else:
            print(f"MISSING mapping for {key} ({row['file']}) — keeping previous URL")
    LIST.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"updated={updated} mapped={len(mapping)}")


if __name__ == "__main__":
    main()
