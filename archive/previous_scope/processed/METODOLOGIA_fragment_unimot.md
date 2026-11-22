# Fragment metodologii — notowania Unimot (do wklejenia do pracy)

*Język: akademicki PL. Miejsce: rozdział „Dane” / „Źródła i konstrukcja zmiennych rynkowych”.*

> **Pełny zestaw §1–4** (Unimot + dźwignia + Day 0 + stopa NBP):  
> [`METODOLOGIA_fragmenty_dane.md`](METODOLOGIA_fragmenty_dane.md)

---

## Wersja skrócona (ok. ½ akapitu)

Dzienne notowania spółek z próby oraz indeksów WIG, WIG20, WIG-energia i WIG-paliwa pochodzą z publicznych serii giełdowych (GPW). W badaniu Unimot S.A. oznaczany jest tickerem **UNT**. Kursy zamknięcia Unimot pobrano z serii Yahoo Finance **`UNT.WA`** (dostosowane o dywidendy i splity, `auto_adjust`), za okres obejmujący bufor estymacji 2018–2019 oraz okno analizy 2020–2025. Ticker Yahoo **`UNI.WA` odpowiada innej spółce (Unibep S.A.)** i nie był wykorzystywany w finalnych szacunkach. Na podstawie skorygowanych kursów obliczono logarytmiczne stopy zwrotu, parametry modelu rynkowego oraz skumulowane stopy nadzwyczajne (CAR); kapitalizację rynkową przybliżono jako iloczyn kursu zamknięcia na koniec kwartału i stałej liczby akcji (ok. 8,20 mln szt.).

---

## Wersja pełna (akapit + przypis)

### Tekst główny

Źródłem dziennych kursów zamknięcia, wolumenu oraz indeksów referencyjnych jest zbiór notowań GPW scalony w pliku roboczym `market_data_all` (okres 2018-01–2025-12, z buforem przed 2020 r. na potrzeby okna estymacji modelu rynkowego). Spółki energetyczno-paliwowe z próby rdzeniowej i rezerwowej identyfikowane są tickerami GPW: PKN, PGE, TPE, ENA, ZEP, JSW oraz — jako kontrast prywatny — **Unimot S.A. (UNT)**.

W przypadku Unimot ostateczna seria kursów pochodzi z Yahoo Finance pod symbolem **`UNT.WA`**, z korektą o działania korporacyjne (`auto_adjust=True`). Zwroty dzienne zdefiniowano jako logarytmiczne stopy zmiany kursu zamknięcia w dniach z dodatnim wolumenem (sesje handlowe). Model rynkowy dla UNT szacowano względem indeksu **WIG** (wybór podyktowany wyższym dopasowaniem R² niż dla WIG-paliwa w oknie estymacji [−250, −11] dni sesyjnych przed dniem zdarzenia). Kapitalizację rynkową w panelu kwartalnym obliczono jako \(P_{i,t}\times N_i\), gdzie \(N_i\) to przybliżona liczba akcji w mln szt. (dla Unimot \(N_{\mathrm{UNT}}\approx 8{,}198\)), traktowana jako stała w próbie — proxy, a nie pełna historia emisji.

### Przypis dolny (opcjonalny, techniczny)

W wersji roboczej pipeline’u wystąpiła pomyłka mapowania tickera badawczego UNT na symbol Yahoo `UNI.WA` (Unibep S.A.). Błąd wykryto przy audycie spójności kapitalizacji i kursów; serię zastąpiono `UNT.WA` (Unimot), a wyniki event study i panel przeliczono. W finalnej pracy wykorzystano wyłącznie skorygowaną serię Unimot.

---

## Tabela źródłowa (do aneksu „Źródła danych”)

| Element | Wartość |
|---------|---------|
| Emitent | Unimot S.A. |
| Ticker w pracy | UNT |
| ISIN | PLUNMOT00013 |
| Seria kursów | Yahoo Finance `UNT.WA` |
| Korekta | auto_adjust (dywidendy, splity) |
| Okres raw | 2018–2025 (w tym bufor estymacji) |
| Zwroty | \(\ln(P_t/P_{t-1})\), dni z Volume > 0 |
| Benchmark CAR | WIG |
| Liczba akcji (proxy mktcap) | ok. 8,198 mln |
| Plik raw | `data/raw/market_data/UNT.csv` |
| Skrypt pobrania/korekty | `data/scripts/fix_unt_prices.py` |

---

## Czego *nie* pisać w tekście głównym (chyba że promotor chce pełnej transparentności pipeline)

- Nazwy plików backup (`UNT_UNIBEP_wrong_backup.csv`) — tylko w aneksie replikacyjnym.
- Sformułowań typu „AI wykryło błąd” — zbędne.
- Porównań liczbowych „przed/po Unibep” w rozdziale wyników — ewentualnie jedna linia w aneksie o kontroli jakości danych.

---

## Angielski abstract / methods (1–2 zdania)

Daily equity prices for Unimot S.A. (ticker UNT) are taken from Yahoo Finance series **UNT.WA** (corporate-action adjusted). Log returns and market-model abnormal returns use the WIG index as benchmark; market capitalization is price times a constant share-count proxy (approx. 8.2 million shares).
