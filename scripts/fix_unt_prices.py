"""Verify the documented Unimot series before rebuilding the market panel."""
from __future__ import annotations

import argparse

from market_data import RAW_MARKET, YAHOO_SNAPSHOTS, stock_source


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yahoo-bundle", help="Previously acquired full Yahoo snapshot name.")
    args = parser.parse_args()
    bundle = YAHOO_SNAPSHOTS / args.yahoo_bundle if args.yahoo_bundle else None
    if bundle is not None:
        bundle.resolve().relative_to(YAHOO_SNAPSHOTS.resolve())
        from market_data import assemble

        market = assemble(bundle)
        series = market.loc[market["Ticker"].eq("UNT")]
    else:
        series = stock_source("UNT", None)

    if series["Close"].min() <= 0 or series["Volume"].gt(0).sum() == 0:
        raise ValueError("Brak wiarygodnych obserwacji dla Unimotu.")
    if bundle is None:
        from market_data import read_prices

        reference = read_prices(RAW_MARKET / "UNT_UNIBEP_wrong_backup.csv")
        paired = series.merge(reference, on="Date", suffixes=("_unt", "_unibep"))
        if paired.empty or paired["Close_unt"].equals(paired["Close_unibep"]):
            raise ValueError("Nie można odróżnić lokalnej serii UNT od kopii błędnych notowań Unibepu.")
    print(f"UNT.WA: {len(series)} obserwacji, {series['Date'].min().date()} – {series['Date'].max().date()}.")
    option = f" --yahoo-bundle {args.yahoo_bundle}" if args.yahoo_bundle else ""
    print(f"Następny krok: python data/scripts/merge_indices.py{option}")
    print("Potem: python data/scripts/build_returns.py i python data/scripts/compute_car.py.")


if __name__ == "__main__":
    main()
