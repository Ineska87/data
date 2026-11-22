#!/usr/bin/env python3
"""Discover annual report PDF/ZIP links from PGE, Tauron, Enea IR pages."""

from __future__ import annotations

import re
import ssl
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

CTX = ssl.create_default_context()
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


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
            text = " ".join(self._text).strip()
            self.links.append((self._href, text))
            self._href = None
            self._text = []


def fetch(url: str, timeout: int = 90) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=CTX, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def abs_url(base: str, href: str) -> str:
    if href.startswith("http"):
        return href
    if href.startswith("//"):
        return "https:" + href
    from urllib.parse import urljoin

    return urljoin(base, href)


def interesting(href: str, text: str) -> bool:
    h = href.lower()
    t = text.lower()
    if any(x in h for x in (".pdf", ".zip", ".7z", "download", "content/download", "coredownload")):
        return True
    keys = (
        "skonsolidowan",
        "sprawozdanie",
        "raport roczny",
        "zarządu",
        "zarzadu",
        "xhtml",
        "esef",
        "annual",
        "pdf",
        "zip",
    )
    return any(k in t for k in keys)


def process_page(url: str) -> None:
    print(f"\n=== {url}")
    try:
        html = fetch(url)
    except Exception as e:
        print(f"ERR: {e}")
        return
    print(f"html_len={len(html)}")
    p = LinkExtractor()
    p.feed(html)
    seen: set[str] = set()
    for href, text in p.links:
        if not interesting(href, text):
            continue
        full = abs_url(url, href)
        if full in seen:
            continue
        seen.add(full)
        print(f"  [{text[:80]}] -> {full[:180]}")
    # also raw regex for content/download
    for m in re.findall(r'href=["\']([^"\']*content/download[^"\']*)["\']', html, re.I):
        full = abs_url(url, m)
        if full not in seen:
            print(f"  [raw] -> {full[:180]}")
            seen.add(full)


PAGES = [
    # PGE year hubs
    "https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/raporty-okresowe-za-2025-rok",
    "https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/raporty-okresowe-za-2024-rok",
    "https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/raporty-okresowe-za-2023-rok",
    "https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/raporty-okresowe-za-2022-rok",
    "https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/sprawozdania-finansowe-za-2021-r",
    "https://www.gkpge.pl/dla-inwestorow/akcje/dane-finansowe/sprawozdania-finansowe-za-2020-r",
    "https://www.gkpge.pl/dla-inwestorow/do-pobrania",
    # Tauron
    "https://www.tauron.pl/tauron/relacje-inwestorskie/raporty-okresowe",
    "https://raport.tauron.pl/o-raporcie/centrum-pobierania-dokumentow",
    # Enea
    "https://ir.enea.pl/pr/867993/skonsolidowany-raport-roczny-srr-2025",
    "https://ir.enea.pl/pr/850126/skonsolidowany-raport-roczny-srr-2024",
    "https://ir.enea.pl/pr/832498/skonsolidowany-raport-roczny-srr-2023",
    "https://ir.enea.pl/pr/797791/skonsolidowany-raport-roczny-srr-2022",
    "https://ir.enea.pl/pr/733533/skonsolidowany-raport-roczny-srr-2021",
    "https://ir.enea.pl/centrum-pobierania-plikow/26927",
    "https://ir.enea.pl/lista-raportow/kategoria/3612/raporty-okresowe",
]


if __name__ == "__main__":
    for u in PAGES:
        process_page(u)
