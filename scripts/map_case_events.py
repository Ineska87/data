"""Zbuduj kalendarium Olefin III z lokalnych komunikatów i dokumentów źródłowych."""

import json
import re
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from build_master import write_pair
from data_paths import DATA_ROOT, EVENTS, METADATA, PROCESSED, RAW, load_study_scope


FIRST_PUBLIC_PROGRAM = "69/2018"
DETAILS = RAW / "espi" / "detail_evidence" / "reports.jsonl"
CASE_FILES = RAW / "reports" / "PKN" / "olefiny_iii" / "manifest.json"
IMPAIRMENT_QUARTERS = [f"impairment_2024_q{q}_bln_pln" for q in range(1, 5)]


def load_espi_evidence(events):
    expected = events.set_index("event_id")[["report_number", "publication_date"]].to_dict("index")
    rows = {}
    with DETAILS.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            detail = json.loads(line)
            event_id = detail["event_id"]
            if event_id not in expected:
                continue
            identity = expected[event_id]
            exact_time = detail.get("publication_time_exact", "")
            if (
                event_id in rows
                or any(detail[key] != value for key, value in identity.items())
                or detail["status"] != "ok"
                or not detail["text"].strip()
                or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d", exact_time)
                or not detail.get("time_source_url")
                or not detail.get("text_source_url")
            ):
                raise ValueError(f"Niespójne lokalne źródło ESPI dla {event_id}.")
            rows[event_id] = {
                "event_id": event_id,
                "full_text_status": detail["status"],
                "full_text_source_url": detail["text_source_url"],
                "full_text_local_path": DETAILS.relative_to(DATA_ROOT).as_posix(),
                "publication_time": exact_time,
                "publication_time_source_url": detail["time_source_url"],
                "espi_attachments": " | ".join(item["url"] for item in detail.get("attachments", [])),
            }
    if expected.keys() != rows.keys():
        raise ValueError(f"Brak źródeł ESPI: {sorted(expected.keys() - rows.keys())}.")
    return pd.DataFrame(rows.values())


def supporting_sources(events, timezone):
    sources = pd.read_csv(METADATA / "olefiny_iii_supporting_sources.csv", dtype=str, keep_default_na=False)
    periods = pd.read_csv(METADATA / "report_publications.csv", dtype=str, keep_default_na=False)
    periods = periods.set_index("report_id")
    if not periods.index.is_unique:
        raise ValueError("Rejestr publikacji zawiera powtórzone raporty okresowe.")
    periods = periods.to_dict("index")
    project_files = {
        Path(item["file"]).name: item["url"]
        for item in json.loads(CASE_FILES.read_text(encoding="utf-8-sig"))["files"]
    }
    clock = events.set_index("report_number")[["event_id", "publication_date", "publication_time"]].to_dict("index")
    result = []
    for source in sources.to_dict("records"):
        path = (DATA_ROOT / source["local_file"]).resolve()
        if not path.is_relative_to(RAW.resolve()) or not path.is_file():
            raise ValueError(f"Brak lokalnego dokumentu: {source['local_file']}.")
        if source["archive_member"]:
            with ZipFile(path) as archive:
                archive.getinfo(source["archive_member"])
        event = clock[source["report_number"]]
        if source["source_kind"] == "periodic_report":
            period = periods[source["periodic_report_id"]]
        elif source["source_kind"] == "project_document":
            period = {"publication_date": "", "published_at": "", "source_url": project_files[path.name]}
        else:
            raise ValueError(f"Nieznany rodzaj dowodu: {source['source_kind']}.")

        event_time = pd.Timestamp(f'{event["publication_date"]}T{event["publication_time"]}', tz=timezone)
        if period["published_at"]:
            published = pd.Timestamp(period["published_at"])
            if published.tzinfo is None:
                raise ValueError(f"Raport bez strefy czasowej: {source['periodic_report_id']}.")
            relation = "before_espi" if published < event_time else "at_or_after_espi"
        elif period["publication_date"] and period["publication_date"] != event["publication_date"]:
            relation = "before_espi" if period["publication_date"] < event["publication_date"] else "at_or_after_espi"
        else:
            relation = "unconfirmed"
        result.append({"event_id": event["event_id"], **source, **period, "publication_relation": relation})
    return pd.DataFrame(result)


def main():
    scope = load_study_scope()
    case = scope["case_study"]
    chronology = pd.read_csv(METADATA / "olefiny_iii_timeline.csv", dtype=str, keep_default_na=False)
    numbers = set(case["reports"]) | {FIRST_PUBLIC_PROGRAM}
    if set(chronology["report_number"]) != numbers or chronology["report_number"].duplicated().any():
        raise ValueError("Zakres kalendarium nie odpowiada konfiguracji studium przypadku.")
    catalog = pd.read_parquet(EVENTS / "espi_catalog.parquet")
    catalog = catalog.loc[catalog["ticker"].eq(case["ticker"]) & catalog["report_number"].isin(numbers)]
    fields = ["report_number", "event_id", "url", "data_pub"]
    timeline = chronology.merge(catalog[fields], on="report_number", how="left", validate="one_to_one")
    if timeline["event_id"].isna().any() or not pd.to_datetime(timeline["publication_date"]).eq(timeline["data_pub"]).all():
        raise ValueError("Rozbieżność numeru lub daty publikacji kalendarium z katalogiem ESPI.")

    timeline = timeline.merge(load_espi_evidence(timeline), on="event_id", validate="one_to_one")
    timeline["in_study_scope"] = timeline["publication_date"].between(scope["period"]["start"], scope["period"]["end"])
    timeline["source_url"] = timeline["url"]
    number_columns = [column for column in chronology if column.endswith("_bln_pln")]
    for column in number_columns:
        timeline[column] = pd.to_numeric(timeline[column].replace("", None), errors="raise").astype("Float64")
    timeline["impairment_fy2024_bln_pln"] = timeline[IMPAIRMENT_QUARTERS].sum(axis=1, min_count=4).round(3)

    sources = supporting_sources(timeline, scope["timezone"])
    cited = sources.loc[sources["periodic_report_id"].ne("")].groupby("event_id")["periodic_report_id"].agg(" | ".join)
    timeline["supporting_periodic_reports"] = timeline["event_id"].map(cited).fillna("")
    target = PROCESSED / "case_studies" / case["project_id"]
    write_pair(timeline.drop(columns="data_pub"), target / "timeline")
    write_pair(sources, target / "timeline_sources")
    print(f"Olefiny III: {len(timeline)} komunikatów, {len(sources)} dodatkowych pozycji źródłowych.")


if __name__ == "__main__":
    main()
