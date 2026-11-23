"""Odtwórz katalog ESPI z jawnie wybranych zrzutów emitentów."""

import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

import pandas as pd

from data_paths import DATA_ROOT, EVENTS, METADATA, RAW, load_study_scope
from espi_identity import classify_report, event_key, normalize_url, numbered_key, report_channel, url_identity


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


def write_pair(frame, stem):
    stem.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(stem.with_suffix(".parquet"), index=False)
    frame.to_csv(stem.with_suffix(".csv"), index=False, encoding="utf-8-sig")


def snapshot_path(ticker, relative_path):
    entry = Path(relative_path)
    if entry.parts[:2] in (("staging", "espi"), ("raw", "espi")):
        root = DATA_ROOT
        allowed = DATA_ROOT.joinpath(*entry.parts[:2], ticker)
    else:
        root = RAW / "espi"
        allowed = root / ticker
    path = (root / entry).resolve()
    if entry.is_absolute() or not path.is_relative_to(allowed) or path.suffix.lower() != ".json":
        raise ValueError(f"Zrzut poza katalogiem emitenta albo nie jest plikiem JSON: {relative_path}")
    return path


def report_row(ticker, path, snapshot_date, company, report, rank):
    date = parse_date(report.get("data"))
    title = str(report.get("tytul") or "").strip()
    number = str(report.get("numer") or "").strip()
    identity = classify_report(number, title, str(report.get("corrects_report_number") or ""))
    reported_url = str(report.get("url") or "").strip()
    url = normalize_url(reported_url)
    source = urlsplit(url)
    archive_year = re.search(r"/raporty-biezace/(\d{4})/", source.path) if ticker == "PKN" else None
    report_year = int(identity.base_number.split("/")[1]) if identity.base_number else None
    linked_correction = identity.correction_suffix and report_year and pd.notna(date) and date.year > report_year
    channel = report_channel(report)
    issue = ""
    if channel == "EBI":
        issue = "non_espi"
    elif pd.isna(date):
        issue = "invalid_date"
    elif date > snapshot_date:
        issue = "date_after_snapshot"
    elif report_year and report_year != date.year and not linked_correction:
        issue = "report_year_mismatch"
    elif archive_year and int(archive_year[1]) != date.year and not linked_correction:
        issue = "publisher_year_mismatch"
    elif not title:
        issue = "missing_title"
    parent = numbered_key(ticker, identity.corrects_report_number) if identity.corrects_report_number else ""
    return {
        "event_id": event_key(ticker, identity, date, url, title),
        "ticker": ticker,
        "spolka": company,
        "numer": number,
        "report_number": identity.report_number,
        "base_report_number": identity.base_number,
        "is_correction": identity.is_correction,
        "corrects_report_number": identity.corrects_report_number,
        "corrects_event_id": parent,
        "channel": channel,
        "data_str": str(report.get("data") or ""),
        "data_pub": date,
        "godzina": normalize_time(report.get("godzina")),
        "tytul": title,
        "url": url,
        "reported_url": reported_url,
        "verification_source": "",
        "verification_note": "",
        "snapshot": path.relative_to(DATA_ROOT).as_posix(),
        "snapshot_date": snapshot_date,
        "catalog_issue": issue,
        "_rank": rank,
        "_url_key": url_identity(url),
    }


def load_source_overrides(path):
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, list):
        raise ValueError("espi_source_overrides.json powinien zawierać listę zweryfikowanych wpisów.")
    fields = {
        "date": "data", "number": "numer", "channel": "kanal", "time": "godzina",
        "corrects_report_number": "corrects_report_number",
    }
    overrides = {}
    for item in payload:
        keys = [(item["ticker"], url_identity(url)) for url in [item["url"], *item.get("aliases", [])]]
        source = urlsplit(item["source_url"])
        if (
            len(keys) != len(set(keys))
            or any(key in overrides or not key[1] for key in keys)
            or source.scheme not in {"https", "http"}
            or not source.netloc
            or not item["note"].strip()
        ):
            raise ValueError(f"Nieprawidłowa weryfikacja źródłowa: {keys[0]}")
        updates = {output: item[field] for field, output in fields.items() if field in item}
        corrected = item.get("corrects_report_number")
        valid_reference = isinstance(corrected, str) and corrected and classify_report(corrected).base_number == corrected
        if (
            not updates
            or ("date" in item and pd.isna(parse_date(item["date"])))
            or ("number" in item and not classify_report(item["number"]).base_number)
            or ("channel" in item and item["channel"] not in {"ESPI", "EBI"})
            or ("time" in item and not normalize_time(item["time"]))
            or ("corrects_report_number" in item and not valid_reference)
        ):
            raise ValueError(f"Weryfikacja zawiera nieprawidłowe pola: {keys[0]}")
        for key in keys:
            overrides[key] = (updates, item["source_url"], item["note"])
    return overrides


def snapshot_rows(ticker, path, snapshot_date, company, reports, rank, overrides):
    for report in reports:
        original = report_row(ticker, path, snapshot_date, company, report, rank)
        checked = overrides.get((ticker, original["_url_key"]))
        if checked is None:
            yield original
            continue
        updates, verification_source, verification_note = checked
        verified = report_row(ticker, path, snapshot_date, company, {**report, **updates}, rank)
        verified["verification_source"] = verification_source
        verified["verification_note"] = verification_note
        evidence_fields = ("numer", "data_pub", "godzina", "channel", "corrects_report_number")
        if any(original[field] != verified[field] for field in evidence_fields):
            original["previous_issue"] = original["catalog_issue"]
            original["catalog_issue"] = "superseded_verified"
            original["verification_source"] = verification_source
            original["verification_note"] = verification_note
            yield original
        yield verified


def load_records(snapshots, overrides=None):
    overrides = overrides or {}
    for ticker, entries in snapshots.items():
        if isinstance(entries, str):
            entries = [entries]
        if (
            not isinstance(entries, list) or not entries
            or not all(isinstance(entry, str) and entry.strip() for entry in entries)
            or len(entries) != len(set(entries))
        ):
            raise ValueError(f"Manifest wymaga listy niepowtarzających się zrzutów: {ticker}")
        rows = []
        for rank, relative_path in enumerate(entries):
            path = snapshot_path(ticker, relative_path)
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            if payload.get("ticker", ticker) != ticker or payload.get("typ", "biezace") != "biezace":
                raise ValueError(f"Zrzut nie jest wykazem ESPI dla {ticker}: {relative_path}")
            snapshot_date = pd.Timestamp(payload["data_scrapowania"]).normalize().tz_localize(None)
            choice = list(
                snapshot_rows(ticker, path, snapshot_date, payload.get("spolka", ticker), payload["raporty"], rank, overrides)
            )
            complete = payload.get("complete_period")
            if complete:
                start, end = map(parse_date, (complete["start"], complete["end"]))
                if pd.isna(start) or pd.isna(end) or end < start or end > snapshot_date:
                    raise ValueError(f"Nieprawidłowy okres kompletności w {relative_path}.")
                years = {
                    item["data_pub"].year for item in choice
                    if not item["catalog_issue"] and start <= item["data_pub"] <= end
                }
                if years != set(range(start.year, end.year + 1)):
                    raise ValueError(f"Brakuje lat w zadeklarowanym kompletnym okresie: {relative_path}.")
                for item in rows:
                    if (
                        not item["catalog_issue"].startswith("superseded")
                        and pd.notna(item["data_pub"]) and start <= item["data_pub"] <= end
                    ):
                        item["previous_issue"] = item["catalog_issue"]
                        item["catalog_issue"] = "superseded_period"
            rows.extend(choice)
        yield from rows


def close_verified_duplicates(records, resolutions):
    for resolution in resolutions:
        eligible = records.loc[
            records["catalog_issue"].eq("")
            & records["ticker"].eq(resolution["ticker"])
            & records["event_id"].eq(resolution["event_id"])
            & records["data_pub"].eq(parse_date(resolution["date"]))
        ]
        canonical = eligible.loc[
            eligible["_url_key"].eq(url_identity(resolution["canonical_url"]))
            & eligible["godzina"].eq(resolution["canonical_time"])
        ]
        duplicates = eligible.loc[
            eligible["_url_key"].eq(url_identity(resolution["duplicate_url"]))
            & eligible["godzina"].eq(resolution["duplicate_time"])
            & eligible["tytul"].isin(canonical["tytul"])
        ]
        records.loc[duplicates.index, "previous_issue"] = "duplicate"
        records.loc[duplicates.index, "catalog_issue"] = "superseded_verified_duplicate"
        records.loc[duplicates.index, "verification_source"] = resolution["canonical_url"]
        records.loc[duplicates.index, "verification_note"] = resolution["note"]


def reconcile_catalog(records, duplicate_resolutions=()):
    records = records.copy()

    # A later listing can correct both the number and publication date of a known publisher link.
    with_link = records.loc[~records["catalog_issue"].str.startswith("superseded") & records["_url_key"].ne("")]
    for _, rows in with_link.groupby(["ticker", "_url_key"], sort=False):
        if rows["_rank"].nunique() < 2:
            continue
        last_rank = rows["_rank"].max()
        top = rows[rows["_rank"].eq(last_rank) & rows["catalog_issue"].isin(["", "non_espi"])]
        identified = top[["event_id", "data_pub", "channel"]].drop_duplicates()
        if len(identified) != 1:
            if top.empty:
                # Keep the newest unresolved publisher evidence and retain the older raw rows.
                replaced = rows[rows["_rank"].lt(last_rank) & rows["catalog_issue"].ne("")]
                records.loc[replaced.index, "previous_issue"] = replaced["catalog_issue"]
                records.loc[replaced.index, "catalog_issue"] = "superseded_unresolved"
            continue
        event, date, channel = identified.iloc[0]
        replaced = rows[
            rows["_rank"].lt(last_rank)
            & (rows["event_id"].ne(event) | rows["data_pub"].ne(date) | rows["channel"].ne(channel))
        ]
        records.loc[replaced.index, "previous_issue"] = replaced["catalog_issue"]
        records.loc[replaced.index, "catalog_issue"] = "superseded_url"

    eligible = records[records["catalog_issue"].eq("")]
    conflicts = eligible.groupby("event_id")["data_pub"].nunique()
    for _, rows in eligible[eligible["event_id"].isin(conflicts[conflicts.gt(1)].index)].groupby("event_id"):
        matching = rows.loc[rows["_rank"].eq(rows["_rank"].max()), "data_pub"].unique()
        if len(matching) == 1:
            records.loc[rows.index[rows["data_pub"].ne(matching[0])], "catalog_issue"] = "superseded_date"
        else:
            records.loc[rows.index, "catalog_issue"] = "conflicting_dates"

    close_verified_duplicates(records, duplicate_resolutions)
    eligible = records.loc[records["catalog_issue"].eq("")].copy()
    eligible["has_url"] = eligible["url"].ne("")
    eligible["has_time"] = eligible["godzina"].ne("")
    eligible = eligible.sort_values(
        ["_rank", "has_url", "has_time", "tytul", "url"], ascending=[False, False, False, True, True]
    )
    duplicates = eligible[eligible["event_id"].duplicated()]
    selected_rank = eligible.drop_duplicates("event_id").set_index("event_id")["_rank"]
    legacy_duplicates = duplicates["_rank"].lt(duplicates["event_id"].map(selected_rank))
    records.loc[duplicates.index, "catalog_issue"] = "duplicate"
    records.loc[duplicates.index[legacy_duplicates], "catalog_issue"] = "superseded_duplicate"
    internal = ["_rank", "_url_key", "previous_issue"]
    catalog = eligible.drop(index=duplicates.index).drop(columns=[*internal, "has_url"], errors="ignore")
    catalog = catalog.sort_values(["ticker", "data_pub", "event_id"]).reset_index(drop=True)
    closed = records["catalog_issue"].str.startswith("superseded") | records["catalog_issue"].eq("non_espi")
    issues = records[records["catalog_issue"].ne("") & ~closed]
    superseded = records[closed]
    return (
        catalog,
        issues.drop(columns=internal, errors="ignore"),
        superseded.drop(columns=["_rank", "_url_key"]),
    )


def main():
    scope = load_study_scope()
    snapshots = json.loads((METADATA / "espi_snapshots.json").read_text(encoding="utf-8"))
    if set(snapshots) != set(scope["tickers"]):
        raise ValueError("Manifest ESPI musi określać zrzuty dla każdego badanego emitenta.")
    overrides = load_source_overrides(METADATA / "espi_source_overrides.json")
    resolutions_path = METADATA / "espi_resolved_duplicates.json"
    duplicate_resolutions = json.loads(resolutions_path.read_text(encoding="utf-8-sig")) if resolutions_path.is_file() else []
    records = pd.DataFrame(load_records(snapshots, overrides))
    catalog, issues, superseded = reconcile_catalog(records, duplicate_resolutions)
    if set(catalog["ticker"]) != set(scope["tickers"]):
        raise ValueError("Co najmniej jeden emitent nie ma poprawnych wierszy w katalogu ESPI.")
    write_pair(catalog, EVENTS / "espi_catalog")
    issues.to_csv(EVENTS / "espi_catalog_issues.csv", index=False, encoding="utf-8-sig")
    superseded.to_csv(EVENTS / "espi_catalog_superseded.csv", index=False, encoding="utf-8-sig")
    print(f"Katalog ESPI: {len(catalog)} pozycji, w tym {catalog['is_correction'].sum()} korekt.")
    print(f"Rejestr rozbieżności i duplikatów: {len(issues)} wierszy. Zamknięte wpisy: {len(superseded)}.")


if __name__ == "__main__":
    main()
