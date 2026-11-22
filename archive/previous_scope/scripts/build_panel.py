#!/usr/bin/env python3
"""Build quarterly firm-time panel for the thesis sample.

Sources
-------
1. PKN Orlen ``*_dane-liczbowe.zip`` (XLS consolidated RI packs) — full P&L / BS / CF.
   Tier ``pkn_xls`` (authoritative for PKN).
2. Peer accounting from BiznesRadar (``peer_accounting_quarterly.parquet`` via
   ``fetch_peer_accounting_br.py``) — PGE, TPE, ENA, ZEP, UNT, JSW (+ optional ORLEN cross-check).
   Tier ``peer_br``. Values converted tys. PLN → mln PLN to match PKN XLS.
3. Daily prices and volume from the previous study's snapshot.
4. ESPI events (``events_master_2019_2025``) — quarterly flags (financing, M&A, dividend, impairment keywords).
5. ``companies.json`` + hard-coded state_control.
6. Macro quarterly (``macro_quarterly.parquet`` from ``fetch_macro.py``) — Brent, FX, power, rates, dummies.

Outputs
-------
All outputs live under data/archive/previous_scope/processed/panel.
"""

from __future__ import annotations

import json
import re
import unicodedata
import zipfile
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd

from data_paths import DATA_ROOT, LEGACY

HISTORICAL = LEGACY / "processed"
RAW_PKN = DATA_ROOT / "raw" / "reports" / "PKN"
OUT = HISTORICAL / "panel"
PRICES = HISTORICAL / "prices_daily.parquet"
MARKET = HISTORICAL / "market" / "market_data_all.parquet"
EVENTS = HISTORICAL / "events_master_2019_2025.parquet"
COMPANIES = DATA_ROOT / "metadata" / "companies.json"
PEER_ACC = OUT / "peer_accounting_quarterly.parquet"
MACRO_Q = DATA_ROOT / "processed" / "macro" / "macro_quarterly.parquet"
SENT_Q = HISTORICAL / "sentiment" / "sentiment_quarterly.parquet"

# Accounting columns shared by PKN XLS and BiznesRadar peers
ACC_VALUE_COLS = [
    "total_assets",
    "equity",
    "cash",
    "debt_interest_bearing",
    "net_debt",
    "revenue",
    "ebit",
    "ebitda",
    "net_income",
    "cfo",
    "capex",
    "investing_cf",
]

# Share counts for market cap (mln shares). Proxy — constant over sample.
# Source: yfinance fast_info (2026-07); PKN post Lotos+PGNiG consolidation.
# UWAGA: do 2026-07 UNT był błędnie zasilany kursami UNI.WA (Unibep) — patrz fix_unt_prices.
SHARES_M = {
    "PKN": 1160.942,  # 1_160_942_050
    "PGE": 2243.713,  # 2_243_712_995 (aktualizacja vs starsze 1869.76)
    "TPE": 1752.549,  # 1_752_549_394
    "ENA": 529.731,   # 529_731_093
    "ZEP": 50.824,    # 50_823_548
    "UNT": 8.198,     # 8_197_818 Unimot
    "JSW": 117.412,   # 117_411_596
}

STATE_CONTROL = {
    "PKN": 1,
    "PGE": 1,
    "TPE": 1,
    "ENA": 1,
    "JSW": 1,
    "ZEP": 0,
    "UNT": 0,
    "LWB": 0,
}

# PKN DPS by fiscal year (from IR table H6)
PKN_DPS = {
    2019: 1.00,
    2020: 3.50,
    2021: 3.50,
    2022: 5.50,
    2023: 4.15,
    2024: 6.00,
    2025: 8.00,
}


_PL = str.maketrans(
    {
        "ą": "a",
        "ć": "c",
        "ę": "e",
        "ł": "l",
        "ń": "n",
        "ó": "o",
        "ś": "s",
        "ź": "z",
        "ż": "z",
        "Ą": "a",
        "Ć": "c",
        "Ę": "e",
        "Ł": "l",
        "Ń": "n",
        "Ó": "o",
        "Ś": "s",
        "Ź": "z",
        "Ż": "z",
    }
)


def norm(s: object) -> str:
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ""
    t = str(s).replace("\n", " ").strip().lower().translate(_PL)
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"\s+", " ", t)
    return t

def parse_filename(path: Path) -> tuple[int, str] | None:
    """Return (year, period) where period in Q1,H1,Q3,Q4,AR."""
    m = re.search(r"PKN_(\d{4})_(AR|Q1|H1|Q3|Q4)_dane-liczbowe\.zip$", path.name, re.I)
    if not m:
        return None
    return int(m.group(1)), m.group(2).upper()


def read_skonsolidowany_xls(zip_path: Path) -> dict[str, pd.DataFrame]:
    with zipfile.ZipFile(zip_path) as zf:
        names = [n for n in zf.namelist() if "skonsolid" in n.lower() and n.lower().endswith((".xls", ".xlsx"))]
        if not names:
            raise FileNotFoundError(f"no consolidated xls in {zip_path.name}")
        raw = zf.read(names[0])
    engine = "openpyxl" if names[0].lower().endswith(".xlsx") else "xlrd"
    return pd.read_excel(BytesIO(raw), engine=engine, sheet_name=None, header=None)


def find_label_row(df: pd.DataFrame, *needles: str) -> int | None:
    for i, row in df.iterrows():
        lab = norm(row.iloc[1] if len(row) > 1 else row.iloc[0])
        if all(n in lab for n in needles):
            return int(i)
    # softer: any needle as full-ish match
    for i, row in df.iterrows():
        lab = norm(row.iloc[1] if len(row) > 1 else row.iloc[0])
        if needles[0] in lab:
            return int(i)
    return None


def detect_value_cols(df: pd.DataFrame, period: str) -> dict[str, int | None]:
    """Map semantic columns from header row (usually row 1)."""
    header = df.iloc[1].tolist() if len(df) > 1 else df.iloc[0].tolist()
    cols: dict[str, int | None] = {"ytd": None, "q": None, "ytd_py": None, "q_py": None, "bs": None}
    for j, cell in enumerate(header):
        h = norm(cell)
        if not h:
            continue
        is_3m = "3 miesi" in h
        is_6m = "6 miesi" in h
        is_9m = "9 miesi" in h
        is_12m = "12 miesi" in h
        is_py = "2023" in h or "2022" in h or "2021" in h or "2020" in h or "2024" in h or "przeksztalcone" in h
        # year of report is in filename; prior year markers messy — use column order
        if is_3m:
            if cols["q"] is None:
                cols["q"] = j
            elif cols["q_py"] is None:
                cols["q_py"] = j
        elif is_6m or is_9m or is_12m:
            if cols["ytd"] is None:
                cols["ytd"] = j
            elif cols["ytd_py"] is None:
                cols["ytd_py"] = j
    # Q1 often only 3M columns
    if period == "Q1" and cols["q"] is None and cols["ytd"] is not None:
        cols["q"] = cols["ytd"]
    # BS: first numeric column with non-zero assets-like values — typically col 3
    # Prefer column index 3 if present
    if df.shape[1] > 3:
        cols["bs"] = 3
    return cols


def get_val(df: pd.DataFrame, row_idx: int | None, col: int | None) -> float | None:
    if row_idx is None or col is None:
        return None
    try:
        v = df.iloc[row_idx, col]
        if pd.isna(v):
            return None
        return float(v)
    except Exception:
        return None


def extract_pack(zip_path: Path) -> dict:
    meta = parse_filename(zip_path)
    if not meta:
        raise ValueError(zip_path.name)
    year, period = meta
    sheets = read_skonsolidowany_xls(zip_path)
    rzis = sheets.get("RZiS")
    bs = sheets.get("Aktywa i Pasywa")
    cf = sheets.get("CF")
    out: dict = {
        "ticker": "PKN",
        "year": year,
        "period": period,
        "source_file": zip_path.name,
        "unit": "mln_PLN",
    }
    if rzis is not None:
        cols = detect_value_cols(rzis, period)
        # prefer quarterly 3M for flow; keep ytd too
        qcol = cols["q"] if cols["q"] is not None else cols["ytd"]
        ycol = cols["ytd"] if cols["ytd"] is not None else cols["q"]
        mapping = {
            "revenue": ("przychody ze sprzedazy",),
            "ebit": ("zysk z dzialalnosci operacyjnej",),
            "net_income": ("zysk netto",),
        }
        # first exact-ish matches
        for key, needles in mapping.items():
            # find best row: exact label start
            best = None
            for i, row in rzis.iterrows():
                lab = norm(row.iloc[1] if len(row) > 1 else "")
                if lab == needles[0] or lab.startswith(needles[0] + " "):
                    best = int(i)
                    break
            if best is None:
                best = find_label_row(rzis, needles[0])
            out[f"{key}_q"] = get_val(rzis, best, qcol)
            out[f"{key}_ytd"] = get_val(rzis, best, ycol)
            # EPS if present
        eps_row = None
        for i, row in rzis.iterrows():
            lab = norm(row.iloc[1] if len(row) > 1 else "")
            if "zysk netto na jedna akcje" in lab or "zysk netto na jedną akcję" in lab or "na jedna akcje" in lab:
                eps_row = int(i)
                break
        if eps_row is not None:
            # EPS sometimes in different cols — scan numeric
            for j in range(2, min(8, rzis.shape[1])):
                v = rzis.iloc[eps_row, j]
                if pd.notna(v) and isinstance(v, (int, float)) and abs(float(v)) < 1000:
                    out["eps_q"] = float(v)
                    break

    if bs is not None:
        bcol = 3 if bs.shape[1] > 3 else None
        # sometimes multiple date columns — pick first with non-zero assets
        candidates = [3, 4, 5, 2]
        for c in candidates:
            if c < bs.shape[1]:
                r = find_label_row(bs, "aktywa razem")
                v = get_val(bs, r, c)
                if v and abs(v) > 1:
                    bcol = c
                    break

        def bs_get(*needles: str) -> float | None:
            # prefer exact-ish
            for i, row in bs.iterrows():
                lab = norm(row.iloc[1] if len(row) > 1 else "")
                if all(n in lab for n in needles) and lab.count(" ") < 12:
                    # avoid subsections wrongly
                    return get_val(bs, int(i), bcol)
            return None

        out["total_assets"] = bs_get("aktywa razem")
        out["equity"] = bs_get("kapital wlasny razem")
        out["cash"] = None
        # cash: label exactly srodki pieniezne under current assets — take first pure match
        for i, row in bs.iterrows():
            lab = norm(row.iloc[1] if len(row) > 1 else "")
            if lab == "srodki pieniezne" or lab.startswith("srodki pieniezne "):
                out["cash"] = get_val(bs, int(i), bcol)
                break
        # debt = LT credits + ST credits
        lt = None
        st = None
        for i, row in bs.iterrows():
            lab = norm(row.iloc[1] if len(row) > 1 else "")
            if lab == "kredyty, pozyczki i obligacje" or lab.startswith("kredyty, pozyczki i obligacje"):
                v = get_val(bs, int(i), bcol)
                if lt is None:
                    lt = v
                elif st is None:
                    st = v
        out["debt_interest_bearing"] = (lt or 0) + (st or 0) if (lt is not None or st is not None) else None
        if out.get("cash") is not None and out.get("debt_interest_bearing") is not None:
            out["net_debt"] = out["debt_interest_bearing"] - out["cash"]
        else:
            out["net_debt"] = None

    if cf is not None:
        cols = detect_value_cols(cf, period)
        qcol = cols["q"] if cols["q"] is not None else cols["ytd"]
        ycol = cols["ytd"] if cols["ytd"] is not None else cols["q"]
        cfo_row = find_label_row(cf, "srodki pieniezne netto z dzialalnosci operacyjnej")
        if cfo_row is None:
            cfo_row = find_label_row(cf, "dzialalnosci operacyjnej")
        out["cfo_q"] = get_val(cf, cfo_row, qcol)
        out["cfo_ytd"] = get_val(cf, cfo_row, ycol)
        # CAPEX = acquisition of PPE (negative in CF) → store positive outflow
        capex_row = None
        for i, row in cf.iterrows():
            lab = norm(row.iloc[1] if len(row) > 1 else "")
            if "nabycie skladnikow rzeczowego majatku trwalego" in lab or "nabycie skladnikow rzeczowego" in lab:
                capex_row = int(i)
                break
        cq = get_val(cf, capex_row, qcol)
        cy = get_val(cf, capex_row, ycol)
        out["capex_q"] = abs(cq) if cq is not None else None
        out["capex_ytd"] = abs(cy) if cy is not None else None

    return out


def build_pkn_accounting() -> pd.DataFrame:
    rows = []
    for zp in sorted(RAW_PKN.glob("PKN_*_dane-liczbowe.zip")):
        try:
            rows.append(extract_pack(zp))
            print("OK", zp.name)
        except Exception as e:
            print("FAIL", zp.name, e)
    return pd.DataFrame(rows)


def period_to_quarter(period: str) -> int | None:
    return {"Q1": 1, "H1": 2, "Q3": 3, "Q4": 4, "AR": 4}.get(period)


def pkn_to_quarterly(acc: pd.DataFrame) -> pd.DataFrame:
    """Collapse packs into year-quarter rows using 3M flows when available.

    Q2: if H1 and Q1 present, flow_Q2 = YTD_H1 - YTD_Q1 (or H1_q if 3M of Q2 in H1 pack).
    """
    records = []
    # index by period
    for year in sorted(acc["year"].unique()):
        sub = acc[acc["year"] == year]
        by_p = {r["period"]: r for _, r in sub.iterrows()}

        def row_q(q: int, period_key: str, prefer_q: bool = True) -> dict:
            r = by_p.get(period_key)
            if r is None and period_key == "Q4":
                r = by_p.get("AR")
            if r is None:
                return {
                    "ticker": "PKN",
                    "year": int(year),
                    "quarter": q,
                    "period_source": None,
                }
            d = {
                "ticker": "PKN",
                "year": int(year),
                "quarter": q,
                "period_source": r["period"],
                "source_file": r.get("source_file"),
                "unit": r.get("unit", "mln_PLN"),
            }
            # stocks from this pack
            for k in ("total_assets", "equity", "cash", "debt_interest_bearing", "net_debt"):
                d[k] = r.get(k)
            # flows: prefer *_q (3M)
            for base in ("revenue", "ebit", "net_income", "cfo", "capex"):
                qv = r.get(f"{base}_q")
                yv = r.get(f"{base}_ytd")
                if prefer_q and qv is not None:
                    d[base] = qv
                elif yv is not None and period_key == "Q1":
                    d[base] = yv  # Q1 ytd = quarter
                else:
                    d[base] = qv if qv is not None else yv
            if r.get("eps_q") is not None:
                d["eps"] = r.get("eps_q")
            return d

        # Q1
        records.append(row_q(1, "Q1"))
        # Q2 from H1 pack 3M column if present, else H1_ytd - Q1,
        # else (when H1 ZIP missing) Q3_ytd - Q1 - Q3  (9M identity)
        h1 = by_p.get("H1")
        q1 = by_p.get("Q1")
        q3 = by_p.get("Q3")
        if h1 is not None:
            d2 = row_q(2, "H1", prefer_q=True)
            # If H1 has true 3M for Q2, revenue_q is Q2; else difference
            if q1 is not None and h1.get("revenue_ytd") is not None and q1.get("revenue_q") is not None:
                # if H1 revenue_q looks like Q2 (not equal ytd), keep; else diff
                if h1.get("revenue_q") is None or (
                    h1.get("revenue_ytd") is not None
                    and h1.get("revenue_q") is not None
                    and abs(h1["revenue_q"] - h1["revenue_ytd"]) < 1
                ):
                    for base in ("revenue", "ebit", "net_income", "cfo", "capex"):
                        ytd_h = h1.get(f"{base}_ytd")
                        q1v = q1.get(f"{base}_q") if q1.get(f"{base}_q") is not None else q1.get(f"{base}_ytd")
                        if ytd_h is not None and q1v is not None:
                            d2[base] = ytd_h - q1v
            records.append(d2)
        elif q1 is not None and q3 is not None:
            # Reconstruct Q2 flows: 9M − Q1 − Q3
            d2 = {
                "ticker": "PKN",
                "year": int(year),
                "quarter": 2,
                "period_source": "RECON_Q3YTD_minus_Q1_Q3",
                "source_file": q3.get("source_file"),
                "unit": q3.get("unit", "mln_PLN"),
            }
            # no reliable EOP BS for Q2 without H1 pack
            for k in ("total_assets", "equity", "cash", "debt_interest_bearing", "net_debt"):
                d2[k] = None
            for base in ("revenue", "ebit", "net_income", "cfo", "capex"):
                ytd9 = q3.get(f"{base}_ytd")
                q1v = q1.get(f"{base}_q") if q1.get(f"{base}_q") is not None else q1.get(f"{base}_ytd")
                q3v = q3.get(f"{base}_q") if q3.get(f"{base}_q") is not None else None
                if ytd9 is not None and q1v is not None and q3v is not None:
                    d2[base] = ytd9 - q1v - q3v
                else:
                    d2[base] = None
            records.append(d2)
        else:
            records.append({"ticker": "PKN", "year": int(year), "quarter": 2, "period_source": None})
        # Q3
        records.append(row_q(3, "Q3"))
        # Q4
        records.append(row_q(4, "Q4"))
    df = pd.DataFrame(records)
    # ratios
    df["capex_int"] = df["capex"] / df["total_assets"].shift(1)  # wrong shift across firms — fix later by group
    return df


def add_ratios(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["ticker", "year", "quarter"]).copy()
    if "total_assets" not in df.columns:
        return df
    assets_lag = df.groupby("ticker")["total_assets"].shift(1)
    if "capex" in df.columns:
        df["capex_int"] = df["capex"] / assets_lag
    if "net_income" in df.columns:
        df["roa"] = df["net_income"] / df["total_assets"]
    if "cfo" in df.columns:
        df["cfoa"] = df["cfo"] / df["total_assets"]
    # Leverage:
    # - lev_assets (PREFERRED): net_debt / total_assets — stabilny, do regresji
    # - lev_op: net_debt / ebitda (else ebit) — kruche przy EBIT(DA)≈0; zachowane dla kompatybilności
    # - lev: alias → lev_assets (główna zmienna w modelach)
    # - lev_assets_w: winsor 1–99% w obrębie całej próby
    if "net_debt" in df.columns and "total_assets" in df.columns:
        assets = df["total_assets"].replace(0, np.nan)
        df["lev_assets"] = df["net_debt"] / assets
        # winsor cross-section (panel)
        s = df["lev_assets"]
        if s.notna().sum() >= 10:
            lo, hi = s.quantile(0.01), s.quantile(0.99)
            df["lev_assets_w"] = s.clip(lo, hi)
        else:
            df["lev_assets_w"] = s
        df["lev"] = df["lev_assets"]  # default covariate
    if "net_debt" in df.columns:
        if "ebitda" in df.columns:
            denom = df["ebitda"].where(df["ebitda"].notna() & (df["ebitda"] != 0))
            if "ebit" in df.columns:
                denom = denom.fillna(df["ebit"].replace(0, np.nan))
        elif "ebit" in df.columns:
            denom = df["ebit"].replace(0, np.nan)
        else:
            denom = np.nan
        df["lev_op"] = df["net_debt"] / denom
    if "cash" in df.columns:
        df["cash_ratio"] = df["cash"] / df["total_assets"]
    return df


def load_peer_accounting() -> pd.DataFrame:
    """Load BiznesRadar peer quarterly accounting (mln PLN). Exclude PKN — XLS wins."""
    if not PEER_ACC.exists():
        print(f"WARN: no peer accounting at {PEER_ACC} — run fetch_peer_accounting_br.py")
        return pd.DataFrame()
    peer = pd.read_parquet(PEER_ACC)
    if peer.empty:
        return peer
    # PKN: XLS packs are authoritative; keep BR only as optional cross-check file, not in panel merge
    peer = peer[peer["ticker"] != "PKN"].copy()
    peer["period_source"] = "biznesradar_Q"
    peer["source_file"] = "biznesradar"
    peer["unit"] = "mln_PLN"
    peer["accounting_tier"] = "peer_br"
    # drop helper cols that should not fight PKN metadata
    drop_meta = [c for c in ("source",) if c in peer.columns]
    if drop_meta:
        peer = peer.drop(columns=drop_meta)
    return peer


def merge_accounting(panel: pd.DataFrame, pkn_q: pd.DataFrame, peer: pd.DataFrame) -> pd.DataFrame:
    """Merge PKN XLS first, then fill peers from BiznesRadar (combine_first)."""
    pkn = pkn_q.copy()
    pkn["accounting_tier"] = "pkn_xls"

    pkn_cols = [c for c in pkn.columns if c not in ("ticker", "year", "quarter")]
    panel = panel.merge(
        pkn[["ticker", "year", "quarter"] + pkn_cols],
        on=["ticker", "year", "quarter"],
        how="left",
    )

    if peer is None or peer.empty:
        return panel

    peer_cols = [c for c in peer.columns if c not in ("ticker", "year", "quarter")]
    panel = panel.merge(
        peer[["ticker", "year", "quarter"] + peer_cols],
        on=["ticker", "year", "quarter"],
        how="left",
        suffixes=("", "_peer"),
    )
    for c in peer_cols:
        pc = f"{c}_peer"
        if pc not in panel.columns:
            continue
        if c in panel.columns:
            panel[c] = panel[c].combine_first(panel[pc])
        else:
            panel[c] = panel[pc]
        panel = panel.drop(columns=[pc])
    return panel

def build_market_quarterly() -> pd.DataFrame:
    """Quarterly market variables for all tickers."""
    if MARKET.exists():
        m = pd.read_parquet(MARKET)
        m["Date"] = pd.to_datetime(m["Date"])
        m = m.rename(columns={"Date": "date", "Close": "close", "Volume": "volume", "Ticker": "ticker"})
    else:
        p = pd.read_parquet(PRICES)
        p = p.reset_index().rename(columns={"date": "date"} if "date" in p.columns or p.index.name == "date" else {})
        if "date" not in p.columns:
            p = p.reset_index()
            p = p.rename(columns={p.columns[0]: "date"})
        p["date"] = pd.to_datetime(p["date"])
        long = p.melt(id_vars=["date"], var_name="ticker", value_name="close")
        long = long[~long["ticker"].str.startswith("WIG")]
        m = long
        m["volume"] = np.nan

    m = m[m["date"] >= "2020-01-01"]
    m = m[m["date"] <= "2025-12-31"]
    m = m[m["ticker"].isin(list(STATE_CONTROL.keys()))]
    m["year"] = m["date"].dt.year
    m["quarter"] = m["date"].dt.quarter
    m = m.sort_values(["ticker", "date"])
    m["ret"] = m.groupby("ticker")["close"].pct_change()

    agg = (
        m.groupby(["ticker", "year", "quarter"])
        .agg(
            price_end=("close", "last"),
            price_mean=("close", "mean"),
            ret_q=("ret", lambda s: (1 + s.fillna(0)).prod() - 1),
            ret_vol=("ret", "std"),
            volume_sum=("volume", "sum"),
            n_trading_days=("close", "count"),
        )
        .reset_index()
    )
    # market cap proxy mln PLN = price * shares_m
    agg["shares_m"] = agg["ticker"].map(SHARES_M)
    agg["mktcap"] = agg["price_end"] * agg["shares_m"]
    return agg


def build_event_flags() -> pd.DataFrame:
    if not EVENTS.exists():
        return pd.DataFrame(columns=["ticker", "year", "quarter"])
    ev = pd.read_parquet(EVENTS)
    ev["event_date"] = pd.to_datetime(ev["event_date"])
    ev = ev[(ev["event_date"] >= "2020-01-01") & (ev["event_date"] <= "2025-12-31")]
    ev["year"] = ev["event_date"].dt.year
    ev["quarter"] = ev["event_date"].dt.quarter
    # normalize ticker UNI->UNT if needed
    ev["ticker"] = ev["ticker"].replace({"UNI": "UNT"})

    def flag(types: list[str]) -> pd.Series:
        return ev["event_type"].isin(types).astype(int)

    ev["fin_event"] = flag(["emisja_finansowanie"])
    ev["ma_event"] = flag(["transakcje_MA"])
    ev["div_event"] = flag(["dywidenda"])
    # impairment heuristic on title
    title = ev["title"].fillna("").str.lower()
    ev["impairment_dummy"] = title.str.contains(
        r"odpis|utrat[ay] wartości|utraty wartosci|impairment|write-?off", regex=True
    ).astype(int)

    g = (
        ev.groupby(["ticker", "year", "quarter"])
        .agg(
            fin_event=("fin_event", "max"),
            ma_event=("ma_event", "max"),
            div_event=("div_event", "max"),
            impairment_dummy=("impairment_dummy", "max"),
            n_espi=("event_id", "count"),
        )
        .reset_index()
    )
    return g


def build_skeleton() -> pd.DataFrame:
    tickers = ["PKN", "PGE", "TPE", "ENA", "ZEP", "UNT", "JSW"]
    rows = []
    for t in tickers:
        for y in range(2020, 2026):
            for q in range(1, 5):
                rows.append(
                    {
                        "ticker": t,
                        "year": y,
                        "quarter": q,
                        "state_control": STATE_CONTROL.get(t, 0),
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    print("=== PKN accounting ZIPs ===")
    acc = build_pkn_accounting()
    acc_path = OUT / "panel_pkn_accounting_raw.csv"
    acc.to_csv(acc_path, index=False)
    print(f"raw packs: {len(acc)} → {acc_path}")

    print("=== PKN quarterly reshape ===")
    pkn_q = pkn_to_quarterly(acc)
    pkn_q = add_ratios(pkn_q)
    # payout: DPS of fiscal year attributed to Q4 recommendation timing approx
    pkn_q["dps"] = pkn_q["year"].map(PKN_DPS)
    pkn_q["payout"] = np.where(
        pkn_q["net_income"].notna() & (pkn_q["net_income"] != 0) & pkn_q["quarter"].eq(4),
        (pkn_q["dps"] * SHARES_M["PKN"]) / pkn_q["net_income"],  # rough: DPS*shares / NI_q — better use ytd NI
        np.nan,
    )
    # better payout on annual: use AR pack ytd NI
    # leave simple for now

    print("=== Market quarterly ===")
    mkt = build_market_quarterly()

    print("=== Event flags ===")
    flags = build_event_flags()

    print("=== Peer accounting (BiznesRadar) ===")
    peer = load_peer_accounting()
    if not peer.empty:
        print(f"peer rows: {len(peer)} tickers={sorted(peer['ticker'].unique())}")
    else:
        print("peer: empty / missing file")

    print("=== Merge ===")
    panel = build_skeleton()
    panel = panel.merge(mkt, on=["ticker", "year", "quarter"], how="left")
    panel = panel.merge(flags, on=["ticker", "year", "quarter"], how="left")
    for c in ("fin_event", "ma_event", "div_event", "impairment_dummy", "n_espi"):
        if c in panel.columns:
            panel[c] = panel[c].fillna(0).astype(int)

    panel = merge_accounting(panel, pkn_q, peer)

    # macro / sector controls (from fetch_macro.py)
    if MACRO_Q.exists():
        mq = pd.read_parquet(MACRO_Q)
        print(f"=== Macro quarterly merge ({len(mq)} rows) ===")
        panel = panel.merge(mq, on=["year", "quarter"], how="left")
    else:
        print("WARN: no macro_quarterly.parquet — run fetch_macro.py")

    # management tone / NLP (from build_corpus_sentiment.py)
    if SENT_Q.exists():
        sq = pd.read_parquet(SENT_Q)
        # avoid name clash: keep NLP metrics + n_docs as n_mgr_docs
        rename = {"n_docs": "n_mgr_docs", "n_words_sum": "n_mgr_words"}
        sq = sq.rename(columns={k: v for k, v in rename.items() if k in sq.columns})
        drop_meta = [c for c in ("doc_types", "source_files") if c in sq.columns]
        if drop_meta:
            sq = sq.drop(columns=drop_meta)
        print(f"=== Sentiment quarterly merge ({len(sq)} rows) ===")
        panel = panel.merge(sq, on=["ticker", "year", "quarter"], how="left")
    else:
        print("WARN: no sentiment_quarterly.parquet — run build_corpus_sentiment.py")

    # recompute ratios on full panel (peers + PKN)
    panel = add_ratios(panel)

    # market-to-book when equity available
    if "equity" in panel.columns and "mktcap" in panel.columns:
        panel["mb"] = panel["mktcap"] / panel["equity"]

    # company role
    if COMPANIES.exists():
        meta = json.loads(COMPANIES.read_text(encoding="utf-8"))
        role = {c["ticker"]: c.get("rola_w_badaniu") for c in meta["companies"]}
        # companies.json uses UNI for Unimot
        role["UNT"] = role.get("UNT") or role.get("UNI")
        panel["role"] = panel["ticker"].map(role)

    # order columns
    front = [
        "ticker",
        "year",
        "quarter",
        "role",
        "state_control",
        "accounting_tier",
        "total_assets",
        "capex",
        "capex_int",
        "net_debt",
        "ebit",
        "ebitda",
        "revenue",
        "net_income",
        "roa",
        "cfo",
        "cfoa",
        "cash",
        "equity",
        "mb",
        "mktcap",
        "price_end",
        "ret_q",
        "ret_vol",
        "payout",
        "dps",
        "impairment_dummy",
        "fin_event",
        "ma_event",
        "div_event",
        "n_espi",
        "period_source",
        "source_file",
        "unit",
    ]
    cols = [c for c in front if c in panel.columns] + [c for c in panel.columns if c not in front]
    panel = panel[cols].sort_values(["ticker", "year", "quarter"]).reset_index(drop=True)

    pq = OUT / "panel_quarterly.parquet"
    csv = OUT / "panel_quarterly.csv"
    panel.to_parquet(pq, index=False)
    panel.to_csv(csv, index=False)
    print(f"panel {panel.shape} → {pq}")

    # missing log
    write_missing_log(panel)
    write_codebook()
    print("done")


def write_missing_log(panel: pd.DataFrame) -> None:
    lines = [
        "# Panel — log braków",
        "",
        f"Obserwacje: **{len(panel)}** (7 tickerów × 24 kwartały = 168 oczekiwanych).",
        "",
        "## Metodologia dwuwarstwowa (accounting_tier)",
        "",
        "| Tier | Spółki | Źródło | Jednostka |",
        "|------|--------|--------|-----------|",
        "| `pkn_xls` | PKN | `raw/reports/PKN/*_dane-liczbowe.zip` (XLS RI) | mln PLN |",
        "| `peer_br` | PGE, TPE, ENA, ZEP, UNT, JSW | BiznesRadar (HTML Q) → `peer_accounting_quarterly.*` | tys.→mln PLN |",
        "",
        "- **PKN wygrywa konflikt:** wiersze BR dla ORLEN nie są włączane do panelu (tylko w raw BR do cross-check).",
        "- Skrypt peer: `data/scripts/fetch_peer_accounting_br.py`.",
        "",
        "## Pokrycie rachunkowe (total_assets / revenue) + tier",
        "",
    ]
    for t in panel["ticker"].unique():
        sub = panel[panel["ticker"] == t]
        n_acc = int(sub["total_assets"].notna().sum()) if "total_assets" in sub else 0
        n_rev = int(sub["revenue"].notna().sum()) if "revenue" in sub else 0
        n_mkt = int(sub["price_end"].notna().sum()) if "price_end" in sub else 0
        n_cfo = int(sub["cfo"].notna().sum()) if "cfo" in sub else 0
        n_capex = int(sub["capex"].notna().sum()) if "capex" in sub else 0
        tier = "—"
        if "accounting_tier" in sub.columns:
            tiers = sub.loc[sub["accounting_tier"].notna(), "accounting_tier"].unique().tolist()
            tier = ",".join(str(x) for x in tiers) if tiers else "—"
        lines.append(
            f"- **{t}**: assets={n_acc}/24, revenue={n_rev}/24, cfo={n_cfo}/24, "
            f"capex={n_capex}/24, market={n_mkt}/24, tier={tier}"
        )
    if "accounting_tier" in panel.columns:
        lines += ["", "## Liczebność tierów", ""]
        vc = panel["accounting_tier"].fillna("none").value_counts()
        for k, v in vc.items():
            lines.append(f"- `{k}`: {int(v)}")
    lines += [
        "",
        "## Źródła",
        "",
        "- **PKN (`pkn_xls`)**: `data/raw/reports/PKN/*_dane-liczbowe.zip` (XLS skonsolidowane RI).",
        "- **Peery (`peer_br`)**: BiznesRadar rachunek/bilans/CF kwartalny; raw: "
        "`data/raw/panel_sources/biznesradar_quarterly_raw.csv`; wide: "
        "`data/processed/panel/peer_accounting_quarterly.parquet`.",
        "- **Rynek + ESPI**: wszystkie 7 spółek (jak wcześniej).",
        "- **Makro**: `data/processed/macro/macro_quarterly.parquet` (z `fetch_macro.py`) — join po year×quarter.",
        "",
        "## Notatki / ograniczenia porównawcze",
        "",
        "- Wszystkie kwoty rachunkowe w panelu w **mln PLN** (BR: /1000 z tys. PLN).",
        "- `capex` PKN = |nabycie PPE+IA+ROU| z CF; BR = linia Capex (lub |CF inwest.| jako proxy).",
        "- EBITDA: dostępna na tier `peer_br`; na `pkn_xls` zwykle NaN.",
        "- **Dźwignia:** `lev` = `lev_assets` = net_debt/assets; `lev_op` = net_debt/EBITDA|EBIT (kruche); `lev_assets_w` winsor.",
        "- Mapowanie wierszy BR jest heurystyczne (etykiety PL) — przy rozbieżnościach weryfikować vs AR PDF.",
        "- `mktcap` = cena × SHARES_M (**proxy** liczby akcji; SHARES_M z yfinance 2026-07).",
        "- **UNT kursy:** od 2026-07 z `UNT.WA` (Unimot). Wcześniejszy błąd: `UNI.WA` = Unibep.",
        "- `payout` tylko zgrubnie dla PKN (DPS × shares / NI Q4).",
        "- Makro: `power_pl_*` = day-ahead PL (nie feed TGE); `eua_proxy_krbn` ≠ cena EUA ICE; FRED bywa timeout (fallback yfinance).",
        "",
        "## Ton zarządu (NLP MVP)",
        "",
        "- Źródło: `processed/sentiment/sentiment_quarterly.parquet` (słownik PL, nie transformer).",
        "- Pokrycie sparse: AR→Q4, H1→Q2; brak tekstu = NaN w `TONE_MGR`.",
        "- TPE AR `*_skonsolidowany.pdf` to często **7z** pod fałszywym rozszerzeniem — użyto Q/H1 `*sprawozdanie.pdf`.",
        "- Brak ręcznej anotacji / TONE_FUND_GAP (checklist 7.2–7.3 otwarte).",
        "",
    ]
    if "TONE_MGR" in panel.columns:
        lines += ["### Pokrycie TONE_MGR (obs. z niepustym tonem)", ""]
        for t in panel["ticker"].unique():
            sub = panel[panel["ticker"] == t]
            n = int(sub["TONE_MGR"].notna().sum())
            lines.append(f"- **{t}**: TONE_MGR={n}/24")
        lines.append("")
    lines += [
        "## H1 2023 PKN (bez osobnego ZIP liczbowego)",
        "",
        "- IR Orlen **nie publikuje** `Dane_ze_sprawozdania_*1H2023*.zip` w `…/2023/2q2023/`.",
        "- **2023Q2 (przepływy):** `period_source=RECON_Q3YTD_minus_Q1_Q3` = YTD 9M(Q3) − Q1 − Q3.",
        "- **2023Q2 bilans EOP:** NaN w tierze XLS (brak bilansu 30.06.2023 w pakietach).",
        "",
    ]
    (OUT / "missing_log.md").write_text("\n".join(lines), encoding="utf-8")


def write_codebook() -> None:
    text = """# Codebook — panel_quarterly

Jednostka obserwacji: **spółka × rok × kwartał** (2020Q1–2025Q4).

## Identyfikatory

| Zmienna | Typ | Opis |
|---------|-----|------|
| ticker | str | Kod GPW (PKN, PGE, TPE, ENA, ZEP, UNT, JSW) |
| year | int | Rok kalendarzowy / obrotowy |
| quarter | int | 1–4 |
| role | str | rola w badaniu (rdzeń / kontrast / rezerwa) |
| state_control | 0/1 | 1 = dominacja SP (PKN, PGE, TPE, ENA, JSW) |
| accounting_tier | str | `pkn_xls` (Orlen RI ZIP) lub `peer_br` (BiznesRadar) |

## Metodologia rachunkowa (dwa tiery)

| Tier | Spółki | Źródło | Uwagi |
|------|--------|--------|-------|
| `pkn_xls` | PKN | `*_dane-liczbowe.zip` skonsolidowane XLS | Autoritative dla PKN; 3M flows gdy dostępne |
| `peer_br` | PGE, TPE, ENA, ZEP, UNT, JSW | BiznesRadar tabele Q | tys. PLN → mln PLN (/1000); publiczna alternatywa Notoria |

**Porównywalność między spółkami:** te same etykiety zmiennych, ale różne źródła pierwotne — w regresie kontrolować `accounting_tier` lub osobne modele PKN vs peery. Nie mieszać bez uwagi EBITDA (peer) z lev-EBIT (PKN).

## Rachunkowość

Kwoty: **mln PLN**.

| Zmienna | Opis |
|---------|------|
| total_assets | Aktywa razem (BS EOP) |
| equity | Kapitał własny (dominująca / razem — wg źródła) |
| cash | Środki pieniężne |
| debt_interest_bearing | Kredyty/pożyczki + obligacje (LT+ST) |
| net_debt | debt_interest_bearing − cash |
| revenue | Przychody ze sprzedaży (kwartał 3M) |
| ebit | Zysk operacyjny (3M) |
| ebitda | EBITDA (głównie `peer_br`; PKN XLS zwykle brak) |
| net_income | Zysk netto (3M; prefer. akcjonariuszy JD) |
| cfo | CF z działalności operacyjnej (3M) |
| capex | Nakłady (wartość dodatnia); PKN z CF nabycia; BR linia Capex |
| capex_int | capex / total_assets(t−1) w obrębie tickera |
| roa | net_income / total_assets |
| cfoa | cfo / total_assets |
| lev | **alias** `lev_assets` (net_debt / total_assets) — używać w regresjach |
| lev_assets | net_debt / total_assets |
| lev_assets_w | lev_assets winsor 1–99% (cała próba) |
| lev_op | net_debt / ebitda (else ebit) — kruche; tylko diagnostyka |
| cash_ratio | cash / total_assets |
| unit | `mln_PLN` |
| period_source | Q1/H1/Q3/Q4/AR / RECON_… / `biznesradar_Q` |
| source_file | nazwa ZIP lub `biznesradar` |

## Rynek (wszystkie spółki)

| Zmienna | Opis |
|---------|------|
| price_end | Kurs zamknięcia EOP kwartału |
| price_mean | Średni kurs w kwartale |
| ret_q | Zwrot złożony w kwartale |
| ret_vol | Odch. std. dziennych zwrotów |
| volume_sum | Suma wolumenu |
| mktcap | price_end × shares_m (**proxy**) |
| shares_m | Przybliżona liczba akcji (mln) |
| mb | mktcap / equity (gdy equity dostępne) |

## ESPI / zdarzenia

| Zmienna | Opis |
|---------|------|
| fin_event | 1 jeśli w kwartale ESPI typu emisja/finansowanie |
| ma_event | 1 jeśli transakcje M&A |
| div_event | 1 jeśli dywidenda |
| impairment_dummy | 1 jeśli tytuł ESPI sugeruje odpis/utratę wartości |
| n_espi | liczba ESPI w kwartale |

## Dywidenda PKN

| Zmienna | Opis |
|---------|------|
| dps | PLN/akcję za rok obrotowy (tabela IR H6) |
| payout | zgrubny wskaźnik (patrz missing_log) |

## Ton zarządu / NLP (MVP)

Źródło: `data/processed/sentiment/sentiment_quarterly.parquet` (`build_corpus_sentiment.py`).

| Zmienna | Opis |
|---------|------|
| TONE_MGR | (pos−neg)/n_words — słownik PL stylu LM |
| UNCERTAINTY | udział leksyki niepewności |
| CERTAINTY | udział leksyki pewności |
| READABILITY | proxy FOG (wyżej = trudniejszy) |
| pos_share, neg_share | udziały słów pos/neg |
| n_mgr_docs, n_mgr_words | liczba dokumentów / słów w agregacie |

AR → Q4; H1 → Q2. Sparse: nie każdy ticker×kwartał ma tekst.

## Makro / sektor (wspólne dla wszystkich spółek w kwartale)

Źródło: `data/processed/macro/macro_quarterly.parquet` (`fetch_macro.py`).

| Prefiks / zmienna | Opis |
|-------------------|------|
| brent_usd_* | ropa Brent (USD/bbl; yfinance BZ=F) |
| eurpln_*, usdpln_* | kursy NBP mid |
| nbp_ref_rate_* | stopa referencyjna NBP (ścieżka RPP) |
| power_pl_eur_mwh_* | day-ahead PL EUR/MWh (proxy TGE) |
| gas_eu_usd_* | gaz NG=F proxy |
| eua_proxy_krbn_* | ETF KRBN — **proxy** carbon, nie ICE EUA |
| wig_*, wig_energia_*, wig_paliwa_* | indeksy z market_data |
| *_qmean / *_qend / *_qchg | średnia / EOP / zmiana % EOP w kwartale |
| COVID_2020, ENERGY_CRISIS, NORMALIZATION, MERGER_ORLEN | dummy podokresów |

## Skrypty

- `data/scripts/build_panel.py` — budowa panelu
- `data/scripts/fetch_peer_accounting_br.py` — peer accounting z BiznesRadar
- `data/scripts/fetch_macro.py` — serie makro
"""
    (OUT / "codebook.md").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
