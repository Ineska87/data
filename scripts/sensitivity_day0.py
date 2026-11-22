"""Publish the two day-zero choices and the non-overlapping sensitivity samples."""
from __future__ import annotations

import pandas as pd

from compute_car import OUT, SCENARIOS
from market_data import write_pair


def main() -> None:
    car = pd.read_parquet(OUT / "car_results.parquet")
    variables = ["day0", "car", "status", "overlap", "n_ar"]
    first, second = [
        car.loc[car["scenario"].eq(scenario), ["event_id", "ticker", *variables]]
        for scenario in SCENARIOS
    ]
    comparison = first.merge(second, on=["event_id", "ticker"], validate="one_to_one",
                             suffixes=("_baseline", "_same_session"))
    comparison["delta_car_same_minus_baseline"] = comparison["car_same_session"] - comparison["car_baseline"]
    comparison["day0_changed"] = (
        comparison["day0_baseline"].notna() & comparison["day0_same_session"].notna()
        & comparison["day0_baseline"].ne(comparison["day0_same_session"])
    )
    output = OUT / "sensitivity"
    write_pair(comparison, output / "day0_comparison")
    write_pair(car.loc[car["status"].eq("complete") & ~car["overlap"]], output / "non_overlapping_car")
    print(f"Zdarzenia porównane: {len(comparison)}, inny dzień 0: {int(comparison['day0_changed'].sum())}.")


if __name__ == "__main__":
    main()
