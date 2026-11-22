# Rozdział 4. Przejawy czynników behawioralnych w decyzjach strategicznych — wielokrotne studium przypadku

*Wersja robocza R4. Oparta na kalendariach `case_studies/kalendarium_*.md`, materiałach NIK/IR oraz mapowaniu CAR (`case_events_enriched`: 45/52 dat). Kody QUAL: zob. `INDEX.md`. Liczby CAPEX/NIK cytuj z ESPI/PDF — w razie rozjazdu z prasą priorytet ma ESPI.*

---

Rozdział dokumentuje **przejawy** inklinacji menedżerskich na materiale decyzyjnym 2020–2025. Jednostką analizy jest **epizod** (ciąg decyzji i komunikatów), a nie pojedynczy współczynnik regresji. Dla każdego case podano: (i) kontekst i aktorów, (ii) ścieżkę deklaracja → realizacja, (iii) kody QUAL, (iv) most do event study (średnie CAR na datach zmapowanych). Interpretacja behawioralna jest **hipotezą roboczą** zbieżną z faktami; alternatywy agencyjne i polityczne omówiono w rozdziale dyskusji.

**Tabela 4.0. Case → hipotezy, pokrycie ESPI/CAR**

| Case | H | n dat mapy | Matched | Śr. CAR[−1,+1] | Śr. CAR[−5,+5] |
|------|---|----------:|--------:|---------------:|---------------:|
| Olefiny III / Nowa Chemia | H1, H2 | 8 | 7 | −0,08% | +0,08% |
| Ostrołęka C | H2 (H1, H3) | 7 | 7 | **−0,82%** | −0,21% |
| M&A Orlen | H3 | 10 | 10 | −0,34% | **−1,40%** |
| NABE | H4 | 8 | 5 | +0,86% | +1,34% |
| Strategie | H5 | 11 | 10 | +0,06% | +1,50% |
| Dywidenda / FIZ | H6 | 8 | 6 | −0,25% | +4,01%* |

\* Duża mediana/średnia w [−5,+5] przy małym \(n\) — interpretować ostrożnie (m.in. epizody JSW).  
Źródło: `case_events_enriched.parquet`.

---

## 4.1. Olefiny III → Nowa Chemia (Orlen) — H1, H2

### 4.1.1. Kontekst

Projekt rozbudowy kompleksu olefin w Płocku (później reframing **Nowa Chemia**) był flagową inwestycją petrochemiczną Orlenu w dekadzie 2020. Wpisuje się w strategię multienergetyczną i memoranda o współpracy petrochemicznej (w tym kontekst partnerstw sygnalizowanych przy fuzji Lotos — wg NIK część memorandum nie zmaterializowała się). Dla BCF epizod jest kotwicą **overconfidence / planning fallacy (H1)** oraz **eskalacji (H2)**.

### 4.1.2. Ścieżka deklaracja vs realizacja

| Moment | CAPEX (oficjalnie ESPI) | Harmonogram | EBITDA inkr. | Interpretacja QUAL |
|--------|-------------------------|-------------|--------------|-------------------|
| V–VI 2021 (FID / EPCC) | **~13,5 mld PLN** | budowa do 1Q2024, produkcja **pocz. 2025** | **~1 mld/rok** | `overconfidence` |
| VI 2023 (rewizja) | **~25 mld** | koniec **1H2027** | **>1 mld** | `escalation`, `framing` (wojna, łańcuchy) |
| XI 2024 (analiza) | kontynuacja **45–51 mld** | nie wcześniej **2030** | — | `escalation` |
| XII 2024 (stop zakresu) | wydane **12,6 mld** (3Q2024); nowy zakres **~34 mld** | produkcja nie wcześniej 2030 | **0,55–0,80 mld (2030)** | wyjście + `framing` („Nowa Chemia”) |
| III 2025 (FY2024) | łącznie od 2021 **14,1 mld**; odpis NC **5,2 mld** (Q4) | — | — | uznanie straty |
| IV 2026 (budżet NC)* | **35,8 mld** | etylen 2029 / pełne 2030 | **0,6 mld (2035)** | kontynuacja w nowej ramie |

\* Poza oknem event study 2019–2025 — kontekst łańcucha decyzji.

**Uwaga metodologiczna:** komunikat prasowy z XII 2024 podawał „pierwotnie 8,3 mld”, podczas gdy ESPI 27 i 34/2021 wskazują **13,5 mld**. W pracy primary source = **ESPI**; 8,3 mld traktować jako narrację komunikacyjną (ew. inny zakres/faza).

### 4.1.3. Kąt behawioralny

1. **H1:** skok CAPEX 13,5 → 25 → (kontrfaktycznie) 45–51 mld przy utrzymywaniu narracji EBITDA rzędu 1 mld w 2021–2023 jest zgodny z niedoszacowaniem kosztów i sztywnością punktu odniesienia.  
2. **H2:** decyzja o stopie następuje dopiero po wydaniu rzędu **13–14 mld** i analizie „kontynuacja nierentowna” — wzorzec późnego wyjścia po skumulowanych nakładach.  
3. **Framing:** rebrand na Nowa Chemia i nowy budżet 34–36 mld pozwala kontynuować petrochemię bez utrzymywania etykiety „Olefiny III” jako porażki projektu w dotychczasowym zakresie.  
4. **CAR:** na 7 zmapowanych datach średni CAR[−1,+1] ≈ **0**; rynek nie „karze” każdego kamienia milowego w wąskim oknie — informacja jest rozłożona, a Orlen generuje równolegle inne ESPI. To **nie unieważnia** H1/H2 dokumentacyjnych.

### 4.1.4. Wniosek case

Olefiny/Nowa Chemia to najsilniejszy w próbie przykład **planowania optymistycznego i eskalacji z reframingiem**. Filar I (dokumenty) jest wystarczający do częściowego wsparcia H1–H2; filar III (CAR) jest neutralny.

---

## 4.2. Ostrołęka C (Enea / Energa / Orlen) — H2

### 4.2.1. Kontekst

Elektrownia Ostrołęka C to projekt bloku ~1000 MW w formule SPV (Enea 50% / Energa 50%), początkowo **węglowy**, z kontraktem z konsorcjum GE (2018) i poleceniem rozpoczęcia prac (NTP). Po przejęciu Energi przez Orlen (IV 2020) zmienił się układ interesariuszy i narracja technologiczna (gaz).

### 4.2.2. Ścieżka węgla → gaz → rozliczenie

| Moment | Decyzja / fakt | Kwoty kluczowe | QUAL |
|--------|----------------|----------------|------|
| 2018 | Kontrakt EPC, NTP, start budowy | blok węglowy ~1000 MW | `overconfidence` (NIK: NTP bez pełnej informacji) |
| II 2020 | Zawieszenie finansowania przez Enea i Energę | — | punkt zwrotny `escalation` |
| 30.04.2020 | Orlen finalizuje Energę | — | kontekst H3 |
| 19.05.2020 | Orlen: zaangażowanie tylko przy **gazie** | — | `framing` multienergii |
| 19.05.2020 | Odpis aktywów SPV (węgiel) | **1 027 mln zł**; wpływ na wynik Energa 2019 **−443 / −453 mln** | `escalation` |
| VIII 2020 | Enea: kontynuacja gaz; rezerwy/odpisy | rezerwa **~219 mln**, odpis pożyczek **~137 mln** | `framing` + koszty wyjścia |
| 2021 | Rozbiórka elementów węglowych; ścieżka CCGT | — | zmiana technologiczna |
| III–IV 2022 | Rozliczenie z generalnym wykonawcą | **958 mln netto** (po **479 mln**/strona) | `escalation` |
| NIK 2020–21 / 2025 | Oceny negatywne; strata **>1,3 mld**; rozliczenie 2022 kwestionowane jako niegospodarne | zawiadomienie do prokuratury (2025) | audyt ex post |

### 4.2.3. Kąt behawioralny i CAR

Ostrołęka ilustruje **koszt utopiony w skali systemowej**: decyzja NTP i kontrakt mocowy, następnie zawieszenie, odpisy rzędu miliarda, rozbiórka i kosztowne rozliczenie z GW. NIK dostarcza zewnętrznej oceny negatywnej na etapie realizacji i rozliczenia — silniejszy filar niż sam CAR.

Na 7 zmapowanych datach średni CAR[−1,+1] wynosi ok. **−0,82%** (mediana podobna) — wyraźniej ujemny niż przy Olefinach. Twarde sygnały (zawieszenie, rozliczenie) są spójne z ujemną reakcją rynku; odpisy bywają częściowo antycypowane.

### 4.2.4. Wniosek case

H2 uzyskuje **wsparcie dokumentacyjne (NIK + ESPI)** oraz **umiarkowane wsparcie rynkowe**. Link do H3: finalizacja Energi zmienia reguły gry w SPV i umożliwia reframing gazowy Orlenu.

---

## 4.3. Konsolidacja Orlenu: Energa, Lotos, PGNiG — H3

### 4.3.1. Trzy fale w skrócie

| | Energa (2020) | Lotos (2022) | PGNiG (2022) |
|--|---------------|--------------|--------------|
| Forma | wezwanie gotówkowe | połączenie + remedium KE | połączenie |
| Finalizacja | 30.04.2020 | 01.08.2022 | 02.11.2022 |
| Skala | ~80% kapitału; ~**2,77 mld zł** | emisja serii E; parytet w planie | emisja serii F; **1,16 mld** akcji łącznie po połączeniach |
| Narracja ex ante | multienergia, OZE/dystrybucja | multienergia, synergie, regionalny lider | gaz, bezpieczeństwo, synergie |
| Ex post | Energa w grupie; Ostrołęka jako „spadek” | **NIK: remedium poniżej wyceny; synergie niepewne** | integracja gazu; obowiązki statutowe bezpieczeństwa RP |

### 4.3.2. Lotos i NIK jako kotwica hubris *ex post*

Publiczne ustalenia NIK (2025) dotyczące zbycia aktywów remedium formułują tezę o sprzedaży **poniżej wycen** (w kalendarium: strata ≥5 mld zł na warunkach remedium; cena vs wyceny Orlen/NIK — **weryfikuj w PDF przed finalnym cytowaniem**), o „poglądowym” charakterze synergii rzędu ~10,7 mld do 2032 oraz o kosztach doradztwa rzędu **253 mln zł**. To jest najmocniejszy w pracy **zewnętrzny audyt narracji fuzji** — nie zastępuje event study, ale uniezależnia ocenę H3 od znaku przeciętnego CAR.

### 4.3.3. CAR na datach case

Średni CAR[−1,+1] na 10 datach ≈ **−0,34%**; CAR[−5,+5] ≈ **−1,4%**. Heterogeniczność etapów (wyniki w rozdz. wyników): ujemne reakcje przy warunkowej zgodzie KE / planach połączeń, dodatnia przy rejestracji PGNiG. **Wniosek:** rynek nie wycenia „hubris” jako stałej premii karnej; wycenia **etap ryzyka regulacyjnego i domknięcia**. H3 wspiera przede wszystkim filar I (NIK + ścieżka remedium), a filar III — warunkowo.

### 4.3.4. Wniosek case

H3: **częściowo wsparta**. Empire-building i koszt remedium są udokumentowane; nie wolno pisać, że średni CAR M&A Orlen jest systematycznie ujemny na każdym etapie.

---

## 4.4. NABE i dezinwestycje węglowe — H4

### 4.4.1. Mechanizm status quo

Od **23.07.2021** (porozumienie SP + PGE + Tauron + Enea + Energa) do **09.07.2025** (rezygnacja MAP z NABE) spółki SP funkcjonowały w narracji: *węgiel wyjdzie z bilansu do agencji państwowej → odblokowanie finansowania OZE*. Przez cztery lata pełny transfer nie nastąpił. MAP komunikowała lukę finansową NABE na **53,8 mld zł** (2025–2040).

### 4.4.2. Co zrobiono „poza” pełnym NABE

| Spółka | Działanie cząstkowe | Znaczenie |
|--------|---------------------|-----------|
| Tauron | Wydobycie → SP za **1 zł** (2022), z oddłużeniem | częściowa dezinwestycja wydobycia, nie cały NABE |
| PGE | Oferta SP na GiEK: equity **849 mln**, dług **5,4 mld** (2023) | transakcja **niesfinalizowana** |
| Enea / Energa | Strony porozumienia; strategie z NABE w tle | wait-and-see |
| **ZE PAK** | **Poza NABE** | prywatna trajektoria odejścia od brunatnego = **kontrast** |

### 4.4.3. CAR i wniosek

Na 5 zmapowanych datach średni CAR[−1,+1] jest dodatni (ok. **+0,9%**), ale \(n\) małe i reakcje zróżnicowane (np. Enea+ vs PGE− na porozumieniu 2021). Rezygnacja MAP 2025-07-09 **nie ma** standardowego ESPI spółek w mapie — Day 0 medialny. **H4 stoi na kalendarium i kontraście ZEP**, nie na jednolitym znaku CAR.

**Kąt behawioralny:** wspólne oczekiwanie na NABE = `status_quo` + `herding` instytucjonalny; częściowe ruchy (Wydobycie) = `framing` „już działamy”, bez domknięcia systemowego.

---

## 4.5. Strategie transformacji 2021–2025 — H5

### 4.5.1. Zbieżność narracji

W oknie badania spółki publikują strategie 2030/2035 z powtarzalnymi motywami: neutralność klimatyczna (2040–2050), cele OZE, multienergia / „nowa energia”, węgiel do wydzielenia lub ringfencing, rosnący CAPEX transformacyjny, często **polityka dywidendowa** w tym samym pakiecie (Orlen).

**Timeline (skrót):** ZEP kierunki 2020 → Orlen 2030 (XI 2020) → PGE 2030 → Enea aktualizacje → Tauron 2022–30 → Orlen aktualizacja 2023 → Unimot 2024–28 → Enea 2035 (CAPEX **107,5 mld**, OZE **4,9 GW**) → Tauron 2025–35 (neutralność **2040**) → Orlen 2035 (CAPEX **350–380 mld**) → PGE 2035 (po rezygnacji z NABE).

### 4.5.2. Herding vs dyferencjacja

| Wzorzec wspólny (herding/framing) | Dyferencjacja |
|-----------------------------------|---------------|
| OZE, net zero, węgiel „poza bilansem” | **ZEP/Unimot:** brak NABE, inna skala i właściciel |
| Aktualizacje 2024–25 po fuzjach i kryzysie | **Orlen:** multienergia po Lotos/PGNiG + petrochemia |
| Dywidenda w pakiecie strategii (SP) | **JSW:** FIZ zamiast „gwarancji Orlenowej” |

Brak formalnej miary podobieństwa tekstu (`STRAT_SIM`) → H5 w pracy to **opis zbieżności motywów i dat**, nie test cosine similarity. CAR wokół publikacji strategii ≈ 0 w [−1,+1] — komunikaty długie, wielowątkowe, częściowo antycypowane.

### 4.5.3. Wniosek case

H5: **słabe / otwarte ilościowo**, **umiarkowane jakościowo** (zbieżność narracji SP). Nie oznaczać jako „potwierdzony herding tekstowy”.

---

## 4.6. Dywidenda Orlen i FIZ JSW — H6

### 4.6.1. Orlen: gwarancja i opcja „wyżej”

Ewolucja polityki: powrót po COVID → aktualizacja 2023 (**40% skorygowanych FCF**, min. dywidenda gwarantowana, ścieżka do 5,20 w 2030) → strategia 2035 (**gwarancja +0,15 zł/rok**, start 4,50; opcja do 25% reguły opartej o CFO). Faktyczne DPS za 2022–2025: **5,50 / 4,15 / 6,00 / 8,00** — często **powyżej** samej gwarancji. Po fuzjach liczba akcji rośnie do **1 160 942 049**, stąd skok sumy wypłat.

Kluczowy komunikat behawioralny: przy odpisach Nowej Chemii Orlen podkreśla, że **polityka oparta o przepływy nie jest ruszana przez odpisy niegotówkowe** (ESPI 12/2025) — klasyczny trop **mental accounting** (oddzielenie „kont” wyniku księgowego i payout).

### 4.6.2. JSW: FIZ jako skarbonka cyklu

FIZ stabilizacyjny: w boomie zasilanie (2022: limit CI 5 mld, zasilenia rzędu **+4,2 mld**, WAN ~4,9 mld EOY 2022); w dołku — umorzenia certyfikatów jako źródło płynności (seria zgód 2024–25). To **wewnętrzny bufor**, nie gwarancja DPS dla akcjonariuszy zewnętrznych — inna etykieta konta niż u Orlenu, ten sam mechanizm niefungibilności.

### 4.6.3. CAR i wniosek

Na 6 matched datach CAR[−1,+1] ≈ −0,25%; [−5,+5] średnia zawyżona małym \(n\). H6 stoi na **epizodach i regułach polityki**, nie na istotnym CAR kategorii „dywidenda” w pełnej próbie ESPI.

---

## 4.7. Synteza kodowania QUAL

**Tabela 4.7. Macierz inklinacja × case (primary codes)**

| Kod QUAL | Olefiny | Ostrołęka | M&A Orlen | NABE | Strategie | Dywidenda/FIZ |
|----------|:-------:|:---------:|:---------:|:----:|:---------:|:-------------:|
| overconfidence | ●● | ● | ● | ● | ● | ● |
| escalation | ●● | ●● | ● | | | |
| hubris_ma | | ● | ●● | | | |
| framing | ●● | ●● | ● | ●● | ●● | ●● |
| status_quo | | ● | | ●● | ● | ● |
| herding | | | | ● | ●● | |
| mental_accounting | | | | | | ●● |

●● = kod wiodący; ● = obecny.

**Wzorce przekrojowe:**

1. **Framing** jest wszechobecny — każda korekta dostaje nową etykietę (Nowa Chemia, gaz zamiast węgla, NABE, dywidenda gwarantowana).  
2. **Escalation** koncentruje się w megaprojektach z długim horyzontem i wysokim sunk cost.  
3. **Status quo + herding** najsilniej w koalicji SP wokół węgla i strategii.  
4. **Mental accounting** — polityka finansowa (payout vs odpisy; FIZ vs wynik).  
5. Rynek (CAR) **nie mapuje 1:1** kodów QUAL: najsilniejsze ujemne średnie case dotyczą Ostrołęki i dłuższego okna M&A, niekoniecznie każdego FID.

## 4.8. Podsumowanie rozdziału

Wielokrotne studium przypadku pokazuje, że w latach 2020–2025 w sektorze energetyczno-paliwowym GPW da się **udokumentować sekwencje decyzji zgodne z kanonicznymi mechanizmami BCF**, szczególnie gdy dostępny jest zewnętrzny audyt (NIK) lub twarda ścieżka rewizji CAPEX. Event study na datach case dostarcza uzupełniającego, lecz **nie jednolitego** sygnału rynkowego. Następny rozdział przenosi ciężar na analizy ilościowe w pełnej próbie ESPI, panelu i podokresach — przy świadomości, że to case buduje treść Bloku A hipotez.

---

## Nota dla autora (usuń przed oddaniem)

| Case | Kalendarium źródłowe |
|------|----------------------|
| Olefiny | `kalendarium_olefiny_iii.md` |
| Ostrołęka | `kalendarium_ostroleka_c.md` |
| M&A | `kalendarium_ma_orlen.md` |
| NABE | `kalendarium_nabe.md` |
| Strategie | `kalendarium_strategie.md` |
| Dywidenda/FIZ | `kalendarium_dywidenda_fiz.md` |
| CAR | `analytical/case_events_enriched.*` |

**Przed oddaniem:**  
1. Zweryfikuj w PDF NIK liczby remedium Lotos i 53,8 mld NABE.  
2. Wstaw 1–2 linie czasu jako rysunki.  
3. Usuń powtórzenia z rozdz. wyników (CAR case) — w R5 skróć odwołaniem do R4.
