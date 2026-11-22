#!/usr/bin/env python3
"""Download NIK Ostrołęka C control PDFs."""

from __future__ import annotations

import json
import ssl
import time
import urllib.request
from datetime import datetime
from data_paths import DATA_ROOT

OUT = DATA_ROOT / "raw" / "nik_reports"
OUT.mkdir(parents=True, exist_ok=True)

FILES = [
    (
        "NIK_ostroleka-c-I-20-002-wystapienie.pdf",
        "https://www.nik.gov.pl/kontrole/wyniki-kontroli-nik/pobierz,kst~i_20_002_202202091542231644417743~id0~01,typ,kj.pdf",
    ),
    (
        "NIK_ostroleka-c-I-21-001-enea-energa-wystapienie.pdf",
        "https://www.nik.gov.pl/kontrole/wyniki-kontroli-nik/pobierz,kst~i_21_001_202202091559361644418776~id1~01,typ,kj.pdf",
    ),
    (
        "NIK_ostroleka-c-I-24-004-rozliczenie-wystapienie.pdf",
        "https://www.nik.gov.pl/kontrole/wyniki-kontroli-nik/pobierz,kst~i_24_004_202508121151151754992275~id0~01,typ,kj.pdf",
    ),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Referer": "https://www.nik.gov.pl/",
}


def main() -> None:
    ctx = ssl.create_default_context()
    results = []
    for name, url in FILES:
        dest = OUT / name
        if dest.exists() and dest.stat().st_size > 1000:
            print(f"SKIP {name}")
            results.append({"file": name, "status": "exists", "bytes": dest.stat().st_size, "url": url})
            continue
        ok = False
        last = None
        for attempt in range(1, 5):
            try:
                time.sleep(0.8 * attempt)
                req = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req, context=ctx, timeout=180) as r:
                    data = r.read()
                if data[:4] != b"%PDF" and data[:20].lstrip().startswith(b"<!DOCTYPE"):
                    raise ValueError("not PDF")
                dest.write_bytes(data)
                print(f"OK  {name} ({len(data)} B)")
                results.append({"file": name, "status": "ok", "bytes": len(data), "url": url})
                ok = True
                break
            except Exception as e:
                last = str(e)
                print(f"FAIL {name} try {attempt}: {e}")
        if not ok:
            results.append({"file": name, "status": "fail", "error": last, "url": url})

    manifest = {
        "case": "Ostrołęka C",
        "downloaded_at": datetime.now().isoformat(timespec="seconds"),
        "files": results,
    }
    (OUT / "manifest_ostroleka.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    ok_n = sum(1 for r in results if r["status"] in ("ok", "exists"))
    print(f"Done: {ok_n}/{len(results)}")


if __name__ == "__main__":
    main()
