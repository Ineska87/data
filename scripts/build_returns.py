"""Build the market-session panel and close-to-close log returns."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from data_paths import load_study_scope
from market_data import INDICES, PROCESSED_MARKET, emitters


def market_panels(market: pd.DataFrame) -> dict[str, pd.DataFrame]:
    if market.duplicated(["Date", "Ticker"]).any():
        raise ValueError("Powtarzające się kombinacje daty i tickera.")
    market = market.copy()
    market["Date"] = pd.to_datetime(market["Date"]).dt.normalize()
    # Genuine WIG observations define the GPW session calendar. For individual
    # equities, provider rows with no executed trades are not observed closes.
    sessions = pd.DatetimeIndex(
        market.loc[market["Ticker"].eq("WIG"), "Date"].unique(), name="date"
    ).sort_values()
    if sessions.empty:
        raise ValueError("Nie można ustalić sesji GPW bez rzeczywistych obserwacji WIG.")
    traded = market.loc[market["Date"].isin(sessions)
                        & (market["Ticker"].isin(INDICES) | market["Volume"].gt(0))]

    def panel(field: str) -> pd.DataFrame:
        wide = traded.pivot(index="Date", columns="Ticker", values=field).reindex(sessions)
        wide.columns.name = None
        return wide

    price_for_return = panel("PriceForReturn")
    if (price_for_return <= 0).to_numpy().any():
        raise ValueError("Kurs użyty do obliczenia zwrotu musi być dodatni.")
    # A missing close leaves its session and the next return missing. No
    # forward fill or multi-session return is silently counted as one day.
    return {
        "prices_daily": panel("Close"),
        "returns_daily": np.log(price_for_return).diff(),
        "volume_daily": panel("Volume"),
    }


def main() -> None:
    market = pd.read_parquet(PROCESSED_MARKET / "market_data_all.parquet")
    panels = market_panels(market)
    for name, frame in panels.items():
        frame.to_parquet(PROCESSED_MARKET / f"{name}.parquet")

    stocks = set(emitters())
    eligible = market.loc[market["Ticker"].isin(stocks | set(INDICES))]
    coverage = {}
    for ticker, rows in eligible.groupby("Ticker"):
        observed = rows if ticker in INDICES else rows.loc[rows["Volume"].gt(0)]
        coverage[ticker] = {
            "first_observation": observed["Date"].min().date().isoformat() if not observed.empty else None,
            "last_observation": observed["Date"].max().date().isoformat() if not observed.empty else None,
            "return_basis": sorted(rows["ReturnBasis"].unique()),
            "source_paths": sorted(rows["SourcePath"].unique()),
        }
    stock_basis = {basis for ticker in stocks for basis in coverage.get(ticker, {}).get("return_basis", [])}
    has_terminal_buffer = all(
        (coverage.get(ticker, {}).get("last_observation") or "") >= "2026-01-05"
        for ticker in stocks | {"WIG", load_study_scope()["benchmark"]}
    )
    detail = {
        "calendar": "observed WIG sessions",
        "daily_return": "ln(close_t / close_t_minus_1), with consecutive valid observations",
        "consistent_stock_return_basis": stock_basis == {"adjusted_close"},
        "has_terminal_buffer": has_terminal_buffer,
        "coverage": coverage,
    }
    (PROCESSED_MARKET / "coverage.json").write_text(
        json.dumps(detail, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Sesje WIG: {len(panels['returns_daily'])}; pełny bufor na końcu: {has_terminal_buffer}")


if __name__ == "__main__":
    main()
