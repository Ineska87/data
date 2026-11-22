#!/usr/bin/env python3
"""Download PKN Orlen quarterly/semi-annual reports + presentations 2020-2025."""

from __future__ import annotations

import json
import ssl
import time
import urllib.request
from datetime import datetime

from data_paths import DATA_ROOT

OUT = DATA_ROOT / "raw" / "reports" / "PKN"
OUT.mkdir(parents=True, exist_ok=True)

# (filename, url) — Q/H1 reports + presentations; no teleconference videos
FILES: list[tuple[str, str]] = [
    # ---- 2025 ----
    (
        "PKN_2025_Q4_sprawozdanie.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2025/4q2025/ORLEN_260219_2025kw4%20-%20RaportIVQ2025.pdf.coredownload.pdf",
    ),
    (
        "PKN_2025_Q4_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2025/4q2025/ORLEN_4Q-2025_Wyniki-Finansowe.pdf.coredownload.pdf",
    ),
    (
        "PKN_2025_Q4_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2025/4q2025/Dane_ze_sprawozdania__4Q2025.zip.coredownload.zip",
    ),
    (
        "PKN_2025_Q3_sprawozdanie.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2025/3q2025/ORLEN_Sprawozdanie_3kw2025.zip.coredownload.zip",
    ),
    (
        "PKN_2025_Q3_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2025/3q2025/Wyniki_3Q25_PL_FINAL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2025_Q3_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2025/3q2025/Dane_ze_sprawozdania__3Q2025.zip.coredownload.zip",
    ),
    (
        "PKN_2025_H1_sprawozdanie.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2025/2q2025/Sprawozdanie_1H2025.zip.coredownload.zip",
    ),
    (
        "PKN_2025_Q2_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2025/2q2025/ORLEN_Q2-2025_Wyniki-Finansowe.pdf.coredownload.pdf",
    ),
    (
        "PKN_2025_H1_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2025/2q2025/Dane_ze_sprawozdania_1H2025.zip.coredownload.zip",
    ),
    (
        "PKN_2025_Q1_sprawozdanie.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2025/1q2025/Sprawozdanie_1kw2025.zip.coredownload.zip",
    ),
    (
        "PKN_2025_Q1_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2025/1q2025/ORLEN_1Q25_PL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2025_Q1_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2025/1q2025/Dane_ze_sprawozdania_1q2025.zip.coredownload.zip",
    ),
    # ---- 2024 ----
    (
        "PKN_2024_Q4_sprawozdanie.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2024/4q2024/orlen_250227_2024kw4%20-%20raport%20ivq2024_signed.pdf.coredownload.pdf",
    ),
    (
        "PKN_2024_Q4_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2024/4q2024/Wyniki_4Q24_PL_FINAL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2024_Q4_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2024/4q2024/Dane_ze_sprawozdania_4q24.zip.coredownload.zip",
    ),
    (
        "PKN_2024_Q3_sprawozdanie.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2024/3q2024/SPRAWOZDANIE_24Q3.zip.coredownload.zip",
    ),
    (
        "PKN_2024_Q3_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2024/3q2024/Wyniki_3Q24_PL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2024_Q3_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2024/3q2024/Dane_ze_sprawozdania_3q24.zip.coredownload.zip",
    ),
    (
        "PKN_2024_H1_sprawozdanie.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2024/2q2024/2024_08_24_Sprawozdanie_fin_1h24.zip.coredownload.zip",
    ),
    (
        "PKN_2024_Q2_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/prezentacje/prezentacje-wynikowe/2024/Skonsolidowane%20wyniki%20finansowe%20Grupy%20ORLEN%202%20kwarta%C5%82%202024.pdf.coredownload.pdf",
    ),
    (
        "PKN_2024_Q2_letter-ceo.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/prezentacje/prezentacje-wynikowe/2024/Skonsolidowane-wyniki-finansowe-ORLEN-S.A.-za-2.-kwarta%C5%82-2024-roku-Wprowadzenie-Prezesa-Zarz%C4%85du.pdf.coredownload.pdf",
    ),
    (
        "PKN_2024_H1_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2024/2q2024/Dane_ze_sprawozdania_1h24.zip.coredownload.zip",
    ),
    (
        "PKN_2024_Q1_sprawozdanie.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2024/1q2024/ORLEN_Sprawozdanie_Q12024_PL.zip.coredownload.zip",
    ),
    (
        "PKN_2024_Q1_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2024/1q2024/Wyniki_1Q24_PL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2024_Q1_letter-ceo.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2024/1q2024/Wprowadzenie_CEO_PL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2024_Q1_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2024/1q2024/ORLEN_Dane_ze_spr_1Q24.zip.coredownload.zip",
    ),
    # ---- 2023 ----
    (
        "PKN_2023_Q4_sprawozdanie.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2023/4q2023/ORLEN_240122_2024kw4%20-%20RAPORT%20IVQ2023.pdf.coredownload.pdf",
    ),
    (
        "PKN_2023_Q4_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2023/4q2023/Wyniki_4Q23_PL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2023_Q4_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2023/4q2023/Dane_ze_sprawozdania_4q23.zip.coredownload.zip",
    ),
    (
        "PKN_2023_Q3_sprawozdanie.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2023/3q2023/ORLEN_231031_2023kw3%20-%20RAPORT%20IIIQ2023.pdf.coredownload.pdf",
    ),
    (
        "PKN_2023_Q3_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2023/3q2023/Wyniki_3Q23_PL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2023_Q3_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2023/3q2023/Dane_ze_sprawozdania_3q23.zip.coredownload.zip",
    ),
    (
        "PKN_2023_H1_sprawozdanie.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2023/2q2023/20230824_Spr_fin_1H23.zip.coredownload.zip",
    ),
    # NOTE: osobny ZIP „dane liczbowe” H1 2023 nie jest w IR Orlen (sprawdzone 2026-07-20).
    # Panel 2023Q2: rekonstrukcja z Q3 YTD − Q1 − Q3 w build_panel.py.
    (
        "PKN_2023_Q2_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2023/2q2023/Wyniki_2Q23_PL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2023_Q1_sprawozdanie.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2023/1q2023/Sprawozdanie_1kw23.zip.coredownload.zip",
    ),
    (
        "PKN_2023_Q1_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2023/1q2023/Wyniki_1Q23_PL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2023_Q1_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2023/1q2023/230525_Dane_ze_sprawozdania_1kw23.zip.coredownload.zip",
    ),
    # ---- 2022 ----
    (
        "PKN_2022_Q4_sprawozdanie.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2022/4q2022/PKN_ORLEN_230224_2022w4%20-%20RAPORT%20IVQ2022_PL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2022_Q4_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2022/4q2022/Wyniki_4Q22_PL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2022_Q4_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2022/4q2022/2022q4_Dane_ze_sprawozdania.zip.coredownload.zip",
    ),
    (
        "PKN_2022_Q3_sprawozdanie.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2022/3q2022/Raport3kw22_PL.zip.coredownload.zip",
    ),
    (
        "PKN_2022_Q3_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2022/3q2022/Wyniki_3Q22_PL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2022_Q3_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2022/3q2022/Dane_ze_sprawozdaniaIIIQ2022PL.zip.coredownload.zip",
    ),
    (
        "PKN_2022_H1_sprawozdanie.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2022/2q2022/PKNORLEN_20220805_1H2022_PL.zip.coredownload.zip",
    ),
    (
        "PKN_2022_Q2_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2022/2q2022/Wyniki_2Q22_PL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2022_H1_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2022/2q2022/Dane_ze_sprawozd_2g2022.zip.coredownload.zip",
    ),
    (
        "PKN_2022_Q1_sprawozdanie.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2022/1q2022/PKN_ORLEN_220428_2022kw1%20-%20RAPORT%20IQ2022_PL.zip.coredownload.zip",
    ),
    (
        "PKN_2022_Q1_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2022/1q2022/Wyniki_1Q22_PL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2022_Q1_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2022/1q2022/Dane_ze_sprawozd_1q2022.zip.coredownload.zip",
    ),
    # ---- 2021 ----
    (
        "PKN_2021_Q4_sprawozdanie.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2021/dokumenty/4q2021/PKN_ORLEN_220127_2021w4%20-%20RAPORT%20IVQ2021_PL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2021_Q4_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2021/dokumenty/4q2021/Wyniki_4Q21_PL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2021_Q4_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2021/dokumenty/4q2021/Dane_ze_sprawozd_4q2021.zip.coredownload.zip",
    ),
    (
        "PKN_2021_Q3_sprawozdanie.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2021/dokumenty/3q2021/PKN_ORLEN_211028_2021kw3%20-%20RAPORT%20IIIQ2021.zip.coredownload.zip",
    ),
    (
        "PKN_2021_Q3_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2021/dokumenty/3q2021/Wyniki_3Q21_PL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2021_Q3_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2021/dokumenty/3q2021/Dane_ze_spr_3kw2021.zip.coredownload.zip",
    ),
    (
        "PKN_2021_H1_sprawozdanie.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2021/dokumenty/PKN_ORLEN_210729_2021polrocze%20-%20RAPORT%20IH2021.zip.coredownload.zip",
    ),
    (
        "PKN_2021_Q2_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2021/dokumenty/Wyniki_2Q21_PL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2021_H1_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2021/dokumenty/Dane_ze_spr2q21_PL.zip.coredownload.zip",
    ),
    (
        "PKN_2021_Q1_sprawozdanie.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2021/dokumenty/PKN_ORLEN_210429_2021kw1%20-%20RAPORT%20IQ2021_PL.zip.coredownload.zip",
    ),
    (
        "PKN_2021_Q1_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2021/dokumenty/Wyniki_1Q21_PL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2021_Q1_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2021/dokumenty/Dane_ze_spr1q21_PL.zip.coredownload.zip",
    ),
    # ---- 2020 ----
    (
        "PKN_2020_Q4_sprawozdanie.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2020/dokumenty/PKN_ORLEN_210204_2020w4%20-%20RAPORT%20IVQ2020_PL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2020_Q4_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2020/dokumenty/Wyniki_4Q20_PL_FINAL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2020_Q4_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2020/dokumenty/Dane_ze_spr4q20_PL.zip.coredownload.zip",
    ),
    (
        "PKN_2020_Q3_sprawozdanie.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2020/dokumenty/Sprawozdanie_3q20.zip.coredownload.zip",
    ),
    (
        "PKN_2020_Q3_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2020/dokumenty/Wyniki_3q20_PL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2020_Q3_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2020/dokumenty/Dane_ze_spr3q20_PL.zip.coredownload.zip",
    ),
    (
        "PKN_2020_H1_sprawozdanie.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2020/dokumenty/PKN_ORLEN_1h20_PL.zip.coredownload.zip",
    ),
    (
        "PKN_2020_Q2_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2020/dokumenty/Wyniki_2Q20_PL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2020_H1_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2020/dokumenty/Dane_ze_spr1h20_PL.zip.coredownload.zip",
    ),
    (
        "PKN_2020_Q1_sprawozdanie.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2020/dokumenty/PKN_ORLEN_200506_2020kw1%20-%20RAPORT%20IQ2020_PL.zip.coredownload.zip",
    ),
    (
        "PKN_2020_Q1_prezentacja.pdf",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2020/dokumenty/Wyniki_1Q20_PL_FINAL.pdf.coredownload.pdf",
    ),
    (
        "PKN_2020_Q1_dane-liczbowe.zip",
        "https://www.orlen.pl/content/dam/internet/orlen/pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania/2020/dokumenty/Dane_spr_fin_1q20.zip.coredownload.zip",
    ),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Referer": "https://www.orlen.pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania",
}


def download(name: str, url: str, ctx: ssl.SSLContext) -> dict:
    dest = OUT / name
    if dest.exists() and dest.stat().st_size > 1000:
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
            dest.write_bytes(data)
            print(f"OK  {name} ({len(data)} B, try {attempt})")
            return {
                "file": name,
                "url": url,
                "status": "ok",
                "bytes": len(data),
                "attempt": attempt,
            }
        except Exception as e:
            last_err = str(e)
            print(f"FAIL {name} try {attempt}: {e}")
    return {"file": name, "url": url, "status": "fail", "error": last_err}


def main() -> None:
    ctx = ssl.create_default_context()
    results = []
    for name, url in FILES:
        results.append(download(name, url, ctx))

    ok = sum(1 for r in results if r["status"] in ("ok", "exists"))
    fail = [r for r in results if r["status"] == "fail"]

    # merge into / update quarter manifest
    q_manifest = {
        "ticker": "PKN",
        "scope": "kwartaly + polrocza + prezentacje 2020-2025 (bez telekonferencji MP4)",
        "downloaded_at": datetime.now().isoformat(timespec="seconds"),
        "ok": ok,
        "total": len(results),
        "failed": fail,
        "files": results,
    }
    (OUT / "manifest_quarters.json").write_text(
        json.dumps(q_manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # refresh summary of all PKN files
    all_files = []
    for p in sorted(OUT.iterdir()):
        if p.suffix == ".json":
            continue
        all_files.append({"file": p.name, "bytes": p.stat().st_size})
    summary = {
        "ticker": "PKN",
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "n_files": len(all_files),
        "total_mb": round(sum(f["bytes"] for f in all_files) / 1e6, 1),
        "files": all_files,
    }
    (OUT / "manifest_all.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\nDone: {ok}/{len(results)} ok")
    if fail:
        print("Failed:")
        for r in fail:
            print(" -", r["file"], r.get("error"))
    print(f"Folder total: {summary['n_files']} files, {summary['total_mb']} MB")


if __name__ == "__main__":
    main()
