"""Read market snapshots and publish matching Arrow and CSV data."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from data_paths import DATA_ROOT, load_study_scope

RAW_MARKET = DATA_ROOT / "raw" / "market_data"
PROCESSED_MARKET = DATA_ROOT / "processed" / "market"
INDICES = ("WIG", "WIG20", "WIG-energia", "WIG-paliwa")
YAHOO_SNAPSHOTS = RAW_MARKET / "snapshots" / "yahoo"
GPW_INDEX_SNAPSHOTS = RAW_MARKET / "snapshots" / "gpw"
GPW_INDEX_ISINS = {
    "PL9999999995": "WIG", "PL9999999987": "WIG20",
    "PL9999999516": "WIG-energia", "PL9999999722": "WIG-paliwa",
}
YAHOO_TICKERS = {"ENA": "ENA.WA", "PGE": "PGE.WA", "PKN": "PKN.WA", "TPE": "TPE.WA",
                 "UNT": "UNT.WA", "ZEP": "ZEP.WA"}
COLUMN_NAMES = {
    "Data": "Date", "Otwarcie": "Open", "Najwyzszy": "High",
    "Najnizszy": "Low", "Zamkniecie": "Close", "Wolumen": "Volume",
}
PRICE_FIELDS = ["Date", "Open", "High", "Low", "Close", "Volume"]


def emitters() -> tuple[str, ...]:
    path = DATA_ROOT / "metadata" / "study_scope.json"
    tickers = tuple(load_study_scope()["tickers"])
    if not tickers or len(tickers) != len(set(tickers)) or set(tickers) - YAHOO_TICKERS.keys():
        raise ValueError(f"Nieprawidłowa lista spółek w {path}: {tickers}")
    return tickers


def write_pair(frame: pd.DataFrame, stem: Path) -> None:
    """Prepare both encodings from one frame before replacing published files."""
    stem.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=stem.parent) as directory:
        temporary = Path(directory)
        parquet = temporary / "table.parquet"
        csv = temporary / "table.csv"
        parquet_target = stem.with_suffix(".parquet")
        previous = temporary / "previous.parquet"
        frame.to_parquet(parquet, index=False)
        frame.to_csv(csv, index=False, encoding="utf-8-sig")
        if parquet_target.exists():
            shutil.copyfile(parquet_target, previous)
        parquet.replace(parquet_target)
        try:
            csv.replace(stem.with_suffix(".csv"))
        except OSError:
            if previous.exists():
                previous.replace(parquet_target)
            else:
                parquet_target.unlink()
            raise


def read_prices(path: Path) -> pd.DataFrame:
    try:
        frame = pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        frame = pd.read_csv(path, encoding="cp1250")
    frame = frame.rename(columns=COLUMN_NAMES)
    if "Volume" not in frame:
        frame["Volume"] = np.nan
    missing = set(PRICE_FIELDS) - set(frame.columns)
    if missing:
        raise ValueError(f"{path}: brak kolumn {sorted(missing)}")
    frame = frame.rename(columns={"Adj Close": "AdjustedClose"})
    fields = PRICE_FIELDS + (["AdjustedClose"] if "AdjustedClose" in frame else [])
    frame = frame[fields].copy()
    frame["Date"] = pd.to_datetime(frame["Date"], errors="raise").dt.normalize()
    for field in fields[1:]:
        frame[field] = pd.to_numeric(frame[field], errors="raise")
    if frame["Date"].duplicated().any() or frame["Date"].isna().any() or frame.empty:
        raise ValueError(f"{path}: pusta seria, powtarzające się lub puste daty.")
    if (frame["Close"].isna() | (frame["Close"] <= 0)).any():
        raise ValueError(f"{path}: niepoprawny kurs zamknięcia.")
    return frame.sort_values("Date")


def decode_yahoo_quotes(payload: bytes, symbol: str) -> pd.DataFrame:
    chart = json.loads(payload)["chart"]
    if chart["error"] or not chart["result"]:
        raise ValueError(f"Yahoo Finance nie zwrócił danych dla {symbol}.")
    series = chart["result"][0]
    metadata = series["meta"]
    if (metadata["symbol"] != symbol or metadata["currency"] != "PLN"
            or metadata["exchangeTimezoneName"] != "Europe/Warsaw"):
        raise ValueError(f"Metadane instrumentu nie pasują do żądanego symbolu {symbol}.")
    indicators = series["indicators"]
    quotes = pd.DataFrame(indicators["quote"][0]).rename(columns=str.title)
    dates = pd.to_datetime(series["timestamp"], unit="s", utc=True).tz_convert("Europe/Warsaw")
    quotes["Date"] = dates.tz_localize(None).normalize()
    quotes["AdjustedClose"] = indicators["adjclose"][0]["adjclose"]
    frame = quotes[PRICE_FIELDS + ["AdjustedClose"]].dropna(subset=["Close"])
    if (frame.empty or frame["AdjustedClose"].isna().any() or frame["Date"].duplicated().any()
            or frame["Close"].le(0).any() or frame["AdjustedClose"].le(0).any()):
        raise ValueError(f"{symbol}: niekompletna migawka.")
    return frame.sort_values("Date")


def stock_source(ticker: str, bundle: Path | None) -> pd.DataFrame:
    if bundle is None:
        path = RAW_MARKET / f"{ticker}.csv"
        frame = read_prices(path)
        frame["Source"] = "local_legacy"
        frame["ReturnBasis"] = "historical_adjusted_UNT" if ticker == "UNT" else "historical_close"
        frame["PriceForReturn"] = frame["Close"]
    else:
        path = bundle / f"{ticker}.json"
        frame = decode_yahoo_quotes(path.read_bytes(), YAHOO_TICKERS[ticker])
        frame["Source"] = "Yahoo Finance"
        frame["ReturnBasis"] = "adjusted_close"
        frame["PriceForReturn"] = frame["AdjustedClose"]
    frame["SourcePath"] = path.relative_to(DATA_ROOT).as_posix()
    frame["Ticker"] = ticker
    return frame


def gpw_index_export() -> pd.DataFrame:
    """Read original GPW index archives using the official ISIN identifiers."""
    columns = {
        "Data": "Date", "Kurs otwarcia": "Open", "Kurs max": "High",
        "Kurs min": "Low", "Kurs zamknięcia": "Close", "Wolumen": "Volume",
    }
    frames = []
    paths = sorted(GPW_INDEX_SNAPSHOTS.glob("*_indices.xls"))
    if paths:
        manifest = json.loads((GPW_INDEX_SNAPSHOTS / "manifest.json").read_text(encoding="utf-8"))
        if {path.name for path in paths} != set(manifest["files"]):
            raise ValueError("Zawartość folderu GPW nie zgadza się z manifestem.")
    for path in paths:
        if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["files"][path.name]["sha256"]:
            raise ValueError(f"Suma kontrolna pliku nie zgadza się z manifestem: {path}")
        frame = pd.read_excel(path, usecols=["ISIN", *columns]).rename(columns=columns)
        frame = frame.loc[frame["ISIN"].isin(GPW_INDEX_ISINS)].copy()
        frame["Ticker"] = frame["ISIN"].map(GPW_INDEX_ISINS)
        frame["Date"] = pd.to_datetime(frame["Date"], errors="raise").dt.normalize()
        expected_date = pd.Timestamp(path.name.removesuffix("_indices.xls"))
        if (not frame["Date"].eq(expected_date).all()
                or len(frame) != len(INDICES) or set(frame["Ticker"]) != set(INDICES)):
            raise ValueError(f"Niekompletny eksport GPW zgodny z datą i czterema indeksami: {path}")
        frame["SourcePath"] = path.relative_to(DATA_ROOT).as_posix()
        frames.append(frame[[*PRICE_FIELDS, "Ticker", "SourcePath"]])
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def index_source(ticker: str, snapshots: pd.DataFrame) -> pd.DataFrame:
    path = RAW_MARKET / f"{ticker}.csv"
    base = read_prices(path)
    base["SourcePath"] = path.relative_to(DATA_ROOT).as_posix()
    base["Ticker"] = ticker
    base["Source"] = "Stooq"
    if not snapshots.empty:
        supplement = snapshots.loc[snapshots["Ticker"].eq(ticker)]
        overlap = base.merge(supplement, on="Date")
        if len(overlap) < 2 or not np.allclose(overlap["Close_x"], overlap["Close_y"], rtol=0, atol=0.011):
            raise ValueError(f"{ticker}: eksport GPW nie odpowiada Stooq na sesjach wspólnych.")
        tail = supplement.loc[supplement["Date"] > base["Date"].max()].copy()
        tail["Source"] = "GPW Archiwum notowań"
        base = pd.concat([base, tail], ignore_index=True)
    base["ReturnBasis"] = "index_close"
    base["PriceForReturn"] = base["Close"]
    return base


def assemble(bundle: Path | None = None) -> pd.DataFrame:
    """Use either all historical local stock inputs or a full verified Yahoo bundle."""
    tickers = emitters()
    if bundle is not None:
        bundle = bundle.resolve()
        bundle.relative_to(YAHOO_SNAPSHOTS.resolve())
        manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
        if set(manifest["symbols"]) != set(tickers):
            raise ValueError("Migawka Yahoo nie obejmuje dokładnie sześciu emitentów.")
        if any(manifest["symbols"][ticker] != YAHOO_TICKERS[ticker] for ticker in tickers):
            raise ValueError("Symbol w manifeście migawki Yahoo nie pasuje do emitenta.")
        for ticker in tickers:
            path = bundle / f"{ticker}.json"
            if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["files"][ticker]["sha256"]:
                raise ValueError(f"Suma kontrolna pliku nie zgadza się z manifestem: {path}")
    snapshots = gpw_index_export()
    frames = [stock_source(ticker, bundle) for ticker in tickers]
    frames.extend(index_source(ticker, snapshots) for ticker in INDICES)
    return pd.concat(frames, ignore_index=True).sort_values(["Ticker", "Date"]).reset_index(drop=True)
