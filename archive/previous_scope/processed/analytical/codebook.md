# Codebook — analytical merge (CAR × panel × cases)

## 1. `events_enriched` (2546 wierszy)

Jednostka: **zdarzenie ESPI** (unikalne `event_id`) z preferowanym benchmarkiem.

| Blok | Pola |
|------|------|
| Id / meta | event_id, ticker, event_date, day0, year, quarter, event_type*, title, numer |
| Model | benchmark, alpha, beta, r2, n_est, resid_sd |
| CAR | car_m1p1, car_m3p3, car_m5p5, car_m10p10, car_m20p20 (+ n_ar_*) |
| Case | is_case, case_ids, hyp_ids, qual_primary, case_labels, n_case_maps |
| Panel same Q | `*_q` (assets, roa, TONE_MGR, brent, dummies, …) |
| Panel lag Q | `*_lag` |

## 2. `case_events_enriched` (52 wierszy)

Jednostka: **priorytetowa data case** H1–H6 (w tym unmatched).

Kolumny z `case_events_map` + panel `_q` / `_lag` + CAR gdy matched.

## 3. `panel_with_car` (168 wierszy)

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
