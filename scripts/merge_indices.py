"""Assemble the six stock series with the genuine WIG benchmark exports."""
from __future__ import annotations

import argparse
import json

from data_paths import METADATA
from market_data import PROCESSED_MARKET, YAHOO_SNAPSHOTS, assemble, write_pair


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sources = METADATA / "market_sources.json"
    default = json.loads(sources.read_text(encoding="utf-8"))["yahoo_bundle"] if sources.exists() else None
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--yahoo-bundle", default=default,
                       help="Name of a complete Yahoo snapshot in raw/market_data/snapshots/yahoo.")
    group.add_argument("--legacy-stocks", action="store_true",
                       help="Use historical local series for legacy reproduction.")
    args = parser.parse_args()
    bundle = YAHOO_SNAPSHOTS / args.yahoo_bundle if args.yahoo_bundle and not args.legacy_stocks else None
    market = assemble(bundle)
    write_pair(market, PROCESSED_MARKET / "market_data_all")
    print(market.groupby("Ticker")["Date"].agg(["count", "min", "max"]).to_string())


if __name__ == "__main__":
    main()
