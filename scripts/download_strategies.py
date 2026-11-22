#!/usr/bin/env python3
"""Download strategy PDFs for PGE, TPE, ZEP, UNT (+ try ENA)."""

from __future__ import annotations

import json
import ssl
import time
import urllib.request
from datetime import datetime

from data_paths import DATA_ROOT

ROOT = DATA_ROOT / "raw" / "reports"

FILES: list[tuple[str, str, str]] = [
    # PGE
    (
        "PGE",
        "PGE_2025_STRAT_strategia-2035.pdf",
        "https://www.gkpge.pl/content/download/3911d266a44aa76d7dec276069e0119b/file/PGE_SA_20250612_Strategia_PGE_2035.pdf",
    ),
    (
        "PGE",
        "PGE_STRAT_strategia-2030-EN.pdf",
        "https://www.gkpge.pl/investor-relations/content/download/59359/file/pge-group-strategy-2030.pdf",
    ),
    # Tauron
    (
        "TPE",
        "TPE_2025_STRAT_strategia-2025-2035.pdf",
        "https://www.tauron.pl/-/media/reportattachments/strategia-grupy-tauron-na-lata-2025-2035-202412171381138159.ashx",
    ),
    (
        "TPE",
        "TPE_2022_STRAT_strategia-2022-2030.pdf",
        "https://www.tauron.pl/-/media/offer-documents/tauron/prezentacje/strategia-grupy-tauron-22-30/strategia-grupy-tauron-na-lata-2022-2030.ashx",
    ),
    (
        "TPE",
        "TPE_2025_STRAT_prezentacja-2025-2035.ashx.pdf",
        "https://www.tauron.pl/-/media/offer-documents/tauron/prezentacje/strategia-grupy-tauron-25-35/strategia-grupy-tauron-na-lata-2025-2035.ashx",
    ),
    # ZE PAK
    (
        "ZEP",
        "ZEP_2020_STRAT_kierunki-strategii.pdf",
        "https://ri.zepak.com.pl/upload/files/kierunki_strategii_fin_v4.pdf",
    ),
    (
        "ZEP",
        "ZEP_2024_STRAT_ESG-2024-2028.pdf",
        "https://ri.zepak.com.pl/upload/files/Strategia_ESG_2024-2028_aktualizacja.pdf",
    ),
    (
        "ZEP",
        "ZEP_2023_STRAT_ESG-2023-2027.pdf",
        "https://ri.zepak.com.pl/upload/files/Strategia_ESG_2023-2027.pdf",
    ),
    # Unimot
    (
        "UNT",
        "UNT_2024_STRAT_strategia-2024-2028.pdf",
        "https://www.unimot.pl/media/4595/download/Strategia%20Unimot%202024-2028.pdf?v=1",
    ),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
}


def download(ticker: str, name: str, url: str, ctx: ssl.SSLContext) -> dict:
    out = ROOT / ticker
    out.mkdir(parents=True, exist_ok=True)
    dest = out / name
    if dest.exists() and dest.stat().st_size > 5000:
        print(f"SKIP {name}")
        return {"file": name, "ticker": ticker, "status": "exists", "bytes": dest.stat().st_size, "url": url}
    last = None
    for attempt in range(1, 5):
        try:
            time.sleep(0.6 * attempt)
            req = urllib.request.Request(url, headers={**HEADERS, "Referer": url.rsplit("/", 1)[0] + "/"})
            with urllib.request.urlopen(req, context=ctx, timeout=300) as r:
                data = r.read()
                ctype = r.headers.get("Content-Type", "")
            if data[:20].lstrip().startswith(b"<!DOCTYPE") or data[:5] == b"<html":
                raise ValueError(f"HTML not file ({ctype})")
            if len(data) < 5000:
                raise ValueError(f"too small {len(data)}")
            dest.write_bytes(data)
            print(f"OK  {ticker}/{name} ({len(data)} B)")
            return {
                "file": name,
                "ticker": ticker,
                "status": "ok",
                "bytes": len(data),
                "url": url,
                "content_type": ctype,
            }
        except Exception as e:
            last = str(e)
            print(f"FAIL {name} try {attempt}: {e}")
    return {"file": name, "ticker": ticker, "status": "fail", "error": last, "url": url}


def main() -> None:
    ctx = ssl.create_default_context()
    results = [download(t, n, u, ctx) for t, n, u in FILES]
    ok = sum(1 for r in results if r["status"] in ("ok", "exists"))
    manifest = {
        "scope": "Strategie PGE TPE ZEP UNT (+ PKN już w PKN/)",
        "downloaded_at": datetime.now().isoformat(timespec="seconds"),
        "ok": ok,
        "total": len(results),
        "files": results,
    }
    (ROOT / "manifest_strategies.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nDone: {ok}/{len(results)}")
    for r in results:
        if r["status"] == "fail":
            print(" FAIL", r["file"], r.get("error"))


if __name__ == "__main__":
    main()
