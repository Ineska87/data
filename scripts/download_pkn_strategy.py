#!/usr/bin/env python3
"""Download PKN Orlen strategy documents 2020-2025."""

from __future__ import annotations

import json
import ssl
import time
import urllib.request
from datetime import datetime
from data_paths import DATA_ROOT

OUT = DATA_ROOT / "raw" / "reports" / "PKN"
OUT.mkdir(parents=True, exist_ok=True)

# Core strategy timeline for thesis (H5 + dywidenda + CAPEX)
FILES: list[tuple[str, str, str]] = [
    # year / label in name, filename, url
    (
        "PKN_2020_STRAT_strategia-2030-prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-biezace/2020/Grupa_ORLEN_Strategia_2030.pdf.coredownload.pdf",
    ),
    (
        "PKN_2020_STRAT_espi-62-2020.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-biezace/2020/Raport_62_2020_Strategia_2030.pdf.coredownload.pdf",
    ),
    (
        "PKN_2020_STRAT_strategia-2030-strona.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/o-firmie/strategia-2030/dokumenty/Grupa_ORLEN_Strategia_2030.pdf",
    ),
    (
        "PKN_2020_STRAT_transformacja-energetyczna.pdf",
        "https://raportzintegrowany2020.orlen.pl/uploads/CENTRUM_DOKUMENTOW/11-Transformacja-energetyczna-Przyszlosc-zaczyna-sie-dzis.pdf",
    ),
    (
        "PKN_2023_STRAT_aktualizacja-2030-prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-biezace/2023/Aktualizacja_Strategii_Grupy_ORLEN_2030_PLs.pdf.coredownload.pdf",
    ),
    (
        "PKN_2023_STRAT_aktualizacja-2030-prezentacja-alt.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-biezace/2023/Aktualizacja_Strategii_Grupy_ORLEN_2030_PLs.pdf",
    ),
    (
        "PKN_2023_STRAT_espi-10-2023.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-biezace/2023/Raport_10_2023_Strategia.pdf.coredownload.pdf",
    ),
    (
        "PKN_2023_STRAT_ORLEN_FFBK.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/o-firmie/dokumenty/ORLEN_FFBK.pdf",
    ),
    (
        "PKN_2025_STRAT_strategia-2035-prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/o-firmie/strategia-2035/dokumenty/Strategia%20ORLEN%202035.pdf",
    ),
    (
        "PKN_2025_STRAT_espi-1-2025.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-biezace/2025/Raport_1_2025_Strategia_2035.pdf.coredownload.pdf",
    ),
    (
        "PKN_2025_STRAT_transition-plan.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/zrownowazony-rozwoj/raporty-i-wska%C5%BAniki/ORLEN_Transition_Plan_pl.pdf",
    ),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Referer": "https://www.orlen.pl/pl/o-firmie/strategia",
}


def download(name: str, url: str, ctx: ssl.SSLContext) -> dict:
    dest = OUT / name
    if dest.exists() and dest.stat().st_size > 500:
        print(f"SKIP {name} ({dest.stat().st_size} B)")
        return {
            "file": name,
            "url": url,
            "status": "exists",
            "bytes": dest.stat().st_size,
        }
    last_err = None
    for attempt in range(1, 5):
        try:
            time.sleep(0.8 * attempt)
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=300) as r:
                data = r.read()
                ctype = r.headers.get("Content-Type", "")
            # reject obvious HTML error pages
            if data[:20].lstrip().startswith(b"<!DOCTYPE") or data[:5] == b"<html":
                raise ValueError(f"got HTML instead of file (ctype={ctype})")
            if len(data) < 500:
                raise ValueError(f"too small: {len(data)} B")
            dest.write_bytes(data)
            print(f"OK  {name} ({len(data)} B, try {attempt})")
            return {
                "file": name,
                "url": url,
                "status": "ok",
                "bytes": len(data),
                "content_type": ctype,
                "attempt": attempt,
            }
        except Exception as e:
            last_err = str(e)
            print(f"FAIL {name} try {attempt}: {e}")
    return {"file": name, "url": url, "status": "fail", "error": last_err}


def main() -> None:
    ctx = ssl.create_default_context()
    results = [download(name, url, ctx) for name, url in FILES]

    # Deduplicate: if both alt and main 2023 presentation ok, drop alt if identical size
    ok = sum(1 for r in results if r["status"] in ("ok", "exists"))
    fail = [r for r in results if r["status"] == "fail"]

    manifest = {
        "ticker": "PKN",
        "scope": "strategie: 2030 (2020), aktualizacja 2030 (2023), 2035 (2025) + transition plan",
        "timeline": [
            {"date": "2020-11-30", "event": "Strategia GK ORLEN do 2030 (ESPI 62/2020)", "codes": ["STRAT", "H5"]},
            {"date": "2022-02-02", "event": "Strategia wodorowa (ESPI 6/2022, tekst w raporcie bieżącym)", "codes": ["STRAT"]},
            {"date": "2023-02-28", "event": "Aktualizacja strategii do 2030 + polityka dywidendowa (ESPI 10/2023)", "codes": ["STRAT", "H5", "H6"]},
            {"date": "2025-01-09", "event": "Strategia ORLEN 2035 + nowa polityka dywidendowa (ESPI 1/2025)", "codes": ["STRAT", "H5", "H6"]},
        ],
        "downloaded_at": datetime.now().isoformat(timespec="seconds"),
        "ok": ok,
        "total": len(results),
        "failed": fail,
        "files": results,
    }
    (OUT / "manifest_strategy.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nDone: {ok}/{len(results)} ok")
    if fail:
        print("Failed:")
        for r in fail:
            print(" -", r["file"], r.get("error"))


if __name__ == "__main__":
    main()
