#!/usr/bin/env python3
"""Download Q1/H1/Q3 reports (+ presentations where listed) for PGE/TPE/ENA 2020-2025."""

from __future__ import annotations

import json
import ssl
import time
import urllib.request
from datetime import datetime, timezone

from data_paths import DATA_ROOT

BASE = DATA_ROOT / "raw" / "reports"
URL_LIST = DATA_ROOT / "metadata" / "download_manifests" / "_quarters_url_list.json"
CTX = ssl.create_default_context()
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
}


def download_one(ticker: str, name: str, url: str, retries: int = 4) -> dict:
    out_dir = BASE / ticker
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    if path.exists() and path.stat().st_size > 30_000:
        return {
            "ticker": ticker,
            "file": name,
            "url": url,
            "status": "skip_exists",
            "bytes": path.stat().st_size,
            "path": path.relative_to(DATA_ROOT.parent).as_posix(),
        }
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=CTX, timeout=240) as r:
                data = r.read()
                ctype = (r.headers.get("Content-Type") or "").lower()
            if len(data) < 15_000:
                raise ValueError(f"too_small ({len(data)} B) ctype={ctype}")
            head = data[:200].lstrip()
            if head.startswith(b"<") or head.startswith(b"<!DOCTYPE") or "html" in ctype and b"%PDF" not in data[:1024]:
                # some ashx may still be PDF
                if not data.startswith(b"%PDF") and b"PK\x03\x04" not in data[:4]:
                    raise ValueError(f"not a binary report (ctype={ctype}, head={head[:40]!r})")
            path.write_bytes(data)
            return {
                "ticker": ticker,
                "file": name,
                "url": url,
                "status": "ok",
                "bytes": len(data),
                "path": path.relative_to(DATA_ROOT.parent).as_posix(),
            }
        except Exception as e:
            last_err = e
            time.sleep(1.2 * attempt)
    return {
        "ticker": ticker,
        "file": name,
        "url": url,
        "status": "fail",
        "error": str(last_err),
    }


def main() -> None:
    rows = json.loads(URL_LIST.read_text(encoding="utf-8"))
    ready = [r for r in rows if r.get("status") == "ready" and r.get("url")]
    results = []
    for r in ready:
        ticker = r["ticker"]
        name = r["file"]
        url = r["url"]
        print(f"… {ticker}/{name}")
        out = download_one(ticker, name, url)
        results.append(out)
        if out["status"] == "ok":
            print(f"  OK  {out['bytes']:,} B")
        elif out["status"] == "skip_exists":
            print(f"  SKIP {out['bytes']:,} B")
        else:
            print(f"  FAIL {out.get('error')}")
        time.sleep(0.35)

    manifest = {
        "scope": "Q1/H1/Q3 (SAR) PGE/TPE/ENA 2020-2025 — sprawozdania + prezentacje PGE + SZ ENA H1",
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "n_ok": sum(1 for x in results if x["status"] in ("ok", "skip_exists")),
        "n_fail": sum(1 for x in results if x["status"] == "fail"),
        "files": results,
    }
    man_path = BASE / "manifest_quarters_pge_tpe_ena.json"
    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nManifest: {man_path}")
    print(f"OK/skip={manifest['n_ok']} fail={manifest['n_fail']} / {len(results)}")
    if manifest["n_fail"]:
        print("Failures:")
        for x in results:
            if x["status"] == "fail":
                print(f"  - {x['file']}: {x.get('error')}")


if __name__ == "__main__":
    main()
