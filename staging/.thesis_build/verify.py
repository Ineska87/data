import hashlib
import json
import math
from pathlib import Path
import sys
from zipfile import ZipFile

from openpyxl import load_workbook
import pandas as pd
from PIL import Image


DATA = Path("data")
OUT = DATA / "processed/thesis_outputs"
TEMP = Path(__file__).parent
INPUTS = {
    "metadata/espi_review.csv": "5eda6c4efd71ae7021e48e0dd0261b5c37246e62d32ed6bb686c40b3515991fd",
    "metadata/investment_passages.csv": "bc4d4aa225e91ad5afcf433937afccff0f1b768dcc43191d067d29e98b52cc29",
    "processed/sentiment/validation/validation_blind.csv": "b08528a12e03afd845a138d73b54173ef24d1acbf87ca2f11f8355dbb790d35d",
    "processed/analytical/investment_analysis_status.json": "cb92a1e4122d3d203f4534ecda90d60bfb6bac2e65d4c1a5a0f5ca07c65fe610",
}
for file, sha in INPUTS.items():
    assert hashlib.sha256((DATA / file).read_bytes()).hexdigest() == sha, file
assert not any(DATA.rglob("regression_summary.json"))

sys.path.insert(0, str(DATA / "scripts"))
from investment_sentiment import load_lexicon, score_passage

extended = pd.read_csv(OUT / "extended_capex_passages.csv", keep_default_na=False)
m3 = pd.read_csv(TEMP / "proba_m3.csv")
assert len(extended) == 11 and extended["reference_report_id"].nunique() == 9
assert len(m3) == 28 and m3["reference_report_id"].nunique() == 25
assert set(extended["event_id"]) == set(m3.loc[m3["source"].eq("broad"), "event_id"])
lexicon = load_lexicon(DATA / "metadata/investment_tone_lexicon.json")
for row in extended.itertuples(index=False):
    assert len(row.fragment_tekstu.strip()) > 0
    score = score_passage(row.fragment_tekstu, lexicon)
    assert all(score[k] == getattr(row, k) for k in ("n_words", "n_positive", "n_negative"))
    assert math.isclose(score["tone_per_100_words"], row.tone_per_100_words, rel_tol=1e-12)
    if row.text_path:
        t = (DATA / row.text_path).read_text(encoding="utf-8")
        assert t[row.start_char:row.end_char] == row.fragment_tekstu

for fname in ("wykres_1_ton_vs_car.png", "wykres_2_olefiny_iii.png"):
    with Image.open(OUT / fname) as im:
        assert all(abs(dpi - 300) < 0.1 for dpi in im.info["dpi"])
        assert im.width >= 2400 and im.height >= 1500 and im.convert("RGB").getpixel((0, 0)) == (255, 255, 255)

filename = TEMP / "ready.xlsx"
worksheets = json.loads((TEMP / "workbook_input.json").read_text(encoding="utf-8"))
with ZipFile(filename) as packed:
    assert packed.testzip() is None
workbook = load_workbook(filename)
assert len(worksheets) == 9
assert workbook.sheetnames == [t["name"] for t in worksheets]
for table in worksheets:
    sheet = workbook[table["name"]]
    assert sheet.sheet_view.showGridLines is False and sheet["A2"].value == table["title"]
    assert [cell.value for cell in sheet[4]] == table["columns"]
    for rownum, expected in enumerate(table["rows"], 5):
        for col, value in enumerate(expected, 1):
            cell = sheet.cell(rownum, col)
            assert cell.data_type not in {"e", "f"}, (table["name"], cell.coordinate, cell.value)
            if isinstance(value, float):
                assert isinstance(cell.value, (int, float)) and math.isclose(cell.value, value, rel_tol=1e-13)
            else:
                assert cell.value == value, (table["name"], cell.coordinate, cell.value, value)
workbook.close()
print(f"Verified {len(worksheets)} worksheets, 11 text scores, both PNGs and the protected inputs.")
if "publish" in sys.argv:
    output = OUT / "Tabele_Rozdzial_3.xlsx"
    assert not output.exists()
    filename.replace(output)
    print(output.absolute())
