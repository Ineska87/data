# Makro — źródła i notatki

| Seria | Plik raw | Źródło | Uwagi |
|-------|----------|--------|-------|
| Brent | `brent_daily.csv` | FRED DCOILBRENTEU | Spot Europe, USD/bbl |
| EURPLN, USDPLN | `fx_daily.csv` | NBP API tabela A | Kurs średni |
| Stopa ref. NBP | `rates.csv` | Ścieżka decyzji RPP | Skokowa; daty w skrypcie |
| PL short rate | `rates.csv` (`pl_short_rate_m`) | FRED IRSTCI01PLM156N | Miesięczna, ffill do dni |
| Gaz EU | `gas_eu_monthly.csv` | FRED PNGASEUUSDM | Miesięczna USD |
| Energia PL | `tge_power_proxy.csv` | energy-charts `bzn=PL` | Day-ahead EUR/MWh; **proxy TGE RDN** (nie feed TGE) |
| EUA | `eua_proxy_daily.csv` | yfinance KRBN | ETF węglowy — **proxy**, nie kontrakt ICE EUA |
| WIG / energia / paliwa | market_data CSV | lokalne pliki | Jeśli obecne |

## Dummy podokresów

| Dummy | Okno |
|-------|------|
| COVID_2020 | 2020-01-01 – 2020-12-31 |
| ENERGY_CRISIS | 2022-01-01 – 2023-12-31 |
| NORMALIZATION | 2024-01-01 – 2025-12-31 |
| MERGER_ORLEN | 2022-07-01 – 2023-06-30 (Lotos+PGNiG) |

## Skrypt

`data/scripts/fetch_macro.py`
