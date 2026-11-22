"""
Filtruje events_master do lat 2019-2025 i zapisuje wersje robocza.
"""
from pathlib import Path
import pandas as pd

BASE    = Path(__file__).parent.parent
IN_FILE = BASE / "processed" / "events_master.parquet"
OUT_DIR = BASE / "processed"

df = pd.read_parquet(IN_FILE)

# filtracja
mask = (df["event_date"].dt.year >= 2019) & (df["event_date"].dt.year <= 2025)
out  = df[mask].copy().reset_index(drop=True)

# zapis
out.to_parquet(OUT_DIR / "events_master_2019_2025.parquet", index=False)
out.to_csv(OUT_DIR / "events_master_2019_2025.csv", index=False, encoding="utf-8-sig")

LABEL_PL = {
    "wyniki_finansowe":   "Wyniki finansowe",
    "dywidenda":          "Dywidenda",
    "prognoza":           "Prognoza/szacunki",
    "zmiany_personalne":  "Zmiany personalne",
    "transakcje_MA":      "Transakcje M&A",
    "emisja_finansowanie":"Emisja/finansowanie",
    "walne_zgromadzenie": "Walne zgromadzenie",
    "rating_rekomendacja":"Rating/rekomendacja",
    "regulatory_prawne":  "Regulacyjne/prawne",
    "akcjonariat":        "Akcjonariat/progi",
    "umowy_kontrakty":    "Umowy/kontrakty",
    "inne":               "Inne",
}

total = len(out)
full  = len(df)
print("=" * 60)
print(f"EVENTS MASTER 2019-2025")
print("=" * 60)
print(f"Wszystkich zdarzen (pelny plik): {full}")
print(f"Po filtracji 2019-2025:          {total}  ({100*total//full}%)")
print()

# rozkład po latach
print("Rok    Zdarzen   Ticker breakdown")
print("-" * 60)
by_year = out.groupby(out["event_date"].dt.year)
for year, grp in by_year:
    per_ticker = grp.groupby("ticker").size()
    ticker_str = "  ".join(f"{t}:{n}" for t, n in per_ticker.items())
    print(f"  {year}   {len(grp):5d}    {ticker_str}")
print(f"  LACZNIE {total:5d}")
print()

# rozkład po kategoriach
print("Kategorie:")
print("-" * 50)
counts = out["event_type"].value_counts()
for cat, n in counts.items():
    label = LABEL_PL.get(cat, cat)
    bar = "#" * (n // 10)
    print(f"  {label:<28s} {n:4d}  ({100*n//total:2d}%)  {bar}")
print()

# rozkład po tickerach
print("Ticker  Zdarzen   has_time   Kategorie (top 3)")
print("-" * 70)
for ticker, grp in out.groupby("ticker"):
    n = len(grp)
    ht = grp["has_time"].sum()
    top3 = grp["event_type"].value_counts().head(3)
    top3_str = ", ".join(f"{LABEL_PL.get(k,k)}({v})" for k, v in top3.items())
    print(f"  {ticker:5s}  {n:5d}     {ht:4d}/{n:4d} ({100*ht//n:2d}%)   {top3_str}")
print()

# has_time ogolnie
ht_total = out["has_time"].sum()
print(f"has_time = True:  {ht_total} ({100*ht_total//total}%)")
print(f"has_time = False: {total - ht_total} ({100*(total-ht_total)//total}%)")
print()
print(f"Zapisano:")
print(f"  {OUT_DIR / 'events_master_2019_2025.parquet'}")
print(f"  {OUT_DIR / 'events_master_2019_2025.csv'}")
