"""Zbuduj kolejkę weryfikacji ESPI i próbę zatwierdzoną na podstawie źródeł."""

import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation

import pandas as pd

from build_master import normalize_time, write_pair
from data_paths import EVENTS, METADATA, RAW, load_study_scope
from publication_order import clock_interval, strictly_before


DECISIONS = {
    "start": "Rozpoczęcie",
    "revision": "Zmiana",
    "suspension": "Wstrzymanie lub zakończenie",
}
BASE_REVIEW_COLUMNS = [
    "event_id", "review_status", "project_id", "decision_type", "adverse_revision",
    "scope_comparable", "previous_plan_url", "previous_plan_date", "source_url",
    "verified_event_time", "time_source_url", "coding_note",
]
REVIEW_EVIDENCE_COLUMNS = [
    "previous_plan_event_id", "previous_plan_time", "previous_plan_time_source_url",
    "first_public_plan_event_id", "first_public_plan_url", "first_public_plan_date",
    "first_public_plan_time", "first_public_plan_time_source_url", "first_public_plan_scope_note",
    "old_capex_mn", "new_capex_mn", "capex_currency", "old_capex_scope", "new_capex_scope", "capex_scope_note",
    "old_milestone_type", "old_milestone_target", "new_milestone_type", "new_milestone_target",
    "milestone_comparable", "actual_spend_mn", "actual_spend_currency", "actual_spend_to",
    "impairment_mn", "impairment_currency", "impairment_period", "comparison_source_url",
]
REVIEW_COLUMNS = BASE_REVIEW_COLUMNS + REVIEW_EVIDENCE_COLUMNS
TRISTATE = {"yes", "no", "unknown"}
CAPEX_SCOPES = {"base_installation", "supporting_infrastructure", "base_and_support", "redesigned_project",
                "programme", "other", "unknown"}
MILESTONES = {"construction_completion", "commissioning", "commercial_operation", "other", "unknown"}
TARGET_PERIOD = re.compile(r"\d{4}(?:-Q[1-4]|-H[12]|-\d{2}(?:-\d{2})?)?")
TITLE_HINT = re.compile(
    r"inwestycj|rozbudow|budow[ayę]|projekt|wstrzyman|farm[ayę]|petrochemi|elektrown"
    r"|harmonogram|budżet|blok gaz|magazyn energ|capex|przyznanie dofinansowania",
    flags=re.IGNORECASE,
)


def evidence_columns(scope_events):
    root = RAW / "espi" / "detail_evidence"
    details = {}
    for path in (
        root / "reports.jsonl", root / "gpw_reports.jsonl", root / "archive_matches.jsonl",
        root / "verified_clock_overrides.jsonl",
    ):
        if path.is_file():
            with path.open(encoding="utf-8-sig") as stream:
                for line in stream:
                    if not line.strip():
                        continue
                    item = json.loads(line)
                    if item.get("event_id"):
                        details.setdefault(item["event_id"], []).append(item)
    candidate_file = root / "investment_candidates.jsonl"
    candidates = set()
    if candidate_file.is_file():
        with candidate_file.open(encoding="utf-8-sig") as stream:
            candidates.update(json.loads(line)["event_id"] for line in stream if line.strip())

    records = []
    for event in scope_events.itertuples(index=False):
        items = details.get(event.event_id, [])
        verified = next(
            (item for item in reversed(items) if item.get("publication_date") == event.event_date.date().isoformat()
             and normalize_time(item.get("publication_time")) and item.get("time_source_url")),
            {},
        )
        readable = next((item for item in reversed(items) if item.get("status") == "ok" and item.get("text")), {})
        records.append({
            "event_id": event.event_id,
            "full_text_status": "ok" if readable else items[0].get("status", "missing") if items else "missing",
            "investment_candidate": event.event_id in candidates,
            "detail_time": normalize_time(verified.get("publication_time")),
            "detail_time_exact": verified.get("publication_time_exact", ""),
            "detail_time_source_url": verified.get("time_source_url", ""),
        })
    return pd.DataFrame.from_records(records, columns=(
        "event_id", "full_text_status", "investment_candidate", "detail_time", "detail_time_exact",
        "detail_time_source_url",
    ))


def read_review(path):
    review = pd.read_csv(path, dtype=str, keep_default_na=False)
    if set(BASE_REVIEW_COLUMNS) - set(review) or set(review) - set(REVIEW_COLUMNS):
        raise ValueError("Nieprawidłowe kolumny espi_review.csv.")
    return review.reindex(columns=REVIEW_COLUMNS, fill_value="")


def review_date(value, event_id):
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return date.fromisoformat(value)
    raise ValueError(f"Oczekiwano daty RRRR-MM-DD: {event_id}")


def verify_plan(row, event, indexed, prefix):
    source, day, clock, time_source, plan_id = (
        getattr(row, f"{prefix}_{field}") for field in ("url", "date", "time", "time_source_url", "event_id")
    )
    if not any((source, day, clock, time_source, plan_id)):
        return
    if not source.startswith(("https://", "http://")) or not day:
        raise ValueError(f"Brakuje daty lub źródła planu: {row.event_id}, {prefix}")
    day = review_date(day, row.event_id)
    event_day = event.event_date.date()
    if bool(clock) != bool(time_source) or clock and (
        clock_interval(clock) is None or not time_source.startswith(("https://", "http://"))
    ):
        raise ValueError(f"Brak poprawnej godziny lub źródła planu: {row.event_id}, {prefix}")
    if plan_id in indexed:
        registered = indexed[plan_id]
        if registered.ticker != event.ticker or registered.event_date.date() != day:
            raise ValueError(f"Niespójny identyfikator planu: {row.event_id}, {plan_id}")
        known_clock = getattr(registered, "publication_time", "")
        if known_clock and clock and (
            strictly_before(day, clock, day, known_clock) is True or
            strictly_before(day, known_clock, day, clock) is True
        ):
            raise ValueError(f"Godzina planu różni się od zarejestrowanej: {row.event_id}, {plan_id}")
        clock = known_clock or clock
    if prefix == "first_public_plan" and plan_id == row.event_id:
        if day != event_day:
            raise ValueError(f"Data pierwszego planu różni się od jego komunikatu: {row.event_id}")
        return
    if strictly_before(day, clock, event_day, getattr(event, "publication_time", "")) is not True:
        raise ValueError(f"Plan musi być udokumentowany jako wcześniejszy: {row.event_id}, {prefix}")


def verify_quantities(row, event_day):
    for amounts, currency in (
        ((row.old_capex_mn, row.new_capex_mn), row.capex_currency),
        ((row.actual_spend_mn,), row.actual_spend_currency),
        ((row.impairment_mn,), row.impairment_currency),
    ):
        if any(amounts):
            if not re.fullmatch(r"[A-Z]{3}", currency):
                raise ValueError(f"Wymagany kod waluty dla kwoty w mln: {row.event_id}")
            for amount in filter(None, amounts):
                try:
                    value = Decimal(amount)
                except InvalidOperation:
                    raise ValueError(f"Nieprawidłowa kwota w mln: {row.event_id}, {amount}") from None
                if not value.is_finite() or value < 0:
                    raise ValueError(f"Nieprawidłowa kwota w mln: {row.event_id}, {amount}")
    if row.actual_spend_mn and not row.actual_spend_to:
        raise ValueError(f"Nakłady wykonane wymagają daty końcowej: {row.event_id}")
    if row.actual_spend_to and review_date(row.actual_spend_to, row.event_id) > event_day:
        raise ValueError(f"Data nakładów wykonanych jest późniejsza od komunikatu: {row.event_id}")
    if row.impairment_mn and not row.impairment_period:
        raise ValueError(f"Odpis wymaga okresu: {row.event_id}")
    for value in (row.old_milestone_target, row.new_milestone_target, row.impairment_period):
        if value and not TARGET_PERIOD.fullmatch(value):
            raise ValueError(f"Nieprawidłowa data lub okres: {row.event_id}, {value}")
    if not {row.old_capex_scope, row.new_capex_scope} - {""} <= CAPEX_SCOPES:
        raise ValueError(f"Nieznany zakres CAPEX: {row.event_id}")
    if not {row.old_milestone_type, row.new_milestone_type} - {""} <= MILESTONES:
        raise ValueError(f"Nieznany kamień milowy: {row.event_id}")
    if row.milestone_comparable and row.milestone_comparable not in TRISTATE:
        raise ValueError(f"Nieznany status porównywalności kamieni milowych: {row.event_id}")
    if row.milestone_comparable == "yes" and (
        row.old_milestone_type not in MILESTONES - {"unknown"}
        or row.old_milestone_type != row.new_milestone_type
        or not (row.old_milestone_target and row.new_milestone_target)
    ):
        raise ValueError(f"Porównywalny termin wymaga dwóch celów tego samego typu: {row.event_id}")


def verify_review(review, scope_events):
    if review["event_id"].duplicated().any():
        raise ValueError("Powtórzone event_id w arkuszu weryfikacji.")
    unknown_ids = set(review["event_id"]) - set(scope_events["event_id"])
    if unknown_ids:
        raise ValueError(f"Kody spoza okresu albo spoza katalogu: {sorted(unknown_ids)}")
    indexed = {event.event_id: event for event in scope_events.itertuples(index=False)}
    for row in review.itertuples(index=False):
        if row.review_status not in {"include", "exclude", "needs_review"}:
            raise ValueError(f"Nieznany status weryfikacji: {row.event_id}")
        if row.review_status in {"include", "exclude"} and not (row.source_url and row.coding_note):
            raise ValueError(f"Brak źródła albo uzasadnienia: {row.event_id}")
        if row.review_status == "include":
            if row.decision_type not in DECISIONS or not row.project_id or not row.previous_plan_url:
                raise ValueError(f"Brak decyzji, projektu lub planu odniesienia: {row.event_id}")
            if row.adverse_revision not in TRISTATE or row.scope_comparable not in TRISTATE:
                raise ValueError(f"Nieprawidłowe kodowanie zakresu albo korekty: {row.event_id}")
        if row.verified_event_time and not (
            clock_interval(row.verified_event_time) and row.time_source_url.startswith(("https://", "http://"))
        ):
            raise ValueError(f"Brak poprawnej godziny lub źródła godziny: {row.event_id}")
        event = indexed[row.event_id]
        verify_plan(row, event, indexed, "previous_plan")
        verify_plan(row, event, indexed, "first_public_plan")
        verify_quantities(row, event.event_date.date())


def main():
    scope = load_study_scope()
    start, end = map(pd.Timestamp, (scope["period"]["start"], scope["period"]["end"]))
    frame = pd.read_parquet(EVENTS / "espi_catalog.parquet")
    frame = frame.rename(columns={"data_pub": "event_date", "godzina": "event_time", "tytul": "title"})
    frame = frame.loc[frame["event_date"].between(start, end)].copy()
    review = read_review(METADATA / "espi_review.csv")
    joined = frame.merge(review, on="event_id", how="left", validate="one_to_one")
    joined = joined.merge(evidence_columns(frame), on="event_id", how="left", validate="one_to_one")
    joined["review_status"] = joined["review_status"].fillna("needs_review")
    joined["title_hint"] = joined["title"].str.contains(TITLE_HINT, na=False)
    manual_clock = joined["verified_event_time"].fillna("")
    verified_time = manual_clock.map(normalize_time)
    has_manual_seconds = manual_clock.str.fullmatch(r"\d{1,2}:\d{2}:\d{2}")
    list_time = joined["event_time"].fillna("").map(normalize_time)
    detail_time = joined.pop("detail_time")
    detail_time_exact = joined.pop("detail_time_exact").fillna("")
    detail_source_url = joined.pop("detail_time_source_url")
    joined["event_time"] = verified_time.where(verified_time.ne(""), detail_time.where(detail_time.ne(""), list_time))
    exact_available = detail_time_exact.ne("") & ~has_manual_seconds & (verified_time.eq("") | verified_time.eq(detail_time))
    manual_exact = verified_time + ":" + manual_clock.str[-2:]
    joined["publication_time"] = detail_time_exact.where(
        exact_available, manual_exact.where(has_manual_seconds, joined["event_time"]),
    )
    list_source_url = joined["url"].where(list_time.ne(""), "")
    joined["publication_time_source_url"] = joined["time_source_url"].where(
        verified_time.ne(""), detail_source_url.where(detail_time.ne(""), list_source_url),
    ).where(~exact_available, detail_source_url)
    joined["has_time"] = joined["event_time"].ne("")
    joined["event_datetime"] = pd.to_datetime(
        joined["event_date"].dt.strftime("%Y-%m-%d") + " " + joined["publication_time"],
        format="mixed",
        errors="coerce",
    ).where(joined["has_time"])
    verify_review(review, joined)
    joined["same_day_espi_count"] = joined.groupby(["ticker", "event_date"])["event_id"].transform("size")
    joined["revision_subgroup"] = joined["adverse_revision"].map(
        {"yes": "adverse", "no": "other", "unknown": "undetermined"},
    ).fillna("")
    joined["source"] = "ESPI"
    queue = joined.sort_values(["title_hint", "ticker", "event_date", "event_datetime", "event_id"],
                               ascending=[False, True, True, True, True])
    queue.to_csv(EVENTS / "espi_review_queue.csv", index=False, encoding="utf-8-sig")
    registry = joined.loc[joined["review_status"].eq("include")].copy()
    registry["same_day_confirmed_count"] = registry.groupby(["ticker", "event_date"])["event_id"].transform("size")
    registry["adverse_revision"] = registry["adverse_revision"].map({"yes": True, "no": False}).astype("boolean")
    registry["event_type"] = registry["decision_type"]
    registry["event_type_pl"] = registry["event_type"].map(DECISIONS)
    label = f"{start.year}_{end.year}"
    write_pair(registry, EVENTS / f"investment_events_{label}")
    print(f"Komunikaty w okresie: {len(queue)}. Zgodne decyzje po weryfikacji: {len(registry)}.")
    print(queue["review_status"].value_counts().to_string())


if __name__ == "__main__":
    main()
