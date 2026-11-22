# Codebook — panel_quarterly

Jednostka obserwacji: **spółka × rok × kwartał** (2020Q1–2025Q4).

## Identyfikatory

| Zmienna | Typ | Opis |
|---------|-----|------|
| ticker | str | Kod GPW (PKN, PGE, TPE, ENA, ZEP, UNT, JSW) |
| year | int | Rok kalendarzowy / obrotowy |
| quarter | int | 1–4 |
| role | str | rola w badaniu (rdzeń / kontrast / rezerwa) |
| state_control | 0/1 | 1 = dominacja SP (PKN, PGE, TPE, ENA, JSW) |
| accounting_tier | str | `pkn_xls` (Orlen RI ZIP) lub `peer_br` (BiznesRadar) |

## Metodologia rachunkowa (dwa tiery)

| Tier | Spółki | Źródło | Uwagi |
|------|--------|--------|-------|
| `pkn_xls` | PKN | `*_dane-liczbowe.zip` skonsolidowane XLS | Autoritative dla PKN; 3M flows gdy dostępne |
| `peer_br` | PGE, TPE, ENA, ZEP, UNT, JSW | BiznesRadar tabele Q | tys. PLN → mln PLN (/1000); publiczna alternatywa Notoria |

**Porównywalność między spółkami:** te same etykiety zmiennych, ale różne źródła pierwotne — w regresie kontrolować `accounting_tier` lub osobne modele PKN vs peery. Nie mieszać bez uwagi EBITDA (peer) z lev-EBIT (PKN).

## Rachunkowość

Kwoty: **mln PLN**.

| Zmienna | Opis |
|---------|------|
| total_assets | Aktywa razem (BS EOP) |
| equity | Kapitał własny (dominująca / razem — wg źródła) |
| cash | Środki pieniężne |
| debt_interest_bearing | Kredyty/pożyczki + obligacje (LT+ST) |
| net_debt | debt_interest_bearing − cash |
| revenue | Przychody ze sprzedaży (kwartał 3M) |
| ebit | Zysk operacyjny (3M) |
| ebitda | EBITDA (głównie `peer_br`; PKN XLS zwykle brak) |
| net_income | Zysk netto (3M; prefer. akcjonariuszy JD) |
| cfo | CF z działalności operacyjnej (3M) |
| capex | Nakłady (wartość dodatnia); PKN z CF nabycia; BR linia Capex |
| capex_int | capex / total_assets(t−1) w obrębie tickera |
| roa | net_income / total_assets |
| cfoa | cfo / total_assets |
| lev | **alias** `lev_assets` (net_debt / total_assets) — używać w regresjach |
| lev_assets | net_debt / total_assets |
| lev_assets_w | lev_assets winsor 1–99% (cała próba) |
| lev_op | net_debt / ebitda (else ebit) — kruche; tylko diagnostyka |
| cash_ratio | cash / total_assets |
| unit | `mln_PLN` |
| period_source | Q1/H1/Q3/Q4/AR / RECON_… / `biznesradar_Q` |
| source_file | nazwa ZIP lub `biznesradar` |

## Rynek (wszystkie spółki)

| Zmienna | Opis |
|---------|------|
| price_end | Kurs zamknięcia EOP kwartału |
| price_mean | Średni kurs w kwartale |
| ret_q | Zwrot złożony w kwartale |
| ret_vol | Odch. std. dziennych zwrotów |
| volume_sum | Suma wolumenu |
| mktcap | price_end × shares_m (**proxy**) |
| shares_m | Przybliżona liczba akcji (mln) |
| mb | mktcap / equity (gdy equity dostępne) |

## ESPI / zdarzenia

| Zmienna | Opis |
|---------|------|
| fin_event | 1 jeśli w kwartale ESPI typu emisja/finansowanie |
| ma_event | 1 jeśli transakcje M&A |
| div_event | 1 jeśli dywidenda |
| impairment_dummy | 1 jeśli tytuł ESPI sugeruje odpis/utratę wartości |
| n_espi | liczba ESPI w kwartale |

## Dywidenda PKN

| Zmienna | Opis |
|---------|------|
| dps | PLN/akcję za rok obrotowy (tabela IR H6) |
| payout | zgrubny wskaźnik (patrz missing_log) |

## Ton zarządu / NLP (MVP)

Źródło: `data/processed/sentiment/sentiment_quarterly.parquet` (`build_corpus_sentiment.py`).

| Zmienna | Opis |
|---------|------|
| TONE_MGR | (pos−neg)/n_words — słownik PL stylu LM |
| UNCERTAINTY | udział leksyki niepewności |
| CERTAINTY | udział leksyki pewności |
| READABILITY | proxy FOG (wyżej = trudniejszy) |
| pos_share, neg_share | udziały słów pos/neg |
| n_mgr_docs, n_mgr_words | liczba dokumentów / słów w agregacie |

AR → Q4; H1 → Q2. Sparse: nie każdy ticker×kwartał ma tekst.

## Makro / sektor (wspólne dla wszystkich spółek w kwartale)

Źródło: `data/processed/macro_quarterly.parquet` (`fetch_macro.py`).

| Prefiks / zmienna | Opis |
|-------------------|------|
| brent_usd_* | ropa Brent (USD/bbl; yfinance BZ=F) |
| eurpln_*, usdpln_* | kursy NBP mid |
| nbp_ref_rate_* | stopa referencyjna NBP (ścieżka RPP) |
| power_pl_eur_mwh_* | day-ahead PL EUR/MWh (proxy TGE) |
| gas_eu_usd_* | gaz NG=F proxy |
| eua_proxy_krbn_* | ETF KRBN — **proxy** carbon, nie ICE EUA |
| wig_*, wig_energia_*, wig_paliwa_* | indeksy z market_data |
| *_qmean / *_qend / *_qchg | średnia / EOP / zmiana % EOP w kwartale |
| COVID_2020, ENERGY_CRISIS, NORMALIZATION, MERGER_ORLEN | dummy podokresów |

## Skrypty

- `data/scripts/build_panel.py` — budowa panelu
- `data/scripts/fetch_peer_accounting_br.py` — peer accounting z BiznesRadar
- `data/scripts/fetch_macro.py` — serie makro
