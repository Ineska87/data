# Wyniki badań empirycznych

*Wersja robocza rozdziału z wynikami. Liczby ze stanu pipeline’u po korekcie Unimot (`UNT.WA`) i recode kategorii M&A (2026-07). Tabele liczbowe: `processed/tables/`; wykresy AAR: `processed/plots/`; case: `analytical/case_events_enriched`.*

---

Rozdział przedstawia wyniki w trzech warstwach. Najpierw oceniono jakość dopasowania modelu rynkowego (Tabela 1). Następnie omówiono przeciętne skumulowane stopy nadzwyczajne (CAR) według kategorii komunikatów ESPI oraz testy BMP i znaku (Tabele 2–3). Na końcu zinterpretowano reakcje rynku wokół priorytetowych dat studiów przypadku (H1–H6), powiązanych z kodami behawioralnymi QUAL. Wyniki event study opisują **krótkookresową reakcję inwestorów**, a nie długookresowy efekt realny inwestycji czy fuzji.

## 4.1. Dopasowanie modelu rynkowego

Dla każdego zdarzenia oszacowano model rynkowy w oknie [−250, −11] dni sesyjnych. Tabela 1 podsumowuje mediany \(\hat\beta\) i \(R^2\) oraz liczbę zdarzeń z policzonym CAR (okno referencyjne [−5,+5] przy unikalnym `event_id`).

**Tabela 1. Parametry modelu rynkowego (mediana per spółka)**

| Spółka | Benchmark | \(\beta\) (med.) | \(R^2\) (med.) | n zdarzeń |
|--------|-----------|------------------:|---------------:|----------:|
| PKN (Orlen) | WIG-paliwa | 1,04 | 0,91 | 464 |
| PGE | WIG-energia | 1,26 | 0,90 | 320 |
| TPE (Tauron) | WIG-energia | 1,09 | 0,77 | 386 |
| ENA (Enea) | WIG-energia | 0,95 | 0,65 | 345 |
| JSW | WIG | 1,32 | 0,24 | 367 |
| LWB (Bogdanka) | WIG | 0,93 | 0,17 | 158 |
| UNT (Unimot) | WIG | 0,76 | 0,13 | 247 |
| ZEP (ZE PAK) | WIG | 0,64 | 0,09 | 259 |

Dla PKN i PGE model rynkowy wyjaśnia ok. 90% wariancji zwrotów w oknie estymacji — AR i CAR są relatywnie precyzyjne. Dla TPE i ENA dopasowanie pozostaje dobre (\(R^2\) 0,65–0,77). Dla JSW, LWB, UNT i zwłaszcza ZEP \(R^2\) jest wyraźnie niższe, co oznacza głośniejsze stopy nadzwyczajne i większą wagę analiz wrażliwości bez spółek o słabym dopasowaniu (UNT, ZEP). Łącznie w próbie 2019–2025 uzyskano CAR dla **2 546** z 2 550 zdarzeń (99,8%).

## 4.2. CAR według kategorii ESPI

### 4.2.1. Okno wąskie [−1,+1]

W trzydniowym oknie wokół Day 0 najsilniejszy i statystycznie istotny efekt BMP dotyczy **ratingów i rekomendacji** (\(n=16\)): średni CAR wynosi **+1,40%** (\(t_{\mathrm{BMP}}=2,65\), \(p=0,018\)), a odsetek dodatnich CAR to 75% (test znaku \(p=0,046\)). Wynik ten jest zgodny z intuicją, że komunikaty agencji i biur maklerskich niosą skoncentrowaną informację cenową, choć mała próba nakazuje ostrożność (bootstrapowy 95% PU: ok. +0,5% do +2,3%).

Kategoria **akcjonariat / progi** (\(n=113\)) daje średni CAR **+0,49%** (BMP \(p=0,081\); znak \(p=0,011\)). **Transakcje M&A** (\(n=126\)) w oknie [−1,+1] mają średnią bliską zera (**−0,05%**, BMP nieistotny), przy jednocześnie lekko podwyższonym odsetku CAR dodatnich (58%, znak \(p=0,075\)). **Wyniki finansowe** (\(n=280\)) i **emisja/finansowanie** (\(n=45\)) wykazują ujemne, lecz nieistotne średnie. Duża kategoria „inne” (\(n=930\)) oraz WZA (\(n=448\)) nie generują istotnych średnich CAR w oknie trzydniowym.

### 4.2.2. Okno [−5,+5]

W jedenastodniowym oknie obraz się wyostrza dla części kategorii.

**Tabela 2 (skrót). Średni CAR i testy — pełna próba, okno [−5,+5]**

| Kategoria | n | Śr. CAR | \(t_{\mathrm{BMP}}\) | \(p_{\mathrm{BMP}}\) | \(P(CAR>0)\) | znak |
|-----------|--:|--------:|---------------------:|---------------------:|-------------:|------|
| Rating/rekomendacja | 16 | +1,21% | 1,37 | 0,192 | 63% | — |
| **Akcjonariat/progi** | **113** | **+0,96%** | **2,30** | **0,023\*\*** | **64%** | \*\*\* |
| Dywidenda | 38 | +0,46% | 0,01 | 0,988 | 63% | — |
| Transakcje M&A | 126 | +0,20% | −0,17 | 0,864 | **63%** | \*\*\* |
| Walne zgromadzenie | 448 | +0,13% | 0,51 | 0,608 | 53% | — |
| Zmiany personalne | 272 | +0,04% | 0,65 | 0,517 | 51% | — |
| Inne | 930 | +0,27% | −0,61 | 0,542 | 53% | — |
| Umowy/kontrakty | 231 | −0,33% | 0,04 | 0,968 | 46% | — |
| Wyniki finansowe | 280 | −0,42% | −0,29 | 0,774 | 56% | \* |
| Emisja/finansowanie | 45 | −0,54% | −0,40 | 0,690 | 58% | — |
| Regulacyjne/prawne | 46 | −2,10% | −1,43 | 0,159 | 44% | — |

Najbardziej robustnym wynikiem parametrycznym w tym oknie jest **akcjonariat**: średni CAR ok. **+1 p.p.** przy \(p_{\mathrm{BMP}}=0,023\) i silnym teście znaku. Efekt ten **nie jest jednak stabilny po wykluczeniu Unimot**: w podpróbie bez UNT średnia spada do −0,31% i traci istotność BMP (Tabela 3). Sugeruje to, że część dodatniej reakcji na komunikaty o akcjonariacie/progu pochodzi ze spółki o wyższej idiosynkratycznej zmienności (UNT), a nie z jednorodnego mechanizmu w całym sektorze SP.

**Transakcje M&A** w [−5,+5] mają średnią **+0,20%** (BMP nieistotny), ale **63%** obserwacji z CAR > 0 (test znaku \(p=0,004\)). W oknach [−3,+3] i [−10,+10] odsetek dodatnich CAR pozostaje istotny znakiem, przy nadal nieistotnym BMP. Taki wzorzec — dodatni skew / mediana przy głośnych ujemnych ogonach — jest spójny z heterogenicznymi transakcjami (od drobnych akwizycji OZE po wieloetapowe połączenia Orlen), a nie z jednolitym „efekcie fuzji”. Dla samego PKN w podzbiorze M&A średni CAR[−1,+1] wynosi ok. **−0,08%** (83 zdarzenia) — przeciętna reakcja na komunikaty M&A Orlen w wąskim oknie jest bliska zeru lub lekko ujemna.

**Regulacje/prawo** (\(n=46\)) dają ujemną średnią ok. **−2,1%** w [−5,+5], bez istotności BMP na standardowych poziomach — kierunek jest ekonomicznie sensowny (koszty compliance, kary, ograniczenia), lecz próba jest mała. **Wyniki finansowe** nie generują silnego przeciętnego CAR; publikacje okresowe są częściowo antycypowane, a treść bywa mieszana (zysk vs odpisy).

Wykresy AAR w oknie [−10,+10] (folder `plots/`) służą diagnostyce wycieku przed zdarzeniem i koncentracji reakcji wokół \(t=0\); interpretację szczegółową warto oprzeć na wizualnej inspekcji przy składaniu aneksu.

## 4.3. Analiza wrażliwości (Tabela 3)

Dla okna [−5,+5] powtórzono testy w wariantach: pełna próba, bez UNT, bez ZEP, bez UNT i ZEP.

- **Akcjonariat:** istotność BMP w pełnej próbie **znika bez UNT**; bez ZEP efekt wręcz rośnie (+1,41%, \(p=0,005\)). Wniosek: wynik jest wrażliwy na skład próby płynnościowej.  
- **M&A:** średnia zmienia znak po wykluczeniu ZEP (−0,21%), ale test znaku pozostaje istotny we wszystkich wariantach (ok. 61–65% CAR > 0).  
- **Rating:** wyniki identyczne we wszystkich wariantach (brak UNT/ZEP w tej kategorii).  
- Spółki o niskim \(R^2\) nie „tworzą” efektu ratingów; mogą natomiast zaburzać kategorie z dużym udziałem ich komunikatów.

## 4.4. Studia przypadków i CAR wokół dat H1–H6

Mapa 52 priorytetowych dat case → ESPI/CAR obejmuje **45 dopasowań** (86,5%). Poniżej: średnie CAR dla dopasowanych wierszy oraz wybrane daty kluczowe. CAR wyrażono w procentach (1 = 100 p.p. w surowych danych parquet → poniżej w %).

**Tabela 4. Średni CAR na dopasowanych datach case**

| Case (hipoteza) | n match | Śr. CAR[−1,+1] | Mediana [−1,+1] | Śr. CAR[−5,+5] |
|-----------------|--------:|---------------:|----------------:|---------------:|
| Olefiny III (H1/H2) | 7 | −0,08% | +0,02% | +0,08% |
| Ostrołęka C (H2) | 7 | −0,82% | −0,78% | −0,21% |
| M&A Orlen (H3) | 10 | −0,34% | ≈0% | −1,40% |
| NABE (H4) | 5 | +0,86% | +1,22% | +1,34% |
| Strategie (H5) | 10 | +0,06% | +0,18% | +1,50% |
| Dywidenda / FIZ (H6) | 6 | −0,25% | +0,13% | +4,01% |

*Uwaga:* małe \(n\) — to nie testy populacyjne, lecz opis reakcji na wybrane, merytorycznie kluczowe komunikaty.

### 4.4.1. Olefiny III / Nowa Chemia (H1–H2, overconfidence → escalation)

FID i komunikat o inwestycji (2021-05-24) wiążą się z lekko dodatnim CAR[−1,+1] (**+0,49%**), natomiast umowa EPCC (2021-06-22) — z **−0,82%**. Rewizja CAPEX (2023-06-29) i komunikaty o analizie strategicznej / zatrzymaniu projektu (XI–XII 2024) dają CAR bliskie zeru w wąskim oknie (rzędu od −0,16% do +0,05%). Rynek **nie wyceniał** kolejnych etapów eskalacji CAPEX jako serii dużych, jednokierunkowych szoków w [−1,+1]; część informacji mogła być stopniowo wchłaniana lub mieszana z innymi newsami Orlen. Wynik jest spójny z narracją behawioralną opartą na dokumentach (niedoszacowanie kosztów ex ante, rewizje, stop), ale **nie potwierdza** hipotezy o trwałej, silnie ujemnej natychmiastowej reakcji na każdy kamień milowy.

### 4.4.2. Ostrołęka C (H2, escalation / framing)

Komunikaty Enei o zawieszeniu prac (2020-02-14) i rozliczeniu z generalnym wykonawcą (2022-03/04) wiążą się z ujemnym CAR[−1,+1] rzędu **−1,4% do −1,9%**. Odpisy (2020-05-19) dają reakcję bliską zera. Średnia dla case Ostrołęka (**−0,82%** w [−1,+1]) jest wyraźniej ujemna niż dla Olefin — rynek reagował silniej na twarde sygnały wstrzymania i rozliczenia projektu węglowego niż na późniejsze reframingi Orlen wokół Nowej Chemii w wąskim oknie.

### 4.4.3. M&A Orlen: Energa, Lotos, PGNiG (H3, hubris_ma)

Ścieżka jest heterogeniczna. Wezwanie na Energę (2019-12-05): CAR[−1,+1] **−1,18%**. Zgoda KE na Energę (2020-03-31): **+0,85%**. Finalizacja Energa (2020-04-30): blisko zera w [−1,+1], dodatnia w [−5,+5]. Warunkowa zgoda KE na Lotos (2020-07-14): silnie ujemna (**−3,21%** / **−6,05%** w [−5,+5]) — koszt remedium i niepewność antymonopolowa. Plany połączenia Lotos/PGNiG (VI–VII 2022) znowu ujemne w [−1,+1] (ok. **−0,7%** i **−3,2%**). Rejestracja połączenia z PGNiG (2022-11-02): wyraźnie dodatnia (**+3,41%** / **+3,21%**).

Przeciętnie case M&A Orlen ma lekko ujemny CAR[−1,+1] (**−0,34%**) i bardziej ujemny CAR[−5,+5] (**−1,4%**). Nie ma jednolitego „premii za empire-building”; raczej **karę za etapy niepewności regulacyjnej i parytetów**, z pozytywną reakcją na domknięcie PGNiG. To wspiera ostrożne sformułowanie H3: hubris/M&A jako narracja ex ante w dokumentach, przy rynkowej wycenie zdominowanej przez warunki transakcji i remedium, nie przez euforię fuzji.

### 4.4.4. NABE i dezinwestycje węglowe (H4)

Porozumienie NABE (2021-07-23) jest zróżnicowane między emitentami: Enea **+2,9%**, Tauron **+1,2%**, PGE **−1,1%** w [−1,+1]. Zbycie Tauron Wydobycie (2022-10-12) silnie dodatnie (**+3,9%** / **+6,5%**). Propozycja SP wobec PGE GiEK (2023-07-14) ujemna (**−2,6%**). Średnia case NABE na dopasowanych datach jest dodatnia, ale \(n=5\) i brak ESPI na decyzję MAP 2025-07-09 ograniczają generalizację. Hipoteza *status quo* (odkładanie wydzielenia) lepiej opiera się na kalendarium i dokumentach niż na jednolitym znaku CAR.

### 4.4.5. Strategie (H5) oraz dywidenda / FIZ (H6)

Publikacje strategii dają przeciętnie CAR bliski zera w [−1,+1] i umiarkowanie dodatni w [−5,+5] — komunikaty strategiczne są długie, wielowątkowe i częściowo antycypowane. Polityka dywidendowa w strategiach Orlen (2023-02-28, 2025-01-09) i uchwała ZWZ (2025-06-05) wiążą się z małymi dodatnimi CAR[−1,+1] (ok. **+0,1% do +0,2%**). Komunikaty JSW o FIZ (2022) są ujemne w [−1,+1] (ok. **−1,1%**), przy dodatnim [−5,+5] — możliwa rotacja informacji w dłuższym oknie. Dni prawa do dywidendy często nie mają ESPI i nie wchodzą do CAR.

### 4.4.6. Kody QUAL a CAR (deskryptywnie)

Na dopasowanych wierszach case: komunikaty oznaczone jako **framing** mają dodatnią średnią CAR[−1,+1] (ok. **+0,66%**, \(n=13\)), **escalation** i **overconfidence** — ujemną (ok. **−0,55%** i **−0,99%**), **hubris_ma** — bliską zera. To są małe podpróby i **nie** zastępują testów na pełnej próbie ESPI; służą porządkowaniu narracji w studiach przypadku.

## 4.5. Podokresy niepewności (H11)

Hipoteza H11 przewiduje silniejsze przejawy zależności behawioralnych / reakcji rynku w podokresach skrajnej niepewności (**2020**, **2022–2023**) niż w fazie **normalizacji (2024–2025)**. Poniżej: średnie CAR z pełnej próby ESPI (testy BMP i znaku jak w §4.2). Pełne tabele: `tables/tabela_h11_periods.csv`, podsumowanie: `h11_periods_summary.md`.

**Tabela 5. CAR[−5,+5] — wszystkie zdarzenia ESPI, pełna próba**

| Podokres | n | Śr. CAR | Mediana | BMP | P(CAR>0) |
|----------|--:|--------:|--------:|-----|----------|
| 2020 (pandemia) | 380 | +0,45% | −0,15% | n.s. | 48% |
| 2022–2023 (kryzys en.) | 779 | −0,07% | +0,18% | n.s. | 53% \* |
| 2024–2025 (normalizacja) | 732 | +0,22% | +0,33% | n.s. | 58% \*\*\* |

**Tabela 6. Transakcje M&A — CAR w podokresach**

| Podokres | n | CAR[−1,+1] | CAR[−5,+5] | Uwagi |
|----------|--:|-----------:|-----------:|-------|
| 2020 | 22 | **−0,85%\*\*** | **−1,19%\*** | Ujemna średnia, BMP istotny/marg. |
| 2022–2023 | 62 | +0,16% | +0,42% | BMP n.s.; **znak \*\*\*** (ok. 69% CAR>0) |
| 2024–2025 | 21 | −0,77% | −0,34% | n.s., małe n |

W oknie [−5,+5] **akcjonariat** jest najsilniejszy w 2020 (+3,0%, n=21), słabszy w 2022–23 i 2024–25. **Regulacje** dają mieszane znaki przy bardzo małych n (8–11). Wyniki **bez UNT+ZEP** nie zmieniają obrazu grand mean (BMP nadal n.s.).

**Wniosek do H11.** Nie widać prostego wzorca „wyższy średni CAR w kryzysie”. Wręcz przeciwnie: w 2022–2023 grand mean jest najbliższy zeru, a w 2020 M&A są istotnie ujemne. Silniejszy jest natomiast **odsetek dodatnich CAR** w niektórych oknach i podokresach (m.in. 2022–23 i 2024–25 dla wszystkich zdarzeń w teście znaku) oraz **zmiana struktury** reakcji w kategorii M&A. H11 należy więc weryfikować jako hipotezę o **moderacji kanałów i heterogeniczności**, a nie o uniwersalnie większej przeciętnej premii rynkowej w latach kryzysu.

## 4.6. CAR a ton zarządu (uzupełnienie)

W podpróbie zdarzeń z dostępnym \(TONE\) z poprzedniego kwartału korelacja Pearsona CAR[−1,+1] z tonem jest bliska zeru (ok. **−0,03**, \(n\approx 770\)). Podział na tercyle tonu nie ukazuje monotonicznej, silnej zależności. Warstwa NLP pozostaje **deskryptywna** i ograniczona pokryciem tekstów; nie opiera się na niej główny wniosek pracy.

## 4.6a. Panel: ton a CAPEX i finansowanie (H7–H8, eksploracyjnie)

Zgodnie z konspektem panel nie jest modelem głównym (7 spółek, \(TONE\) w 74/168 komórkach). Oszacowano FE (within + dummy roku) z SE klastrami po spółce (\(G=7\)).

**Tabela 7. H7/H8 — wybrane współczynniki przy \(TONE_{t-1}\)** (szczegóły: `h7_panel_summary.md`)

| Spec | Zależna | n | \(\hat\beta_{TONE}\) | p | Interpretacja robocza |
|------|---------|--:|---------------------:|--:|------------------------|
| A (FE + kontrole) | \(\mathrm{capex\_int}_{t+1}\) | 66 | −0,031 | 0,83 | n.s., znak przeciw H7 |
| B (FE, tylko ton) | \(\mathrm{capex\_int}_{t+1}\) | 67 | −0,040 | 0,76 | n.s. |
| D (FE) | \(\Delta D^{net}/A\) | 67 | **+1,13\*\*** | 0,03 | ton → większy przyrost długu netto? |
| E (H8) | \(\mathrm{capex\_int}_{t+1}\) | 66 | interakcja TONE×CFO **+5,42\*** | 0,09 | słaby sygnał, niska moc |
| F (pooled + state) | \(\mathrm{capex\_int}_{t+1}\) | 66 | **−0,52\*** | 0,06 | ujemny (przeciwnie do H7) |

Korelacja \(TONE_{lag}\)–\(\mathrm{capex}_{t+1}\) wynosi ok. **−0,20**. **H7 w brzmieniu „wyższy ton → wyższe inwestycje” nie znajduje wsparcia.** Dodatni efekt tonu na przyrost długu netto (spec D) jest ciekawy deskryptywnie, ale przy \(G=7\) nie stanowi solidnego potwierdzenia agresywniejszego finansowania. H8 (interakcja z CFO) pozostaje na granicy 10% i nie powinna dźwigać wniosków pracy.

## 4.7. Synteza wyników

1. **Model rynkowy** jest wiarygodny dla dużych, płynnych spółek (PKN, PGE, TPE, ENA); dla UNT/ZEP AR są głośniejsze.  
2. W pełnej próbie ESPI **najbardziej istotny parametrycznie** efekt w [−5,+5] dotyczy **akcjonariatu**, ale jest **wrażliwy na Unimot**.  
3. **Ratingi** dają silną dodatnią reakcję w [−1,+1] przy małym \(n\).  
4. **M&A** nie ma istotnej średniej CAR (BMP), lecz **istotnie więcej** obserwacji z CAR > 0; ścieżka Orlen (H3) jest heterogeniczna (kara za niepewność KE/remedium, plus na domknięcie PGNiG).  
5. **Case CAPEX** (Olefiny, Ostrołęka): silniejsze ujemne reakcje przy twardych sygnałach wstrzymania/rozliczenia (Ostrołęka) niż przy wieloletnim łańcuchu rewizji Olefin w wąskim oknie.  
6. **Ton zarządu** nie współgra silnie z CAR w dostępnej podpróbie.  
7. **H11 (podokresy):** brak wyższego grand mean CAR w 2022–23; w 2020 M&A ujemne; różnice dotyczą raczej **struktury i znaku** reakcji niż uniwersalnej „siły kryzysu”.  
8. **H7 (panel):** ton **nie** podnosi CAPEX (FE n.s., korelacja ujemna); H8 interakcja TONE×CFO tylko słabo (p≈0,09).

Wyniki te należy czytać łącznie z ograniczeniami z rozdziału metod (brak godzin ESPI dla PKN, regułowa klasyfikacja tytułów, dualne źródła rachunkowe, brak newsów). Następny rozdział (dyskusja) może powiązać wzorce CAR z hipotezami behawioralnymi bez nadinterpretacji nieistotnych średnich.

---

## Nota dla autora (usuń przed oddaniem)

| Artefakt | Ścieżka |
|----------|---------|
| Ten rozdział | `data/processed/ROZDZIAL_Wyniki.md` |
| Tabela 1–3 CSV/TeX | `data/processed/tables/` |
| AAR PNG | `data/processed/plots/` |
| Case + CAR | `data/processed/analytical/case_events_enriched.*` |
| Statystyki | `data/processed/stat_tests_results.csv` |

**Do zrobienia przy składzie:** wstawić numery tabel zgodne ze spisem; dodać odwołania do rysunków AAR; w dyskusji zestawić H1–H6 z §4.4; nie twierdzić o „dowodzie hubris” na podstawie średniej M&A ≈ 0.
