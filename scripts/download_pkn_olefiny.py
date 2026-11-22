#!/usr/bin/env python3
"""Download PKN Olefiny III / Nowa Chemia source PDFs."""

from __future__ import annotations

import json
import ssl
import time
import urllib.request
from datetime import datetime
from data_paths import DATA_ROOT

OUT = DATA_ROOT / "raw" / "reports" / "PKN" / "olefiny_iii"
OUT.mkdir(parents=True, exist_ok=True)

FILES = [
    (
        "PKN_STRAT_olefiny-iii-potencjal-przedsiewziecia.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/o-firmie/olefiny/Prezentacja-Budowa-Kompleksu-Olefin-III-potencjal-przedsiewziecia.pdf.coredownload.pdf",
    ),
    (
        "PKN_OTHER_olefiny-wplyw-srodowiskowo-spoleczny.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/o-firmie/olefiny/Wp%C5%82yw%20inwestycji%20na%20otoczenie%20%C5%9Brodowiskowo-spo%C5%82eczne.pdf.coredownload.pdf",
    ),
    (
        "PKN_OTHER_olefiny-ocena-wplywu-spolecznego.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/o-firmie/olefiny/Ocena%20wp%C5%82ywu%20spo%C5%82ecznego.pdf.coredownload.pdf",
    ),
    (
        "PKN_OTHER_olefiny-non-technical-summary-2023.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/o-firmie/olefiny/Non%20Technical%20Summary.pdf.coredownload.pdf",
    ),
    (
        "PKN_2024_LETTER_egm-justification-olefins-iii-EN.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/en/investor-relations/general-meetings/archive-records/documents/06-02-2024/Justification_OLEFINS%20III%20Project.pdf.coredownload.pdf",
    ),
    (
        "../PKN_2024_Q2_letter-ceo.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/prezentacje/prezentacje-wynikowe/2024/Skonsolidowane-wyniki-finansowe-ORLEN-S.A.-za-2.-kwarta%C5%82-2024-roku-Wprowadzenie-Prezesa-Zarz%C4%85du.pdf.coredownload.pdf",
    ),
    (
        "PKN_2024_Q2_letter-ceo-olefiny-context-alt.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/prezentacje/2024/Skonsolidowane-wyniki-finansowe-ORLEN-S.A.-za-2.-kwarta%C5%82-2024-roku-Wprowadzenie-Prezesa-Zarz%C4%85du.pdf.pdf.coredownload.pdf",
    ),
    (
        "PKN_2025_OTHER_merger-plan-orlen-olefiny.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/en/investor-relations/merger_orlen_oolefiny/20250422_Merger_plan_ORLEN_ORLEN_Olefiny.pdf.coredownload.pdf",
    ),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Referer": "https://www.orlen.pl/",
}


def download(name: str, url: str, ctx: ssl.SSLContext) -> dict:
    dest = OUT / name
    if dest.exists() and dest.stat().st_size > 1000:
        print(f"SKIP {name}")
        return {"file": name, "url": url, "status": "exists", "bytes": dest.stat().st_size}
    last_err = None
    for attempt in range(1, 5):
        try:
            time.sleep(0.7 * attempt)
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=300) as r:
                data = r.read()
                ctype = r.headers.get("Content-Type", "")
            if data[:20].lstrip().startswith(b"<!DOCTYPE") or data[:5] == b"<html":
                raise ValueError(f"HTML not PDF (ctype={ctype})")
            if len(data) < 1000:
                raise ValueError(f"too small: {len(data)}")
            dest.write_bytes(data)
            print(f"OK  {name} ({len(data)} B)")
            return {
                "file": name,
                "url": url,
                "status": "ok",
                "bytes": len(data),
                "content_type": ctype,
            }
        except Exception as e:
            last_err = str(e)
            print(f"FAIL {name} try {attempt}: {e}")
    return {"file": name, "url": url, "status": "fail", "error": last_err}


def main() -> None:
    ctx = ssl.create_default_context()
    results = [download(n, u, ctx) for n, u in FILES]
    ok = sum(1 for r in results if r["status"] in ("ok", "exists"))
    manifest = {
        "case": "Olefiny III / Nowa Chemia",
        "ticker": "PKN",
        "downloaded_at": datetime.now().isoformat(timespec="seconds"),
        "ok": ok,
        "total": len(results),
        "files": results,
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Done: {ok}/{len(results)}")


if __name__ == "__main__":
    main()
