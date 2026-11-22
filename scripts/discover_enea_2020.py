#!/usr/bin/env python3
"""Find Enea 2020 consolidated AR attachments."""

from __future__ import annotations

import re
import ssl
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin

CTX = ssl.create_default_context()
UA = {"User-Agent": "Mozilla/5.0"}


class L(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.h: str | None = None
        self.t: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.h = href
                self.t = []

    def handle_data(self, data: str) -> None:
        if self.h is not None:
            self.t.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.h is not None:
            self.links.append((self.h, " ".join(self.t).strip()))
            self.h = None


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=CTX, timeout=90) as r:
        return r.read().decode("utf-8", errors="replace")


URLS = [
    "https://ir.enea.pl/lista-raportow/kategoria/3612/raporty-okresowe?from=2021-01-01T00:00:00Z&to=2021-12-31T23:59:59Z",
    "https://ir.enea.pl/lista-raportow/kategoria/3612/raporty-okresowe?from=2020-01-01T00:00:00Z&to=2021-06-01T00:00:00Z",
    "https://ir.enea.pl/pr/656146/skonsolidowany-raport-roczny-srr-2020",
    "https://ir.enea.pl/pr/656147/skonsolidowany-raport-roczny-srr-2020",
    "https://ir.enea.pl/pr/656148/skonsolidowany-raport-roczny-rs-2020",
]

# also search listing pages for srr-2020
LISTING = "https://ir.enea.pl/lista-raportow/kategoria/3612/raporty-okresowe"


def main() -> None:
    # parse listing for 2020/2021 annual
    try:
        html = fetch(LISTING + "?pageLimit=100")
        print("listing", len(html))
        for m in re.finditer(r'href="([^"]+)"[^>]*>([^<]*(?:2020|SRR|skonsolidowany raport roczny)[^<]*)', html, re.I):
            print("LIST", m.group(2).strip()[:80], "->", m.group(1))
        p = L()
        p.feed(html)
        for h, t in p.links:
            if "2020" in t or "2020" in h or "srr" in h.lower():
                print("L", t[:90], "->", h)
    except Exception as e:
        print("list ERR", e)

    for u in URLS:
        print("\n===", u)
        try:
            html = fetch(u)
            print("ok", len(html))
            p = L()
            p.feed(html)
            for h, t in p.links:
                if "cdn-netpr" in h or any(x in h.lower() for x in (".pdf", ".zip", ".xhtml")):
                    print(t[:90], "->", h[:160])
        except Exception as e:
            print("ERR", e)


if __name__ == "__main__":
    main()
