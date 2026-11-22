# Codebook — macro_daily / macro_quarterly

Okres daily: 2019-01-01 – 2025-12-31. Panel quarterly: 2020-01-01 – 2025-12-31.

## macro_daily (2557 wierszy)

Kluczowe poziomy: `brent_usd`, `eurpln`, `usdpln`, `nbp_ref_rate`, `pl_short_rate_m`,
`gas_eu_usd`, `power_pl_eur_mwh`, `eua_proxy_krbn`, opcjonalnie `wig*`.

Zwroty log: `dlog_<seria>`.

Dummy: `COVID_2020`, `ENERGY_CRISIS`, `NORMALIZATION`, `MERGER_ORLEN`.

## macro_quarterly (24 wierszy)

Dla każdej serii: `*_qmean`, `*_qend`; dla wybranych `*_qchg` (pct change EOP).

Dummy: max w kwartale (=1 jeśli choć jeden dzień).

## Ograniczenia

- `power_pl_eur_mwh` = day-ahead PL (energy-charts), nie komercyjny feed TGE.
- `eua_proxy_krbn` ≠ cena EUA na ICE — do FE jako proxy sektora carbon; nie cytować jako EUA spot.
- Stopy: ref. NBP ze ścieżki decyzji; `pl_short_rate_m` miesięczna OECD/FRED.

Zob. też `data/raw/macro/sources.md`.
