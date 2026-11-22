#!/usr/bin/env python3
"""Find and download PKN 2023 H1 numerical data ZIP."""

from __future__ import annotations

import ssl
import urllib.error
import urllib.request
from pathlib import Path

OUT = Path("data/raw/reports/PKN/PKN_2023_H1_dane-liczbowe.zip")
CTX = ssl.create_default_context()
H = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

BASE = (
    "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/"
    "relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2023/2q2023/"
)

NAMES = [
    "Dane_ze_sprawozdania_1H23.zip.coredownload.zip",
    "Dane_ze_sprawozdania_1H2023.zip.coredownload.zip",
    "Dane_ze_sprawozdania__1H2023.zip.coredownload.zip",
    "Dane_ze_sprawozdania_1h23.zip.coredownload.zip",
    "Dane_ze_sprawozdania_1h2023.zip.coredownload.zip",
    "Dane_ze_sprawozdania_IH2023.zip.coredownload.zip",
    "Dane_ze_sprawozdania_IH23.zip.coredownload.zip",
    "Dane_ze_sprawozdaniaIH2023.zip.coredownload.zip",
    "Dane_ze_sprawozdania1H23.zip.coredownload.zip",
    "Dane_ze_sprawozd_1H23.zip.coredownload.zip",
    "Dane_ze_sprawozd_1H2023.zip.coredownload.zip",
    "Dane_ze_sprawozd_2q2023.zip.coredownload.zip",
    "Dane_ze_sprawozd_2Q2023.zip.coredownload.zip",
    "Dane_ze_sprawozdania_2q23.zip.coredownload.zip",
    "Dane_ze_sprawozdania_2Q23.zip.coredownload.zip",
    "Dane_ze_sprawozdania_2kw23.zip.coredownload.zip",
    "Dane_ze_sprawozdania_2kw2023.zip.coredownload.zip",
    "230824_Dane_ze_sprawozdania_1H23.zip.coredownload.zip",
    "20230824_Dane_ze_sprawozdania_1H23.zip.coredownload.zip",
    "20230824_Dane_ze_sprawozdania_1H2023.zip.coredownload.zip",
    "ORLEN_230824_Dane_ze_sprawozdania_1H23.zip.coredownload.zip",
    "Dane_ze_sprawozdania_1H23.xls.coredownload.zip",
    "Dane_skonsolidowane_RI_IH2023.zip.coredownload.zip",
    "Dane_skonsolidowane_RI_1H2023.zip.coredownload.zip",
    # without coredownload
    "Dane_ze_sprawozdania_1H23.zip",
    "Dane_ze_sprawozdania_1H2023.zip",
    "Dane_ze_sprawozd_1H23.zip",
]


def try_url(url: str) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers=H)
        with urllib.request.urlopen(req, context=CTX, timeout=60) as r:
            data = r.read()
            ctype = (r.headers.get("Content-Type") or "").lower()
        if len(data) < 5000:
            return None
        if data[:2] != b"PK" and "zip" not in ctype and data[:4] != b"PK\x03\x04":
            # might still be zip
            if data[:2] != b"PK":
                print("  not zip", ctype, data[:30])
                return None
        return data
    except Exception as e:
        print("  no", getattr(e, "code", type(e).__name__), url.split("/")[-1])
        return None


def main() -> None:
    for name in NAMES:
        url = BASE + name
        print("try", name)
        data = try_url(url)
        if data:
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_bytes(data)
            print("SAVED", OUT, len(data), "from", url)
            return
    print("NOT FOUND among candidates")


if __name__ == "__main__":
    main()
