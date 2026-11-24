"""Synchronizuj lokalne arkusze ocen w Excelu z plikami roboczymi CSV."""

import argparse
import csv
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from tempfile import NamedTemporaryFile

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from build_events import CAPEX_SCOPES, DECISIONS, MILESTONES, TARGET_PERIOD, TRISTATE
from data_paths import DATA_ROOT
from publication_order import clock_interval


@dataclass(frozen=True)
class Field:
    description: str
    kind: str = "text"
    choices: tuple[str, ...] = ()


COMPARABILITY = tuple(code for code in ("yes", "no", "unknown") if code in TRISTATE)
SCOPES = tuple(sorted(CAPEX_SCOPES))
MILESTONE_TYPES = tuple(sorted(MILESTONES))
BLIND_FIELDS = {"reviewer_label": Field("Twoja ocena fragmentu.", choices=("positive", "neutral", "negative"))}
BLIND_COLUMNS = ("item_id", "text", "reviewer_label")
BLIND_HISTORY_COLUMNS = {"twoja_poprzednia_ocena", "zmieniono", "uzasadnienie_korekty"}
EVENT_FIELDS = {
    "manual_review_status": Field(
        "Kwalifikacja: uwzględnij, wyklucz lub pozostaw do dalszej weryfikacji.",
        choices=("include", "exclude", "needs_review"),
    ),
    "manual_project_id": Field("Stały identyfikator projektu. Używaj go także przy kolejnych rewizjach."),
    "manual_decision_type": Field(
        "Rozpoczęcie, rewizja albo wstrzymanie lub zakończenie inwestycji.", choices=tuple(DECISIONS),
    ),
    "manual_adverse_revision": Field(
        "yes: porównywalny koszt wzrósł, realizację opóźniono lub wstrzymano. no: brak niekorzystnej rewizji. "
        "unknown: podgrupa undetermined z CAR, poza główną regresją.", choices=COMPARABILITY,
    ),
    "manual_scope_comparable": Field("Czy oba plany dotyczą porównywalnego zakresu?", choices=COMPARABILITY),
    "manual_milestone_comparable": Field(
        "Czy porównujesz dwa terminy tego samego, ustalonego rodzaju?", choices=COMPARABILITY,
    ),
    "manual_first_public_plan_event_id": Field("Identyfikator najwcześniejszego udokumentowanego planu."),
    "manual_first_public_plan_url": Field("Adres źródła pierwszego publicznego planu.", "url"),
    "manual_first_public_plan_date": Field("Data publikacji pierwszego publicznego planu.", "date"),
    "manual_first_public_plan_time": Field("Godzina pierwszego planu w czasie lokalnym GPW.", "time"),
    "manual_first_public_plan_time_source_url": Field("Adres źródła potwierdzającego tę godzinę.", "url"),
    "manual_previous_plan_event_id": Field("Identyfikator zdarzenia, które ustanowiło aktualizowany plan."),
    "manual_previous_plan_url": Field("Adres źródła aktualizowanego planu.", "url"),
    "manual_previous_plan_date": Field("Data publikacji aktualizowanego planu.", "date"),
    "manual_previous_plan_time": Field("Godzina poprzedniego planu w czasie lokalnym GPW.", "time"),
    "manual_previous_plan_time_source_url": Field("Adres źródła potwierdzającego tę godzinę.", "url"),
    "manual_previous_capex": Field("Prognozowany CAPEX w poprzednim planie, w mln.", "amount"),
    "manual_new_capex": Field("Prognozowany CAPEX w nowym planie, w mln.", "amount"),
    "manual_capex_currency": Field("Kod waluty porównywanych prognoz CAPEX.", "currency"),
    "manual_previous_scope": Field("Zakres inwestycji objęty poprzednią prognozą.", choices=SCOPES),
    "manual_new_scope": Field("Zakres inwestycji objęty nową prognozą.", choices=SCOPES),
    "manual_previous_milestone_type": Field("Rodzaj kamienia milowego w poprzednim planie.", choices=MILESTONE_TYPES),
    "manual_new_milestone_type": Field("Rodzaj kamienia milowego w nowym planie.", choices=MILESTONE_TYPES),
    "manual_previous_milestone_date": Field("Termin w poprzednim planie, z precyzją źródła.", "period"),
    "manual_new_milestone_date": Field("Termin w nowym planie, z precyzją źródła.", "period"),
    "manual_actual_spend": Field("Faktycznie poniesione nakłady narastająco, w mln.", "amount"),
    "manual_actual_spend_currency": Field("Kod waluty faktycznie poniesionych nakładów.", "currency"),
    "manual_actual_spend_to": Field("Data, do której zsumowano faktycznie poniesione nakłady.", "date"),
    "manual_impairment": Field("Kwota odpisu aktualizującego aktywa w budowie, w mln.", "amount"),
    "manual_impairment_currency": Field("Kod waluty odpisu.", "currency"),
    "manual_impairment_period": Field("Okres ujęcia odpisu, z precyzją źródła.", "period"),
    "manual_comparison_source_url": Field("Adres źródła porównania planów lub danych inwestycyjnych.", "url"),
    "manual_coding_note": Field("Uzasadnij kwalifikację, zakres porównania i ewentualne braki w źródłach."),
}
FORMAT_GUIDE = {
    "text": "Tekst", "url": "Adres https:// lub http://", "date": "RRRR-MM-DD",
    "time": "GG:MM lub GG:MM:SS, zgodnie z precyzją źródła",
    "period": "RRRR, RRRR-Q1…Q4, RRRR-H1/H2, RRRR-MM lub RRRR-MM-DD",
    "amount": "Liczba ≥ 0 w mln, np. 14,1", "currency": "3 wielkie litery, np. PLN, EUR, USD",
}
EVENT_FRONT = (
    "event_id", "title", "manual_review_status", "manual_decision_type", "manual_adverse_revision",
    "espi_text", "periodic_excerpts", "reference_report_id", "newer_periodic_report_ids", "attachments",
    "prior_espi_references", "manual_coding_note",
)
TEXT_WIDTHS = {
    "item_id": 22, "text": 108, "reviewer_label": 22, "event_id": 19, "ticker": 11, "title": 41,
    "espi_text": 74, "periodic_excerpts": 68, "manual_coding_note": 42, "attachments": 34,
    "prior_espi_references": 37, "candidate_evidence": 38, "money_mentions": 34, "date_mentions": 34,
    "reference_local_files": 40, "eligible_corpus_documents": 40, "event_date": 14, "event_time": 13,
}
SOURCE_HEADER = PatternFill("solid", fgColor="24384A")
EDIT_HEADER = PatternFill("solid", fgColor="FFF2CC")
STRIPE = PatternFill("solid", fgColor="F3F6F8")
BODY = Font(name="Arial", size=10, color="23313C")
WRAPPED = Alignment(vertical="top", wrap_text=True)


@dataclass(frozen=True)
class Review:
    csv_path: Path
    key: str
    sheet_name: str
    fields: dict[str, Field]

    @property
    def blind(self):
        return self.key == "item_id"

    @property
    def xlsx_path(self):
        return DATA_ROOT / "staging" / "excel_review" / self.csv_path.with_suffix(".xlsx").name


def review_files():
    validation = DATA_ROOT / "processed" / "sentiment" / "validation"
    return (
        Review(validation / "calibration_blind.csv", "item_id", "Kalibracja", BLIND_FIELDS),
        Review(validation / "validation_blind.csv", "item_id", "Walidacja", BLIND_FIELDS),
        Review(DATA_ROOT / "staging" / "candidates_review_workbench.csv", "event_id", "Kandydaci", EVENT_FIELDS),
    )


def read_csv(review):
    with review.csv_path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        columns = tuple(reader.fieldnames or ())
        if (len(columns) != len(set(columns)) or not {review.key, *review.fields} <= set(columns)
                or review.blind and set(columns) != set(BLIND_COLUMNS)):
            raise ValueError(f"Niezgodne nagłówki w {review.csv_path.name}.")
        rows = list(reader)
    if any(None in row or None in row.values() for row in rows):
        raise ValueError(f"Nieprawidłowa liczba pól w {review.csv_path.name}.")
    keys = [row[review.key] for row in rows]
    if not all(keys) or len(keys) != len(set(keys)):
        raise ValueError(f"Puste lub zduplikowane {review.key} w {review.csv_path.name}.")
    return columns, rows


def clean_value(value, field):
    if value is None or isinstance(value, str) and not value.strip():
        return ""
    if isinstance(value, bool):
        raise ValueError("Oczekiwano wartości zgodnej z opisem kolumny.")
    text = str(value).strip()
    if field.choices and text not in field.choices:
        raise ValueError("Dozwolone wartości to " + ", ".join(field.choices) + ".")
    if field.kind in {"date", "period"}:
        if isinstance(value, datetime):
            value = value.date()
        if isinstance(value, date):
            return value.isoformat()
        if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", text):
            return datetime.strptime(text, "%d.%m.%Y").date().isoformat()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            return date.fromisoformat(text).isoformat()
        if field.kind == "date" or not TARGET_PERIOD.fullmatch(text):
            raise ValueError("Oczekiwano " + FORMAT_GUIDE[field.kind] + ".")
    if field.kind == "time":
        if isinstance(value, time) and not value.microsecond:
            return value.isoformat(timespec="seconds" if value.second else "minutes")
        if not clock_interval(text):
            raise ValueError("Oczekiwano godziny GG:MM lub GG:MM:SS.")
        return text.zfill(5 if text.count(":") == 1 else 8)
    if field.kind == "amount":
        # Excel wpisuje liczbę zgodnie z ustawieniami polskimi, a potok czyta z kropką.
        try:
            amount = Decimal(re.sub(r"[ \u00a0\u202f]", "", text).replace(",", "."))
        except InvalidOperation:
            raise ValueError("Oczekiwano liczby w mln.") from None
        if not amount.is_finite() or amount < 0:
            raise ValueError("Oczekiwano skończonej liczby nieujemnej.")
        return str(amount)
    if field.kind == "currency" and not re.fullmatch(r"[A-Z]{3}", text):
        raise ValueError("Kod waluty wymaga 3 wielkich liter, np. PLN.")
    if field.kind == "url" and not re.fullmatch(r"https?://\S+", text):
        raise ValueError("Oczekiwano adresu http:// lub https://.")
    return text


def put_text(cell, value):
    if len(value) > 32767:
        raise ValueError(f"Tekst w {cell.coordinate} przekracza limit komórki Excela.")
    cell.value = value if value else None
    if value:
        cell.data_type = "s"


def put_editable(cell, value, field):
    value = clean_value(value, field)
    if field.kind == "amount":
        cell.value = Decimal(value) if value else None
        cell.number_format = "#,##0.########"
    elif field.kind == "date":
        cell.value = date.fromisoformat(value) if value else None
        cell.number_format = "yyyy-mm-dd"
    else:
        put_text(cell, value)
        cell.number_format = "@"


def display_excerpts(value):
    blocks = []
    for item in json.loads(value or "[]"):
        anchor = item["project_anchor"] or "kontekst CAPEX"
        blocks.append(
            f"{anchor} · {item['document_id']} · wiersz {item['start_line']}\n"
            f"{item['quote']}\n"
            f"Publikacja: {item['published_at'] or item['publication_date']}\n"
            f"Plik: {item['text_path']}"
        )
    return "\n\n".join(blocks)


def style_header(cell, editable):
    cell.fill = EDIT_HEADER if editable else SOURCE_HEADER
    cell.font = Font(name="Arial", size=10, bold=True, color="443519" if editable else "FFFFFF")
    cell.alignment = Alignment(vertical="center", wrap_text=True)


def setup_sheet(sheet, last_column, last_row):
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:{get_column_letter(last_column)}{last_row}"
    sheet.sheet_view.showGridLines = False
    sheet.row_dimensions[1].height = 32


def add_validation(sheet, column, last_row, field):
    if last_row < 2:
        return
    if field.choices:
        validation = DataValidation(type="list", formula1='"' + ",".join(field.choices) + '"', showDropDown=False)
        validation.error = "Wybierz jedną z wartości z listy albo pozostaw pole puste."
    elif field.kind == "currency":
        cell = f"{column}2"
        letters = '"ABCDEFGHIJKLMNOPQRSTUVWXYZ"'
        letters_check = ",".join(f"ISNUMBER(FIND(MID({cell},{i},1),{letters}))" for i in (1, 2, 3))
        validation = DataValidation(type="custom", formula1=f"AND(LEN({cell})=3,{letters_check})")
        validation.error = "Wpisz 3 wielkie litery, np. PLN, EUR lub USD."
    elif field.kind == "amount":
        validation = DataValidation(type="decimal", operator="greaterThanOrEqual", formula1="0")
        validation.error = "Wpisz nieujemną kwotę w milionach."
    else:
        return
    validation.allow_blank = True
    validation.errorStyle = "stop"
    validation.showErrorMessage = True
    validation.errorTitle = "Nieprawidłowy wpis"
    sheet.add_data_validation(validation)
    validation.add(f"{column}2:{column}{last_row}")


def add_guide(workbook, fields):
    sheet = workbook.create_sheet("Sciagawka_kodowania")
    sheet.append(("Kolumna", "Co wpisać", "Dozwolone wartości lub format"))
    for cell in sheet[1]:
        style_header(cell, False)
    for name, field in fields.items():
        sheet.append((name, field.description, ", ".join(field.choices) if field.choices else FORMAT_GUIDE[field.kind]))
        sheet.row_dimensions[sheet.max_row].height = 42
        for cell in sheet[sheet.max_row]:
            cell.font = BODY
            cell.alignment = WRAPPED
            if cell.row % 2 == 0:
                cell.fill = STRIPE
    setup_sheet(sheet, 3, sheet.max_row)
    for column, width in zip("ABC", (45, 69, 57)):
        sheet.column_dimensions[column].width = width
    sheet.append(())
    sheet.append(("Praca w arkuszu", "Żółte nagłówki wskazują pola do edycji. Puste pole oznacza brak decyzji lub danych."))
    sheet.append(("Długie treści", "Pełną treść ESPI lub fragmentu odczytasz w rozwiniętym pasku formuły."))
    sheet.append(("Kolejność zdarzeń", "Komunikaty z tego samego dnia mają osobne identyfikatory. "
                  "Godziny wpisuj zgodnie ze źródłem i uzupełnij adres źródła godziny."))
    for row in sheet.iter_rows(min_row=len(fields) + 3):
        sheet.row_dimensions[row[0].row].height = 39
        for cell in row:
            cell.alignment = WRAPPED
            cell.font = BODY


def temporary_path(target):
    with NamedTemporaryFile(dir=target.parent, prefix=f".{target.stem}-", suffix=target.suffix, delete=False) as temp:
        return Path(temp.name)


def export_review(review, columns, rows):
    display = BLIND_COLUMNS if review.blind else tuple(dict.fromkeys((*EVENT_FRONT, *review.fields, *columns)))
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = review.sheet_name
    height_columns = ("text",) if review.blind else ("title", "espi_text", "periodic_excerpts", "manual_coding_note")
    for index, name in enumerate(display, 1):
        cell = sheet.cell(1, index, name)
        style_header(cell, name in review.fields)
        letter = get_column_letter(index)
        sheet.column_dimensions[letter].width = TEXT_WIDTHS.get(name, min(42, max(18, len(name) + 3)))
        if name in review.fields:
            add_validation(sheet, letter, len(rows) + 1, review.fields[name])
    for index, row in enumerate(rows, 2):
        shown = {**row, "periodic_excerpts": display_excerpts(row["periodic_excerpts"])} if not review.blind else row
        for column, name in enumerate(display, 1):
            cell = sheet.cell(index, column)
            if name in review.fields:
                put_editable(cell, row[name], review.fields[name])
            else:
                put_text(cell, shown[name])
            cell.font = BODY
            cell.alignment = WRAPPED
            if index % 2 == 0:
                cell.fill = STRIPE
        lines = max(sum(max(1, (len(line) + width - 1) // width) for line in shown[name].splitlines())
                    for name in height_columns for width in (TEXT_WIDTHS[name] - 5,))
        sheet.row_dimensions[index].height = min(116, max(30, 14 * lines + 5))
    setup_sheet(sheet, len(display), len(rows) + 1)
    if not review.blind:
        add_guide(workbook, review.fields)
    target = review.xlsx_path
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = temporary_path(target)
    try:
        workbook.save(temp)
        temp.replace(target)
    finally:
        temp.unlink(missing_ok=True)
    return target


def import_review(review, columns, rows):
    workbook = load_workbook(review.xlsx_path, read_only=True, data_only=False)
    originals = {row[review.key]: row for row in rows}
    seen = set()
    try:
        sheet = workbook[review.sheet_name]
        cells = sheet.iter_rows()
        headers = [cell.value for cell in next(cells, ())]
        required = set(columns)
        allowed = required | BLIND_HISTORY_COLUMNS if review.blind else required
        header_names = set(headers)
        if len(headers) != len(header_names) or not required <= header_names <= allowed:
            raise ValueError("Nagłówki skoroszytu różnią się od pliku CSV.")
        index = {name: col for col, name in enumerate(headers)}
        for number, row in enumerate(cells, 2):
            if all(cell.value is None for cell in row):
                continue
            key = row[index[review.key]].value
            if key not in originals or key in seen:
                raise ValueError(f"Wiersz {number}: nieznany lub powtórzony identyfikator {key!r}.")
            original = originals[key]
            if review.blind and (row[index["text"]].value or "") != original["text"]:
                raise ValueError(f"Wiersz {number}: tekst fragmentu {key} różni się od źródła.")
            seen.add(key)
            for name, field in review.fields.items():
                cell = row[index[name]]
                try:
                    if cell.data_type in {"f", "e"}:
                        raise ValueError("Oczekiwano wartości, bez formuł ani błędów komórki.")
                    original[name] = clean_value(cell.value, field)
                except ValueError as error:
                    label = f"{get_column_letter(index[name] + 1)}{number}"
                    raise ValueError(f"{label}, {key}, {name}: {error}") from None
        if len(seen) != len(originals):
            raise ValueError(f"Brakuje {len(originals) - len(seen)} wierszy źródłowych.")
    finally:
        workbook.close()


def write_review_csvs(pending):
    staged = {}
    try:
        for review, columns, rows in pending:
            target = review.csv_path
            staged[target] = temporary_path(target)
            with staged[target].open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=columns)
                writer.writeheader()
                writer.writerows(rows)
        for target, temporary in staged.items():
            temporary.replace(target)
    finally:
        for temporary in staged.values():
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--export", action="store_true", help="Utwórz skoroszyty z bieżących plików CSV.")
    mode.add_argument("--import", dest="load", action="store_true", help="Zapisz oceny ze skoroszytów do plików CSV.")
    args = parser.parse_args()
    pending = []
    for review in review_files():
        try:
            columns, rows = read_csv(review)
            if args.export:
                target = export_review(review, columns, rows)
                print(f"{target.name}: {len(rows)} wierszy")
            else:
                import_review(review, columns, rows)
                pending.append((review, columns, rows))
        except (OSError, ValueError, KeyError) as error:
            parser.exit(1, f"{review.xlsx_path.name}: {error}\n")
    if args.load:
        write_review_csvs(pending)
        for review, _, rows in pending:
            print(f"{review.csv_path.name}: {len(rows)} wierszy")


if __name__ == "__main__":
    main()
