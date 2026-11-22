"""
Po recode categorize_events: synchronizuje event_type w car_results
bez pełnego przeliczenia modelu rynkowego (CAR nie zależy od kategorii).

Wejście: events_master_2019_2025.parquet, car_results.parquet
Wyjście: car_results.parquet / .csv (nadpisane meta)
"""

from data_paths import LEGACY
import pandas as pd

BASE = LEGACY
PROC = BASE / "processed"

ev = pd.read_parquet(PROC / "events_master_2019_2025.parquet")[
    ["event_id", "event_type", "event_type_pl", "title"]
]
car = pd.read_parquet(PROC / "car_results.parquet")

before = car.groupby("event_type").size()
car = car.drop(columns=["event_type", "event_type_pl"], errors="ignore")
# keep car title as source of truth for text; only overwrite types
meta = ev.drop_duplicates("event_id")
car = car.merge(meta[["event_id", "event_type", "event_type_pl"]], on="event_id", how="left")

missing = car["event_type"].isna().sum()
if missing:
    print(f"[WARN] {missing} wierszy CAR bez event_type po merge")

# restore column order roughly
cols = list(car.columns)
for c in ("event_type", "event_type_pl"):
    if c in cols:
        cols.remove(c)
# insert after day0 if present
if "day0" in cols:
    i = cols.index("day0") + 1
    cols = cols[:i] + ["event_type", "event_type_pl"] + cols[i:]
else:
    cols = ["event_type", "event_type_pl"] + cols
car = car[cols]

car.to_parquet(PROC / "car_results.parquet", index=False)
try:
    car.to_csv(PROC / "car_results.csv", index=False, encoding="utf-8-sig")
except Exception as e:
    print(f"[INFO] car_results.csv skip: {e}")

after = car.groupby("event_type").size() // 5  # 5 windows
print("event_type w car_results (unikalne zdarzenia ≈ n/5):")
print(after.sort_values(ascending=False).to_string())
print(f"n_rows={len(car)} unique_events={car.event_id.nunique()}")
print("OK: car_results zsynchronizowane z events_master_2019_2025")
