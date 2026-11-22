# Korekta kursów UNT (Unimot) — 2026-07

## Błąd

`download_stooq_data.py` mapował ticker badawczy **UNT** na symbol Yahoo **`UNI.WA`**.

| Symbol | Spółka | Typowy kurs |
|--------|--------|-------------|
| `UNI.WA` | **Unibep** S.A. (budowlanka) | ~10–14 PLN |
| `UNT.WA` | **Unimot** S.A. (paliwa) | ~20–160 PLN |

Skutek: zwroty, CAR, mktcap i MB dla „Unimot” liczone na Unibepie.

## Korekta

- Źródło: yfinance `UNT.WA`, `auto_adjust=True`, 2018–2025
- Plik: `UNT.csv` (backup błędnego: `UNT_UNIBEP_wrong_backup.csv`)
- Mapowanie w skrypcie: `UNT` → `UNT.WA`
- Wymagane: `build_returns.py` + `compute_car.py` + `build_panel.py`
