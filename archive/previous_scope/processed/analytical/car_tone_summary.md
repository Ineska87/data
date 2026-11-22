# CAR × panel × cases — podsumowanie deskryptywne

Eventy (preferowany benchmark): **2546**
Case map rows: **52** (matched=45)
Panel firm×Q: **168**

## CAR[-1,+1] — case vs reszta ESPI (2020–2025)

- **case**: n=37, mean=0.0083%, median=0.0294%, std=2.0018%, share<0=43.2%
- **non-case**: n=2191, mean=0.1337%, median=0.0473%, std=3.9627%, share<0=47.9%

## CAR[-1,+1] × TONE_MGR tercile (lag, gdy dostępny)

- **tone low** (n=257): mean CAR=0.3669%, median=0.0390%
- **tone mid** (n=255): mean CAR=0.1308%, median=0.0932%
- **tone high** (n=256): mean CAR=0.0445%, median=0.1102%
- Pearson corr(CAR[-1+1], TONE_MGR_lag) = **-0.0264** (n=768)

## CAR[-1,+1] wg QUAL (tylko case matched)

- **escalation**: n=10, mean=-0.5457%, median=-0.1029%
- **framing**: n=13, mean=0.6600%, median=0.2287%
- **herding**: n=3, mean=-2.4556%, median=-2.6150%
- **hubris_ma**: n=9, mean=-0.0312%, median=-0.0331%
- **mental_accounting**: n=3, mean=-0.6517%, median=-1.0835%
- **overconfidence**: n=3, mean=-0.9906%, median=-0.8167%
- **status_quo**: n=4, mean=0.7846%, median=0.6670%

## CAR[-1,+1] wg case

- **dywidenda_fiz**: n=6, mean=-0.2461%, median=0.1250%
- **ma_orlen**: n=10, mean=-0.3389%, median=-0.0027%
- **nabe**: n=5, mean=0.8572%, median=1.2177%
- **olefiny_iii**: n=7, mean=-0.0788%, median=0.0168%
- **ostroleka_c**: n=7, mean=-0.8246%, median=-0.7771%
- **strategie**: n=10, mean=0.0591%, median=0.1813%

## Panel: średni CAR w kwartale vs TONE_MGR

- corr(mean CAR quarter, TONE_MGR) = **0.0488** (n=74)
- mean |CAR| when case events present: 1.4634%

## Pliki

- `events_enriched.parquet` — jednostka: ESPI event
- `case_events_enriched.parquet` — jednostka: data case H1–H6
- `panel_with_car.parquet` — jednostka: spółka×kwartał

## Uwagi

- Benchmark (jak w compute_car): PGE/TPE/ENA → WIG-energia; PKN → WIG-paliwa; UNT/ZEP/JSW/LWB → WIG.
- Kovarianty `_q` = ten sam kwartał co data zdarzenia; `_lag` = poprzedni kwartał.
- TONE często sparse → CAR×TONE na podpróbce z niepustym tonem (lag).
- To **descriptives**, nie wnioskowanie przyczynowe.

Skrypt: `data/scripts/build_analytical.py`
