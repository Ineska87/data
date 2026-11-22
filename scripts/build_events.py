"""Zbuduj kolejkę weryfikacji ESPI i próbę zatwierdzoną na podstawie źródeł."""

import re

import pandas as pd

from build_master import normalize_time, write_pair
from data_paths import EVENTS, METADATA, load_study_scope


DECISIONS = {
    "start": "Rozpoczęcie",
    "revision": "Zmiana",
    "suspension": "Wstrzymanie lub zakończenie",
}
REVIEW_COLUMNS = [
    "event_id", "review_status", "project_id", "decision_type", "adverse_revision",
    "scope_comparable", "previous_plan_url", "previous_plan_date", "source_url",
    "verified_event_time", "time_source_url", "coding_note",
]
TITLE_HINT = re.compile(
    r"inwestycj|rozbudow|budow[ayę]|projekt|wstrzyman|farm[ayę]|petrochemi|elektrown"
    r"|harmonogram|budżet|blok gaz|magazyn energ|capex|przyznanie dofinansowania",
    flags=re.IGNORECASE,
)


def verify_review(review, scope_events):
    if review["event_id"].duplicated().any():
        raise ValueError("Powtórzone event_id w arkuszu weryfikacji.")
    unknown_ids = set(review["event_id"]) - set(scope_events["event_id"])
    if unknown_ids:
        raise ValueError(f"Kody spoza okresu albo spoza katalogu: {sorted(unknown_ids)}")
    for row in review.itertuples(index=False):
        if row.review_status not in {"include", "exclude", "needs_review"}:
            raise ValueError(f"Nieznany status weryfikacji: {row.event_id}")
        if row.review_status in {"include", "exclude"} and not (row.source_url and row.coding_note):
            raise ValueError(f"Brak źródła albo uzasadnienia: {row.event_id}")
        if row.review_status == "include":
            if row.decision_type not in DECISIONS or not row.project_id or not row.previous_plan_url:
                raise ValueError(f"Brak decyzji, projektu lub planu odniesienia: {row.event_id}")
            earlier = pd.to_datetime(row.previous_plan_date, format="%Y-%m-%d", errors="coerce")
            date = scope_events.loc[scope_events["event_id"].eq(row.event_id), "event_date"].iloc[0]
            if pd.isna(earlier) or earlier >= date:
                raise ValueError(f"Plan odniesienia musi być wcześniejszy: {row.event_id}")
            if row.adverse_revision not in {"yes", "no", "unknown"} or row.scope_comparable not in {"yes", "no", "unknown"}:
                raise ValueError(f"Nieprawidłowe kodowanie zakresu albo korekty: {row.event_id}")
        if row.verified_event_time and not (normalize_time(row.verified_event_time) and row.time_source_url):
            raise ValueError(f"Brak poprawnej godziny lub źródła godziny: {row.event_id}")


def main():
    scope = load_study_scope()
    start, end = map(pd.Timestamp, (scope["period"]["start"], scope["period"]["end"]))
    frame = pd.read_parquet(EVENTS / "espi_catalog.parquet")
    frame = frame.rename(columns={"data_pub": "event_date", "godzina": "event_time", "tytul": "title"})
    frame = frame.loc[frame["event_date"].between(start, end)].copy()
    review = pd.read_csv(METADATA / "espi_review.csv", dtype=str, keep_default_na=False)
    if list(review.columns) != REVIEW_COLUMNS:
        raise ValueError("Nieprawidłowe kolumny espi_review.csv.")
    verify_review(review, frame)
    joined = frame.merge(review, on="event_id", how="left", validate="one_to_one")
    joined["review_status"] = joined["review_status"].fillna("needs_review")
    joined["title_hint"] = joined["title"].str.contains(TITLE_HINT, na=False)
    verified_time = joined["verified_event_time"].fillna("").map(normalize_time)
    joined["event_time"] = verified_time.where(verified_time.ne(""), joined["event_time"])
    joined["has_time"] = joined["event_time"].ne("")
    joined["event_datetime"] = pd.to_datetime(
        joined["event_date"].dt.strftime("%Y-%m-%d") + " " + joined["event_time"],
        format="%Y-%m-%d %H:%M",
        errors="coerce",
    )
    joined["source"] = "ESPI"
    queue = joined.sort_values(["title_hint", "ticker", "event_date"], ascending=[False, True, True])
    queue.to_csv(EVENTS / "espi_review_queue.csv", index=False, encoding="utf-8-sig")
    registry = joined.loc[joined["review_status"].eq("include")].copy()
    registry["adverse_revision"] = registry["adverse_revision"].map({"yes": True, "no": False}).astype("boolean")
    registry["event_type"] = registry["decision_type"]
    registry["event_type_pl"] = registry["event_type"].map(DECISIONS)
    label = f"{start.year}_{end.year}"
    write_pair(registry, EVENTS / f"investment_events_{label}")
    print(f"Komunikaty w okresie: {len(queue)}. Zgodne decyzje po weryfikacji: {len(registry)}.")
    print(queue["review_status"].value_counts().to_string())


if __name__ == "__main__":
    main()
