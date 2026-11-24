import hashlib
import itertools
import json
import math
import re
import sys
from pathlib import Path

import fitz
import numpy as np
import pandas as pd
from scipy import stats

data = Path("data").resolve()
work = data / "staging/.thesis_build"
out = data / "processed/thesis_outputs"
out.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(data / "scripts"))
from investment_sentiment import load_lexicon, score_passage


def sha(content):
    return hashlib.sha256(content).hexdigest()


def anchored(text, beginning, ending):
    # Match anchors across line wrapping without changing the stored offsets.
    def pattern(anchor):
        return r"\s+".join(re.escape(part) for part in anchor.split())

    lo = re.search(pattern(beginning), text).start()
    occurrence = re.search(pattern(ending), text[lo:])
    stop = lo + occurrence.end()
    return lo, stop, text[lo:stop].strip()


current = pd.read_parquet(data / "processed/analytical/investment_analysis.parquet")
current = current.loc[
    current.scenario.eq("baseline") & current.status.eq("complete") & current.n_ar.eq(3)
    & current.adverse_revision.notna()
].copy()
current["adverse_revision"] = current.adverse_revision.map({True: "yes", False: "no"})
current = current.set_index("event_id").sort_index()
original = current.loc[current.link_status.eq("linked")].copy()
assert len(current) == 28 and len(original) == 17
missing = current.loc[~current.index.isin(original.index)]
manifest = pd.read_csv(data / "processed/corpus/report_manifest.csv", keep_default_na=False)
manifest = manifest.set_index("document_id")
refs = pd.read_csv(data / "raw/reports/publication_archive/event_periodic_references.csv",
                   keep_default_na=False).set_index("event_id")
lex_file = data / "metadata/investment_tone_lexicon.json"
lex = load_lexicon(lex_file)
assert lex["version"] == "investment-pl-0.2"

local_sources = {
    "PKN-2021-H1": ("PKN_2021_H1_sprawozdanie__narrative",
        "Na 2030 rok PKN ORLEN przyjął następujące cele finansowe i operacyjne:",
        "ponad 3 500 stacji paliw i ponad 1 000 stacji szybkiego ładowania samochodów elektrycznych.",
        "Strategia Grupy ORLEN do 2030 r. — cele ilościowe i łączny CAPEX",
        "narracja, w. 545–557"),
    "PKN-2022-Q1": ("PKN_2022_Q1_sprawozdanie__narrative",
        "Budowa ponad 100 ogólnodostępnych",
        "zewnętrznego finansowania, w tym bezzwrotnego, związanego z innowacjami i transformacją energetyczną.",
        "Strategia wodorowa — portfel inwestycji w moce i infrastrukturę",
        "narracja, w. 272–284"),
    "PKN-2022-Q3": ("PKN_2022_Q3_sprawozdanie__narrative",
        "Strony Porozumienia przewidują, że po połączeniu Spółki z Grupą LOTOS kontynuowane będą kluczowe inwestycje",
        "Gdańsku.",
        "Program kontynuacji inwestycji po połączeniu z Grupą LOTOS",
        "narracja, w. 496–505"),
    "PKN-2023-Q1": ("PKN_2023_Q1_sprawozdanie",
        "Seria A euroobligacji PKN ORLEN o wartości nominalnej 500 mln EUR",
        "stopnia ich realizacji oraz ich wpływu na środowisko.",
        "Plany inwestycji transformacyjnych w ramach zielonego finansowania",
        "s. 38, sekcja 5.12, w. 6210–6214"),
}

supplements = {
    "TPE-2024-Q3": (8, "W odpowiedzi na wyzwania wynikające z sytuacji na rynku",
        "ocenie ich uzasadnienia biznesowego.",
        "Realizacja inwestycji strategicznych — strategia i portfel fotowoltaiki",
        "https://www.tauron.pl/-/media/offer-documents/tauron/raporty-okresowe/2024/iii-kwartal/tauron-pe-pozostale-informacje-do-raportu-gkt-za-iii-kwartal-2024-r.ashx"),
    "TPE-2025-Q3": (41, "Realizacja naszych inwestycji strategicznych przebiega zgodnie z planem.",
        "To konkretne kroki w stronę nowoczesnej, niskoemisyjnej energetyki.",
        "Realizacja inwestycji strategicznych — wypowiedź wiceprezesa ds. majątku i rozwoju",
        "https://pap-mediaroom.pl/sites/default/files/attachments/202511/DOC.20251119.52925095.zal02_TAURON_PE_pozostale_informacje_do_raportu_za_III_kwartal__2025_r.pdf"),
    "ZEP-2021-Q1": (12, "W 2020 roku Grupa ZE PAK SA rozpoczęła",
        "i wytwórczych.",
        "Realizacja programu inwestycyjnego — portfel biomasy, PV i wodoru",
        "https://ri.zepak.com.pl/upload/files/ZEPAK_2021-1Q_POZOSTAE_INFORMACJE_publikacja-sig-sig-sig-sig-sig.pdf"),
    "ZEP-2021-Q3": (14, "W trzecim kwartale 2021 roku Grupa ZE PAK SA kontynuowała",
        "i wytwórczych.",
        "Realizacja programu inwestycyjnego — portfel biomasy, PV, wodoru i kolejnych OZE",
        "https://ri.zepak.com.pl/upload/files/ZEPAK_2021-3Q_POZOSTAE_INFORMACJE_2-sig-sig-sig-sig-sig.pdf"),
    "ZEP-2022-Q3": (16, "W III kwartale 2022 roku aktywność inwestycyjna Grupy ZE PAK SA",
        "wytwórczych.",
        "Realizacja programu inwestycyjnego — portfel wiatrowy i wodorowy oraz prace przygotowawcze",
        "https://ri.zepak.com.pl/upload/files/zepak_2022-3q_pozostae_informacje-sig-sig_signed.pdf"),
}

extended = []
for event_id, event in missing.iterrows():
    ref = refs.loc[event_id]
    report_id = event.reference_report_id
    assert report_id == ref.reference_report_id
    assert pd.Timestamp(ref.report_published_at).date() < event.event_date.date()
    if report_id in local_sources:
        identifier, beginning, ending, subject, locator = local_sources[report_id]
        entry = manifest.loc[identifier]
        assert entry.report_id == report_id and entry.extract_status == "ok"
        text_path = entry.text_path
        text = (data / text_path).read_text(encoding="utf-8")
        url = entry.source_url
        pdf_hash, page, basis = "", "", "Tekst z manifestu korpusu, pełny plik"
    else:
        page, beginning, ending, subject, url = supplements[report_id]
        identifier = report_id.replace("-", "_") + "_pozostale-informacje"
        source = work / "model_sources" / (identifier + ".pdf")
        with fitz.open(source) as pdf:
            text = pdf[page - 1].get_text(sort=True)
            displayed_page = page - (1 if report_id.startswith("TPE") else 0)
        pdf_hash = sha(source.read_bytes())
        text_path = ""
        locator = f"Pozostałe informacje, s. {displayed_page}, strona PDF {page}"
        basis = f"Tekst strony PDF, PyMuPDF {fitz.__version__}, get_text(sort=True)"
    start, end, fragment = anchored(text, beginning, ending)
    scores = score_passage(fragment, lex)
    assert scores["n_words"] >= 45
    extended.append({
        "event_id": event_id, "ticker": event.ticker, "project_id": event.project_id,
        "reference_report_id": report_id, "adverse_revision": event.adverse_revision,
        "publication_at": ref.report_published_at, "document_id": identifier,
        "source_locator": locator, "source_url": url, "text_path": text_path,
        "text_basis": basis, "pdf_page": page, "pdf_sha256": pdf_hash,
        "text_sha256": sha(text.encode("utf-8")), "start_char": start, "end_char": end,
        "zakres_narracji": subject, "lexicon_version": lex["version"], **scores,
        "fragment_tekstu": fragment,
    })
extended = pd.DataFrame(extended)
assert len(extended) == 11 and extended.reference_report_id.nunique() == 9
extended.to_csv(out / "extended_capex_passages.csv", index=False, encoding="utf-8-sig")
expanded = current.copy()
expanded["source"] = np.where(expanded.index.isin(original.index), "exact", "broad")
tone_column = "tone_per_100_words"
expanded.loc[missing.index, tone_column] = extended.set_index("event_id")[tone_column]
assert expanded[tone_column].notna().all()
plot_cols = ["ticker", "reference_report_id", "adverse_revision", tone_column, "car", "source"]
expanded[plot_cols].to_csv(work / "proba_m3.csv", index_label="event_id", encoding="utf-8-sig")


def design_matrix(sample, use_effects):
    yes = sample.adverse_revision.eq("yes").astype(float)
    tone = sample[tone_column]
    columns = {"const": np.ones(len(sample))}
    if use_effects:
        factors = pd.get_dummies(sample[["ticker", "decision_type"]], drop_first=True, dtype=float)
        columns.update({f: factors[f] for f in factors})
        controls = np.column_stack(list(columns.values()))
        if np.linalg.matrix_rank(np.column_stack((controls, yes))) > np.linalg.matrix_rank(controls):
            columns["adverse"] = yes
    else:
        columns["adverse"] = yes
    columns["tone_yes"] = tone * yes
    columns["tone_no"] = tone * (1 - yes)
    return pd.DataFrame(columns, index=sample.index)


SLOPES = ("tone_yes", "tone_no")


def identifiable(x, column, rank):
    return rank > np.linalg.matrix_rank(np.delete(x, column, axis=1))


def fit_sample(sample, use_effects):
    design = design_matrix(sample, use_effects)
    names = list(design)
    x, y = design.to_numpy(dtype=float), sample.car.to_numpy(dtype=float)
    rank = np.linalg.matrix_rank(x)
    beta = np.linalg.pinv(x) @ y
    residuals = y - x @ beta
    inverse = np.linalg.pinv(x)
    leverage = np.einsum("ij,ji->i", x, inverse)
    unit_leverage = np.isclose(leverage, 1)
    clusters = list(sample.groupby("reference_report_id", sort=True).indices.values())
    n_draws = 1000
    draws = np.random.default_rng(42).integers(len(clusters), size=(n_draws, len(clusters)))
    estimates = {term: [] for term in SLOPES}
    full_rank_draws = 0
    for draw in draws:
        selection = np.concatenate([clusters[g] for g in draw])
        sub = x[selection]
        subrank = np.linalg.matrix_rank(sub)
        if subrank == len(names):
            full_rank_draws += 1
        partial_beta = np.linalg.lstsq(sub, y[selection], rcond=None)[0]
        for term in SLOPES:
            col = names.index(term)
            if identifiable(sub, col, subrank):
                estimates[term].append(float(partial_beta[col]))

    results = {}
    for name in names:
        col = names.index(name)
        if not identifiable(x, col, rank):
            results[name] = {"coef": None, "se": None, "p": None}
            continue
        # Observations with leverage 1 give an undefined HC3 correction when
        # the coefficient depends on them. Zero loadings contribute nothing.
        hc3_undefined = bool(np.any(unit_leverage & ~np.isclose(inverse[col], 0)))
        scaled = residuals[~unit_leverage] / (1 - leverage[~unit_leverage])
        se = None if hc3_undefined else float(np.linalg.norm(inverse[col, ~unit_leverage] * scaled))
        p = None if not se else float(2 * stats.t.sf(abs(beta[col]) / se, len(sample) - rank))
        results[name] = {"coef": float(beta[col]), "se": se, "p": p}

    for term in SLOPES:
        col = names.index(term)
        pivotal = []
        if results[term]["coef"] is not None:
            for g in clusters:
                remainder = np.delete(x, g, axis=0)
                if not identifiable(remainder, col, np.linalg.matrix_rank(remainder)):
                    pivotal.append(sample.iloc[g[0]].reference_report_id)
        stable = results[term]["coef"] is not None and not pivotal and len(estimates[term]) >= 800
        results[term].update(valid=len(estimates[term]), pivotal=pivotal)
        results[term]["ci95"] = (np.quantile(estimates[term], [0.025, 0.975]).tolist()
                                    if stable else None)
    return {"n": len(sample), "clusters": len(clusters), "rank": int(rank), "p_cols": len(names),
            "df": len(sample) - int(rank), "full_rank": full_rank_draws,
            "unit_leverage": sample.index[unit_leverage].tolist(), "terms": results,
            "n_yes": int(sample.adverse_revision.eq("yes").sum()),
            "n_no": int(sample.adverse_revision.eq("no").sum())}


m1_names = ("M1 · bazowy", "M2 · oszczędny", "M3a · kontekst CAPEX", "M3b · CAPEX + efekty stałe")
models = {
    m1_names[0]: fit_sample(original, True),
    m1_names[1]: fit_sample(original, False),
    m1_names[2]: fit_sample(expanded, False),
    m1_names[3]: fit_sample(expanded, True),
}
base = json.loads((data / "processed/analytical/investment_analysis_status.json").read_text(
    encoding="utf-8"))["models"]["baseline_all"]
assert np.isclose(models[m1_names[0]]["terms"]["tone_yes"]["coef"], base["tone_adverse"]["coefficient"])
assert models[m1_names[0]]["terms"]["tone_no"]["coef"] == base["tone_other"]["coefficient"]
assert models[m1_names[0]]["terms"]["tone_yes"]["valid"] == base["tone_adverse"]["valid_bootstrap"]

x, y = (original.loc[original.adverse_revision.eq("yes"), c].to_numpy()
        for c in (tone_column, "car"))
assert len(x) == 12
rho = stats.spearmanr(x, y)
tau = stats.kendalltau(x, y, variant="b")
assert np.count_nonzero(x) == 1
point = int(np.flatnonzero(x)[0])
x_permuted = [np.roll(x, i - point) for i in range(len(x))]
permuted_rho = np.array([stats.spearmanr(a, y).statistic for a in x_permuted])
permuted_tau = np.array([stats.kendalltau(a, y, variant="b").statistic for a in x_permuted])
rank_tests = {
    "Spearman": {"estimate": float(rho.statistic),
                 "p": float(np.mean(np.abs(permuted_rho) >= abs(rho.statistic) - 1e-12)),
                 "p_asymptotic": float(rho.pvalue)},
    "Kendall": {"estimate": float(tau.statistic),
                "p": float(np.mean(np.abs(permuted_tau) >= abs(tau.statistic) - 1e-12)),
                "p_asymptotic": float(tau.pvalue)},
}


def percent(value):
    return None if value is None else round(100 * value, 4)


records = []


def row(label, generator):
    records.append({"Miara": label, **{name: generator(v, i) for i, (name, v) in enumerate(models.items())}})


row("Próba zdarzeń", lambda v, i: "Ścisłe dopasowanie" if i < 2 else "Ścisłe dopasowanie + kontekst CAPEX")
row("Efekty stałe spółki i typu decyzji", lambda v, i: "Tak" if i in {0, 3} else "Nie")
row("Liczba zdarzeń", lambda v, i: v["n"])
row("Niekorzystne korekty (yes)", lambda v, i: v["n_yes"])
row("Pozostałe zdarzenia (no)", lambda v, i: v["n_no"])
row("Liczba odrębnych raportów", lambda v, i: v["clusters"])
row("Stopnie swobody reszt", lambda v, i: v["df"])
row("Rząd macierzy / liczba kolumn", lambda v, i: f'{v["rank"]}/{v["p_cols"]}')
row("Pełny rząd w bootstrapie, liczba na 1000", lambda v, i: v["full_rank"])
row("Pełny rząd w bootstrapie, odsetek (%)", lambda v, i: round(v["full_rank"] / 10, 1))

for label, term in [("Niekorzystne korekty (yes)", "tone_yes"), ("Pozostałe zdarzenia (no)", "tone_no")]:
    row(f"{label} · współczynnik tonu (p.p.)", lambda v, i: percent(v["terms"][term]["coef"]))
    row(f"{label} · błąd standardowy HC3 (p.p.)", lambda v, i: None if i == 0 else percent(v["terms"][term]["se"]))
    row(f"{label} · p-value HC3", lambda v, i: None if i == 0 or v["terms"][term]["p"] is None else round(v["terms"][term]["p"], 4))
    row(f"{label} · identyfikowalne losowania na 1000", lambda v, i: v["terms"][term]["valid"])
    row(f"{label} · dolna granica 95% PU bootstrap (p.p.)",
        lambda v, i: None if v["terms"][term]["ci95"] is None else percent(v["terms"][term]["ci95"][0]))
    row(f"{label} · górna granica 95% PU bootstrap (p.p.)",
        lambda v, i: None if v["terms"][term]["ci95"] is None else percent(v["terms"][term]["ci95"][1]))
for label, term in [("Wyraz wolny", "const"), ("Wskaźnik niekorzystnej korekty", "adverse")]:
    row(f"{label} · współczynnik (p.p.)",
        lambda v, i: None if i in {0, 3} else percent(v["terms"][term]["coef"]))
    row(f"{label} · błąd HC3 (p.p.)",
        lambda v, i: None if i in {0, 3} else percent(v["terms"][term]["se"]))
row("Spearman ρ w grupie yes (n = 12)", lambda v, i: round(rank_tests["Spearman"]["estimate"], 4) if i == 1 else None)
row("Spearman · p-value dokładne permutacyjne", lambda v, i: round(rank_tests["Spearman"]["p"], 4) if i == 1 else None)
row("Kendall τ-b w grupie yes (n = 12)", lambda v, i: round(rank_tests["Kendall"]["estimate"], 4) if i == 1 else None)
row("Kendall · p-value dokładne permutacyjne", lambda v, i: round(rank_tests["Kendall"]["p"], 4) if i == 1 else None)

table = pd.DataFrame(records, dtype=object)
table.to_csv(out / "Tabela_3_modele.csv", index=False, encoding="utf-8-sig")
notes = """**Uwagi.** Zmienną zależną jest CAR[−1,+1] względem WIG w podstawowym wariancie dnia 0. Współczynniki i błędy wyrażono w punktach procentowych CAR na jednostkę tonu. Jednostka tonu to jedno dodatnie dopasowanie netto na 100 słów. M1 odtwarza model z pliku `processed/analytical/investment_analysis_status.json`, sekcja `models.baseline_all`. Efekty typu decyzji w M1 i M3b obejmują wskaźnik grupy korekty z uwagi na współliniowość. Grupa `unknown` pozostaje poza modelami.

Bootstrap par losuje z powtórzeniami 1000 prób całych raportów przy stałym ziarnie 42. Pełny rząd wymaga identyfikacji wszystkich kolumn oryginalnej specyfikacji. Osobno zliczono losowania identyfikujące dany współczynnik mimo zależności pozostałych kolumn. Przedział percentylowy 95% podano przy co najmniej 800 z 1000 identyfikowalnych losowań oraz gdy po usunięciu dowolnego pojedynczego raportu parametr pozostaje identyfikowalny. HC3 przy dźwigni równej jeden jest nieokreślony dla parametrów zależnych od tej obserwacji. W kolumnie M1 pokazano wniosek bazowej diagnostyki bootstrapu, a błędy HC3 podano dla wariantów M2, M3a i M3b z p-value względem rozkładu t o stopniach swobody reszt.

P-wartości korelacji rangowych są dwustronne, permutacyjne i dokładne przy jednej obserwacji o niezerowym tonie. Enumeracja obejmuje 12 możliwych przypisań tej wartości do obserwowanego CAR.

M3 zachowuje 17 ścisłych dopasowań i rozszerza próbę o 11 powiązań z ogólną narracją inwestycyjną z 9 raportów odniesienia. Ten sam fragment w jednym raporcie ma ten sam ton dla wszystkich zdarzeń uzupełnianych z tego raportu. Uzupełnienia mierzą tło inwestycyjne spółki, a zatem rozszerzenie zmienia zakres mierzonej narracji i skład próby. Raport może obejmować inne projekty niż komunikat, do którego przypisano kontekst.

Pięć uzupełnień ORLENU pochodzi z czterech raportów w manifeście korpusu. Pozostałe sześć pochodzi z pięciu oficjalnych załączników do raportów okresowych. Kolumna `fragment_tekstu` w `extended_capex_passages.csv` zawiera tekst przekazany do słownika. Początek zakresu liczy się od zera, a koniec wyłącza znak końcowy. Przy pliku z manifestu znaki liczy się od początku pełnego tekstu. Przy załączniku znaki liczy się od początku tekstu jednej strony PDF, odczytanego w kolejności wizualnej przez PyMuPDF `get_text(sort=True)`. Kolumna `pdf_page` numeruje strony pliku od 1. Wstawione przez ekstraktor złamania wierszy i wcięcia zachowano w fragmencie. Funkcja słownika v0.2 wykonuje własną normalizację podczas pomiaru tonu.
"""


def markdown_table(frame):
    def cell(value):
        if value is None or pd.isna(value):
            return "—"
        return str(value).replace(".", ",") if isinstance(value, float) else str(value)

    rows = ["| " + " | ".join(frame.columns) + " |", "| " + " | ".join(["---"] * len(frame.columns)) + " |"]
    rows.extend("| " + " | ".join(cell(x) for x in r) + " |" for r in frame.itertuples(index=False, name=None))
    return "\n".join(rows)


(out / "Tabela_3_modele.md").write_text(
    "# Tabela 3. Zależność między tonem wcześniejszego raportu a CAR[−1,+1]\n\n"
    + markdown_table(table) + "\n\n" + notes, encoding="utf-8"
)
m3a_terms = models[m1_names[2]]["terms"]
plot_coefficients = {
    "yes": {"intercept": m3a_terms["const"]["coef"] + m3a_terms["adverse"]["coef"],
            "slope": m3a_terms["tone_yes"]["coef"]},
    "no": {"intercept": m3a_terms["const"]["coef"], "slope": m3a_terms["tone_no"]["coef"]},
}
(work / "model_m3a.json").write_text(json.dumps(plot_coefficients, indent=2), encoding="utf-8")
(work / "models_stats.json").write_text(
    json.dumps({"models": models, "rank_tests": rank_tests}, ensure_ascii=False, indent=2),
    encoding="utf-8")
print(extended[["event_id", "reference_report_id", "n_words", tone_column]].to_string(index=False))
print(table.to_string(index=False))
