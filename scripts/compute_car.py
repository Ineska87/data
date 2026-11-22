"""Compute full [-1,+1] market-model CAR for reviewed investment events."""
from __future__ import annotations

import argparse
from datetime import datetime, time
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from data_paths import DATA_ROOT, load_study_scope
from market_data import INDICES, PROCESSED_MARKET, emitters, write_pair

MARKET_CLOSE = time(17)
OFFSET_START, OFFSET_END, MIN_OBS = -250, -11, 100
WINDOW = "[-1+1]"
SCENARIOS = ("baseline", "same_session")
RETURNS = PROCESSED_MARKET / "returns_daily.parquet"
EVENTS = DATA_ROOT / "processed" / "events" / "investment_events_2020_2025.parquet"
OUT = DATA_ROOT / "processed" / "event_study"

CAR_COLUMNS = {
    "event_id": "string", "ticker": "string", "benchmark": "string", "event_date": "datetime64[ns]",
    "event_year": "Int64", "event_type": "string", "event_type_pl": "string", "has_time": "boolean",
    "numer": "string", "title": "string", "scenario": "string", "day0": "datetime64[ns]",
    "overlap": "boolean", "alpha": "float64", "beta": "float64", "r2": "float64",
    "n_est": "Int64", "resid_sd": "float64", "window": "string", "w_start": "Int64",
    "w_end": "Int64", "car": "float64", "n_ar": "Int64", "status": "string",
}
AR_COLUMNS = {
    "event_id": "string", "ticker": "string", "benchmark": "string", "scenario": "string",
    "day0": "datetime64[ns]", "date": "datetime64[ns]", "rel_day": "Int64",
    "r_stock": "float64", "r_market": "float64", "ar": "float64",
}


def publication_time(event: pd.Series) -> time | None:
    known = event.get("has_time")
    if pd.notna(known) and not bool(known):
        return None
    value = event.get("event_time")
    if pd.isna(value):
        return None
    try:
        clock = time.fromisoformat(str(value).strip())
    except ValueError:
        return None
    if clock.tzinfo is None:
        return clock
    timestamp = datetime.combine(event["event_date"].date(), clock)
    return timestamp.astimezone(ZoneInfo("Europe/Warsaw")).time()


def day_zero(sessions: pd.DatetimeIndex, date: pd.Timestamp,
             announced: time | None, scenario: str) -> int | None:
    """Use WIG session dates and the 17:00 closing price cutoff in Warsaw time."""
    if pd.isna(date) or len(sessions) == 0 or date < sessions[0]:
        return None
    index = int(sessions.searchsorted(date))
    if index >= len(sessions):
        return None
    is_session = sessions[index] == date
    if is_session and (announced >= MARKET_CLOSE if announced is not None else scenario == "baseline"):
        index += 1
    return index if index < len(sessions) else None


def market_model(estimation: pd.DataFrame) -> tuple[float, float, float, float] | None:
    stock, market = estimation.to_numpy().T
    if len(stock) < MIN_OBS or np.ptp(market) == 0:
        return None
    design = np.column_stack([np.ones(len(stock)), market])
    coefficients, _, _, _ = np.linalg.lstsq(design, stock, rcond=None)
    residual = stock - design @ coefficients
    error = np.sum(residual**2)
    total = np.sum((stock - stock.mean())**2)
    return (*coefficients, 1 - error / total if total > 0 else np.nan,
            np.sqrt(error / (len(stock) - 2)))


def event_rows(event: pd.Series, returns: pd.DataFrame, benchmark: str) -> tuple[list[dict], list[dict]]:
    issuer = event["ticker"]
    date = pd.Timestamp(event["event_date"]).normalize()
    announced = publication_time(event)
    common = {
        "event_id": event["event_id"], "ticker": issuer, "benchmark": benchmark,
        "event_date": date, "event_year": date.year, "has_time": announced is not None,
        "event_type": event.get("event_type", event.get("decision_type")),
        "event_type_pl": event.get("event_type_pl"), "numer": event.get("numer"),
        "title": event.get("title"), "window": WINDOW, "w_start": -1, "w_end": 1,
    }
    car_rows = []
    ar_rows = []
    for scenario in SCENARIOS:
        car = common | {"scenario": scenario, "status": "missing_day0", "n_ar": 0}
        car_rows.append(car)
        index = day_zero(returns.index, date, announced, scenario)
        if index is None:
            continue
        day0 = returns.index[index]
        car["day0"] = day0
        if issuer not in returns or benchmark not in returns:
            car["status"] = "missing_market_series"
            continue
        pair = returns[[issuer, benchmark]]
        end = index + OFFSET_END + 1
        start = max(index + OFFSET_START, 0)
        estimation = pair.iloc[start:max(start, end)].dropna()
        model = market_model(estimation)
        car["n_est"] = len(estimation)
        if model is None:
            car["status"] = "insufficient_estimation" if len(estimation) < MIN_OBS else "constant_benchmark"
            continue
        alpha, beta, r2, resid_sd = model
        car.update(alpha=alpha, beta=beta, r2=r2, resid_sd=resid_sd, status="incomplete_window")
        abnormal = []
        for offset in (-1, 0, 1):
            position = index + offset
            if not 0 <= position < len(returns):
                continue
            stock_return, market_return = pair.iloc[position].to_numpy()
            ar = stock_return - alpha - beta * market_return
            if np.isfinite(ar):
                abnormal.append(ar)
            ar_rows.append({
                "event_id": event["event_id"], "ticker": issuer, "benchmark": benchmark,
                "scenario": scenario, "day0": day0, "date": returns.index[position],
                "rel_day": offset, "r_stock": stock_return, "r_market": market_return, "ar": ar,
            })
        car["n_ar"] = len(abnormal)
        if len(abnormal) == 3:
            car.update(car=sum(abnormal), status="complete")
    return car_rows, ar_rows


def mark_overlaps(car: pd.DataFrame, sessions: pd.DatetimeIndex) -> None:
    """Mark both events in all same-issuer windows sharing at least one session."""
    car["overlap"] = False
    for _, group in car.dropna(subset=["day0"]).groupby(["ticker", "scenario"]):
        ordered = group.sort_values("day0")
        position = pd.Series(sessions.get_indexer(ordered["day0"]), index=ordered.index)
        overlap = position.diff().le(2) | position.diff(-1).ge(-2)
        car.loc[overlap[overlap].index, "overlap"] = True


def compute(events: pd.DataFrame, returns: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    required = {"event_id", "ticker", "event_date"}
    missing = required - set(events.columns)
    if missing:
        raise ValueError(f"Brak kolumn rejestru zdarzeń: {sorted(missing)}")
    events = events.copy()
    events["event_date"] = pd.to_datetime(events["event_date"], errors="raise").dt.normalize()
    unknown = set(events["ticker"]) - set(emitters())
    if unknown or events["event_id"].isna().any() or events["event_id"].duplicated().any():
        raise ValueError(f"Rejestr zawiera powtórzone/brakujące ID lub kod spółki spoza próby: {unknown}")
    scope = load_study_scope()
    if not events["event_date"].between(scope["period"]["start"], scope["period"]["end"]).all():
        raise ValueError("Rejestr zawiera zdarzenia bez daty lub spoza lat 2020–2025.")
    benchmark = scope["benchmark"]
    if benchmark not in INDICES:
        raise ValueError(f"Nieznana seria indeksu w zakresie badania: {benchmark}")
    returns = returns.sort_index()
    if not isinstance(returns.index, pd.DatetimeIndex) or not returns.index.is_unique:
        raise ValueError("Oczekiwano jednego wiersza zwrotów na sesję GPW.")
    cars, abnormal = [], []
    for _, event in events.iterrows():
        event_cars, event_abnormal = event_rows(event, returns, benchmark)
        cars.extend(event_cars)
        abnormal.extend(event_abnormal)
    car = pd.DataFrame(cars, columns=list(CAR_COLUMNS)).astype(CAR_COLUMNS)
    ar = pd.DataFrame(abnormal, columns=list(AR_COLUMNS)).astype(AR_COLUMNS)
    mark_overlaps(car, returns.index)
    return car, ar


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, default=EVENTS)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    events = pd.read_parquet(args.events)
    returns = pd.read_parquet(RETURNS)
    car, abnormal = compute(events, returns)
    write_pair(car, args.output_dir / "car_results")
    abnormal.to_parquet(args.output_dir / "ar_daily.parquet", index=False)
    health = {
        "input_events": len(events),
        "scenarios": {scenario: car.loc[car["scenario"].eq(scenario), "status"].value_counts().to_dict()
                      for scenario in SCENARIOS},
        "overlap_rule": "same issuer, shared trading session within [-1,+1]",
        "nominal_close_warsaw": MARKET_CLOSE.isoformat(),
        "reference_index": load_study_scope()["benchmark"],
    }
    (args.output_dir / "coverage.json").write_text(
        json.dumps(health, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(health, indent=2))


if __name__ == "__main__":
    main()
