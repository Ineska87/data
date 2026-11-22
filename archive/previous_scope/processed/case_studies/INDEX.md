# Case studies H1–H6 — indeks i kody QUAL

**Cel:** spięcie jakościowych studiów przypadku z event study (ESPI/CAR) i panelem.  
**Okres:** 2020–2025 (+ kontekst 2018–2019 i 2026 tam, gdzie łańcuch decyzji jest ciągły).

---

## Mapa hipotez → pliki

| H | Tytuł | Kalendarium | Źródła PDF/ESPI | Tabela deklaracja vs ex post |
|---|--------|-------------|-----------------|------------------------------|
| **H1 / H2** | Olefiny III → Nowa Chemia (Orlen) | [`kalendarium_olefiny_iii.md`](kalendarium_olefiny_iii.md) | `raw/reports/PKN/olefiny_iii/` | [x] w pliku |
| **H2** | Ostrołęka C (Enea/Energa/Orlen) | [`kalendarium_ostroleka_c.md`](kalendarium_ostroleka_c.md) | `nik_reports/NIK_ostroleka*`, `ENA/ostroleka/`, `PKN/ostroleka/` | [x] w pliku |
| **H3** | M&A Orlen: Energa / Lotos / PGNiG | [`kalendarium_ma_orlen.md`](kalendarium_ma_orlen.md) | `PKN/ma_*`, `nik_reports/NIK_orlen-lotos*` | [x] w pliku (+ NIK Lotos) |
| **H4** | NABE + dezinwestycje węglowe | [`kalendarium_nabe.md`](kalendarium_nabe.md) | `PGE/nabe/`, ESPI ENA/TPE | [x] w pliku |
| **H5** | Strategie transformacji | [`kalendarium_strategie.md`](kalendarium_strategie.md) | `*STRAT*` wszystkich tickerów | [x] w pliku |
| **H6** | Dywidenda Orlen + FIZ JSW | [`kalendarium_dywidenda_fiz.md`](kalendarium_dywidenda_fiz.md) | `PKN/dywidenda/`, `JSW/fiz/` | [x] w pliku |

---

## Słownik kodów QUAL (używać w kalendariach i rozdziale)

| Kod | Znaczenie behawioralne | Typowe case |
|-----|------------------------|-------------|
| `overconfidence` | niedoszacowanie kosztów/ryzyka; zbyt pewne FID/NTP | Olefiny 2021; Ostrołęka 2018; NABE ex ante |
| `escalation` | eskalacja zaangażowania / sunk cost; rewizje CAPEX; stop po stratach | Olefiny 2023–26; Ostrołęka rozliczenie GW; NIK Lotos remedium |
| `hubris_ma` | empire-building / hubris w M&A; synergie ex ante | Energa–Lotos–PGNiG |
| `framing` | etykietowanie (Nowa Chemia, gaz zamiast węgla, „bezpieczeństwo”) | stop Olefiny; CCGT Ostrołęka; NABE; dywidenda gwarantowana |
| `status_quo` | odkładanie zmiany; czekanie na NABE; gwarancja payout | NABE 2021–25; dywidenda Orlen |
| `herding` | zbieżność narracji strategii / wspólne porozumienia SP | strategie 2030–35; porozumienie NABE |
| `mental_accounting` | osobne „kubełki” gotówki (FIZ vs dywidenda; CFO vs odpisy) | JSW FIZ; Orlen DPS mimo odpisów |

**Zasada kodowania:** jedna data może mieć 1–2 kody; primary source = ESPI/NIK/IR, nie prasa (prasa = framing komunikacyjny).

---

## Most do event study (CAR)

**Mapowanie zrobione:** skrypt `data/scripts/map_case_events.py`  
**Wyniki:**

| Plik | Opis |
|------|------|
| [`case_events_map.csv`](case_events_map.csv) / `.parquet` | case_date → event_id + CAR |
| [`case_events_coverage.md`](case_events_coverage.md) | raport pokrycia + tabela CAR |

**Pokrycie (2026-07-20):** **45 / 52** dat priorytetowych trafionych w ESPI + CAR.

| Case | Match |
|------|-------|
| ma_orlen | 10/10 |
| ostroleka_c | 7/7 |
| strategie | 10/11 |
| olefiny_iii | 7/8 |
| dywidenda_fiz | 6/8 |
| nabe | 5/8 |

**Świadomie bez ESPI (nie „błąd mapowania”):**

- **NABE 2025-07-09** (PGE/TPE/ENA) — decyzja MAP, brak raportu MAR spółek → Day0 ręczny (media) jeśli CAR event study
- **Olefiny 2026-04-15** — poza oknem `events_master_2019_2025`
- **Dni prawa dywidendy** (2023-08-10, 2025-08-14) — często bez ESPI (uchwała ZWZ = inna data)
- **ZEP 2020-10-01** strategia — publikacja IR, niekoniecznie ESPI

Szybka lista „must map” (core):

| Case | Daty priorytetowe | Tickery |
|------|-------------------|---------|
| Olefiny | 2021-05-24, 2021-06-22, 2023-06-29, 2024-11-06, 2024-12-11, 2025-03-31 | PKN |
| Ostrołęka | 2020-05-19, 2020-08-11, 2022-04-01 | ENA (+ PKN kontekst) |
| M&A | 2019-12-05, 2020-04-30, 2022-08-01, 2022-11-02 | PKN |
| NABE | 2021-07-23, 2022-10-12, 2023-07-14; *2025-07-09 = media* | PGE, TPE, ENA |
| Strategie | 2023-02-28, 2024-11-28, 2024-12-17, 2025-01-09, 2025-06-12 | PKN, ENA, TPE, PGE |
| Dywidenda/FIZ | 2023-02-28, 2025-01-09, 2025-06-05 ZWZ; JSW FIZ 2022/2025 | PKN, JSW |

---

## Checklist jakości case (stan)

| Wymóg checklisty §4 | Status |
|---------------------|--------|
| Kalendarium `data \| zdarzenie \| źródło \| QUAL` | [x] 6/6 |
| Folder źródeł PDF/ESPI | [x] 6/6 |
| Tabela deklaracja zarządu vs realizacja | [x] 6/6 |
| Kody QUAL w legendzie | [x] ten plik |

---

*Indeks: 2026-07-20. Źródła szczegółowe — w poszczególnych kalendariach.*
