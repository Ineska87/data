"""Odtwórz katalog ESPI z jawnie wybranych zrzutów emitentów."""

import hashlib
import json
import re
from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pandas as pd

from data_paths import EVENTS, METADATA, RAW, load_study_scope


def parse_date(value):
    for form in ("%d.%m.%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return pd.Timestamp(datetime.strptime(str(value).strip(), form))
        except ValueError:
            continue
    return pd.NaT


def normalize_time(value):
    match = re.fullmatch(r"(\d{1,2}):(\d{2})(?::\d{2})?", str(value or "").strip())
    if match:
        hour, minute = map(int, match.groups())
        if 0 <= hour < 24 and 0 <= minute < 60:
            return f"{hour:02d}:{minute:02d}"
    return ""


def normalize_number(value):
    match = re.search(r"(?<!\d)(\d{1,4})\s*[/\-]\s*((?:19|20)\d{2})(?!\d)", value)
    return f"{int(match[1])}/{match[2]}" if match else ""


def normalize_url(value):
    if not value:
        return ""
    url = urlsplit(value)
    parameters = [(key, val) for key, val in parse_qsl(url.query) if not key.lower().startswith("utm_")]
    return urlunsplit((url.scheme.lower(), url.netloc.lower(), url.path.rstrip("/"), urlencode(sorted(parameters)), ""))


def stable_key(ticker, report_number, date, url, title):
    if report_number:
        number, year = report_number.split("/")
        return f"{ticker}_{year}_{number}"
    date_key = date.strftime("%Y-%m-%d") if pd.notna(date) else "invalid_date"
    identity = url or f"{date_key}|{' '.join(title.casefold().split())}"
    digest = hashlib.sha256(identity.encode()).hexdigest()[:20]
    return f"{ticker}_espi_{digest}"


def write_pair(frame, stem):
    stem.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(stem.with_suffix(".parquet"), index=False)
    frame.to_csv(stem.with_suffix(".csv"), index=False, encoding="utf-8-sig")


def load_records(snapshots):
    for ticker, relative_path in snapshots.items():
        espi_root = (RAW / "espi").resolve()
        path = (espi_root / relative_path).resolve()
        if not path.is_relative_to(espi_root / ticker):
            raise ValueError(f"Zrzut poza katalogiem emitenta: {relative_path}")
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        snapshot_date = pd.Timestamp(payload["data_scrapowania"]).normalize().tz_localize(None)
        for report in payload["raporty"]:
            date = parse_date(report.get("data"))
            hour = normalize_time(report.get("godzina"))
            title = str(report.get("tytul") or "").strip()
            number = str(report.get("numer") or "").strip()
            report_number = normalize_number(number)
            url = normalize_url(str(report.get("url") or "").strip())
            issue = ""
            if pd.isna(date):
                issue = "invalid_date"
            elif date > snapshot_date:
                issue = "date_after_snapshot"
            elif report_number and int(report_number.split("/")[1]) != date.year:
                issue = "report_year_mismatch"
            elif not title:
                issue = "missing_title"
            yield {
                "event_id": stable_key(ticker, report_number, date, url, title),
                "ticker": ticker,
                "spolka": payload.get("spolka", ticker),
                "numer": number,
                "report_number": report_number,
                "data_str": str(report.get("data") or ""),
                "data_pub": date,
                "godzina": hour,
                "tytul": title,
                "url": url,
                "snapshot": (path.relative_to(RAW.parent)).as_posix(),
                "snapshot_date": snapshot_date,
                "catalog_issue": issue,
            }


def main():
    scope = load_study_scope()
    snapshots = json.loads((METADATA / "espi_snapshots.json").read_text(encoding="utf-8"))
    if set(snapshots) != set(scope["tickers"]):
        raise ValueError("Manifest ESPI musi określać po jednym zrzucie dla każdego badanego emitenta.")
    records = pd.DataFrame(load_records(snapshots))
    okay = records["catalog_issue"].eq("")
    conflicting_dates = records.loc[okay].groupby("event_id")["data_pub"].nunique()
    conflict = records["event_id"].isin(conflicting_dates[conflicting_dates > 1].index)
    records.loc[okay & conflict, "catalog_issue"] = "conflicting_dates"
    eligible = records.loc[records["catalog_issue"].eq("")].copy()
    eligible["has_url"] = eligible["url"].ne("")
    eligible["has_time"] = eligible["godzina"].ne("")
    eligible = eligible.sort_values(["has_url", "has_time", "tytul"], ascending=[False, False, True])
    duplicate_rows = eligible.index[eligible["event_id"].duplicated()]
    records.loc[duplicate_rows, "catalog_issue"] = "duplicate"
    catalog = eligible.drop(index=duplicate_rows).drop(columns="has_url")
    catalog = catalog.sort_values(["ticker", "data_pub", "event_id"]).reset_index(drop=True)
    write_pair(catalog, EVENTS / "espi_catalog")
    discarded = records.loc[records["catalog_issue"].ne("")]
    discarded.to_csv(EVENTS / "espi_catalog_issues.csv", index=False, encoding="utf-8-sig")
    print(f"Katalog ESPI: {len(catalog)} pozycji, {len(discarded)} wierszy w rejestrze rozbieżności.")


if __name__ == "__main__":
    main()
