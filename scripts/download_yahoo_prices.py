"""Acquire an immutable Yahoo Finance stock snapshot for the full study window."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlencode

import pandas as pd

from market_data import YAHOO_SNAPSHOTS, YAHOO_TICKERS, decode_yahoo_quotes, emitters


def source_url(symbol: str, start: str, end: str) -> str:
    def epoch(day: str) -> int:
        return int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp())

    query = urlencode({"period1": epoch(start), "period2": epoch(end), "interval": "1d",
                      "includeAdjustedClose": "true"})
    return f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?{query}"


def download_stock(url: str) -> bytes:
    import requests

    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.content


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2018-01-01")
    parser.add_argument("--end", default="2026-01-16", help="End date, exclusive.")
    parser.add_argument("--name", required=True, help="New snapshot directory name.")
    parser.add_argument("--response-dir", type=Path, help="Reuse six original public endpoint responses.")
    args = parser.parse_args()
    if Path(args.name).name != args.name or args.name in {"", ".", ".."}:
        parser.error("--name musi być samą nazwą katalogu.")
    if date.fromisoformat(args.start) > date(2018, 12, 31) or date.fromisoformat(args.end) < date(2026, 1, 6):
        parser.error("Migawka powinna obejmować bufor przed 2020 r. i pierwsze sesje stycznia 2026 r.")
    if args.start >= args.end:
        parser.error("--start musi poprzedzać --end.")
    output = YAHOO_SNAPSHOTS / args.name
    if output.exists():
        parser.error(f"Migawka już istnieje: {output}")
    symbols = {ticker: YAHOO_TICKERS[ticker] for ticker in emitters()}
    YAHOO_SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=YAHOO_SNAPSHOTS) as folder:
        temporary = Path(folder) / "snapshot"
        temporary.mkdir()
        results = {}
        for ticker, symbol in symbols.items():
            endpoint = source_url(symbol, args.start, args.end)
            staged = args.response_dir / f"{ticker}.json" if args.response_dir else None
            payload = staged.read_bytes() if staged else download_stock(endpoint)
            frame = decode_yahoo_quotes(payload, symbol)
            if (frame["Date"].min() > pd.Timestamp(args.start) + pd.Timedelta(days=10)
                    or frame["Date"].max() < pd.Timestamp(args.end) - pd.Timedelta(days=6)
                    or frame["Date"].max() >= pd.Timestamp(args.end)):
                raise ValueError(f"{symbol}: brak zakresu pokrywającego wymagane bufory.")
            target = temporary / f"{ticker}.json"
            target.write_bytes(payload)
            results[ticker] = {
                "source_url": f"https://finance.yahoo.com/quote/{symbol}/history/",
                "data_url": endpoint,
                "rows": len(frame),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
            if staged:
                fetched = datetime.fromtimestamp(staged.stat().st_mtime, timezone.utc)
                results[ticker]["fetched_at"] = fetched.isoformat()
        manifest = {
            "source": "Yahoo Finance daily chart",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "prices": "close and adjusted close",
            "start": args.start,
            "end_exclusive": args.end,
            "symbols": symbols,
            "files": results,
        }
        (temporary / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        temporary.rename(output)
    print(f"Zapisano spójną migawkę: {output}")


if __name__ == "__main__":
    main()
