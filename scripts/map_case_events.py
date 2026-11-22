"""Powiąż udokumentowane zdarzenia Olefin III z dokładnymi numerami ESPI."""

import pandas as pd

from build_master import write_pair
from data_paths import EVENTS, METADATA, PROCESSED, load_study_scope


def main():
    case = load_study_scope()["case_study"]
    chronology = pd.read_csv(METADATA / "olefiny_iii_timeline.csv", dtype={"report_number": str})
    if set(chronology["report_number"]) != set(case["reports"]):
        raise ValueError("Zakres kalendarium nie odpowiada konfiguracji studium przypadku.")
    catalog = pd.read_parquet(EVENTS / "espi_catalog.parquet")
    catalog = catalog.loc[catalog["ticker"].eq(case["ticker"]) & catalog["report_number"].isin(case["reports"])]
    fields = ["report_number", "event_id", "url", "data_pub"]
    joined = chronology.merge(catalog[fields], on="report_number", how="left", validate="many_to_one")
    if joined["event_id"].isna().any():
        raise ValueError("Brak dokładnego numeru ESPI dla co najmniej jednej pozycji kalendarium.")
    if not pd.to_datetime(joined["publication_date"]).eq(joined["data_pub"]).all():
        raise ValueError("Rozbieżność między datą publikacji w kalendarium a katalogiem ESPI.")
    target = PROCESSED / "case_studies" / case["project_id"]
    write_pair(joined.drop(columns="data_pub"), target / "timeline")
    print(f"Olefiny III: {joined['event_id'].nunique()} komunikaty źródłowe, {len(joined)} pozycji kalendarium.")


if __name__ == "__main__":
    main()
