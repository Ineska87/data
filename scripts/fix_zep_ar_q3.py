#!/usr/bin/env python3
"""Re-download correct ZEP AR SSF (not payments) + missing Q3 2024/2025."""

from __future__ import annotations

import ssl
import urllib.request
from data_paths import DATA_ROOT

BASE = DATA_ROOT / "raw" / "reports" / "ZEP"
CTX = ssl.create_default_context()
H = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://ri.zepak.com.pl/",
}

# Correct consolidated financial statements + missing quarters
FILES = [
    (
        "ZEP_2020_AR_skonsolidowany.pdf",
        "https://ri.zepak.com.pl/upload/files/ZEPAK_2020-R_Skonsolidowane_Sprawozdanie_Finansowe-sig-sig-sig-sig-sig-sig.pdf",
    ),
    (
        "ZEP_2021_AR_skonsolidowany.pdf",
        "https://ri.zepak.com.pl/upload/files/ZEPAK_2021-R_Skonsolidowane_Sprawozdanie_Finansowe_GKZEPAK.pdf",
    ),
    (
        "ZEP_2023_AR_skonsolidowany.pdf",
        "https://ri.zepak.com.pl/upload/files/ZEPAK_2023_R_Skonsolidowane__Sprawozdanie_Finansowe.pdf",
    ),
    (
        "ZEP_2025_AR_skonsolidowany.pdf",
        "https://ri.zepak.com.pl/upload/files/GK_ZEPAK_2025-R_SKONSOLIDOWANE_SPRAWOZDANIE_FINANSOWE-sig-sig-sig-sig.pdf",
    ),
    (
        "ZEP_2021_AR_sprawozdanie-zarzadu.pdf",
        "https://ri.zepak.com.pl/upload/files/Sprawozdanie_zarzadu_z_dziaalnoci_ZE_PAK.pdf",
    ),
    # Q3 2024 / 2025 were misclassified as Q1
    (
        "ZEP_2024_Q3_sprawozdanie.pdf",
        "https://ri.zepak.com.pl/upload/files/zepak_2024-3q_rozszerzony_skonsolidowany_raport_za_iii_kwarta_2024-sig-sig-sig_signed.pdf",
    ),
    (
        "ZEP_2025_Q3_sprawozdanie.pdf",
        "https://ri.zepak.com.pl/upload/files/ZEPAK_2025-3Q_ROZSZERZONY_SKONSOLIDOWANY_RAPORT_ZA_III_KWARTA_2025_ROKU.pdf",
    ),
    # Q1 2023 if missing
    (
        "ZEP_2023_Q1_sprawozdanie.pdf",
        "https://ri.zepak.com.pl/upload/files/ZEP_2023-03-31_pl.pdf",
    ),
]


def main() -> None:
    BASE.mkdir(parents=True, exist_ok=True)
    for name, url in FILES:
        path = BASE / name
        print(f"… {name}")
        try:
            req = urllib.request.Request(url, headers=H)
            with urllib.request.urlopen(req, context=CTX, timeout=180) as r:
                data = r.read()
            if not data.startswith(b"%PDF"):
                print(f"  FAIL not pdf {data[:40]!r}")
                continue
            path.write_bytes(data)
            print(f"  OK {len(data):,}")
        except Exception as e:
            print(f"  FAIL {e}")


if __name__ == "__main__":
    main()
