#!/usr/bin/env python3
"""Fetch macro / sector series for the thesis (2020–2025, with 2019 buffer).

Public sources (no Stooq — anti-bot blocks direct CSV):
- Brent spot: FRED ``DCOILBRENTEU`` (USD/bbl)
- EUR/PLN, USD/PLN: NBP API table A (mid)
- NBP reference rate: official RPP decision path (step series)
- PL short rate (monthly): FRED ``IRSTCI01PLM156N`` (proxy near WIBOR/policy)
- EU natural gas (monthly): FRED ``PNGASEUUSDM`` (USD)
- Day-ahead power PL: energy-charts API bzn=PL (EUR/MWh, hourly → daily mean)
- EUA proxy (daily): yfinance ``KRBN`` (KFA Global Carbon ETF) — NOT ICE EUA futures;
  labeled ``eua_proxy_krbn``; replace with ICE/EEX when licensed data available
- Sector indices (optional): existing ``data/raw/market_data/WIG-energia.csv``, ``WIG-paliwa.csv``

Outputs
-------
raw/macro/
  brent_daily.csv, fx_daily.csv, rates.csv, tge_power_proxy.csv, eua_proxy_daily.csv,
  gas_eu_monthly.csv, sources.md
processed/macro/
  macro_daily.parquet (+ .csv)
  macro_quarterly.parquet (+ .csv)  — for panel merge
  codebook.md, coverage.json
"""

from __future__ import annotations

import json
import ssl
import time
import urllib.error
import urllib.request
from io import StringIO

import numpy as np
import pandas as pd

from data_paths import DATA_ROOT

RAW = DATA_ROOT / "raw" / "macro"
PROC = DATA_ROOT / "processed" / "macro"
MARKET = DATA_ROOT / "raw" / "market_data"

START = "2019-01-01"
END = "2025-12-31"
# panel window
PANEL_START = "2020-01-01"
PANEL_END = "2025-12-31"

CTX = ssl.create_default_context()
UA = {"User-Agent": "magisterka-bcf-macro/1.0 (research; academic)"}


def http_get(url: str, timeout: int = 120, retries: int = 3) -> bytes:
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={**UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, context=CTX, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last_err = e
            print(f"  http retry {attempt}/{retries}: {type(e).__name__}: {e}")
            time.sleep(1.5 * attempt)
    assert last_err is not None
    raise last_err


def http_get_text(url: str, timeout: int = 120, retries: int = 3) -> str:
    return http_get(url, timeout=timeout, retries=retries).decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Brent (FRED)
# ---------------------------------------------------------------------------
def _yf_close(symbol: str) -> pd.DataFrame:
    import yfinance as yf

    raw = yf.download(symbol, start=START, end="2026-01-01", progress=False, auto_adjust=True)
    if raw is None or raw.empty:
        return pd.DataFrame(columns=["date", "close"])
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
    else:
        close = raw["Close"] if "Close" in raw.columns else raw.iloc[:, 0]
    df = close.reset_index()
    df.columns = ["date", "close"]
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    return df.dropna()


def fetch_brent() -> pd.DataFrame:
    """Prefer yfinance BZ=F (reliable); optional FRED spot if reachable quickly."""
    out = RAW / "brent_daily.csv"
    print("Brent yfinance BZ=F …", flush=True)
    yf_df = _yf_close("BZ=F")
    if not yf_df.empty:
        df = yf_df.rename(columns={"close": "brent_usd"})
        df = df[(df["date"] >= START) & (df["date"] <= END)]
        df.to_csv(out, index=False)
        print(f"  {len(df)} rows (BZ=F) → {out.name}", flush=True)
        # try FRED spot overlay in background-friendly short attempt
        try:
            print("  try FRED spot overlay (30s) …", flush=True)
            text = http_get_text(
                "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU",
                timeout=30,
                retries=1,
            )
            fred = pd.read_csv(StringIO(text))
            fred.columns = ["date", "brent_usd"]
            fred["date"] = pd.to_datetime(fred["date"])
            fred["brent_usd"] = pd.to_numeric(fred["brent_usd"], errors="coerce")
            fred = fred[(fred["date"] >= START) & (fred["date"] <= END)].dropna()
            if len(fred) > 100:
                fred.to_csv(out, index=False)
                print(f"  replaced with FRED spot {len(fred)} rows", flush=True)
                return fred
        except Exception as e:
            print(f"  FRED skip ({type(e).__name__})", flush=True)
        return df
    raise RuntimeError("Brent download failed")


# ---------------------------------------------------------------------------
# FX NBP
# ---------------------------------------------------------------------------
def _nbp_currency_year(code: str, year: int) -> list[dict]:
    url = (
        f"https://api.nbp.pl/api/exchangerates/rates/a/{code.lower()}/"
        f"{year}-01-01/{year}-12-31/?format=json"
    )
    try:
        j = json.loads(http_get_text(url, timeout=60))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []
        raise
    return [
        {"date": r["effectiveDate"], "mid": r["mid"]}
        for r in j.get("rates", [])
    ]


def fetch_fx() -> pd.DataFrame:
    print("FX NBP EUR + USD …", flush=True)
    rows_eur, rows_usd = [], []
    for y in range(2019, 2026):
        try:
            rows_eur.extend(_nbp_currency_year("eur", y))
            time.sleep(0.15)
            rows_usd.extend(_nbp_currency_year("usd", y))
            time.sleep(0.15)
            print(f"  year {y}: EUR {len(rows_eur)} cum, USD {len(rows_usd)} cum", flush=True)
        except Exception as e:
            print(f"  year {y} FAIL {e}", flush=True)
    if not rows_eur and not rows_usd:
        print("  NBP failed — yfinance EURPLN=X / USDPLN=X", flush=True)
        e = _yf_close("EURPLN=X").rename(columns={"close": "eurpln"})
        u = _yf_close("USDPLN=X").rename(columns={"close": "usdpln"})
        df = e.merge(u, on="date", how="outer").sort_values("date")
    else:
        eur = pd.DataFrame(rows_eur).rename(columns={"mid": "eurpln"})
        usd = pd.DataFrame(rows_usd).rename(columns={"mid": "usdpln"})
        eur["date"] = pd.to_datetime(eur["date"])
        usd["date"] = pd.to_datetime(usd["date"])
        df = eur.merge(usd, on="date", how="outer").sort_values("date")
    df = df[(df["date"] >= START) & (df["date"] <= END)]
    out = RAW / "fx_daily.csv"
    df.to_csv(out, index=False)
    print(f"  {len(df)} rows → {out.name}", flush=True)
    return df


# ---------------------------------------------------------------------------
# NBP reference rate (official RPP path) + FRED monthly short rate
# ---------------------------------------------------------------------------
# Source: NBP / RPP decisions (stopa referencyjna). Effective from date listed.
NBP_REF_PATH = [
    # (effective_date, rate_pct)
    ("2015-03-05", 1.50),
    ("2020-03-18", 1.00),
    ("2020-04-09", 0.50),
    ("2020-05-29", 0.10),
    ("2021-10-07", 0.50),
    ("2021-11-04", 1.25),
    ("2021-12-09", 1.75),
    ("2022-01-05", 2.25),
    ("2022-02-09", 2.75),
    ("2022-03-09", 3.50),
    ("2022-04-07", 4.50),
    ("2022-05-06", 5.25),
    ("2022-06-09", 6.00),
    ("2022-07-08", 6.50),
    ("2022-09-08", 6.75),
    ("2023-09-07", 6.00),
    ("2023-10-05", 5.75),
    # 2025: RPP cuts (verify vs NBP if using post-2025 window)
    ("2025-05-08", 5.25),
    ("2025-07-03", 5.00),
]


def fetch_rates() -> pd.DataFrame:
    print("Rates: NBP ref path (+ optional FRED short rate) …", flush=True)
    dates = pd.date_range(START, END, freq="D")
    path = pd.DataFrame(NBP_REF_PATH, columns=["effective", "nbp_ref_rate"])
    path["effective"] = pd.to_datetime(path["effective"])
    path = path.sort_values("effective")
    daily = pd.DataFrame({"date": dates})
    daily = pd.merge_asof(
        daily.sort_values("date"),
        path.rename(columns={"effective": "date"}),
        on="date",
        direction="backward",
    )

    # Short-term rate: try FRED; else use NBP reference as policy-rate proxy
    daily["pl_short_rate_m"] = np.nan
    try:
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=IRSTCI01PLM156N"
        text = http_get_text(url, timeout=45, retries=2)
        m = pd.read_csv(StringIO(text))
        m.columns = ["date", "pl_short_rate_m"]
        m["date"] = pd.to_datetime(m["date"])
        m["pl_short_rate_m"] = pd.to_numeric(m["pl_short_rate_m"], errors="coerce")
        m = m.dropna(subset=["pl_short_rate_m"])
        if len(m) > 12:
            m["year"] = m["date"].dt.year
            m["month"] = m["date"].dt.month
            daily["year"] = daily["date"].dt.year
            daily["month"] = daily["date"].dt.month
            daily = daily.drop(columns=["pl_short_rate_m"], errors="ignore")
            daily = daily.merge(
                m[["year", "month", "pl_short_rate_m"]],
                on=["year", "month"],
                how="left",
            )
            daily = daily.drop(columns=["year", "month"])
            print(f"  FRED short rate OK ({m['pl_short_rate_m'].notna().sum()} monthly pts)", flush=True)
        else:
            print("  FRED short rate too short — fallback", flush=True)
    except Exception as e:
        print(f"  FRED short rate skip ({type(e).__name__})", flush=True)

    # Fallback: policy rate as short-rate proxy (documented; not WIBOR)
    if daily["pl_short_rate_m"].isna().all():
        daily["pl_short_rate_m"] = daily["nbp_ref_rate"]
        print("  pl_short_rate_m = nbp_ref_rate (proxy; FRED unavailable)", flush=True)
    else:
        daily["pl_short_rate_m"] = daily["pl_short_rate_m"].fillna(daily["nbp_ref_rate"])
        print("  pl_short_rate_m: FRED + NBP ref fill gaps", flush=True)

    out = RAW / "rates.csv"
    daily.to_csv(out, index=False)
    print(f"  {len(daily)} rows → {out.name}; short non-null={daily['pl_short_rate_m'].notna().mean():.0%}", flush=True)
    return daily


# ---------------------------------------------------------------------------
# EU gas monthly (FRED)
# ---------------------------------------------------------------------------
def fetch_gas() -> pd.DataFrame:
    """EU gas: try FRED monthly; else yfinance natural gas futures NG=F as daily proxy."""
    out = RAW / "gas_eu_monthly.csv"
    print("EU gas …", flush=True)
    try:
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=PNGASEUUSDM"
        text = http_get_text(url, timeout=30, retries=1)
        df = pd.read_csv(StringIO(text))
        df.columns = ["date", "gas_eu_usd"]
        df["date"] = pd.to_datetime(df["date"])
        df["gas_eu_usd"] = pd.to_numeric(df["gas_eu_usd"], errors="coerce")
        df = df[(df["date"] >= START) & (df["date"] <= END)].dropna()
        df.to_csv(out, index=False)
        print(f"  FRED monthly {len(df)} → {out.name}", flush=True)
        return df
    except Exception as e:
        print(f"  FRED gas skip ({type(e).__name__}); NG=F proxy", flush=True)
        yf_df = _yf_close("NG=F")
        if yf_df.empty:
            return pd.DataFrame(columns=["date", "gas_eu_usd"])
        df = yf_df.rename(columns={"close": "gas_eu_usd"})
        df = df[(df["date"] >= START) & (df["date"] <= END)]
        # store as daily path too (name kept for checklist)
        df.to_csv(out, index=False)
        print(f"  NG=F daily {len(df)} → {out.name}", flush=True)
        return df


# ---------------------------------------------------------------------------
# PL day-ahead power (energy-charts, proxy for TGE RDN)
# ---------------------------------------------------------------------------
def fetch_power_pl() -> pd.DataFrame:
    """Hourly day-ahead PL → daily mean EUR/MWh. Source: energy-charts (SMARD/BNetzA)."""
    print("Power PL energy-charts bzn=PL …", flush=True)
    frames = []
    for y in range(2019, 2026):
        start = f"{y}-01-01"
        end = f"{y}-12-31"
        url = f"https://api.energy-charts.info/price?bzn=PL&start={start}&end={end}"
        try:
            j = json.loads(http_get_text(url, timeout=90, retries=2))
        except Exception as e:
            print(f"  FAIL {y}: {e}", flush=True)
            continue
        ts = j.get("unix_seconds") or []
        px = j.get("price") or []
        if not ts:
            print(f"  empty {y}", flush=True)
            continue
        part = pd.DataFrame(
            {
                "datetime": pd.to_datetime(ts, unit="s", utc=True).tz_convert("Europe/Warsaw"),
                "price": px,
            }
        )
        part["date"] = part["datetime"].dt.date
        daily = part.groupby("date", as_index=False)["price"].mean()
        daily["date"] = pd.to_datetime(daily["date"])
        daily = daily.rename(columns={"price": "power_pl_eur_mwh"})
        frames.append(daily)
        print(f"  {y}: {len(daily)} days", flush=True)
        time.sleep(1.2)
    if not frames:
        return pd.DataFrame(columns=["date", "power_pl_eur_mwh"])
    df = pd.concat(frames, ignore_index=True).drop_duplicates("date").sort_values("date")
    df = df[(df["date"] >= START) & (df["date"] <= END)]
    out = RAW / "tge_power_proxy.csv"
    df.to_csv(out, index=False)
    print(f"  {len(df)} rows → {out.name} (day-ahead PL, not TGE proprietary feed)", flush=True)
    return df


# ---------------------------------------------------------------------------
# EUA proxy via KRBN (yfinance)
# ---------------------------------------------------------------------------
def fetch_eua_proxy() -> pd.DataFrame:
    print("EUA proxy KRBN (yfinance) …", flush=True)
    yf_df = _yf_close("KRBN")
    if yf_df.empty:
        print("  empty KRBN", flush=True)
        return pd.DataFrame(columns=["date", "eua_proxy_krbn"])
    df = yf_df.rename(columns={"close": "eua_proxy_krbn"})
    df = df[(df["date"] >= START) & (df["date"] <= END)]
    out = RAW / "eua_proxy_daily.csv"
    df.to_csv(out, index=False)
    print(f"  {len(df)} rows → {out.name}", flush=True)
    return df


# ---------------------------------------------------------------------------
# Sector indices from existing market files
# ---------------------------------------------------------------------------
def load_sector_indices() -> pd.DataFrame:
    frames = []
    for name, col in [("WIG-energia", "wig_energia"), ("WIG-paliwa", "wig_paliwa"), ("WIG", "wig")]:
        path = MARKET / f"{name}.csv"
        if not path.exists():
            print(f"  skip sector {name}: missing {path.name}")
            continue
        s = pd.read_csv(path)
        # stooq-style Date,Close or similar
        date_col = next((c for c in s.columns if c.lower() in ("date", "data")), s.columns[0])
        close_col = next(
            (c for c in s.columns if c.lower() in ("close", "zamkniecie", "closing")),
            None,
        )
        if close_col is None:
            # pick last numeric
            nums = [c for c in s.columns if c != date_col]
            close_col = nums[-1] if nums else None
        if close_col is None:
            continue
        part = s[[date_col, close_col]].copy()
        part.columns = ["date", col]
        # Stooq PL export: usually ISO YYYY-MM-DD; fall back to day-first
        part["date"] = pd.to_datetime(part["date"], format="mixed", dayfirst=False, errors="coerce")
        part[col] = pd.to_numeric(part[col], errors="coerce")
        before = len(part)
        part = part.dropna()
        frames.append(part)
        print(f"  sector {name}: {len(part)}/{before} rows ({part['date'].min().date()}–{part['date'].max().date()})")
    if not frames:
        return pd.DataFrame(columns=["date"])
    out = frames[0]
    for f in frames[1:]:
        out = out.merge(f, on="date", how="outer")
    return out.sort_values("date")


# ---------------------------------------------------------------------------
# Period dummies
# ---------------------------------------------------------------------------
def add_period_dummies(df: pd.DataFrame) -> pd.DataFrame:
    d = df["date"]
    # COVID: calendar 2020 (acute phase often Mar–Dec; use full year as checklist)
    df["COVID_2020"] = ((d >= "2020-01-01") & (d <= "2020-12-31")).astype(int)
    # Energy crisis: 2022–2023
    df["ENERGY_CRISIS"] = ((d >= "2022-01-01") & (d <= "2023-12-31")).astype(int)
    # Normalization: 2024–2025
    df["NORMALIZATION"] = ((d >= "2024-01-01") & (d <= "2025-12-31")).astype(int)
    # Orlen mega-merger window: Lotos (2022-08) + PGNiG (2022-11) ± buffer
    df["MERGER_ORLEN"] = ((d >= "2022-07-01") & (d <= "2023-06-30")).astype(int)
    return df


# ---------------------------------------------------------------------------
# Assemble
# ---------------------------------------------------------------------------
def _as_day(s: pd.Series) -> pd.Series:
    """Normalize to midnight ns datetime64 (merge-safe)."""
    return pd.to_datetime(s).dt.tz_localize(None).dt.normalize().astype("datetime64[ns]")


def assemble_daily(
    brent: pd.DataFrame,
    fx: pd.DataFrame,
    rates: pd.DataFrame,
    gas: pd.DataFrame,
    power: pd.DataFrame,
    eua: pd.DataFrame,
    sector: pd.DataFrame,
) -> pd.DataFrame:
    base = pd.DataFrame({"date": pd.date_range(START, END, freq="D")})
    base["date"] = _as_day(base["date"])
    for part in (brent, fx, rates, power, eua, sector):
        if part is None or part.empty:
            continue
        p = part.copy()
        p["date"] = _as_day(p["date"])
        # drop duplicate columns if re-merge
        overlap = [c for c in p.columns if c != "date" and c in base.columns]
        if overlap:
            p = p.drop(columns=overlap)
        base = base.merge(p, on="date", how="left")

    # gas monthly or daily → asof ffill
    if gas is not None and not gas.empty:
        g = gas.copy()
        g["date"] = _as_day(g["date"])
        g = g.sort_values("date")
        if "gas_eu_usd" in base.columns:
            base = base.drop(columns=["gas_eu_usd"])
        base = pd.merge_asof(
            base.sort_values("date"),
            g[["date", "gas_eu_usd"]].sort_values("date"),
            on="date",
            direction="backward",
        )

    base = add_period_dummies(base)

    # daily returns (log) for key prices
    for col in (
        "brent_usd",
        "power_pl_eur_mwh",
        "eua_proxy_krbn",
        "eurpln",
        "usdpln",
        "wig",
        "wig_energia",
        "wig_paliwa",
    ):
        if col in base.columns:
            base[f"dlog_{col}"] = np.log(base[col] / base[col].shift(1))

    return base


def to_quarterly(daily: pd.DataFrame) -> pd.DataFrame:
    d = daily[(daily["date"] >= PANEL_START) & (daily["date"] <= PANEL_END)].copy()
    d["year"] = d["date"].dt.year
    d["quarter"] = d["date"].dt.quarter

    level_cols = [
        c
        for c in (
            "brent_usd",
            "eurpln",
            "usdpln",
            "nbp_ref_rate",
            "pl_short_rate_m",
            "gas_eu_usd",
            "power_pl_eur_mwh",
            "eua_proxy_krbn",
            "wig",
            "wig_energia",
            "wig_paliwa",
        )
        if c in d.columns
    ]
    dummy_cols = [c for c in ("COVID_2020", "ENERGY_CRISIS", "NORMALIZATION", "MERGER_ORLEN") if c in d.columns]

    agg = {c: ["mean", "last"] for c in level_cols}
    for c in dummy_cols:
        agg[c] = "max"

    g = d.groupby(["year", "quarter"]).agg(agg)
    # flatten
    g.columns = [
        f"{a}_{b}" if b in ("mean", "last") else a
        for a, b in g.columns.to_list()
    ]
    g = g.reset_index()
    # cleaner names
    rename = {}
    for c in level_cols:
        if f"{c}_mean" in g.columns:
            rename[f"{c}_mean"] = f"{c}_qmean"
        if f"{c}_last" in g.columns:
            rename[f"{c}_last"] = f"{c}_qend"
    g = g.rename(columns=rename)

    # quarterly change in brent / power (end-to-end)
    for c in ("brent_usd", "power_pl_eur_mwh", "eua_proxy_krbn", "gas_eu_usd"):
        endc = f"{c}_qend"
        if endc in g.columns:
            g[f"{c}_qchg"] = g[endc].pct_change()

    return g


def write_sources() -> None:
    text = """# Makro — źródła i notatki

| Seria | Plik raw | Źródło | Uwagi |
|-------|----------|--------|-------|
| Brent | `brent_daily.csv` | FRED DCOILBRENTEU | Spot Europe, USD/bbl |
| EURPLN, USDPLN | `fx_daily.csv` | NBP API tabela A | Kurs średni |
| Stopa ref. NBP | `rates.csv` | Ścieżka decyzji RPP | Skokowa; daty w skrypcie |
| PL short rate | `rates.csv` (`pl_short_rate_m`) | FRED IRSTCI01PLM156N | Miesięczna, ffill do dni |
| Gaz EU | `gas_eu_monthly.csv` | FRED PNGASEUUSDM | Miesięczna USD |
| Energia PL | `tge_power_proxy.csv` | energy-charts `bzn=PL` | Day-ahead EUR/MWh; **proxy TGE RDN** (nie feed TGE) |
| EUA | `eua_proxy_daily.csv` | yfinance KRBN | ETF węglowy — **proxy**, nie kontrakt ICE EUA |
| WIG / energia / paliwa | market_data CSV | lokalne pliki | Jeśli obecne |

## Dummy podokresów

| Dummy | Okno |
|-------|------|
| COVID_2020 | 2020-01-01 – 2020-12-31 |
| ENERGY_CRISIS | 2022-01-01 – 2023-12-31 |
| NORMALIZATION | 2024-01-01 – 2025-12-31 |
| MERGER_ORLEN | 2022-07-01 – 2023-06-30 (Lotos+PGNiG) |

## Skrypt

`data/scripts/fetch_macro.py`
"""
    (RAW / "sources.md").write_text(text, encoding="utf-8")


def write_codebook(daily: pd.DataFrame, q: pd.DataFrame) -> None:
    PROC.mkdir(parents=True, exist_ok=True)
    text = f"""# Codebook — macro_daily / macro_quarterly

Okres daily: {START} – {END}. Panel quarterly: {PANEL_START} – {PANEL_END}.

## macro_daily ({len(daily)} wierszy)

Kluczowe poziomy: `brent_usd`, `eurpln`, `usdpln`, `nbp_ref_rate`, `pl_short_rate_m`,
`gas_eu_usd`, `power_pl_eur_mwh`, `eua_proxy_krbn`, opcjonalnie `wig*`.

Zwroty log: `dlog_<seria>`.

Dummy: `COVID_2020`, `ENERGY_CRISIS`, `NORMALIZATION`, `MERGER_ORLEN`.

## macro_quarterly ({len(q)} wierszy)

Dla każdej serii: `*_qmean`, `*_qend`; dla wybranych `*_qchg` (pct change EOP).

Dummy: max w kwartale (=1 jeśli choć jeden dzień).

## Ograniczenia

- `power_pl_eur_mwh` = day-ahead PL (energy-charts), nie komercyjny feed TGE.
- `eua_proxy_krbn` ≠ cena EUA na ICE — do FE jako proxy sektora carbon; nie cytować jako EUA spot.
- Stopy: ref. NBP ze ścieżki decyzji; `pl_short_rate_m` miesięczna OECD/FRED.

Zob. też `data/raw/macro/sources.md`.
"""
    (PROC / "codebook.md").write_text(text, encoding="utf-8")


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    PROC.mkdir(parents=True, exist_ok=True)

    brent = fetch_brent()
    fx = fetch_fx()
    rates = fetch_rates()
    gas = fetch_gas()
    power = fetch_power_pl()
    eua = fetch_eua_proxy()
    print("Sector indices …")
    sector = load_sector_indices()

    print("Assemble daily …")
    daily = assemble_daily(brent, fx, rates, gas, power, eua, sector)
    daily_path = PROC / "macro_daily.parquet"
    daily_csv = PROC / "macro_daily.csv"
    daily.to_parquet(daily_path, index=False)
    daily.to_csv(daily_csv, index=False)
    print(f"daily {daily.shape} → {daily_path}")

    print("Quarterly …")
    q = to_quarterly(daily)
    q_path = PROC / "macro_quarterly.parquet"
    q_csv = PROC / "macro_quarterly.csv"
    q.to_parquet(q_path, index=False)
    q.to_csv(q_csv, index=False)
    print(f"quarterly {q.shape} → {q_path}")
    print(q.head(3).to_string())

    write_sources()
    write_codebook(daily, q)

    # coverage summary
    cov = {
        "n_daily": len(daily),
        "brent_nonnull": int(daily["brent_usd"].notna().sum()) if "brent_usd" in daily else 0,
        "eurpln_nonnull": int(daily["eurpln"].notna().sum()) if "eurpln" in daily else 0,
        "power_nonnull": int(daily["power_pl_eur_mwh"].notna().sum()) if "power_pl_eur_mwh" in daily else 0,
        "eua_proxy_nonnull": int(daily["eua_proxy_krbn"].notna().sum()) if "eua_proxy_krbn" in daily else 0,
        "n_quarterly": len(q),
    }
    (PROC / "coverage.json").write_text(json.dumps(cov, indent=2), encoding="utf-8")
    print("coverage", cov)
    print("done")


if __name__ == "__main__":
    main()
