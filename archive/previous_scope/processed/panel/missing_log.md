# Panel — log braków

Obserwacje: **168** (7 tickerów × 24 kwartały = 168 oczekiwanych).

## Metodologia dwuwarstwowa (accounting_tier)

| Tier | Spółki | Źródło | Jednostka |
|------|--------|--------|-----------|
| `pkn_xls` | PKN | `raw/reports/PKN/*_dane-liczbowe.zip` (XLS RI) | mln PLN |
| `peer_br` | PGE, TPE, ENA, ZEP, UNT, JSW | BiznesRadar (HTML Q) → `peer_accounting_quarterly.*` | tys.→mln PLN |

- **PKN wygrywa konflikt:** wiersze BR dla ORLEN nie są włączane do panelu (tylko w raw BR do cross-check).
- Skrypt peer: `data/scripts/fetch_peer_accounting_br.py`.

## Pokrycie rachunkowe (total_assets / revenue) + tier

- **ENA**: assets=24/24, revenue=24/24, cfo=24/24, capex=24/24, market=24/24, tier=peer_br
- **JSW**: assets=24/24, revenue=24/24, cfo=24/24, capex=24/24, market=24/24, tier=peer_br
- **PGE**: assets=24/24, revenue=24/24, cfo=24/24, capex=24/24, market=24/24, tier=peer_br
- **PKN**: assets=23/24, revenue=24/24, cfo=24/24, capex=24/24, market=24/24, tier=pkn_xls
- **TPE**: assets=24/24, revenue=24/24, cfo=24/24, capex=24/24, market=24/24, tier=peer_br
- **UNT**: assets=24/24, revenue=24/24, cfo=24/24, capex=24/24, market=24/24, tier=peer_br
- **ZEP**: assets=24/24, revenue=24/24, cfo=24/24, capex=24/24, market=24/24, tier=peer_br

## Liczebność tierów

- `peer_br`: 144
- `pkn_xls`: 24

## Źródła

- **PKN (`pkn_xls`)**: `data/raw/reports/PKN/*_dane-liczbowe.zip` (XLS skonsolidowane RI).
- **Peery (`peer_br`)**: BiznesRadar rachunek/bilans/CF kwartalny; raw: `data/raw/panel_sources/biznesradar_quarterly_raw.csv`; wide: `data/processed/panel/peer_accounting_quarterly.parquet`.
- **Rynek + ESPI**: wszystkie 7 spółek (jak wcześniej).
- **Makro**: `data/processed/macro_quarterly.parquet` (z `fetch_macro.py`) — join po year×quarter.

## Notatki / ograniczenia porównawcze

- Wszystkie kwoty rachunkowe w panelu w **mln PLN** (BR: /1000 z tys. PLN).
- `capex` PKN = |nabycie PPE+IA+ROU| z CF; BR = linia Capex (lub |CF inwest.| jako proxy).
- EBITDA: dostępna na tier `peer_br`; na `pkn_xls` zwykle NaN.
- **Dźwignia:** `lev` = `lev_assets` = net_debt/assets; `lev_op` = net_debt/EBITDA|EBIT (kruche); `lev_assets_w` winsor.
- Mapowanie wierszy BR jest heurystyczne (etykiety PL) — przy rozbieżnościach weryfikować vs AR PDF.
- `mktcap` = cena × SHARES_M (**proxy** liczby akcji; SHARES_M z yfinance 2026-07).
- **UNT kursy:** od 2026-07 z `UNT.WA` (Unimot). Wcześniejszy błąd: `UNI.WA` = Unibep.
- `payout` tylko zgrubnie dla PKN (DPS × shares / NI Q4).
- Makro: `power_pl_*` = day-ahead PL (nie feed TGE); `eua_proxy_krbn` ≠ cena EUA ICE; FRED bywa timeout (fallback yfinance).

## Ton zarządu (NLP MVP)

- Źródło: `processed/sentiment/sentiment_quarterly.parquet` (słownik PL, nie transformer).
- Pokrycie sparse: AR→Q4, H1→Q2; brak tekstu = NaN w `TONE_MGR`.
- TPE AR `*_skonsolidowany.pdf` to często **7z** pod fałszywym rozszerzeniem — użyto Q/H1 `*sprawozdanie.pdf`.
- Brak ręcznej anotacji / TONE_FUND_GAP (checklist 7.2–7.3 otwarte).

### Pokrycie TONE_MGR (obs. z niepustym tonem)

- **ENA**: TONE_MGR=12/24
- **JSW**: TONE_MGR=12/24
- **PGE**: TONE_MGR=6/24
- **PKN**: TONE_MGR=9/24
- **TPE**: TONE_MGR=18/24
- **UNT**: TONE_MGR=8/24
- **ZEP**: TONE_MGR=9/24

## H1 2023 PKN (bez osobnego ZIP liczbowego)

- IR Orlen **nie publikuje** `Dane_ze_sprawozdania_*1H2023*.zip` w `…/2023/2q2023/`.
- **2023Q2 (przepływy):** `period_source=RECON_Q3YTD_minus_Q1_Q3` = YTD 9M(Q3) − Q1 − Q3.
- **2023Q2 bilans EOP:** NaN w tierze XLS (brak bilansu 30.06.2023 w pakietach).
