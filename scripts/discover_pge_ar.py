#!/usr/bin/env python3
"""Discover PGE annual report download links with browser-like headers."""

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


PAGES = [
    "https://www.gkpge.pl/dla-inwestorow/do-pobrania",
    "https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe",
    "https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/raporty-okresowe-za-2025-rok",
    "https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/raporty-okresowe-za-2024-rok",
    "https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/raporty-okresowe-za-2023-rok",
    "https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/raporty-okresowe-za-2022-rok",
    "https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/sprawozdania-finansowe-za-2021-r",
    "https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/sprawozdania-finansowe-za-2020-r",
]


def main() -> None:
    for url in PAGES:
        print(f"\n=== {url}")
        try:
            html = fetch(url)
        except Exception as e:
            print("ERR", e)
            continue
        print("html_len", len(html))
        p = LinkExtractor()
        p.feed(html)
        seen: set[str] = set()
        for href, text in p.links:
            full = urljoin(url, href)
            blob = (full + " " + text).lower()
            if not any(
                k in blob
                for k in (
                    "download",
                    ".pdf",
                    ".zip",
                    ".7z",
                    "skonsolid",
                    "sprawozdanie",
                    "raport roczny",
                    "zarządu",
                    "zarzadu",
                    "xhtml",
                    "roczny",
                    "2020",
                    "2021",
                    "2022",
                    "2023",
                    "2024",
                    "2025",
                )
            ):
                continue
            if full in seen:
                continue
            # focus downloads / year pages
            if "download" in full or full.endswith((".pdf", ".zip", ".7z")) or "dane-finansowe" in full:
                seen.add(full)
                print(f"  [{text[:100]}] -> {full[:200]}")
        # raw content/download
        for m in re.findall(r'href=["\']([^"\']*content/download[^"\']*)["\']', html, re.I):
            full = urljoin(url, m)
            if full not in seen:
                print(f"  [raw] -> {full[:200]}")
                seen.add(full)


if __name__ == "__main__":
    main()
