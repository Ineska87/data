#!/usr/bin/env python3
"""Discover quarterly / semi-annual report links for PGE, TPE, ENA."""

from __future__ import annotations

import re
import ssl
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin

CTX = ssl.create_default_context()
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
}


class LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
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
            self._text = []


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=CTX, timeout=90) as r:
        return r.read().decode("utf-8", errors="replace")


def dump(url: str, filter_keys: tuple[str, ...] | None = None) -> None:
    print(f"\n=== {url}")
    try:
        html = fetch(url)
    except Exception as e:
        print("ERR", e)
        return
    print("html_len", len(html))
    p = LinkExtractor()
    p.feed(html)
    seen: set[str] = set()
    for href, text in p.links:
        full = urljoin(url, href)
        blob = (full + " " + text).lower()
        if filter_keys and not any(k in blob for k in filter_keys):
            continue
        if full in seen:
            continue
        # skip noise
        if any(
            x in full.lower()
            for x in (
                "javascript:",
                "mailto:",
                "#",
                "facebook",
                "twitter",
                "linkedin",
                "youtube",
            )
        ):
            continue
        if filter_keys or any(
            k in blob
            for k in (
                "download",
                ".pdf",
                ".zip",
                ".ashx",
                "kwartal",
                "polrocz",
                "półrocz",
                "q1",
                "q2",
                "q3",
                "q4",
                "hy",
                "psr",
                "qsr",
                "sprawozdanie",
                "skonsolid",
                "prezentac",
            )
        ):
            seen.add(full)
            print(f"  [{text[:90]}] -> {full[:220]}")


# PGE year hubs + known quarter page patterns
PGE_PAGES = [
    "https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe",
    "https://www.gkpge.pl/dla-inwestorow/do-pobrania",
]
for y in range(2020, 2026):
    PGE_PAGES += [
        f"https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/raporty-okresowe-za-{y}-rok",
        f"https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/skonsolidowany-raport-kwartalny-za-i-kwartal-{y}-r",
        f"https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/skonsolidowany-raport-za-i-polrocze-{y}-r",
        f"https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/skonsolidowany-raport-kwartalny-za-iii-kwartal-{y}-r",
    ]
# alternate 2021 naming
PGE_PAGES += [
    "https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/skonsolidowany-raport-polroczny-za-i-polrocze-2021-r",
    "https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/sprawozdania-finansowe-za-2021-r",
    "https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/sprawozdania-finansowe-za-2020-r",
]

TPE_PAGES = [
    "https://www.tauron.pl/tauron/relacje-inwestorskie/raporty-okresowe",
]

ENA_PAGES = [
    "https://ir.enea.pl/lista-raportow/kategoria/3612/raporty-okresowe?pageLimit=100",
]


if __name__ == "__main__":
    print("########## PGE ##########")
    for u in PGE_PAGES:
        dump(
            u,
            (
                "download",
                ".pdf",
                "kwartal",
                "polrocz",
                "półrocz",
                "raport",
                "sprawozdanie",
                "prezentac",
                "q1",
                "q3",
                "hy",
                "2020",
                "2021",
                "2022",
                "2023",
                "2024",
                "2025",
            ),
        )

    print("\n########## TPE ##########")
    for u in TPE_PAGES:
        dump(
            u,
            (
                "kwartal",
                "polrocz",
                "półrocz",
                "i-kwartal",
                "iii-kwartal",
                "i-polrocze",
                "skonsolidowane-sprawozdanie",
                "rozszerzony",
                ".ashx",
            ),
        )

    print("\n########## ENA listing ##########")
    for u in ENA_PAGES:
        dump(u, ("kwartal", "półrocz", "polrocz", "qsr", "psr", "2020", "2021", "2022", "2023", "2024", "2025"))
