# Mapa hipotez H1–H11 → filary, tabele, status i luki

**Źródło hipotez:** `Hipotezy_i_konspekt_magisterki.docx`  
**Stan empiryki:** 2026-07 (po korekcie UNT, recode M&A, rozdziały Dane/Wyniki)  
**Zasada z konspektu:** hipotezę blokową uznaje się za wspartą dopiero przy **zbieżności ≥ 2 filarów** (case / tekst / event study / panel).

---

## 0. Legenda statusu

| Status | Znaczenie |
|--------|-----------|
| **WS** | Wsparta (dwa+ filary, spójny kierunek) |
| **CZ** | Częściowo wsparta (1 silny filar lub mieszane znaki) |
| **NK** | Nie potwierdzona ilościowo / brak efektu w dostępnych testach |
| **OT** | Otwarta — brak kluczowej operacjonalizacji lub danych |
| **WY** | Wyłączona z wersji bazowej (świadomie; wariant „bez newsów”) |

Filary:

| Kod | Filar |
|-----|--------|
| **I** | Studia przypadku + dokumenty + NIK |
| **II** | NLP / ton komunikacji |
| **III** | Event study (ESPI → CAR) |
| **IV** | Panel kwartalny / modele dyskretne |

---

## 1. Hipoteza główna (HG)

> Czynniki behawioralne (inklinacje menedżerskie + sentyment otoczenia) współwyjaśniają decyzje inwestycyjno-finansowe i reakcję rynku, po kontroli fundamentów i szoków 2020–2025.

| | |
|--|--|
| **Status** | **CZ** (bez H10 / pełnego panelu H7–H9 HG nie domyka się w pełnym brzmieniu konspektu) |
| **Co już jest** | Filary I+III w dużej części; II częściowo (TONE MVP); IV panel zbudowany, bez regresji decyzji |
| **Jak domknąć** | (1) tabela statusów H1–H11 w dyskusji; (2) jedna prosta regresja panelowa CAPEX~TONE (H7); (3) jawne wyłączenie H10 lub wariant „bez newsów” w HG |
| **Sformułowanie ostrożne** | „Praca dokumentuje *przejawy* inklinacji w decyzjach i komunikacji oraz heterogeniczną reakcję rynku na ESPI; nie estymuje pełnego, przyczynowego wkładu sentymentu medialnego.” |

---

## 2. Blok A — inklinacje w decyzjach strategicznych

### H1 — Overconfidence / złudzenie planowania (megaprojekty)

| Element | Treść |
|---------|--------|
| **Treść** | Niedoszacowanie CAPEX i czasu; rewizje w górę; kategoryczność komunikacji |
| **Kotwice** | Olefiny III (8,3 → 45–51 mld); Jaworzno 910 MW (awarie/roszczenia — **słabiej zebrane**) |
| **Filar I** | **Gotowy:** `kalendarium_olefiny_iii.md` + tabela deklaracja vs ex post |
| **Filar II** | **Częściowo:** CERTAINTY w korpusie, ale nie per projekt Olefiny |
| **Filar III** | **Słabo:** CAR na datach FID/EPCC/rewizja/stop ≈ 0 w [−1,+1] (`ROZDZIAL_Wyniki` §4.4.1) — rynek nie „karze” każdego kamienia milowego |
| **Filar IV** | **Brak** TIME_TO / regresji |
| **Tabele / pliki** | Case Tabela 4; kalendarium Olefiny; opcjonalnie ścieżka CAPEX w AR |
| **Status** | **CZ** — silny dowód dokumentacyjny (I), słaby/neutralny CAR (III) |
| **Luka** | Jaworzno (TPE) — noty w AR/ESPI nie wyciągnięte do kalendarium; CERTAINTY nie zlinkowany do epizodów |
| **Werdykt do dyskusji** | H1 **wsparta jakościowo** na Olefinach; nie wymaga istotnego ujemnego CAR, bo inklinacja dotyczy *decyzji*, nie natychmiastowej wyceny |

---

### H2 — Eskalacja zaangażowania / koszty utopione

| Element | Treść |
|---------|--------|
| **Treść** | Po negatywnych szokach późniejsze odpisy/wyjście; TIME_TO_IMPAIRMENT; TONE × szok |
| **Kotwice** | Ostrołęka C (odpisy, NIK); Olefiny stop XII 2024 po dużych nakładach |
| **Filar I** | **Gotowy:** `kalendarium_ostroleka_c.md`, `kalendarium_olefiny_iii.md`, NIK PDF |
| **Filar II** | **Brak** interakcji NEG_SHOCK × TONE (brak panelu odpisów) |
| **Filar III** | **Częściowo:** Ostrołęka średni CAR[−1,+1] **−0,82%** (twardsze sygnały); Olefiny stop ≈ 0 |
| **Filar IV** | **Brak** logit/przeżycia TIME_TO_IMPAIRMENT |
| **Tabele / pliki** | Case Tabela 4; NIK Ostrołęka; QUAL `escalation` |
| **Status** | **CZ** — oś czasu i NIK (I) + umiarkowany CAR Ostrołęka (III) |
| **Luka** | Modele survival/logit; jawny „pierwszy sygnał ostrzegawczy” → data odpisów dla wszystkich spółek |
| **Werdykt** | H2 **wsparta jakościowo**; ilościowe opóźnienie odpisów = luka, nie fałsyfikacja |

---

### H3 — Hubris w M&A (Roll)

| Element | Treść |
|---------|--------|
| **Treść** | Przeszacowanie synergii; niekorzystne remedium; CAR akwizytora |
| **Kotwice** | Orlen: Energa, Lotos, PGNiG; NIK Lotos (remedium poniżej wartości) |
| **Filar I** | **Gotowy:** `kalendarium_ma_orlen.md` + NIK Lotos |
| **Filar II** | — |
| **Filar III** | **Gotowy:** kategoria `transakcje_MA` n=126; case ma_orlen n=10; Tabela 2 + §4.4.3 |
| **Wynik III** | Średni CAR M&A ≈ 0 (BMP n.s.), znak \*\*\* (więcej CAR>0); **ścieżka Orlen heterogeniczna** (KE Lotos −3% / −6%; rejestracja PGNiG +3,4%) |
| **Filar IV** | — |
| **Status** | **CZ** — NIK + kalendarium (I) wspierają hubris *ex post*; rynek **nie** daje jednolitej kary CAR (III) |
| **Luka** | Tabela „synergie deklarowane vs zrealizowane” (liczby z prezentacji); wyceny remedium w aneksie |
| **Werdykt** | H3 **wsparta dokumentacyjnie (NIK)**; **nie** formułować jako „rynek systematycznie karze M&A Orlen” |

---

### H4 — Status quo / awersja do strat (węgiel, NABE)

| Element | Treść |
|---------|--------|
| **Treść** | SP odracza dezinwestycje vs prywatni (ZEP) |
| **Kotwice** | NABE 2021→2025; ZEP trajektoria odejścia od brunatnego |
| **Filar I** | **Gotowy:** `kalendarium_nabe.md` + MAP PDF + notatka ZEP |
| **Filar III** | **Częściowo:** n=5 matched; reakcje mieszane (ENA+, PGE− na porozumieniu) |
| **Filar IV** | — |
| **Status** | **CZ / WS jakościowo** — kalendarium i kontrast ZEP wystarczają na filar I |
| **Luka** | Brak ESPI na rezygnację MAP 2025-07-09; formalne porównanie dat dezinwestycji SP vs ZEP w jednej tabeli |
| **Werdykt** | H4 **wsparta kalendarium i kontrastem ZEP**; CAR nie jest głównym testem |

---

### H5 — Herding strategii transformacji

| Element | Treść |
|---------|--------|
| **Treść** | Podobieństwo tekstów strategii, zbieżność dat i celów OZE |
| **Filar I** | **Częściowo:** `kalendarium_strategie.md` + PDF STRAT |
| **Filar II** | **Brak** `STRAT_SIM` (cosine similarity dokumentów) |
| **Filar III** | CAR strategii ≈ 0 — nie testuje herdingu |
| **Status** | **OT / CZ** — materiały zebrane, **brak miary podobieństwa** |
| **Luka priorytetowa** | Macierz podobieństwa strategii (tf-idf/embeddings) + tabela dat publikacji 2021–2025 |
| **Werdykt** | Na razie tylko opis zbieżności narracji; nie oznaczać H5 jako potwierdzonej |

---

### H6 — Kotwiczenie / mental accounting (dywidenda, FIZ)

| Element | Treść |
|---------|--------|
| **Treść** | Payout sztywny vs FCF; FIZ jako osobna „kieszeń” |
| **Kotwice** | Orlen polityka DPS; JSW FIZ vs strata 2024 |
| **Filar I** | **Gotowy:** `kalendarium_dywidenda_fiz.md` + tabele IR |
| **Filar III** | **Słabo:** małe CAR na polityce dywidendy; kategoria dywidenda n=38, CAR n.s. |
| **Filar IV** | **Brak** regresji payout ~ FCF / sztywności |
| **Status** | **CZ** — silny filar I; brak ekonometrii payout |
| **Luka** | Wykres DPS vs NI/FCF Orlen; ścieżka aktywów FIZ JSW vs CAPEX/wynik |
| **Werdykt** | H6 **wsparta epizodami** (I); nie twierdzić o „sztywności statystycznej” bez panelu |

---

## 3. Blok B — komunikacja i panel

### H7 — Ton → CAPEX i dźwignia (t+1)

| Element | Treść |
|---------|--------|
| **Operacjonalizacja** | `capex_int_{t+1}`, `Δnet_debt/A` ~ `TONE_MGR` lag + FE + kontrole |
| **Output** | `panel_h7_tone_capex.py` → `h7_panel_summary.md`, `tables/tabela_h7_*.csv` |
| **Próba** | n≈66–68, 7 spółek; TONE non-null 74/168 |
| **Wynik CAPEX (spec A, FE)** | β(TONE_lag)=**−0,031**, p=**0,83** — **nieistotny**, znak przeciwny do H7 |
| **Wynik CAPEX (spec F, pooled)** | β=**−0,52\***, p=0,058 — ujemny (przeciwnie do „optymizm → więcej CAPEX”) |
| **Wynik finansowanie (spec D)** | β(TONE→Δnet_debt/A)=**+1,13\*\***, p=0,033 — dodatni przyrost długu netto (ostrożnie: niska moc, możliwa spekulacja) |
| **Status** | **NK** dla kanału CAPEX; **CZ/eksploracyjnie** dla długu (nie w hipotezie bazowej H7 jako „więcej inwestycji”) |
| **Werdykt** | H7 **nie potwierdzona** w brzmieniu „wyższy ton → wyższy CAPEX”. Korelacja TONE–capex_lead ≈ **−0,20**. Panel zbyt słaby na silne wnioski. |

---

### H8 — Interakcja TONE × CFO (inwestycje z własnej gotówki)

| Element | Treść |
|---------|--------|
| **Output** | Spec E w `h7_panel_summary.md` |
| **Wynik** | `TONE×cfoa`: β≈**+5,42\***, p=0,087; TONE i cfoa osobno n.s. |
| **Status** | **CZ/słabe** — interakcja na granicy 10%, n=66, G=7; **nie** traktować jako potwierdzenie |
| **Werdykt** | H8 **nie potwierdzona wiarygodnie**; najwyżej „słaby sygnał eksploracyjny” |

---

### H9 — TONE_FUND_GAP i korekta CAR [+2,+20]

| Element | Treść |
|---------|--------|
| **Operacjonalizacja** | Luka tonu vs fundamenty; CAR krótkie vs średnie |
| **Dane** | TONE jest; **TONE_FUND_GAP nie zbudowany** |
| **Częściowy wynik** | Corr(CAR[−1,+1], TONE_lag) ≈ −0,03 — brak prostej zależności |
| **Status** | **OT / NK** na uproszczonym teście |
| **Luka** | Definicja gap (np. residual tonu na ROA/ret); CAR okno [+2,+20] w `compute_car` / osobny skrypt |
| **Werdykt** | H9 **nie potwierdzona** w MVP; nie budować wokół niej głównego wkładu |

---

## 4. Blok C — newsy i kryzys

### H10 — Sentyment newsowy i uwaga medialna

| Element | Treść |
|---------|--------|
| **Dane** | `raw/news/` puste; checklista: wariant **bez newsów** |
| **Status** | **WY** z wersji bazowej |
| **Co napisać w metodach/dyskusji** | „H10 wyłączono z braku historycznej warstwy newsowej; wkład pracy opiera się na ESPI, case i komunikacji IR.” |
| **Opcja przyszła** | PAP/bankier w oknach wokół top-50 ESPI — tylko jeśli czas |

---

### H11 — Moderacja niepewnością (2020, 2022–23 vs 2024–25)

| Element | Treść |
|---------|--------|
| **Operacjonalizacja** | Split CAR po podokresach + kategorie ESPI |
| **Dane / output** | `stat_tests_h11_periods.py` → `h11_periods_summary.md`, `tables/tabela_h11_*.csv` |
| **Wynik (grand mean CAR[−5,+5], wszystkie ESPI)** | 2020 **+0,45%** (n=380); 2022–23 **−0,07%** (n=779); 2024–25 **+0,22%** (n=732); BMP n.s. we wszystkich |
| **M&A CAR[−5,+5]** | 2020 **−1,19%\*** (n=22); 2022–23 **+0,42%** (n=62, znak\*\*\*); 2024–25 **−0,34%** (n=21) |
| **Status** | **CZ / NK w brzmieniu „wyższy średni CAR w kryzysie”** — grand mean **nie** jest najwyższy w 2022–23; w 2020 M&A istotnie ujemne; w 2022–23 więcej CAR>0 (znak), niekoniecznie wyższa średnia |
| **Werdykt do dyskusji** | H11 **przeformułować**: w kryzysie zmienia się **struktura** reakcji (M&A, akcjonariat, regulacje), nie uniwersalnie „silniejszy dodatni CAR”. Ostrożnie: *moderacja kanałów*, nie *większa średnia premia*. |
| **Dalsze (opcjonalne)** | Case H1–H6 tylko w 2022–23 vs 2024–25; split tonu po podokresach |

---

## 5. Macierz skrócona: hipoteza × status × następny krok

| H | Status | Główny filar | Następny krok (jeśli w ogóle) |
|---|--------|--------------|------------------------------|
| HG | CZ | I+III | Ująć wyłączenie H10; 1 regresja H7 |
| H1 | CZ | I | Dopisać Jaworzno **lub** zostawić tylko Olefiny |
| H2 | CZ | I (+ III Ostrołęka) | Opcja: TIME_TO (duży koszt) |
| H3 | CZ | I + III | Tabela synergie/NIK w case |
| H4 | CZ≈WS(I) | I | Tabela SP vs ZEP daty |
| H5 | OT | I materiały | **STRAT_SIM** lub obniżyć ambicję H5 |
| H6 | CZ | I | Wykres DPS/FCF + FIZ |
| H7 | **NK** (CAPEX) | IV | Wyniki w `h7_panel_summary.md` |
| H8 | **CZ/słabe** | IV | Interakcja p≈0,09 — nie opierać wkładu |
| H9 | OT/NK | II–III | TONE_FUND_GAP lub porzucić |
| H10 | WY | — | Zostawić wyłączoną |
| H11 | **CZ** (po tabelach) | III | Przeformułować; wyniki w `h11_periods_summary.md` |

---

## 6. Mapowanie na rozdziały pracy (konspekt vs stan)

| Rozdział konspektu | Hipotezy | Stan treści |
|--------------------|----------|-------------|
| R4 case (4.1–4.6) | H1–H6 | Kalendaria + QUAL + CAR case w `ROZDZIAL_Wyniki` §4.4 |
| R5.1 ton opis | H7–H9 tło | `sentiment_*`, sparse |
| R5.2 TONE_FUND_GAP | H9 | **Brak** |
| R5.3 event study | H3, H9, H10 | Tabele 1–3; H10 off; H9 słabo |
| R5.4 panel CAPEX | H7, H8 | Panel jest, **regresji brak** |
| R5.5 logit odpisów | H2 | **Brak** |
| R5.6 podokresy | H11 | **Brak** |
| R6 dyskusja | wszystkie | **Do napisania** z tej mapy |

---

## 7. Rekomendowana strategia domknięcia (realistyczna magisterka)

### Must-have przed oddaniem (niski koszt, wysoki zwrot)

1. **Rozdział 6 (dyskusja):** tabela statusów H1–H11 z kolumną „filary I–IV” (ten plik).  
2. **H11:** CAR [−5,+5] w 3 podokresach (pełna próba + M&A).  
3. **H10:** jednoznaczne wyłączenie w metodach i HG.  
4. **H5:** albo 1 strona porównania dat/celów strategii **bez** similarity, albo mała macierz podobieństwa.  
5. **H6:** 1 wykres/tabela DPS Orlen + ścieżka FIZ JSW (liczby z AR/kalendarium).

### Should-have (jeśli 1–2 dni)

6. **H7:** prosta FE `capex_int ~ TONE_lag + lev + makro + year FE` (N małe → eksploracyjnie).  
7. **H3:** box „deklaracje synergii vs NIK” w case M&A.

### Nice-to-have / nie blokować oddania

8. H8, H9 pełne, survival H2, newsy H10, anotacja NLP, ATURN/AVOL.

---

## 8. Sugerowane sformułowania weryfikacji (do R6)

| H | Sugerowany werdykt w tekście |
|---|------------------------------|
| H1 | „Potwierdzona w materiale dokumentacyjnym Olefin III; rynek nie dostarcza jednolitej kary CAR.” |
| H2 | „Potwierdzona kalendarium Ostrołęki/Olefin i ustaleniami NIK; modele czasu do odpisu poza zakresem oszacowań.” |
| H3 | „Częściowo: NIK i niekorzystne remedium wspierają hubris *ex post*; CAR M&A heterogeniczny, średnia ≈ 0.” |
| H4 | „Potwierdzona kalendarium NABE i kontrastem ZE PAK.” |
| H5 | „Wymaga ostrożności: zbieżność narracji widoczna opisowo; brak formalnej miary herdingu tekstowego.” |
| H6 | „Potwierdzona epizodami dywidendy gwarantowanej i FIZ; bez testu sztywności payout w panelu.” |
| H7–H8 | „H7 nie potwierdzona (ton nie podnosi CAPEX; FE n.s.). H8: słaba interakcja TONE×CFO (p≈0,09), niska moc — eksploracyjnie.” |
| H9 | „Brak wsparcia w prostej korelacji CAR–ton; TONE_FUND_GAP nie zbudowano.” |
| H10 | „Poza zakresem (brak warstwy newsowej).” |
| H11 | „Częściowo: różnice między podokresami w M&A i odsetku CAR>0; brak wyższego grand mean CAR w kryzysie 2022–23.” |

---

## 9. Pliki powiązane

| Plik | Rola |
|------|------|
| `Hipotezy_i_konspekt_magisterki.docx` | Definicje H1–H11 |
| `ROZDZIAL_Dane_i_metody.md` | Metody |
| `ROZDZIAL_Wyniki.md` | Tabele 1–4, case CAR |
| `case_studies/INDEX.md` | QUAL + kalendaria H1–H6 |
| `analytical/case_events_enriched.*` | CAR na datach case |
| `tables/tabela2_*.csv` | CAR × kategoria ESPI |
| `METODOLOGIA_fragmenty_dane.md` | Fragmenty do metod |

---

*Mapa robocza — aktualizuj kolumnę Status po H11/H7.*
