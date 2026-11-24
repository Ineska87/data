import csv
import json
import re
from pathlib import Path

WORK = Path(__file__).parent
OUT = Path("data/processed/thesis_outputs")
NAMES = {
    "Tabela_1a_walidacja_klasy": ("1a Walidacja klas",
        "Precyzja bez przewidzianej klasy jest niezdefiniowana. W arkuszu takie pole jest puste."),
    "Tabela_1b_walidacja_ogolem": ("1b Wyniki walidacji",
        "Próg dobrano na kalibracji N = 108. Test obejmuje tę samą próbę N = 100 dla obu słowników."),
    "Tabela_1c_struktura_proby": ("1c Struktura próby",
        "Raport liczy się raz w danej grupie. Raporty wspólne dla kilku grup uwzględnia się w każdej z nich."),
    "Tabela_1d_wykaz_zdarzen": ("1d Zdarzenia i raporty",
        "Dostępność tonu dotyczy ścisłego dopasowania projektu w raporcie przypisanym przed ESPI."),
    "Tabela_2_car": ("2 Statystyki CAR",
        "Bieżący plik wyników zawiera wyłącznie okno [−1,+1]. Testy t i Wilcoxona są dwustronne."),
    "Tabela_2b_testy": ("2b Różnice między grupami",
        "Test Manna–Whitneya porównuje rangi. Odczyt jako różnica median wymaga porównywalnego kształtu rozkładów."),
    "Tabela_3_modele": ("3 Porównanie modeli",
        "M1 i M2 używają ścisłych fragmentów projektu. M3 dodatkowo używa ogólnej narracji CAPEX w brakujących przypadkach."),
    "Tabela_4_olefiny_iii": ("4 Studium Olefiny III",
        "CAPEX porównuj w granicach wskazanego zakresu. CAR opisuje reakcję rynku wokół publikacji ESPI."),
    "extended_capex_passages": ("M3 Fragmenty CAPEX",
        "Zakresy znaków są półotwarte i liczone od zera w tekście z manifestu korpusu."),
}


def cell_value(cell):
    if not cell:
        return None
    timestamp = re.fullmatch(r"(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})([+-]\d{2}:\d{2})", cell)
    if timestamp:
        # Explicit offset prevents the spreadsheet importer from converting GPW time to UTC.
        return f"{timestamp[1]} {timestamp[2]} (UTC{timestamp[3]})"
    if re.fullmatch(r"[+-]?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[Ee][+-]?[0-9]+)?", cell):
        return float(cell) if "." in cell or "e" in cell.lower() else int(cell)
    return cell


worksheets = []
sources = sorted(OUT.glob("*.csv"), key=lambda f: (f.stem.startswith("extended_"), f.stem.replace("Tabela_2_", "Tabela_2a_")))
for path in sources:
    stem = path.stem
    name, note = NAMES.get(stem, (stem.replace("Tabela_", "").replace("_", " ")[:31], ""))
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        columns = next(reader)
        rows = [[cell_value(c) for c in row] for row in reader]
    assert len(set(columns)) == len(columns) and all(len(row) == len(columns) for row in rows), path
    markdown = path.with_suffix(".md")
    title = markdown.read_text(encoding="utf-8-sig").splitlines()[0].lstrip("# ").strip() if markdown.exists() else name
    worksheets.append({"name": name, "title": title, "note": note, "id": stem, "columns": columns, "rows": rows})
assert len({x["name"].casefold() for x in worksheets}) == len(worksheets)
(WORK / "workbook_input.json").write_text(json.dumps(worksheets, ensure_ascii=False), encoding="utf-8")
