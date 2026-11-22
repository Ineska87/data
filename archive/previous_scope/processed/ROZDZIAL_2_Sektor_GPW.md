# Rozdział 2. Sektor energetyczno-paliwowy na GPW w latach 2020–2025

*Wersja robocza R2. Liczby z kalendariów case, NIK/IR oraz panelu pracy (aktywa/mktcap na 2024Q4, mln PLN). Przed oddaniem: dopnij odwołania do konkretnych stron PDF NIK/AR i ewentualnie wykresy indeksów z `data/raw/market_data/`.*

---

## 2.1. Struktura sektora, indeksy i charakterystyka próby

### 2.1.1. Dwa bieguny: paliwa i elektroenergetyka

Na GPW segment energetyczno-paliwowy nie jest jednorodny. W uproszczeniu można wyróżnić:

1. **Paliwa / multienergia** — rafinacja, petrochemia, handel paliwami, coraz silniej gaz i energia (po konsolidacji): centralnie **Orlen (PKN)**, z kontrastem dystrybucyjno-handlowym **Unimot (UNT)**.  
2. **Elektroenergetyka** — wytwarzanie, dystrybucja, sprzedaż, ciepło: **PGE, Tauron (TPE), Enea (ENA)** oraz — w niszy węgla brunatnego i transformacji — **ZE PAK (ZEP)**.  
3. **Surowce węglowe** — **JSW** (węgiel koksowy/energetyczny) jako rezerwa empiryczna o innej ekspozycji cenowej (stal, koks).

Indeksy **WIG-energia** i **WIG-paliwa** pełnią w badaniu podwójną rolę: opisują tło sektorowe oraz stanowią **benchmarki modelu rynkowego** (odpowiednio dla spółek elektroenergetycznych i — w przypadku PKN — WIG-paliwa; dla UNT/ZEP/JSW przyjęto WIG ze względu na lepsze dopasowanie \(R^2\)).

### 2.1.2. Próba badawcza: role i skale

Dobór jest celowy i podporządkowany logice porównawczej (SP vs prywatni; paliwa vs energia; megaprojekty vs transformacja).

**Tabela 2.1. Spółki w badaniu — role i skala (panel, 2024Q4, mln PLN)**

| Ticker | Spółka | Rola | Kontrola SP* | Aktywa | Mktcap (proxy) | Przychody Q |
|--------|--------|------|:------------:|-------:|---------------:|------------:|
| PKN | Orlen | rdzeń | tak | 262 742 | 54 796 | 77 169 |
| PGE | PGE | rdzeń | tak | 103 994 | 13 619 | 17 627 |
| TPE | Tauron | rdzeń | tak | 45 714 | 6 588 | 9 873 |
| ENA | Enea | rdzeń | tak | 39 468 | 6 839 | 8 813 |
| JSW | JSW | rezerwa | tak | 22 873 | 2 432 | 2 459 |
| ZEP | ZE PAK | rezerwa / kontrast | nie | 3 850 | 695 | 623 |
| UNT | Unimot | kontrast prywatny | nie | 3 402 | 1 086 | 3 930 |

\* `state_control` w panelu: 1 = dominacja SP w logice badania (nie pełna ocena ładu KSH).  
Źródło skali: `panel_quarterly` (rachunkowość dualna PKN XLS / peer BiznesRadar; mktcap = cena × proxy liczby akcji).

**Wniosek strukturalny:** po fuzjach Orlen jest o rząd wielkości większy od pozostałych podmiotów próby. Ma to konsekwencje metodologiczne (wpływ PKN na kategorię M&A w event study; osobna warstwa rachunkowa `pkn_xls`) i merytoryczne (konsolidacja zmienia mapę konkurencji i ESPI).

### 2.1.3. Macierz porównawcza (własność × ekspozycja)

**Tabela 2.2. Macierz spółek — własność, ekspozycja, intensywność decyzji 2020–2025**

| Spółka | Własność (w badaniu) | Główna ekspozycja | Kluczowe decyzje w oknie |
|--------|----------------------|-------------------|---------------------------|
| PKN | SP / multi | ropa, gaz, petrochemia, energia | M&A, Olefiny/Nowa Chemia, dywidenda, strategie |
| PGE | SP | węgiel → OZE, system | NABE/GiEK, strategie, OZE |
| TPE | SP | węgiel, dystrybucja, OZE | NABE, Wydobycie→SP, strategie, Jaworzno (kontekst) |
| ENA | SP | węgiel, dystrybucja, OZE | Ostrołęka C, NABE, strategie |
| ZEP | prywatna | węgiel brunatny → transformacja | wcześniejsza trajektoria odejścia od brunatnego (kontrast H4) |
| UNT | prywatna | handel/dystrybucja paliw | kontrast CAPEX/M&A vs SP; płynność |
| JSW | SP | węgiel koksowy | FIZ, CAPEX vs wynik, cykl surowcowy |

## 2.2. Szoki zewnętrzne i podokresy 2020–2025

Dla H11 i interpretacji CAR wyróżniono podokresy zbieżne z dummy w panelu makro.

### 2.2.1. 2020 — pandemia i krach cen ropy

Rok 2020 przyniósł załamanie popytu na paliwa i ekstremalną zmienność cen ropy, spadek mobilności oraz szok dla wyników segmentu downstream. Równolegle Orlen finalizował wezwanie na **Energę** (kontrola ok. 80% kapitału, rozliczenie 30.04.2020, wartość gotówkowa rzędu 2,8 mld zł — kalendarium M&A). Dla elektroenergetyki istotny był kontekst projektu **Ostrołęka C** (zawieszenie finansowania, odpisy, wejście narracji gazowej).

### 2.2.2. 2021 — ramy polityki i start NABE

**PEP2040** (luty 2021) utrwalił ramy transformacji. 23.07.2021 zawarto **porozumienie** SP z PGE, Tauronem, Eneą i Energą o współpracy przy wydzieleniu aktywów węglowych do **NABE** — punkt startu wieloletniego status quo (H4). Orlen rozwijał ścieżkę Lotos (warunkowa zgoda KE 14.07.2020 z remediami; kolejne umowy 2021).

### 2.2.3. 2022–2023 — kryzys energetyczny i konsolidacja

Agresja na Ukrainę, szok cen gazu i energii oraz europejska odpowiedź (m.in. REPowerEU) zmieniły strukturę ryzyka sektora. W Polsce:

- **sierpień 2022** — rejestracja połączenia Orlen–Lotos;  
- **listopad 2022** — rejestracja połączenia Orlen–PGNiG;  
- spółki elektroenergetyczne komunikowały presję na finansowanie aktywów węglowych i częściowe dezinwestycje (np. sprzedaż Tauron Wydobycie do SP, 2022);  
- ceny energii i EUA podnosiły zarówno marże, jak i koszty transformacji.

Dla BCF jest to okres maksymalnej gęstości **decyzji strategicznych i ESPI** — stąd osobne testy CAR w podokresach (H11).

### 2.2.4. 2024–2025 — normalizacja, korekty, rezygnacja z NABE

Faza względnej normalizacji cen współwystępuje z korektami projektów (zatrzymanie Olefin III w dotychczasowym zakresie, XII 2024; odpisy / Nowa Chemia) oraz z **rezygnacją MAP z NABE (09.07.2025)** przy komunikowanej luce finansowej rzędu **53,8 mld zł** na lata 2025–2040 (kalendarium NABE). Spółki aktualizują strategie 2030/2035 i polityki dywidendowe.

**Tabela 2.3. Podokresy a hipotezy**

| Podokres | Dummy w danych | Główne zjawiska | Powiązanie H |
|----------|----------------|-----------------|--------------|
| 2020 | COVID_2020 | pandemia, ropa, Energa, Ostrołęka | H2, H3, H11 |
| 2021 | — | PEP2040, start NABE, ścieżka Lotos | H3, H4 |
| 2022–2023 | ENERGY_CRISIS | wojna, ceny energii, Lotos+PGNiG | H3, H4, H11 |
| 2024–2025 | NORMALIZATION | korekty CAPEX, strategie, koniec NABE | H1, H4, H5, H6, H11 |

## 2.3. Skarb Państwa, ład korporacyjny i kontrast prywatny

### 2.3.1. SP jako akcjonariusz strategiczny

W próbie rdzeniowej dominuje logika właściciela państwowego: cele bezpieczeństwa energetycznego, transformacji i — w przypadku Orlenu — budowy multienergetycznego czempiona. Dla BCF ma to trzy konsekwencje:

1. **Funkcja celu menedżera** może obejmować mandat polityczny, nie tylko NPV akcjonariusza mniejszościowego.  
2. **Rotacje zarządów** i cykle wyborcze zmieniają horyzont decyzji (istotne przy eskalacji i status quo).  
3. **Rozwiązania systemowe** (NABE, rynek mocy, remedium KE) stają się zewnętrznymi punktami odniesienia, na które spółki „czekają” — mechanizm bliski status quo bias, ale częściowo instytucjonalny.

### 2.3.2. Kontrast: ZE PAK i Unimot

**ZE PAK** — mniejsza kapitalizacja, ekspozycja na węgiel brunatny, prywatna kontrola — w badaniu służy jako **kontrast H4**: trajektoria odejścia od brunatnego bez oczekiwania na NABE. Niska płynność i niski \(R^2\) modelu rynkowego ograniczają precyzję CAR, ale nie unieważniają porównania kalendarzy decyzji.

**Unimot** — prywatny gracz paliwowy — kontrast dla SP w polityce inwestycyjnej i komunikatach ESPI. W event study wymagał korekty serii kursów (`UNT.WA`, nie Unibep); niski \(R^2\) względem WIG uzasadnia analizy wrażliwości bez UNT.

### 2.3.3. P6 w praktyce

Pytanie o wzmocnienie inklinacji przy dominacji SP **nie ma prostego testu „SP = bardziej behawioralny”**. Praca porównuje **trajektorie decyzji** (kiedy wychodzi się z węgla, jak buduje się skalę, jak kotwiczy się dywidendę), a nie przypisuje irracjonalności wyłącznie spółkom SP. Część wzorców (oczekiwanie na NABE) jest **wspólna dla koalicji SP**, co bliższe herdingu instytucjonalnego (H5) niż indywidualnej miscalibration CEO.

## 2.4. Konsolidacja sektora wokół Orlenu

### 2.4.1. Trzy fale

| Fala | Transakcja | Kamienie milowe | Skala (orient.) |
|------|------------|-----------------|-----------------|
| 1 | **Energa** | wezwanie 05.12.2019; KE 31.03.2020; finalizacja 30.04.2020 | ~80% kapitału; ~2,8 mld zł gotówki |
| 2 | **Lotos** | warunkowa KE 14.07.2020 + remedia; plan 02.06.2022; rejestracja **01.08.2022** | emisja serii E; sukcesja uniwersalna |
| 3 | **PGNiG** | plan 29.07.2022; rejestracja **02.11.2022** | gaz + multienergia |

Źródło: `kalendarium_ma_orlen.md` (ESPI Orlen).

### 2.4.2. Remedia i NIK (kontekst H3)

Warunkowa zgoda KE na Lotos wymagała zbycia m.in. udziału w rafinerii gdańskiej, stacji i innych aktywów. Kontrola NIK (komunikacja publiczna 2025) formułuje tezę o istotnej stracie na warunkach remedium względem wartości referencyjnych (w kalendarium: m.in. 30% rafinerii — 1,1 vs ok. 4,6 mld zł w ustaleniach NIK — **weryfikuj w PDF przed cytowaniem w tekście finalnym**). Dla BCF jest to **kotwica ex post**: narracja synergii i multienergii vs audyt warunków transakcji.

### 2.4.3. Konsekwencje dla projektu badawczego

1. **Próba i ESPI** — po 2022 Orlen „wchłania” archiwa Lotos/PGNiG; Energa jako osobny emitent GPW znika z mapy.  
2. **Benchmarki** — WIG-paliwa silnie powiązany z PKN.  
3. **Identyfikacja** — dummy `MERGER_ORLEN` w makro (okno fuzji) kontroluje tło.  
4. **CAR** — nie sumować naiwnie wszystkich ESPI M&A jako jednorodnej próby „hubris”; analizować **etapy** (wezwanie, KE, plan, rejestracja).

## 2.5. Kalendarium kluczowych decyzji inwestycyjno-finansowych 2020–2025

Poniższa oś łączy szoki zewnętrzne z decyzjami case (szczegóły w plikach `kalendarium_*.md`).

**Tabela 2.4. Oś czasu (wybór)**

| Okres | Zdarzenie | Spółki | H |
|-------|-----------|--------|---|
| 2019-12 / 2020-04 | Wezwanie i finalizacja Energa | PKN | H3 |
| 2020 Q1–Q3 | Ostrołęka: zawieszenie, odpisy, gaz | ENA, PKN | H2 |
| 2020-07 | Warunkowa zgoda KE Lotos | PKN | H3 |
| 2021-02 | PEP2040 | system | H4, H5 |
| 2021-05/06 | FID / EPCC Olefiny | PKN | H1 |
| 2021-07 | Porozumienie NABE | PGE, TPE, ENA, Energa | H4, H5 |
| 2022-08 | Połączenie Lotos | PKN | H3 |
| 2022-10 | Tauron Wydobycie → SP | TPE | H4 |
| 2022-11 | Połączenie PGNiG | PKN | H3 |
| 2023-02+ | Strategie / polityka dywidendy Orlen | PKN | H5, H6 |
| 2023-06 | Rewizja CAPEX Olefin | PKN | H1, H2 |
| 2023-07 | Oferta SP na PGE GiEK (niesfinalizowana) | PGE | H4 |
| 2024-12 | Stop Olefiny III (dotychczasowy zakres) | PKN | H1, H2 |
| 2025-01+ | Strategie 2035, dywidenda | PKN, sektor | H5, H6 |
| 2025-07 | Rezygnacja z NABE (luka 53,8 mld) | MAP / PGE, TPE, ENA | H4 |
| 2022–2025 | FIZ JSW: nabycia / umorzenia certyfikatów | JSW | H6 |

## 2.6. Implikacje dla hipotez i metod

1. **Gęstość decyzji** uzasadnia event study na ESPI i case, a nie wyłącznie panel 168 obserwacji.  
2. **SP + NABE** generują wspólne oczekiwanie systemowe — idealne tło H4/H5, słabe dla czystego testu „osobowości CEO”.  
3. **Konsolidacja Orlenu** dominuje kategorię M&A i wymaga czytania CAR etapami (H3).  
4. **Szoki 2020 i 2022–23** uzasadniają H11, ale empiria pokazuje, że grand mean CAR nie musi być wyższy w kryzysie — sektor jest jednocześnie poddany szokom fundamentalnym (ceny energii, EUA, ropa), które event study kontroluje tylko częściowo przez benchmark.  
5. **Kontrast prywatny** (ZEP, UNT) jest metodologicznie cenny, lecz ograniczony płynnością i \(R^2\).

## 2.7. Podsumowanie rozdziału

Sektor energetyczno-paliwowy na GPW w latach 2020–2025 to arena fuzji systemowych, transformacji węglowej, megaprojektów i kotwic polityki finansowej — w warunkach skrajnych szoków zewnętrznych i silnej roli państwa. Próba badawcza odzwierciedla tę strukturę: rdzeń SP (PKN, PGE, TPE, ENA), kontrasty prywatne (UNT, ZEP) i rezerwa surowcowa (JSW). Rozdział dostarczył ramy instytucjonalnej i kalendarza decyzji; kolejny rozdział (metodologia) operacjonalizuje, jak te decyzje i komunikaty ESPI są mierzone w event study, panelu i studiach przypadku.

---

## Nota dla autora (usuń przed oddaniem)

| Element | Plik |
|---------|------|
| R2 Sektor | `data/processed/ROZDZIAL_2_Sektor_GPW.md` |
| Kalendaria | `case_studies/kalendarium_*.md` |
| Panel (skale) | `panel/panel_quarterly.parquet` |

**Do wstawienia graficznie (opcjonalnie):**  
- wykres WIG-energia i WIG-paliwa 2020–2025 (`raw/market_data/`);  
- oś czasu z Tabeli 2.4 jako rysunek;  
- mapa: Orlen multienergia po 2022.

**Weryfikacja przed cytowaniem NIK:** otwórz PDF w `raw/nik_reports/` i potwierdź liczby 1,1 / 4,6 mld oraz 53,8 mld (NABE — źródło MAP/media w kalendarium).

**Następny krok:** proza R4 case (`case olefiny` itd.) albo scalenie wszystkich `ROZDZIAL_*.md`.
