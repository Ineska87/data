"""
Krok 0: Analiza alternatywnych benchmarków dla spółek o niskim R².

Porównuje R² modelu rynkowego (OLS) przy różnych benchmarkach.
Spółki: UNT (obecny R²≈0.029), ZEP (≈0.086), JSW (≈0.239), LWB (≈0.166).
"""


from data_paths import LEGACY
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=RuntimeWarning)

BASE = LEGACY
RET_F     = BASE / "processed" / "returns_daily.parquet"
EVENTS_F  = BASE / "processed" / "events_master_2019_2025.parquet"
CURRENT_R2 = BASE / "processed" / "car_results.parquet"

EST_START     = -250
EST_END       = -11
MIN_OBS       = 100
MKTCLOSE_HOUR = 17

ret    = pd.read_parquet(RET_F).sort_index()
events = pd.read_parquet(EVENTS_F)
td     = ret.index


def nearest_td_from(date):
    i = td.searchsorted(date)
    return int(i) if i < len(td) else None


def get_day0(row):
    date  = pd.Timestamp(row["event_date"])
    shift = False
    if row["has_time"] and row["event_time"]:
        try:
            h = int(str(row["event_time"]).split(":")[0])
            if h >= MKTCLOSE_HOUR:
                shift = True
        except Exception:
            shift = True
    else:
        shift = True
    if shift:
        date += pd.Timedelta(days=1)
    i = nearest_td_from(date)
    return td[i] if i is not None else None


def compute_r2_for_benchmark(ticker, bench, evs):
    """Zwraca listę R² dla każdego zdarzenia przy danym benchmarku."""
    if bench not in ret.columns:
        return None
    r2s = []
    betas = []
    for _, ev in evs.iterrows():
        day0 = get_day0(ev)
        if day0 is None:
            continue
        i0 = int(td.searchsorted(day0))
        if i0 >= len(td) or td[i0] != day0:
            continue
        i_s = max(i0 + EST_START, 0)
        i_e = i0 + EST_END + 1
        if i_e <= i_s:
            continue
        est    = ret.iloc[i_s:i_e]
        r_s    = est[ticker].dropna()
        r_m    = est[bench].dropna()
        common = r_s.index.intersection(r_m.index)
        if len(common) < MIN_OBS:
            continue
        X = np.column_stack([np.ones(len(common)), r_m.loc[common].values])
        b = np.linalg.lstsq(X, r_s.loc[common].values, rcond=None)[0]
        pred   = X @ b
        ss_res = float(np.sum((r_s.loc[common].values - pred) ** 2))
        ss_tot = float(np.sum((r_s.loc[common].values - r_s.loc[common].mean()) ** 2))
        if ss_tot > 0:
            r2s.append(1.0 - ss_res / ss_tot)
            betas.append(float(b[1]))
    return r2s, betas


# Kandydaci benchmarków do porównania
CANDIDATES = {
    "UNT": ["WIG-paliwa", "WIG", "WIG20"],
    "ZEP": ["WIG", "WIG-energia", "WIG20"],
    "JSW": ["WIG", "WIG20"],
    "LWB": ["WIG", "WIG20"],
}

# Obecny benchmark (z compute_car.py)
CURRENT_BENCH = {
    "UNT": "WIG-paliwa",
    "ZEP": "WIG",
    "JSW": "WIG",
    "LWB": "WIG",
}

print("=" * 76)
print("ANALIZA ALTERNATYWNYCH BENCHMARKÓW — PORÓWNANIE R²")
print("Estymacja: OLS, okno [-250, -11] dni sesyjnych")
print("=" * 76)

recommendations = {}

for ticker, benchmarks in CANDIDATES.items():
    evs = events[events["ticker"] == ticker]
    n_total = len(evs)

    print(f"\n{'─' * 70}")
    print(f"  {ticker}  (n_zdarzeń = {n_total})")
    print(f"  {'Benchmark':<16}  {'n_ok':>5}  {'mean R²':>8}  "
          f"{'median R²':>10}  {'min R²':>8}  {'mean β':>8}")
    print(f"  {'─' * 60}")

    best_bench = None
    best_mean  = -1.0

    for bench in benchmarks:
        result = compute_r2_for_benchmark(ticker, bench, evs)
        if result is None:
            print(f"  {bench:<16}  BRAK DANYCH w returns_daily")
            continue
        r2s, betas = result
        if not r2s:
            print(f"  {bench:<16}  za mało obserwacji (min {MIN_OBS})")
            continue

        mean_r2   = float(np.mean(r2s))
        median_r2 = float(np.median(r2s))
        min_r2    = float(np.min(r2s))
        mean_beta = float(np.mean(betas))
        is_current = " ← OBECNY" if bench == CURRENT_BENCH[ticker] else ""

        print(f"  {bench:<16}  {len(r2s):5d}  {mean_r2:8.4f}  "
              f"{median_r2:10.4f}  {min_r2:8.4f}  {mean_beta:8.3f}{is_current}")

        if mean_r2 > best_mean:
            best_mean  = mean_r2
            best_bench = bench

    recommendations[ticker] = (best_bench, best_mean)
    current_bench = CURRENT_BENCH[ticker]
    improvement   = best_bench != current_bench

    if improvement:
        print(f"\n  ⚡ REKOMENDACJA: zmień {current_bench} → {best_bench} "
              f"(mean R² wzrośnie do {best_mean:.4f})")
    else:
        print(f"\n  ✓  Obecny benchmark '{current_bench}' jest optymalny "
              f"(mean R² = {best_mean:.4f})")

print("\n\n" + "=" * 76)
print("PODSUMOWANIE — co zmienić w BENCHMARK dict (compute_car.py)")
print("=" * 76)

changes_needed = False
for ticker, (best_bench, best_r2) in recommendations.items():
    current = CURRENT_BENCH[ticker]
    if best_bench != current:
        print(f"  {ticker}: '{current}' → '{best_bench}'  (mean R² = {best_r2:.4f})")
        changes_needed = True

if not changes_needed:
    print("  Żadnych zmian — obecne benchmarki są optymalne.")

print("=" * 76)
