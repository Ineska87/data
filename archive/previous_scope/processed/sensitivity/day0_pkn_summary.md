# Sensitivity Day 0 — PKN / ZEP (brak godziny ESPI)

## Reguły

| Reguła | Opis |
|--------|------|
| `baseline_shift` | jak `compute_car`: brak godziny → data+1 → najbliższa sesja |
| `same_calendar_day` | data ESPI → najbliższa sesja ≥ data (bez +1, gdy brak godziny) |

Gdy `has_time` i godzina ≥ 17:00 — obie reguły i tak przesuwają na następną sesję.

## PKN

### Okno [-1+1]

| Reguła | n | mean CAR | median CAR |
|--------|---|----------|------------|
| baseline_shift | 464 | -0.004% | +0.090% |
| same_calendar_day | 464 | -0.037% | +0.088% |

Korelacja CAR (event-level) między regułami: **0.631** (n=464).

Mean CAR po kategorii:

| Kategoria | baseline | same_day | Δ (pp) |
|-----------|----------|----------|--------|
| Akcjonariat/progi | +0.142% | +0.264% | +0.122 |
| Dywidenda | -0.218% | -0.326% | -0.108 |
| Emisja/finansowanie | +0.028% | +0.207% | +0.179 |
| Inne | +0.011% | +0.002% | -0.008 |
| Rating/rekomendacja | +0.027% | +0.095% | +0.067 |
| Regulacyjne/prawne | -0.403% | -0.174% | +0.229 |
| Transakcje M&A | -0.082% | -0.307% | -0.226 |
| Umowy/kontrakty | -0.385% | -0.123% | +0.262 |
| Walne zgromadzenie | +0.129% | +0.075% | -0.054 |
| Wyniki finansowe | -0.080% | -0.145% | -0.065 |
| Zmiany personalne | +0.152% | +0.115% | -0.036 |

### Okno [-5+5]

| Reguła | n | mean CAR | median CAR |
|--------|---|----------|------------|
| baseline_shift | 464 | +0.045% | +0.350% |
| same_calendar_day | 464 | +0.011% | +0.336% |

Korelacja CAR (event-level) między regułami: **0.901** (n=464).

Mean CAR po kategorii:

| Kategoria | baseline | same_day | Δ (pp) |
|-----------|----------|----------|--------|
| Akcjonariat/progi | +0.701% | +0.729% | +0.028 |
| Dywidenda | -0.553% | -0.412% | +0.141 |
| Emisja/finansowanie | +0.094% | +0.081% | -0.013 |
| Inne | -0.062% | +0.064% | +0.126 |
| Rating/rekomendacja | +2.237% | +2.493% | +0.256 |
| Regulacyjne/prawne | -2.052% | -2.207% | -0.155 |
| Transakcje M&A | -0.010% | -0.086% | -0.075 |
| Umowy/kontrakty | -0.096% | -0.378% | -0.282 |
| Walne zgromadzenie | -0.007% | -0.054% | -0.048 |
| Wyniki finansowe | +0.099% | -0.220% | -0.319 |
| Zmiany personalne | +0.651% | +0.599% | -0.052 |

## ZEP

### Okno [-1+1]

| Reguła | n | mean CAR | median CAR |
|--------|---|----------|------------|
| baseline_shift | 259 | +0.535% | -0.235% |
| same_calendar_day | 260 | +0.663% | -0.297% |

Korelacja CAR (event-level) między regułami: **0.661** (n=259).

Mean CAR po kategorii:

| Kategoria | baseline | same_day | Δ (pp) |
|-----------|----------|----------|--------|
| Akcjonariat/progi | +0.321% | +0.192% | -0.130 |
| Emisja/finansowanie | -1.718% | -3.146% | -1.427 |
| Inne | +0.320% | +0.650% | +0.330 |
| Regulacyjne/prawne | +1.803% | -1.670% | -3.474 |
| Transakcje M&A | +0.004% | -0.692% | -0.696 |
| Umowy/kontrakty | +1.856% | +2.804% | +0.949 |
| Walne zgromadzenie | -0.130% | +0.149% | +0.279 |
| Wyniki finansowe | -1.128% | -0.986% | +0.142 |
| Zmiany personalne | +1.979% | +1.288% | -0.691 |

### Okno [-5+5]

| Reguła | n | mean CAR | median CAR |
|--------|---|----------|------------|
| baseline_shift | 259 | +0.234% | -1.074% |
| same_calendar_day | 260 | +0.524% | -0.953% |

Korelacja CAR (event-level) między regułami: **0.929** (n=259).

Mean CAR po kategorii:

| Kategoria | baseline | same_day | Δ (pp) |
|-----------|----------|----------|--------|
| Akcjonariat/progi | -1.990% | -0.618% | +1.373 |
| Emisja/finansowanie | +0.493% | -2.065% | -2.557 |
| Inne | +0.963% | +0.857% | -0.107 |
| Regulacyjne/prawne | -0.521% | -1.960% | -1.438 |
| Transakcje M&A | +4.076% | +5.918% | +1.842 |
| Umowy/kontrakty | -1.385% | -1.596% | -0.211 |
| Walne zgromadzenie | -0.707% | +0.035% | +0.742 |
| Wyniki finansowe | -2.249% | -2.122% | +0.126 |
| Zmiany personalne | +1.681% | +2.116% | +0.435 |

## Częstość zmiany Day 0 (PKN)

- Zdarzeń PKN 2019–2025: **465**
- Day 0 różny między regułami: **457** (98.3%)
- `has_time` PKN: **0.0%** (prawie zawsze shift w baseline)

## Pliki

- `day0_pkn_zep_cars.csv` — CAR long
- `day0_compare_*-1p1.csv`, `day0_compare_*-5p5.csv` — event-level Δ

Skrypt: `data/scripts/sensitivity_day0.py`
