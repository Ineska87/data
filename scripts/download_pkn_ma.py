#!/usr/bin/env python3
"""Download core M&A docs: Energa, Lotos, PGNiG + NIK Lotos."""

from __future__ import annotations

import json
import ssl
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from data_paths import DATA_ROOT

BASE = DATA_ROOT / "raw" / "reports" / "PKN"
NIK = DATA_ROOT / "raw" / "nik_reports"
NIK.mkdir(parents=True, exist_ok=True)

# (subdir, filename, url)
FILES: list[tuple[str, str, str]] = [
    # --- ENERGA ---
    (
        "ma_energa",
        "PKN_2019_MA_energa-wezwanie.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-biezace/2019/04/Raport-biezacy-nr-44-2019/20191205_WEZWANIE.pdf.coredownload.pdf",
    ),
    # --- LOTOS ---
    (
        "ma_lotos",
        "PKN_2022_MA_lotos-plan-polaczenia.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/archiwum-lotos/po%C5%82%C4%85czenielotos/Plan%20Po%C5%82%C4%85czenia.pdf.coredownload.pdf",
    ),
    (
        "ma_lotos",
        "PKN_2022_MA_lotos-sprawozdanie-zarzadu-orlen.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/archiwum-lotos/po%C5%82%C4%85czenielotos/Sprawozdanie_Zarzadu_PKN_ORLEN_SA_dla_celow_Polaczenia.pdf.coredownload.pdf",
    ),
    (
        "ma_lotos",
        "PKN_2022_MA_lotos-sprawozdanie-zarzadu-lotos.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/archiwum-lotos/po%C5%82%C4%85czenielotos/Sprawozdanie_Zarzadu_Grupy_LOTOS_SA_dla_celow_Polaczenia.pdf.coredownload.pdf",
    ),
    (
        "ma_lotos",
        "PKN_2022_MA_lotos-prezentacja-inwestorska.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/archiwum-lotos/po%C5%82%C4%85czenielotos/PL%20Project%20Kwiatek%20-%20Investor%20Presentation_vF.pdf.coredownload.pdf",
    ),
    (
        "ma_lotos",
        "PKN_2022_MA_lotos-opinia-bieglego.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/archiwum-lotos/po%C5%82%C4%85czenielotos/Opinia_bieglego_polaczenie_PKN_ORLEN_LOTOS.pdf.coredownload.pdf",
    ),
    (
        "ma_lotos",
        "PKN_2022_MA_lotos-dokument-wylaczeniowy.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/archiwum-lotos/po%C5%82%C4%85czenielotos/Dokument_Wylaczeniowy.pdf.coredownload.pdf",
    ),
    (
        "ma_lotos",
        "PKN_2022_MA_lotos-zal4-wartosc-przejmowanej.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/archiwum-lotos/po%C5%82%C4%85czenielotos/Zalacznik_nr_4_do_Planu_Polaczenia.pdf.coredownload.pdf",
    ),
    (
        "ma_lotos",
        "PKN_2022_MA_lotos-zal5-wartosc-przejmujacej.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/archiwum-lotos/po%C5%82%C4%85czenielotos/Zalacznik_nr_5_do_Planu_Polaczenia.pdf.coredownload.pdf",
    ),
    # --- PGNIG ---
    (
        "ma_pgnig",
        "PKN_2022_MA_pgnig-plan-polaczenia.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/archiwum-pgnig/po%C5%82%C4%85czenie-pgnig/Plan_Po%C5%82aczenia_PKN%20ORLEN_PGNiG_20220729.pdf.coredownload.pdf",
    ),
    (
        "ma_pgnig",
        "PKN_2022_MA_pgnig-sprawozdanie-zarzadu-orlen.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/archiwum-pgnig/po%C5%82%C4%85czenie-pgnig/Sprawozdanie%20Zarz%C4%85du%20PKN%20ORLEN-%20Po%C5%82%C4%85czenie%20PKN%20ORLEN-PGNiG_20220729.pdf.coredownload.pdf",
    ),
    (
        "ma_pgnig",
        "PKN_2022_MA_pgnig-sprawozdanie-zarzadu-pgnig.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/archiwum-pgnig/po%C5%82%C4%85czenie-pgnig/Sprawozdanie_Zarzadu_PGNiG_Polaczenie_PKN_ORLEN_PGNiG_20220729.pdf.coredownload.pdf",
    ),
    (
        "ma_pgnig",
        "PKN_2022_MA_pgnig-prezentacja-inwestorska.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/archiwum-pgnig/po%C5%82%C4%85czenie-pgnig/Projekt-PGNiG-PL-Prezentacja-Inwestorska.pdf.coredownload.pdf",
    ),
    (
        "ma_pgnig",
        "PKN_2022_MA_pgnig-opinia-bieglego.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/archiwum-pgnig/po%C5%82%C4%85czenie-pgnig/Opinia_bieglego_PKNORLEN_PGNIG.pdf.coredownload.pdf",
    ),
    (
        "ma_pgnig",
        "PKN_2022_MA_pgnig-dokument-wylaczeniowy.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/archiwum-pgnig/po%C5%82%C4%85czenie-pgnig/Polaczenie_ORLEN_PGNIG_DokWyl.pdf.coredownload.pdf",
    ),
    (
        "ma_pgnig",
        "PKN_2022_MA_pgnig-zal4-wartosc-przejmowanej.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/archiwum-pgnig/po%C5%82%C4%85czenie-pgnig/Zalacznik_nr_4_do_Planu_Polaczenia_PKN_ORLEN_PGNiG_20220729.pdf.coredownload.pdf",
    ),
    (
        "ma_pgnig",
        "PKN_2022_MA_pgnig-zal5-wartosc-przejmujacej.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/archiwum-pgnig/po%C5%82%C4%85czenie-pgnig/Zalacznik_nr_5_do_Planu_Polaczenia_PKN_ORLEN_PGNiG_20220729.pdf.coredownload.pdf",
    ),
    # --- NIK Lotos ---
    (
        "nik",
        "NIK_orlen-lotos-info.pdf",
        "https://www.nik.gov.pl/plik/id,31288.pdf",
    ),
    (
        "nik",
        "NIK_orlen-lotos-wystapienie-pokontrolne.pdf",
        "https://www.nik.gov.pl/kontrole/wyniki-kontroli-nik/pobierz,kgp~i_24_003_202404051218161712312296~id0~02,typ,kj.pdf",
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


def dest_path(subdir: str, name: str) -> Path:
    if subdir == "nik":
        return NIK / name
    d = BASE / subdir
    d.mkdir(parents=True, exist_ok=True)
    return d / name


def download(subdir: str, name: str, url: str, ctx: ssl.SSLContext) -> dict:
    dest = dest_path(subdir, name)
    if dest.exists() and dest.stat().st_size > 1000:
        print(f"SKIP {name}")
        return {"file": name, "subdir": subdir, "status": "exists", "bytes": dest.stat().st_size, "url": url}
    last_err = None
    for attempt in range(1, 5):
        try:
            time.sleep(0.6 * attempt)
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=300) as r:
                data = r.read()
            if data[:20].lstrip().startswith(b"<!DOCTYPE") or data[:5] == b"<html":
                raise ValueError("got HTML")
            if len(data) < 1000:
                raise ValueError(f"too small {len(data)}")
            dest.write_bytes(data)
            print(f"OK  {name} ({len(data)} B)")
            return {"file": name, "subdir": subdir, "status": "ok", "bytes": len(data), "url": url}
        except Exception as e:
            last_err = str(e)
            print(f"FAIL {name} try {attempt}: {e}")
    return {"file": name, "subdir": subdir, "status": "fail", "error": last_err, "url": url}


def main() -> None:
    ctx = ssl.create_default_context()
    results = [download(s, n, u, ctx) for s, n, u in FILES]
    ok = sum(1 for r in results if r["status"] in ("ok", "exists"))
    manifest = {
        "scope": "M&A Energa + Lotos + PGNiG + NIK Lotos (core docs)",
        "downloaded_at": datetime.now().isoformat(timespec="seconds"),
        "ok": ok,
        "total": len(results),
        "files": results,
    }
    (BASE / "manifest_ma.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nDone: {ok}/{len(results)}")
    for r in results:
        if r["status"] == "fail":
            print(" FAIL:", r["file"], r.get("error"))


if __name__ == "__main__":
    main()
