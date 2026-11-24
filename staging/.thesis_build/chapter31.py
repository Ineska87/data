import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


DATA = Path("data")
OUT = DATA / "processed/thesis_outputs"
sys.path.insert(0, str(DATA / "scripts"))
from investment_sentiment import load_lexicon, passage_tones, tone_class, validation_metrics


def write_table(frame, name, title, note, percents=()):
    frame.to_csv(OUT / f"{name}.csv", index=False, encoding="utf-8-sig")
    header = list(frame)
    lines = [f"# {title}", "", "| " + " | ".join(header) + " |",
             "| " + " | ".join("---" for _ in header) + " |"]
    for row in frame.itertuples(index=False, name=None):
        cells = []
        for field, value in zip(header, row):
            if pd.isna(value):
                cell = "—"
            elif field in percents:
                cell = f"{value:.1%}".replace(".", ",")
            elif isinstance(value, float):
                cell = f"{value:.3f}".replace(".", ",")
            else:
                cell = str(value).replace("|", r"\|")
            cells.append(cell)
        lines.append("| " + " | ".join(cells) + " |")
    (OUT / f"{name}.md").write_text("\n".join(lines + ["", note, ""]), encoding="utf-8")


def validation():
    validation_dir = DATA / "processed/sentiment/validation"
    blind = pd.read_csv(validation_dir / "validation_blind.csv", dtype=str, keep_default_na=False)
    status = json.loads((validation_dir / "validation_status.json").read_text(encoding="utf-8"))
    comparison = status["holdout_comparison"]
    assert status["status"] == "evaluated" and status["reviewed_calibration"] == 108
    assert len(blind) == 100 and blind["item_id"].is_unique
    pool = pd.read_csv(DATA / "metadata/sentiment_validation_pool.csv")
    manifest = pd.read_csv(DATA / "processed/corpus/report_manifest.csv", keep_default_na=False)
    available = pool[pool["split"].eq("holdout")].copy()
    available["item_id"] = [
        hashlib.sha256(f"{r.document_id}:{r.start_char}:{r.end_char}".encode()).hexdigest()[:16]
        for r in available.itertuples(index=False)
    ]
    available = available.merge(manifest[["document_id", "ticker", "text_path"]], validate="many_to_one")
    sample = blind.merge(available, on="item_id", how="left", validate="one_to_one")
    assert sample["ticker"].notna().all() and sample["ticker"].eq("JSW").sum() == 15
    assert set(sample["ticker"]) == {"PKN", "PGE", "TPE", "ENA", "ZEP", "UNT", "JSW"}
    for document in sample.itertuples(index=False):
        source = (DATA / document.text_path).read_text(encoding="utf-8")
        assert source[document.start_char:document.end_char] == document.text
    names = {"negative": "Negatywna", "neutral": "Neutralna", "positive": "Pozytywna"}
    paths = {"investment-pl-0.1": "investment_tone_lexicon_v0.1.json",
             "investment-pl-0.2": "investment_tone_lexicon.json"}
    rows, summary = [], []
    for version, path in paths.items():
        expected = comparison[version]
        cutoff = expected["neutral_cutoff"]
        lexicon = load_lexicon(DATA / "metadata" / path)
        assert lexicon["version"] == version
        score = passage_tones(sample[["text"]].to_dict("records"), lexicon)
        for subset, mask in [
            ("Cała próba", np.ones(len(sample), dtype=bool)),
            ("Spółki badane", sample["ticker"].ne("JSW").to_numpy()),
            ("JSW – poza próbą spółek", sample["ticker"].eq("JSW").to_numpy()),
        ]:
            actual = sample.loc[mask, "reviewer_label"].tolist()
            predicted = [tone_class(s, cutoff) for s in score[mask]]
            metrics = validation_metrics(score[mask], actual, cutoff)
            assert sum(r["support"] for r in metrics) == len(actual)
            accuracy = sum(a == b for a, b in zip(actual, predicted)) / len(actual)
            chance = sum(m["support"] * m["predicted"] for m in metrics) / len(actual) ** 2
            kappa = (accuracy - chance) / (1 - chance)
            macro = np.mean([m["f1"] or 0.0 for m in metrics])
            if subset == "Cała próba":
                assert metrics == expected["holdout_metrics"]
                assert np.isclose(macro, expected["macro_f1"]) and accuracy == expected["accuracy"]
            summary.append([subset, version, len(actual), cutoff, macro, accuracy, kappa])
            for item in metrics:
                rows.append([subset, version, len(actual), names[item["label"]], item["support"],
                             item["predicted"], item["precision"], item["recall"], item["f1"]])
    classes = pd.DataFrame(rows, columns=["Zakres walidacji", "Słownik", "N próby", "Klasa",
                                         "Liczebność klasy", "Przewidziane", "Precyzja", "Czułość", "F1"])
    total = pd.DataFrame(summary, columns=["Zakres walidacji", "Słownik", "N próby", "Próg neutralności",
                                           "Makro-F1", "Trafność", "Kappa Cohena"])
    order = {"Cała próba": 0, "Spółki badane": 1, "JSW – poza próbą spółek": 2}
    for table in (classes, total):
        table.sort_values("Zakres walidacji", key=lambda labels: labels.map(order), kind="stable", inplace=True)
    write_table(classes, "Tabela_1a_walidacja_klasy", "Tabela 1a. Walidacja słowników według klas",
                "Próbę łączną N = 100 rozbito na 85 fragmentów spółek badanych i 15 fragmentów JSW. "
                "Kreska oznacza brak mianownika, np. gdy słownik nie przewidział danej klasy.",
                ("Precyzja", "Czułość"))
    write_table(total, "Tabela_1b_walidacja_ogolem", "Tabela 1b. Wyniki ogólne walidacji słowników",
                "Progi pochodzą z próby kalibracyjnej N = 108. W makro-F1 każda z trzech klas ma równą wagę. "
                "Kappa Cohena uwzględnia zgodność oczekiwaną z rozkładów brzegowych.", ("Trafność",))
    print(total.to_string(index=False))


def structure():
    issuer = {"PKN": "ORLEN", "PGE": "PGE", "TPE": "TAURON", "ENA": "Enea", "ZEP": "ZE PAK", "UNT": "UNIMOT"}
    decisions = {"start": "Rozpoczęcie", "revision": "Rewizja", "suspension": "Wstrzymanie"}
    groups = {"yes": "Tak", "no": "Nie", "unknown": "Nieustalona"}
    events = pd.read_csv(DATA / "processed/events/investment_events_2020_2025.csv", dtype=str)
    links = pd.read_parquet(DATA / "processed/corpus/event_report_links.parquet")
    data = events.merge(links[["event_id", "reference_report_id", "link_status"]], validate="one_to_one")
    data["adverse_revision"] = data["revision_subgroup"].map(
        {"other": "no", "adverse": "yes", "undetermined": "unknown"}
    )
    assert len(data) == 33 and data["reference_report_id"].notna().all()
    assert data["adverse_revision"].value_counts().to_dict() == {"no": 15, "yes": 13, "unknown": 5}
    assert data["decision_type"].value_counts().to_dict() == {"start": 15, "revision": 13, "suspension": 5}
    data["Rok"] = data["event_date"].str[:4].astype(int)
    data["Ton dostępny"] = data["link_status"].eq("linked")
    data["Próba M1"] = data["Ton dostępny"] & data["adverse_revision"].ne("unknown")
    assert data["reference_report_id"].nunique() == 29 and data["Próba M1"].sum() == 17

    def count(set_):
        return [len(set_), set_["reference_report_id"].nunique(), int(set_["Ton dostępny"].sum()),
                int(set_["Próba M1"].sum())]

    rows = [["Łącznie", "Wszystkie decyzje", *count(data)]]
    for column, dimension, names in [
        ("ticker", "Spółka", issuer),
        ("Rok", "Rok zdarzenia", {i: str(i) for i in range(2020, 2026)}),
        ("decision_type", "Typ decyzji", decisions),
        ("adverse_revision", "Niekorzystna korekta", groups),
    ]:
        for code, label in names.items():
            rows.append([dimension, label, *count(data[data[column].eq(code)])])
    frame = pd.DataFrame(rows, columns=["Przekrój", "Pozycja", "Zdarzenia", "Odrębne raporty",
                                        "Zdarzenia z tonem projektu", "Zdarzenia w M1"])
    write_table(frame, "Tabela_1c_struktura_proby", "Tabela 1c. Struktura 33 zatwierdzonych zdarzeń",
                "Liczebność raportów oznacza unikalne edycje w danym przekroju. Jeden raport może wystąpić "
                "w kilku wierszach. Zdarzenia o nieustalonym kierunku korekty mają CAR i pozostają poza M1.")
    detail = data.assign(Spółka=data["ticker"].map(issuer), Decyzja=data["decision_type"].map(decisions),
                         Korekta=data["adverse_revision"].map(groups))
    detail.sort_values(["event_date", "event_id"], inplace=True)
    detail = detail[["event_id", "Spółka", "event_date", "Rok", "Decyzja", "Korekta", "reference_report_id",
                     "Ton dostępny", "Próba M1"]].rename(columns={"event_id": "ESPI", "event_date": "Data",
                                        "Korekta": "Niekorzystna korekta", "reference_report_id": "Raport odniesienia"})
    for name in ("Ton dostępny", "Próba M1"):
        detail[name] = detail[name].map({True: "Tak", False: "Nie"})
    write_table(detail, "Tabela_1d_wykaz_zdarzen", "Tabela 1d. Wykaz zdarzeń i raportów odniesienia",
                "Wykaz pozwala odtworzyć wszystkie przekroje próby i sprawdzić wielokrotne użycie raportu.")


if __name__ == "__main__":
    validation()
    structure()
