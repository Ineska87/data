#!/usr/bin/env python3
"""Download annual reports (AR) 2020–2025 for PGE, TPE (Tauron), ENA (Enea).

Naming: {TICKER}_{YYYY}_AR_{typ}.{pdf,zip,7z}
Priority: skonsolidowane sprawozdanie (SSF) + sprawozdanie zarządu (SZ).
"""

from __future__ import annotations

import json
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from data_paths import DATA_ROOT

BASE = DATA_ROOT / "raw" / "reports"
CTX = ssl.create_default_context()
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
}

# (ticker, filename, url)
FILES: list[tuple[str, str, str]] = [
    # ========== PGE ==========
    (
        "PGE",
        "PGE_2025_AR_skonsolidowany.pdf",
        "https://www.gkpge.pl/content/download/b27b8e69a804749c5ee7071daf1a3772/file/pge_ssf2025.pdf",
    ),
    (
        "PGE",
        "PGE_2025_AR_sprawozdanie-zarzadu.pdf",
        "https://www.gkpge.pl/content/download/1c17c9bb500a8cc7ea488bc573451f3e/file/pge_sz2025.pdf",
    ),
    (
        "PGE",
        "PGE_2024_AR_skonsolidowany.pdf",
        "https://www.gkpge.pl/content/download/d8aee6d031cf5f08e5902b918a861d4a/file/ssf_gkpge_2024_pl.pdf",
    ),
    (
        "PGE",
        "PGE_2024_AR_sprawozdanie-zarzadu.pdf",
        "https://www.gkpge.pl/content/download/ae87254f9a72f57bc4ee84feb63bbd75/file/sz_gkpge_2024_pl.pdf",
    ),
    (
        "PGE",
        "PGE_2023_AR_skonsolidowany.pdf",
        "https://www.gkpge.pl/content/download/962cdfd8d37c4a2d8e9603d407e6554c/file/ssf-gkpge-2023_pl.pdf",
    ),
    (
        "PGE",
        "PGE_2023_AR_sprawozdanie-zarzadu.pdf",
        "https://www.gkpge.pl/content/download/f132c059707d5614bed37b779cf5f022/file/sz2023_pl.pdf",
    ),
    (
        "PGE",
        "PGE_2022_AR_skonsolidowany.pdf",
        "https://www.gkpge.pl/content/download/53cc034e797daa5d6cae7ffb3bef4e87/file/skonsolidowanesfgkpge2022.pdf",
    ),
    (
        "PGE",
        "PGE_2022_AR_sprawozdanie-zarzadu.pdf",
        "https://www.gkpge.pl/content/download/224332f4d0df3fd64195e65b5fe01b2b/file/sz-gkpge_2022.pdf",
    ),
    (
        "PGE",
        "PGE_2021_AR_skonsolidowany.pdf",
        "https://www.gkpge.pl/content/download/51834b1563a78c5aa9f8199d16fe4b94/file/skonsolidowanesfgkpge2021.pdf",
    ),
    (
        "PGE",
        "PGE_2021_AR_sprawozdanie-zarzadu.pdf",
        "https://www.gkpge.pl/content/download/5ea6d0d3b5b83610f40f29f3e049d0f1/file/sz_fy2021_gkpge.pdf",
    ),
    (
        "PGE",
        "PGE_2020_AR_skonsolidowany.pdf",
        "https://www.gkpge.pl/content/download/5e8dc64644d41a858f0ea9191a10865b/file/f2279f1ea94483386361d7502faa3026.pdf",
    ),
    (
        "PGE",
        "PGE_2020_AR_sprawozdanie-zarzadu.pdf",
        "https://www.gkpge.pl/content/download/c3a628d8bdb56efe48eb7787d96f86ce/file/6b04fddf8739205ebb4445c375ca5f26.pdf",
    ),
    # ========== TPE (Tauron) — skonsolidowany raport roczny ==========
    (
        "TPE",
        "TPE_2025_AR_skonsolidowany.zip",
        "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2025/roczny/skonsolidowany-raport-roczny-za-2025-r.ashx",
    ),
    (
        "TPE",
        "TPE_2024_AR_skonsolidowany.7z",
        "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2024/roczny/skonsolidowany-raport-roczny-za-2024-r.ashx",
    ),
    (
        "TPE",
        "TPE_2023_AR_skonsolidowany.7z",
        "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2023/roczny/skonsolidowany-raport-roczny_2023.ashx",
    ),
    (
        "TPE",
        "TPE_2022_AR_skonsolidowany.7z",
        "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2022/roczny/skonsolidowany-raport-roczny-za-2022-r.ashx",
    ),
    (
        "TPE",
        "TPE_2021_AR_skonsolidowany.zip",
        "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2021/roczny/skonsolidowany_raport_roczny_2021.ashx",
    ),
    (
        "TPE",
        "TPE_2020_AR_skonsolidowany.zip",
        "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2020/roczny/skonsolidowany_raport_roczny_2020.ashx",
    ),
    # ========== ENA (Enea) ==========
    (
        "ENA",
        "ENA_2025_AR_skonsolidowany.pdf",
        "https://cdn-netpr.pl/file/attachment/2967612/64/sprawozdanie_finansowe_gk_enea.pdf",
    ),
    (
        "ENA",
        "ENA_2025_AR_sprawozdanie-zarzadu.pdf",
        "https://cdn-netpr.pl/file/attachment/2967617/f0/sprawozdanie_zarzadu_z_dzialalnosci_enea_s_a_oraz_gk_enea.pdf",
    ),
    (
        "ENA",
        "ENA_2024_AR_skonsolidowany.pdf",
        "https://cdn-netpr.pl/file/attachment/2795637/2e/skonsolidowane_sprawozdanie_finansowe_gk_enea.pdf",
    ),
    (
        "ENA",
        "ENA_2024_AR_sprawozdanie-zarzadu.pdf",
        "https://cdn-netpr.pl/file/attachment/2795638/45/sprawozdanie_zarzadu_z_dzialalnosci.pdf",
    ),
    (
        "ENA",
        "ENA_2023_AR_skonsolidowany.pdf",
        "https://cdn-netpr.pl/file/attachment/2632078/51/skonsolidowane_sprawozdanie_finansowe_gk_enea.pdf",
    ),
    (
        "ENA",
        "ENA_2023_AR_sprawozdanie-zarzadu.pdf",
        "https://cdn-netpr.pl/file/attachment/2632081/c/sprawozdanie_zarzadu_z_dzialalnosci.pdf",
    ),
    (
        "ENA",
        "ENA_2022_AR_skonsolidowany.pdf",
        "https://cdn-netpr.pl/file/attachment/2421279/f0/skonsolidowane_sprawozdanie_finansowe_gk_enea_za_2022_r_pdf_.pdf",
    ),
    (
        "ENA",
        "ENA_2022_AR_sprawozdanie-zarzadu.pdf",
        "https://cdn-netpr.pl/file/attachment/2421280/51/sprawozdanie_zarza_du_z_dzialalnos_ci_enea_s_a_i_gk_enea_za_2022_r_pdf_.pdf",
    ),
    (
        "ENA",
        "ENA_2021_AR_skonsolidowany.pdf",
        "https://cdn-netpr.pl/file/attachment/2154342/b9/sprawozdanie_skonsolidowane_za_2021_rok.pdf",
    ),
    (
        "ENA",
        "ENA_2021_AR_sprawozdanie-zarzadu.pdf",
        "https://cdn-netpr.pl/file/attachment/2154343/2c/sprawozdanie_zarzadu_z_dzialalnosci_enea_s_a_i_gk_enea_w_2021_roku.pdf",
    ),
    (
        "ENA",
        "ENA_2020_AR_skonsolidowany.pdf",
        "https://cdn-netpr.pl/file/attachment/1878244/6c/skonsolidowane_sprawozdanie_finansowe_gk_enea_w_2020_roku.pdf",
    ),
    (
        "ENA",
        "ENA_2020_AR_sprawozdanie-zarzadu.pdf",
        "https://cdn-netpr.pl/file/attachment/1877579/55/sprawozdanie_zarzadu_z_dzialalnosci_enea_s_a_oraz_gk_enea_w_2020_roku_.pdf",
    ),
]


SIGNATURES = {
    ".pdf": (b"%PDF-",),
    ".zip": (b"PK\x03\x04",),
    ".7z": (b"7z\xbc\xaf\x27\x1c",),
}


def download_one(ticker: str, name: str, url: str, retries: int = 4) -> dict:
    out_dir = BASE / ticker
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    expected_signature = SIGNATURES[path.suffix]
    if path.exists() and path.stat().st_size >= 10_000:
        with path.open("rb") as existing:
            if existing.read(8).startswith(expected_signature):
                return {
                    "ticker": ticker,
                    "file": name,
                    "url": url,
                    "status": "skip_exists",
                    "bytes": path.stat().st_size,
                    "path": path.relative_to(DATA_ROOT.parent).as_posix(),
                }
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=CTX, timeout=180) as r:
                data = r.read()
                ctype = (r.headers.get("Content-Type") or "").lower()
            if len(data) < 10_000:
                raise ValueError(f"too_small ({len(data)} B), ctype={ctype}")
            if not data.startswith(expected_signature):
                raise ValueError(f"expected {path.suffix} file, got {data[:8]!r}, ctype={ctype}")
            path.write_bytes(data)
            return {
                "ticker": ticker,
                "file": name,
                "url": url,
                "status": "ok",
                "bytes": len(data),
                "path": path.relative_to(DATA_ROOT.parent).as_posix(),
            }
        except Exception as e:
            last_err = e
            time.sleep(1.5 * attempt)
    return {
        "ticker": ticker,
        "file": name,
        "url": url,
        "status": "fail",
        "error": str(last_err),
    }


def main() -> None:
    results = []
    for ticker, name, url in FILES:
        print(f"… {ticker}/{name}")
        r = download_one(ticker, name, url)
        results.append(r)
        if r["status"] == "ok":
            print(f"  OK  {r['bytes']:,} B")
        elif r["status"] == "skip_exists":
            print(f"  SKIP exists {r['bytes']:,} B")
        else:
            print(f"  FAIL {r.get('error')}")
        time.sleep(0.4)

    manifest = {
        "scope": "AR skonsolidowane + sprawozdanie zarządu PGE/TPE/ENA 2020-2025",
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "n_ok": sum(1 for x in results if x["status"] in ("ok", "skip_exists")),
        "n_fail": sum(1 for x in results if x["status"] == "fail"),
        "files": results,
    }
    man_path = BASE / "manifest_ar_pge_tpe_ena.json"
    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nManifest: {man_path}")
    print(f"OK/skip={manifest['n_ok']} fail={manifest['n_fail']} / {len(results)}")


if __name__ == "__main__":
    main()
