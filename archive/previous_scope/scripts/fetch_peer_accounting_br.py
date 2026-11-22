#!/usr/bin/env python3
"""Fetch quarterly accounting peers from BiznesRadar (public HTML tables).

Tickers: PGE, TPE (TAURON), ENA, ZEP (ZEPAK), UNT (UNIMOT-GAZ), JSW, PKN (ORLEN cross-check).
Values on BR are typically **tys. PLN** → convert to **mln PLN** (/1000) to match PKN XLS packs.

Outputs
-------
- data/raw/panel_sources/biznesradar_quarterly_raw.csv
- data/processed/panel/peer_accounting_quarterly.parquet
"""

from __future__ import annotations

import re
import time
import ssl
import urllib.request
from io import StringIO

import numpy as np
import pandas as pd

from data_paths import DATA_ROOT, LEGACY

RAW_OUT = DATA_ROOT / "raw" / "panel_sources"
PROC_OUT = LEGACY / "processed" / "panel"
CTX = ssl.create_default_context()
H = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pl-PL,pl;q=0.9",
}

# thesis ticker -> BR slug
BR_SLUG = {
    "PGE": "PGE",
    "TPE": "TAURON",
    "ENA": "ENA",
    "ZEP": "ZEPAK",
    "UNT": "UNIMOT-GAZ",
    "JSW": "JSW-JASTRZEBSKA-SPOLKA-WEGLOWA",
    "PKN": "ORLEN",
}

STATEMENTS = {
    "rzis": "raporty-finansowe-rachunek-zyskow-i-strat",
    "bs": "raporty-finansowe-bilans",
    "cf": "raporty-finansowe-przeplywy-pieniezne",
}

# row label (normalized substring) -> field
RZIS_MAP = {
    "przychody ze sprzedazy": "revenue",
    "zysk operacyjny (ebit)": "ebit",
    "ebitda": "ebitda",
    "zysk netto akcjonariuszy jednostki dominujacej": "net_income",
    "zysk netto": "net_income",  # fallback if no parent NI
}
BS_MAP = {
    "aktywa razem": "total_assets",
    "srodki pieniezne i inne aktywa pieniezne": "cash",
    "kapital wlasny akcjonariuszy jednostki dominujacej": "equity",
}
CF_MAP = {
    "przeplywy pieniezne z dzialalnosci operacyjnej": "cfo",
    "capex (niematerialne i rzeczowe)": "capex",
    "przeplywy pieniezne z dzialalnosci inwestycyjnej": "investing_cf",
}


def norm(s: object) -> str:
    t = str(s or "").lower().replace("\n", " ")
    for a, b in [
        ("ą", "a"),
        ("ć", "c"),
        ("ę", "e"),
        ("ł", "l"),
        ("ń", "n"),
        ("ó", "o"),
        ("ś", "s"),
        ("ź", "z"),
        ("ż", "z"),
    ]:
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t).strip()


def parse_cell(val) -> float | None:
    """Extract first integer-like amount from BR cell (spaces as thousands sep)."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return float(val)
    s = str(val)
    # strip r/r annotations: take before 'r/r' or first long digit run
    s0 = s.split("r/r")[0].split("~")[0]
    # keep digits, spaces, minus
    m = re.search(r"-?\d[\d\s]*", s0.replace("\xa0", " "))
    if not m:
        return None
    num = m.group(0).replace(" ", "").replace("\xa0", "")
    try:
        return float(num)
    except ValueError:
        return None


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers=H)
    with urllib.request.urlopen(req, context=CTX, timeout=90) as r:
        return r.read().decode("utf-8", errors="replace")


def main_table(html: str) -> pd.DataFrame:
    tables = pd.read_html(StringIO(html))
    return max(tables, key=lambda t: t.shape[0] * t.shape[1])


def col_year_quarter(col) -> tuple[int, int] | None:
    s = str(col)
    m = re.search(r"(20\d{2})/Q([1-4])", s)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def extract_statement(df: pd.DataFrame, row_map: dict[str, str], prefer_order: list[str] | None = None) -> list[dict]:
    """Return list of {year, quarter, field, value_tys}."""
    label_col = df.columns[0]
    # map each row index to field (first match; prefer more specific keys first)
    keys = prefer_order or list(row_map.keys())
    row_field: dict[int, str] = {}
    used_fields: set[str] = set()
    for i, lab in enumerate(df[label_col].tolist()):
        nlab = norm(lab)
        for key in keys:
            field = row_map[key]
            if key in nlab:
                # exact-ish: for zysk netto avoid matching 'z dzialalnosci zaniechanej' before parent NI
                if field in used_fields and field == "net_income":
                    continue
                if field == "net_income" and "zaniechanej" in nlab:
                    continue
                if field == "net_income" and "akcjonariuszy" in nlab:
                    row_field[i] = field
                    used_fields.add(field)
                    break
                if field != "net_income" or "akcjonariuszy" not in "".join(norm(x) for x in df[label_col].astype(str)):
                    if field not in used_fields or key == "zysk netto akcjonariuszy jednostki dominujacej":
                        row_field[i] = field
                        used_fields.add(field)
                        break
                break

    out = []
    for col in df.columns[1:]:
        yq = col_year_quarter(col)
        if not yq:
            continue
        year, q = yq
        if year < 2020 or year > 2025:
            continue
        for i, field in row_field.items():
            v = parse_cell(df.iloc[i][col])
            if v is None:
                continue
            out.append({"year": year, "quarter": q, "field": field, "value_tys": v})
    return out


def fetch_ticker(ticker: str, slug: str) -> pd.DataFrame:
    rows = []
    for kind, path in STATEMENTS.items():
        url = f"https://www.biznesradar.pl/{path}/{slug},Q"
        print(f"  {ticker} {kind} …")
        try:
            html = fetch_html(url)
            df = main_table(html)
        except Exception as e:
            print(f"    FAIL {e}")
            continue
        if kind == "rzis":
            pref = [
                "zysk netto akcjonariuszy jednostki dominujacej",
                "zysk operacyjny (ebit)",
                "przychody ze sprzedazy",
                "ebitda",
                "zysk netto",
            ]
            part = extract_statement(df, RZIS_MAP, pref)
        elif kind == "bs":
            part = extract_statement(df, BS_MAP)
            # debt = sum of credit lines + bonds LT+ST
            part += extract_debt(df)
        else:
            part = extract_statement(df, CF_MAP)
        for p in part:
            p["ticker"] = ticker
            p["statement"] = kind
            p["source_url"] = url
        rows.extend(part)
        time.sleep(0.6)
    return pd.DataFrame(rows)


def extract_debt(df: pd.DataFrame) -> list[dict]:
    """Sum Kredyty i pożyczki + dłużne papiery (LT+ST) per quarter."""
    label_col = df.columns[0]
    debt_rows = []
    for i, lab in enumerate(df[label_col].tolist()):
        nlab = norm(lab)
        if nlab in ("kredyty i pozyczki", "z tytulu emisji dluznych papierow wartosciowych"):
            debt_rows.append(i)
    out = []
    for col in df.columns[1:]:
        yq = col_year_quarter(col)
        if not yq:
            continue
        year, q = yq
        if year < 2020 or year > 2025:
            continue
        total = 0.0
        anyv = False
        for i in debt_rows:
            v = parse_cell(df.iloc[i][col])
            if v is not None:
                total += v
                anyv = True
        if anyv:
            out.append(
                {
                    "year": year,
                    "quarter": q,
                    "field": "debt_interest_bearing",
                    "value_tys": total,
                }
            )
    return out


def pivot_to_wide(long_df: pd.DataFrame) -> pd.DataFrame:
    if long_df.empty:
        return long_df
    # prefer last occurrence if duplicates
    long_df = long_df.drop_duplicates(["ticker", "year", "quarter", "field"], keep="last")
    wide = long_df.pivot_table(
        index=["ticker", "year", "quarter"],
        columns="field",
        values="value_tys",
        aggfunc="last",
    ).reset_index()
    wide.columns.name = None
    # tys → mln
    value_cols = [c for c in wide.columns if c not in ("ticker", "year", "quarter")]
    for c in value_cols:
        wide[c] = wide[c] / 1000.0
    # capex: BR line often negative outflow — store positive
    if "capex" in wide.columns:
        wide["capex"] = wide["capex"].abs()
    elif "investing_cf" in wide.columns:
        # investing CF negative = outflow; use abs as capex proxy
        wide["capex"] = wide["investing_cf"].abs()
    if "debt_interest_bearing" in wide.columns and "cash" in wide.columns:
        wide["net_debt"] = wide["debt_interest_bearing"] - wide["cash"]
    wide["unit"] = "mln_PLN"
    wide["source"] = "biznesradar"
    wide["accounting_tier"] = "peer_br"
    return wide


def main() -> None:
    RAW_OUT.mkdir(parents=True, exist_ok=True)
    PROC_OUT.mkdir(parents=True, exist_ok=True)
    all_long = []
    for ticker, slug in BR_SLUG.items():
        print(f"=== {ticker} ({slug}) ===")
        df = fetch_ticker(ticker, slug)
        print(f"  rows {len(df)}")
        all_long.append(df)
    long_df = pd.concat(all_long, ignore_index=True) if all_long else pd.DataFrame()
    long_path = RAW_OUT / "biznesradar_quarterly_raw.csv"
    long_df.to_csv(long_path, index=False)
    print("raw", long_path, len(long_df))

    wide = pivot_to_wide(long_df)
    outp = PROC_OUT / "peer_accounting_quarterly.parquet"
    outc = PROC_OUT / "peer_accounting_quarterly.csv"
    wide.to_parquet(outp, index=False)
    wide.to_csv(outc, index=False)
    print("wide", wide.shape, outp)
    print(wide.groupby("ticker").size())
    # coverage of key fields
    for t in wide["ticker"].unique():
        sub = wide[wide["ticker"] == t]
        print(
            t,
            "n=",
            len(sub),
            "rev",
            sub["revenue"].notna().sum() if "revenue" in sub else 0,
            "assets",
            sub["total_assets"].notna().sum() if "total_assets" in sub else 0,
            "cfo",
            sub["cfo"].notna().sum() if "cfo" in sub else 0,
            "capex",
            sub["capex"].notna().sum() if "capex" in sub else 0,
        )


if __name__ == "__main__":
    main()
