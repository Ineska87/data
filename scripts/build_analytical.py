#!/usr/bin/env python3
"""Merge CAR × panel × cases (+ tone/macro already in panel) into analysis-ready tables.

Outputs → data/processed/analytical/
------------------------------------
1. events_enriched.parquet  — ESPI events (preferred benchmark) + CAR windows
   + panel (same quarter & lag) + case flags + QUAL
2. case_events_enriched.parquet — H1–H6 map rows + panel/tone/macro context
3. panel_with_car.parquet — firm×quarter panel + within-quarter CAR aggregates
4. car_tone_summary.md — descriptive CAR × TONE / case / QUAL
5. codebook.md
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from data_paths import DATA_ROOT, EVENTS, LEGACY, load_study_scope
from investment_sentiment import CORPUS, PASSAGE_SCORES, VALIDATION

ROOT = DATA_ROOT.parent
PROC = LEGACY / "processed"
OUT = PROC / "analytical"

CAR_F = PROC / "car_results.parquet"
EVENTS_F = PROC / "events_master_2019_2025.parquet"
PANEL_F = PROC / "panel" / "panel_quarterly.parquet"
CASE_F = PROC / "case_studies" / "case_events_map.parquet"

# Preferred market model benchmark per ticker — MUST match compute_car.BENCHMARK
# (UNT/ZEP: WIG ma wyższe R² niż indeks sektorowy; nie nadpisywać „docelowym” sektorem)
PREF_BENCH = {
    "PKN": "WIG-paliwa",
    "UNT": "WIG",
    "JSW": "WIG",
    "PGE": "WIG-energia",
    "TPE": "WIG-energia",
    "ENA": "WIG-energia",
    "ZEP": "WIG",
    "LWB": "WIG",
}

WINDOWS = ["[-1+1]", "[-3+3]", "[-5+5]", "[-10+10]", "[-20+20]"]
WIN_COL = {
    "[-1+1]": "car_m1p1",
    "[-3+3]": "car_m3p3",
    "[-5+5]": "car_m5p5",
    "[-10+10]": "car_m10p10",
    "[-20+20]": "car_m20p20",
}

# Panel columns useful as covariates (keep lean for event table)
PANEL_COVARS = [
    "role",
    "state_control",
    "accounting_tier",
    "total_assets",
    "capex",
    "capex_int",
    "net_debt",
    "ebit",
    "ebitda",
    "revenue",
    "net_income",
    "roa",
    "cfo",
    "cfoa",
    "cash",
    "equity",
    "mb",
    "mktcap",
    "ret_q",
    "ret_vol",
    "lev",
    "lev_assets",
    "lev_assets_w",
    "lev_op",
    "cash_ratio",
    "impairment_dummy",
    "fin_event",
    "ma_event",
    "div_event",
    "n_espi",
    "TONE_MGR",
    "UNCERTAINTY",
    "CERTAINTY",
    "READABILITY",
    "n_mgr_docs",
    "n_mgr_words",
    "brent_usd_qmean",
    "power_pl_eur_mwh_qmean",
    "eurpln_qmean",
    "nbp_ref_rate_qend",
    "gas_eu_usd_qmean",
    "eua_proxy_krbn_qmean",
    "COVID_2020",
    "ENERGY_CRISIS",
    "NORMALIZATION",
    "MERGER_ORLEN",
]


def load_car_wide() -> pd.DataFrame:
    """One row per event_id × ticker with preferred benchmark CARs wide."""
    car = pd.read_parquet(CAR_F)
    car["event_date"] = pd.to_datetime(car["event_date"])
    car["day0"] = pd.to_datetime(car["day0"])

    # choose preferred benchmark per ticker (fallback: WIG, then any)
    rows = []
    for (eid, ticker), g in car.groupby(["event_id", "ticker"]):
        pref = PREF_BENCH.get(ticker, "WIG")
        sub = g[g["benchmark"] == pref]
        if sub.empty:
            sub = g[g["benchmark"] == "WIG"]
        if sub.empty:
            sub = g
        bench = sub["benchmark"].iloc[0]
        base = sub.iloc[0][
            [
                "event_id",
                "ticker",
                "event_date",
                "event_year",
                "day0",
                "event_type",
                "event_type_pl",
                "has_time",
                "numer",
                "title",
                "alpha",
                "beta",
                "r2",
                "n_est",
                "resid_sd",
            ]
        ].to_dict()
        base["benchmark"] = bench
        for w, col in WIN_COL.items():
            ww = sub[sub["window"] == w]
            base[col] = float(ww["car"].iloc[0]) if len(ww) else np.nan
            base[col.replace("car_", "n_ar_")] = int(ww["n_ar"].iloc[0]) if len(ww) else np.nan
        rows.append(base)
    out = pd.DataFrame(rows)
    out["year"] = out["event_date"].dt.year
    out["quarter"] = out["event_date"].dt.quarter
    return out


def lag_yq(year: int, quarter: int) -> tuple[int, int]:
    if quarter == 1:
        return year - 1, 4
    return year, quarter - 1


def attach_panel(events: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    covars = [c for c in PANEL_COVARS if c in panel.columns]
    p = panel[["ticker", "year", "quarter"] + covars].copy()

    # current quarter
    cur = p.rename(columns={c: f"{c}_q" for c in covars})
    ev = events.merge(cur, on=["ticker", "year", "quarter"], how="left")

    # lag quarter keys
    lag_keys = ev.apply(lambda r: lag_yq(int(r["year"]), int(r["quarter"])), axis=1, result_type="expand")
    lag_keys.columns = ["year_lag", "quarter_lag"]
    ev = pd.concat([ev, lag_keys], axis=1)
    lag = p.rename(
        columns={
            "year": "year_lag",
            "quarter": "quarter_lag",
            **{c: f"{c}_lag" for c in covars},
        }
    )
    ev = ev.merge(lag, on=["ticker", "year_lag", "quarter_lag"], how="left")
    return ev


def attach_cases(events: pd.DataFrame, cases: pd.DataFrame) -> pd.DataFrame:
    cm = cases[cases["matched"] == True].copy()  # noqa: E712
    if cm.empty:
        events["is_case"] = 0
        events["case_ids"] = ""
        events["hyp_ids"] = ""
        events["qual_primary"] = np.nan
        return events

    # one event may map to multiple case rows
    g = (
        cm.groupby("event_id")
        .agg(
            is_case=("case", lambda s: 1),
            case_ids=("case", lambda s: "|".join(sorted(set(s.dropna().astype(str))))),
            hyp_ids=("hyp", lambda s: "|".join(sorted(set(s.dropna().astype(str))))),
            qual_primary=("qual", "first"),
            case_labels=("label", lambda s: " || ".join(s.dropna().astype(str)[:3])),
            n_case_maps=("case", "count"),
        )
        .reset_index()
    )
    out = events.merge(g, on="event_id", how="left")
    out["is_case"] = out["is_case"].fillna(0).astype(int)
    out["n_case_maps"] = out["n_case_maps"].fillna(0).astype(int)
    for c in ("case_ids", "hyp_ids", "case_labels", "qual_primary"):
        if c in out.columns:
            out[c] = out[c].fillna("")
    return out


def enrich_cases(cases: pd.DataFrame, panel: pd.DataFrame, car_wide: pd.DataFrame) -> pd.DataFrame:
    c = cases.copy()
    c["case_date"] = pd.to_datetime(c["case_date"])
    c["year"] = c["case_date"].dt.year
    c["quarter"] = c["case_date"].dt.quarter
    # prefer map CAR; fill from car_wide if needed
    if "event_id" in c.columns:
        cw = car_wide[
            ["event_id", "car_m1p1", "car_m5p5", "car_m10p10", "benchmark", "alpha", "beta", "r2"]
        ].drop_duplicates("event_id")
        c = c.merge(cw, on="event_id", how="left", suffixes=("", "_cw"))
        for col in ("car_m1p1", "car_m5p5"):
            if col in c.columns and f"{col}_cw" in c.columns:
                c[col] = c[col].combine_first(c[f"{col}_cw"])
        # map file uses car_m1p1 already
        if "car_m1p1" not in c.columns and "car_m1p1_cw" in c.columns:
            c["car_m1p1"] = c["car_m1p1_cw"]

    covars = [x for x in PANEL_COVARS if x in panel.columns]
    p = panel[["ticker", "year", "quarter"] + covars]
    c = c.merge(p, on=["ticker", "year", "quarter"], how="left", suffixes=("", "_panel"))

    lag_keys = c.apply(
        lambda r: lag_yq(int(r["year"]), int(r["quarter"])) if pd.notna(r["year"]) else (np.nan, np.nan),
        axis=1,
        result_type="expand",
    )
    lag_keys.columns = ["year_lag", "quarter_lag"]
    c = pd.concat([c, lag_keys], axis=1)
    pl = p.rename(
        columns={
            "year": "year_lag",
            "quarter": "quarter_lag",
            **{x: f"{x}_lag" for x in covars},
        }
    )
    c = c.merge(pl, on=["ticker", "year_lag", "quarter_lag"], how="left")
    return c


def panel_with_car(panel: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Aggregate event CARs into firm-quarter cells."""
    ev = events[(events["year"] >= 2020) & (events["year"] <= 2025)].copy()
    if ev.empty:
        return panel.copy()

    def agg(g: pd.DataFrame) -> pd.Series:
        return pd.Series(
            {
                "n_events_car": len(g),
                "car_m1p1_mean": g["car_m1p1"].mean(),
                "car_m1p1_median": g["car_m1p1"].median(),
                "car_m5p5_mean": g["car_m5p5"].mean(),
                "car_m1p1_abs_mean": g["car_m1p1"].abs().mean(),
                "n_case_events": int(g["is_case"].sum()) if "is_case" in g else 0,
                "car_m1p1_case_mean": g.loc[g["is_case"] == 1, "car_m1p1"].mean()
                if "is_case" in g and (g["is_case"] == 1).any()
                else np.nan,
                "car_m1p1_noncase_mean": g.loc[g["is_case"] == 0, "car_m1p1"].mean()
                if "is_case" in g and (g["is_case"] == 0).any()
                else np.nan,
                "share_neg_car_m1p1": (g["car_m1p1"] < 0).mean(),
            }
        )

    a = ev.groupby(["ticker", "year", "quarter"]).apply(agg, include_groups=False).reset_index()
    # fix if apply structure odd
    if "n_events_car" not in a.columns:
        rows = []
        for keys, g in ev.groupby(["ticker", "year", "quarter"]):
            s = agg(g)
            rows.append({"ticker": keys[0], "year": keys[1], "quarter": keys[2], **s.to_dict()})
        a = pd.DataFrame(rows)

    out = panel.merge(a, on=["ticker", "year", "quarter"], how="left")
    out["n_events_car"] = out["n_events_car"].fillna(0).astype(int)
    out["n_case_events"] = out["n_case_events"].fillna(0).astype(int)
    return out


def tone_tercile(s: pd.Series) -> pd.Series:
    x = s.astype(float)
    try:
        return pd.qcut(x, 3, labels=["low", "mid", "high"])
    except ValueError:
        return pd.Series(["mid"] * len(x), index=x.index)


def write_summary(events: pd.DataFrame, cases: pd.DataFrame, panel_car: pd.DataFrame) -> None:
    lines = [
        "# CAR × panel × cases — podsumowanie deskryptywne",
        "",
        f"Eventy (preferowany benchmark): **{len(events)}**",
        f"Case map rows: **{len(cases)}** (matched={int(cases['matched'].sum()) if 'matched' in cases else 'n/a'})",
        f"Panel firm×Q: **{len(panel_car)}**",
        "",
        "## CAR[-1,+1] — case vs reszta ESPI (2020–2025)",
        "",
    ]
    ev = events[(events["year"] >= 2020) & (events["year"] <= 2025)].copy()
    if "is_case" in ev.columns and "car_m1p1" in ev.columns:
        for flag, lab in [(1, "case"), (0, "non-case")]:
            s = ev.loc[ev["is_case"] == flag, "car_m1p1"].dropna()
            lines.append(
                f"- **{lab}**: n={len(s)}, mean={s.mean():.4%}, median={s.median():.4%}, "
                f"std={s.std():.4%}, share<0={(s < 0).mean():.1%}"
            )
    lines += ["", "## CAR[-1,+1] × TONE_MGR tercile (lag, gdy dostępny)", ""]
    tone_col = "TONE_MGR_lag" if "TONE_MGR_lag" in ev.columns else "TONE_MGR_q"
    if tone_col in ev.columns:
        sub = ev.dropna(subset=["car_m1p1", tone_col]).copy()
        if len(sub) >= 30:
            sub["tone_terc"] = tone_tercile(sub[tone_col])
            for t, g in sub.groupby("tone_terc", observed=False):
                s = g["car_m1p1"]
                lines.append(
                    f"- **tone {t}** (n={len(s)}): mean CAR={s.mean():.4%}, median={s.median():.4%}"
                )
            # simple correlation
            corr = sub["car_m1p1"].corr(sub[tone_col])
            lines.append(f"- Pearson corr(CAR[-1+1], {tone_col}) = **{corr:.4f}** (n={len(sub)})")
        else:
            lines.append(f"- za mało obs. z tonem ({len(sub)})")
    else:
        lines.append("- brak kolumny TONE w eventach")

    lines += ["", "## CAR[-1,+1] wg QUAL (tylko case matched)", ""]
    cm = cases[cases.get("matched", False) == True] if "matched" in cases.columns else cases  # noqa: E712
    car_col = "car_m1p1" if "car_m1p1" in cm.columns else None
    if car_col and "qual" in cm.columns:
        for q, g in cm.dropna(subset=[car_col]).groupby("qual"):
            s = g[car_col]
            lines.append(f"- **{q}**: n={len(s)}, mean={s.mean():.4%}, median={s.median():.4%}")

    lines += ["", "## CAR[-1,+1] wg case", ""]
    if car_col and "case" in cm.columns:
        for q, g in cm.dropna(subset=[car_col]).groupby("case"):
            s = g[car_col]
            lines.append(f"- **{q}**: n={len(s)}, mean={s.mean():.4%}, median={s.median():.4%}")

    lines += [
        "",
        "## Panel: średni CAR w kwartale vs TONE_MGR",
        "",
    ]
    if "car_m1p1_mean" in panel_car.columns and "TONE_MGR" in panel_car.columns:
        sub = panel_car.dropna(subset=["car_m1p1_mean", "TONE_MGR"])
        if len(sub):
            corr = sub["car_m1p1_mean"].corr(sub["TONE_MGR"])
            lines.append(f"- corr(mean CAR quarter, TONE_MGR) = **{corr:.4f}** (n={len(sub)})")
            lines.append(
                f"- mean |CAR| when case events present: "
                f"{panel_car.loc[panel_car['n_case_events'] > 0, 'car_m1p1_abs_mean'].mean():.4%}"
                if "car_m1p1_abs_mean" in panel_car.columns
                else ""
            )

    lines += [
        "",
        "## Pliki",
        "",
        "- `events_enriched.parquet` — jednostka: ESPI event",
        "- `case_events_enriched.parquet` — jednostka: data case H1–H6",
        "- `panel_with_car.parquet` — jednostka: spółka×kwartał",
        "",
        "## Uwagi",
        "",
        "- Benchmark (jak w compute_car): PGE/TPE/ENA → WIG-energia; PKN → WIG-paliwa; UNT/ZEP/JSW/LWB → WIG.",
        "- Kovarianty `_q` = ten sam kwartał co data zdarzenia; `_lag` = poprzedni kwartał.",
        "- TONE często sparse → CAR×TONE na podpróbce z niepustym tonem (lag).",
        "- To **descriptives**, nie wnioskowanie przyczynowe.",
        "",
        "Skrypt: `data/scripts/build_analytical.py`",
        "",
    ]
    (OUT / "car_tone_summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_codebook(n_ev: int, n_case: int, n_panel: int) -> None:
    text = f"""# Codebook — analytical merge (CAR × panel × cases)

## 1. `events_enriched` ({n_ev} wierszy)

Jednostka: **zdarzenie ESPI** (unikalne `event_id`) z preferowanym benchmarkiem.

| Blok | Pola |
|------|------|
| Id / meta | event_id, ticker, event_date, day0, year, quarter, event_type*, title, numer |
| Model | benchmark, alpha, beta, r2, n_est, resid_sd |
| CAR | car_m1p1, car_m3p3, car_m5p5, car_m10p10, car_m20p20 (+ n_ar_*) |
| Case | is_case, case_ids, hyp_ids, qual_primary, case_labels, n_case_maps |
| Panel same Q | `*_q` (assets, roa, TONE_MGR, brent, dummies, …) |
| Panel lag Q | `*_lag` |

## 2. `case_events_enriched` ({n_case} wierszy)

Jednostka: **priorytetowa data case** H1–H6 (w tym unmatched).

Kolumny z `case_events_map` + panel `_q` / `_lag` + CAR gdy matched.

## 3. `panel_with_car` ({n_panel} wierszy)

Jednostka: **spółka × rok × kwartał** (pełny panel) + agregaty CAR w tym kwartale:

| Pole | Opis |
|------|------|
| n_events_car | liczba ESPI z policzonym CAR |
| car_m1p1_mean / median | średnia / mediana CAR[-1+1] |
| car_m5p5_mean | średnia CAR[-5+5] |
| n_case_events | ile z nich to case |
| car_m1p1_case_mean | średni CAR tylko case |
| share_neg_car_m1p1 | odsetek ujemnych CAR |

## Preferowany benchmark (zgodny z `compute_car.BENCHMARK`)

| Ticker | Benchmark | Uwaga |
|--------|-----------|--------|
| PGE, TPE, ENA | WIG-energia | sektor |
| PKN | WIG-paliwa | sektor |
| UNT, ZEP, JSW, LWB | WIG | wyższe R² niż indeks sektorowy (UNT/ZEP) |

## Skrypt

`data/scripts/build_analytical.py`
"""
    (OUT / "codebook.md").write_text(text, encoding="utf-8")


def legacy_main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=== Load ===", flush=True)
    panel = pd.read_parquet(PANEL_F)
    cases = pd.read_parquet(CASE_F)
    print(f"panel {panel.shape}, cases {cases.shape}", flush=True)

    print("=== CAR wide (preferred bench) ===", flush=True)
    car_wide = load_car_wide()
    print(f"events {car_wide.shape}, benches {car_wide['benchmark'].value_counts().to_dict()}", flush=True)

    print("=== Attach panel + cases ===", flush=True)
    events = attach_panel(car_wide, panel)
    events = attach_cases(events, cases)
    # filter thesis window optional full keep 2019-2025
    events.to_parquet(OUT / "events_enriched.parquet", index=False)
    events.to_csv(OUT / "events_enriched.csv", index=False)
    print(f"events_enriched {events.shape}", flush=True)

    print("=== Case enriched ===", flush=True)
    case_en = enrich_cases(cases, panel, car_wide)
    case_en.to_parquet(OUT / "case_events_enriched.parquet", index=False)
    case_en.to_csv(OUT / "case_events_enriched.csv", index=False)
    print(f"case_events_enriched {case_en.shape}", flush=True)

    print("=== Panel + CAR aggregates ===", flush=True)
    panel_car = panel_with_car(panel, events)
    panel_car.to_parquet(OUT / "panel_with_car.parquet", index=False)
    panel_car.to_csv(OUT / "panel_with_car.csv", index=False)
    print(f"panel_with_car {panel_car.shape}", flush=True)

    print("=== Summary ===", flush=True)
    write_summary(events, case_en, panel_car)
    write_codebook(len(events), len(case_en), len(panel_car))

    cov = {
        "n_events": len(events),
        "n_events_2020_2025": int(((events["year"] >= 2020) & (events["year"] <= 2025)).sum()),
        "n_case_flagged_events": int(events["is_case"].sum()),
        "n_case_rows": len(case_en),
        "n_case_matched": int(case_en["matched"].sum()) if "matched" in case_en else None,
        "n_panel": len(panel_car),
        "n_panel_with_tone_and_car": int(
            panel_car.dropna(subset=["TONE_MGR", "car_m1p1_mean"]).shape[0]
        )
        if "TONE_MGR" in panel_car and "car_m1p1_mean" in panel_car
        else 0,
        "benchmarks": events["benchmark"].value_counts().to_dict(),
    }
    (OUT / "coverage.json").write_text(json.dumps(cov, indent=2), encoding="utf-8")
    print("coverage", cov, flush=True)
    print("done →", OUT, flush=True)


def build_event_report_links(events: pd.DataFrame, passages: pd.DataFrame) -> pd.DataFrame:
    """Link to a verified, earlier publication about the same issuer and project."""
    columns = ["event_id", "link_status", "report_id", "publication_date", "published_at",
               "publication_source_url", "n_passages", "n_words", "n_positive", "n_negative", "tone_per_100_words"]
    eligible = passages[passages["publication_date"].ne("") & passages["n_words"].gt(0)].copy()
    eligible["report_day"] = pd.to_datetime(eligible["publication_date"])
    eligible["publication_time"] = pd.to_datetime(eligible["published_at"], utc=True, errors="coerce", format="mixed")
    rows = []
    for event in events.itertuples(index=False):
        row = {"event_id": event.event_id, "link_status": "no_earlier_reviewed_report"}
        candidates = eligible[eligible["ticker"].eq(event.ticker) & eligible["project_id"].eq(event.project_id)]
        event_day = pd.Timestamp(event.event_date).normalize()
        earlier = candidates["report_day"].lt(event_day)
        if pd.notna(event.event_datetime):
            event_time = pd.Timestamp(event.event_datetime)
            if event_time.tzinfo is None:
                event_time = event_time.tz_localize("Europe/Warsaw")
            earlier |= candidates["report_day"].eq(event_day) & candidates["publication_time"].lt(event_time)
        candidates = candidates.loc[earlier]
        if not candidates.empty:
            latest_day = candidates[candidates["report_day"].eq(candidates["report_day"].max())]
            reports = latest_day.drop_duplicates("report_id")
            if len(reports) > 1 and reports["publication_time"].notna().all():
                reports = reports[reports["publication_time"].eq(reports["publication_time"].max())]
            if len(reports) == 1:
                report = reports.iloc[0]
                spans = latest_day[latest_day["report_id"].eq(report["report_id"])]
                count = spans[["n_words", "n_positive", "n_negative"]].sum()
                row.update({
                    "link_status": "linked", "report_id": report["report_id"],
                    "publication_date": report["publication_date"], "published_at": report["published_at"],
                    "publication_source_url": report["publication_source_url"], "n_passages": len(spans),
                    **count.to_dict(),
                    "tone_per_100_words": 100 * (count["n_positive"] - count["n_negative"]) / count["n_words"],
                })
            else:
                row["link_status"] = "ambiguous_publications"
        rows.append(row)
    return pd.DataFrame(rows, columns=columns)


def bootstrap_tone_model(analysis: pd.DataFrame, replicates: int = 1000) -> dict:
    """Fit issuer/decision effects and two tone slopes, resampling whole reports."""
    sample = analysis.dropna(subset=["adverse_revision", "tone_per_100_words", "car", "report_id"])
    reports_by_group = sample.groupby("adverse_revision")["report_id"].nunique()
    coverage = {"n_observations": len(sample), "n_reports": sample["report_id"].nunique(),
                "reports_adverse": int(reports_by_group.get(True, 0)),
                "reports_other": int(reports_by_group.get(False, 0))}
    if min(coverage["reports_adverse"], coverage["reports_other"]) < 2:
        return {"status": "insufficient_independent_reports", **coverage}
    adverse = sample["adverse_revision"].to_numpy(dtype=bool)
    tone = sample["tone_per_100_words"].to_numpy(dtype=float)
    factors = pd.get_dummies(sample[["ticker", "decision_type"]], drop_first=True, dtype=float)
    # The adverse level effect may be collinear with the decision category. The effect
    # cannot be added in that case, but the two within-group slopes can still be identified.
    base = np.column_stack([np.ones(len(sample)), factors.to_numpy()])
    with_adverse = np.column_stack([base, adverse])
    if np.linalg.matrix_rank(with_adverse) > np.linalg.matrix_rank(base):
        base = with_adverse
    design = np.column_stack([base, tone * adverse, tone * ~adverse])
    target = sample["car"].to_numpy(dtype=float)
    if len(sample) <= design.shape[1]:
        return {"status": "too_few_observations_for_fixed_effects", **coverage}
    coefficients, _, rank, _ = np.linalg.lstsq(design, target, rcond=None)
    if rank != design.shape[1]:
        return {"status": "unidentified_model", **coverage}
    groups = list(sample.reset_index(drop=True).groupby("report_id", sort=True).indices.values())
    random = np.random.default_rng(42)
    boot = []
    for indices in random.integers(0, len(groups), size=(replicates, len(groups))):
        rows = np.concatenate([groups[index] for index in indices])
        estimates, _, rank, _ = np.linalg.lstsq(design[rows], target[rows], rcond=None)
        if rank == design.shape[1]:
            boot.append(estimates[-2:])
    if len(boot) < replicates * 0.8:
        return {"status": "unstable_bootstrap", "valid_bootstrap": len(boot),
                "requested_bootstrap": replicates, **coverage}
    intervals = np.quantile(np.asarray(boot), [0.025, 0.975], axis=0)
    return {"status": "estimated", **coverage, "bootstrap_unit": "report_id",
            "valid_bootstrap": len(boot), "requested_bootstrap": replicates,
            "tone_adverse": {"coefficient": float(coefficients[-2]), "ci95": intervals[:, 0].tolist()},
            "tone_other": {"coefficient": float(coefficients[-1]), "ci95": intervals[:, 1].tolist()}}


def build_current_analysis() -> None:
    output = DATA_ROOT / "processed" / "analytical"
    output.mkdir(parents=True, exist_ok=True)
    scope = load_study_scope()
    start, end = map(pd.Timestamp, (scope["period"]["start"], scope["period"]["end"]))
    events = pd.read_parquet(EVENTS / f"investment_events_{start.year}_{end.year}.parquet")
    passages = pd.read_parquet(PASSAGE_SCORES)
    links = build_event_report_links(events, passages)
    links.to_parquet(CORPUS / "event_report_links.parquet", index=False)
    cars = pd.read_parquet(DATA_ROOT / "processed" / "event_study" / "car_results.parquet")
    cars = cars[cars["window"].eq("[-1+1]")]
    results = events.merge(links, on="event_id", validate="one_to_one").merge(
        cars[["event_id", "scenario", "car", "n_ar", "overlap", "status"]],
        on="event_id", how="left", validate="one_to_many",
    )
    results.to_parquet(output / "investment_analysis.parquet", index=False)
    queue = pd.read_csv(EVENTS / "espi_review_queue.csv", usecols=["review_status"])
    pending = int(queue["review_status"].eq("needs_review").sum())
    validation_path = VALIDATION / "validation_status.json"
    validation = json.loads(validation_path.read_text(encoding="utf-8")) if validation_path.exists() else {}
    if not set(passages["lexicon_version"]).issubset({validation.get("lexicon_version")}):
        validation = {"status": "lexicon_version_mismatch"}
    complete = results[results["status"].eq("complete") & results["n_ar"].eq(3)]
    diagnostics = {
        "confirmed_events": len(events), "unreviewed_communications": pending,
        "events_with_linked_report": int(links["link_status"].eq("linked").sum()),
        "events_with_complete_car": int(complete["event_id"].nunique()),
        "validation_status": validation.get("status", "pending_review"),
        "models": {},
    }
    for scenario in ("baseline", "same_session"):
        selected = complete[complete["scenario"].eq(scenario)]
        for without_overlap in (False, True):
            sample = selected if not without_overlap else selected[selected["overlap"].eq(False)]
            key = f"{scenario}_{'without_overlaps' if without_overlap else 'all'}"
            if pending or diagnostics["validation_status"] != "evaluated":
                diagnostics["models"][key] = {
                    "status": "awaiting_screening_or_validation",
                    "n_available": len(sample.dropna(subset=["report_id", "adverse_revision", "tone_per_100_words"])),
                }
            else:
                diagnostics["models"][key] = bootstrap_tone_model(sample)
    (output / "investment_analysis_status.json").write_text(
        json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8",
    )
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Join investment events to earlier verified reports and CAR.")
    parser.add_argument("--legacy", action="store_true", help="Regenerate the archived quarterly analysis.")
    if parser.parse_args().legacy:
        legacy_main()
    else:
        build_current_analysis()
