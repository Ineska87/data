---
title: "Przejawy czynników behawioralnych w decyzjach inwestycyjno-finansowych wybranych spółek sektora energetyczno-paliwowego notowanych na GPW w latach 2020–2025"
type: magisterka-robocza
status: draft-scalone
note: "Scalenie z ROZDZIAL_*.md — ujednolicić numerację i bibliografię przed oddaniem."
---

# Przejawy czynników behawioralnych w decyzjach inwestycyjno-finansowych wybranych spółek sektora energetyczno-paliwowego notowanych na GPW w latach 2020–2025

**Praca magisterska (wersja robocza — plik scalony)**

Szkoła Główna Handlowa w Warszawie

*Dokument scalony z `data/processed/ROZDZIAL_*.md` + streszczenie. W treści wyników mogą pozostać wewnętrzne numery sekcji z wersji roboczej (np. 4.x) — do ujednolicenia w Wordzie jako Rozdział 5.*

---

## Spis treści (roboczy)

1. Streszczenie
2. Wstęp
3. Rozdział 1 — Teoria BCF
4. Rozdział 2 — Sektor GPW 2020–2025
5. Rozdział 3 — Dane i metody
6. Rozdział 4 — Studia przypadku
7. Rozdział 5 — Wyniki empiryczne
8. Rozdział 6 — Dyskusja
9. Zakończenie

**Materiały poza plikiem (odsyłacze):** `MAPA_HIPOTEZ.md`, `METODOLOGIA_fragmenty_dane.md`, `h7_panel_summary.md`, `h11_periods_summary.md`, `tables/`, `plots/`, `case_studies/kalendarium_*.md`, `Bibliography/moje_pdfy/`

---

# Streszczenie

Niniejsza praca bada przejawy czynników behawioralnych w decyzjach inwestycyjno-finansowych wybranych spółek sektora energetyczno-paliwowego notowanych na Giełdzie Papierów Wartościowych w Warszawie w latach 2020–2025 oraz krótkookresową reakcję rynku na komunikaty o tych decyzjach. Punktem wyjścia jest luka w polskiej empirii *behavioral corporate finance*: dominują badania zachowań inwestorów, podczas gdy inklinacje menedżerów rzadko weryfikuje się na materiale emisyjno-sprawozdawczym konkretnych emitentów.

Zastosowano podejście wielometodowe. Po pierwsze, wielokrotne studium przypadku (m.in. Olefiny III, Ostrołęka C, konsolidacja Orlen–Energa–Lotos–PGNiG, program NABE, polityki dywidendowe i FIZ JSW) z konfrontacją dokumentów IR i ustaleń NIK. Po drugie, analizę zdarzeń na raportach ESPI (model rynkowy, CAR, testy BMP i znaku; ok. 2,5 tys. zdarzeń z oszacowanym CAR). Po trzecie, panel kwartalny spółka–czas oraz uzupełniający, słownikowy pomiar tonu komunikacji zarządczej. Warstwę sentymentu medialnego wyłączono z wersji bazowej z powodu braku stabilnych danych historycznych. Wnioskowanie oparto na triangulacji filarów; panel przy siedmiu spółkach traktowano eksploracyjnie.

Wyniki wskazują, że w materiale dokumentacyjnym dają się odtworzyć wzorce zgodne z overconfidence i złudzeniem planowania, eskalacją zaangażowania, hubris w M&A (w świetle NIK), efektem status quo przy dezinwestycjach węglowych oraz kotwiczeniem w polityce finansowej. Event study pokazuje heterogeniczną reakcję rynku: istotnie dodatni CAR m.in. przy komunikatach o akcjonariacie/progach (z wrażliwością na skład próby) i ratingach, przy braku jednolitej, istotnej średniej CAR dla transakcji M&A mimo istotnego odsetka obserwacji z CAR > 0; ścieżka Orlen jest etapowa (od ujemnych reakcji przy niepewności regulacyjnej po dodatnie przy domknięciu połączeń). Eksploracyjny panel nie potwierdza hipotezy, że wyższy ton zarządu poprzedza wyższy CAPEX. Podział na podokresy kryzysowe nie ujawnia wyższego przeciętnego CAR w latach 2022–2023 względem normalizacji 2024–2025.

Wkład pracy polega na empirycznym przeniesieniu narzędzi BCF na polskich emitentów sektora strategicznego, zbudowaniu replikowalnego mostu ESPI–CAR–case oraz jawnej weryfikacji hipotez z uwzględnieniem wyników negatywnych i ograniczeń identyfikacyjnych.

**Słowa kluczowe:** behavioral corporate finance; event study; ESPI; CAPEX; fuzje i przejęcia; sektor energetyczno-paliwowy; GPW; NIK; ton komunikacji zarządczej.

---

# Wstęp

*Wersja robocza. Tytuł pracy: „Przejawy czynników behawioralnych w decyzjach inwestycyjno-finansowych wybranych spółek sektora energetyczno-paliwowego notowanych na GPW w latach 2020–2025”.*

---

## Uzasadnienie tematu i znaczenie problemu

Klasyczna teoria finansów przedsiębiorstw opiera się na założeniu, że menedżerowie maksymalizują wartość firmy w warunkach racjonalnych oczekiwań, a ceny rynkowe odzwierciedlają dostępne informacje. Empiria ostatnich dekad — zarówno po stronie *behavioral finance* inwestorów, jak i *behavioral corporate finance* (BCF) — pokazuje, że decyzje o inwestycjach, fuzjach, strukturze finansowania i dywidendach bywają spójne z inklinacjami poznawczymi i motywacyjnymi: nadmierną pewnością siebie, złudzeniem planowania, eskalacją zaangażowania, pychą w przejęciach, awersją do realizacji strat, zachowaniami stadnymi czy mentalnym księgowaniem nadwyżek. Równolegle literatura o ujawnieniach tekstowych dowodzi, że ton, kategoryczność i niepewność w komunikacji zarządczej niosą informację mierzalną narzędziami analizy języka.

Polski sektor energetyczno-paliwowy na GPW w latach **2020–2025** stanowi wyjątkowo gęste laboratorium tych zjawisk. W jednym oknie czasowym zbiegły się: pandemiczny szok popytowo-podażowy i krach cen ropy (2020), aktualizacja polityki energetycznej państwa (m.in. kontekst PEP2040), kryzys energetyczny po agresji Rosji na Ukrainę (2022–2023), wielka konsolidacja wokół Orlenu (Energa, Lotos, PGNiG), próby wydzielenia aktywów węglowych (NABE), megaprojekty petrochemiczne i energetyczne z rewizjami CAPEX, a także korekty strategiczne i względna normalizacja (2024–2025). Decyzje te są w wysokim stopniu udokumentowane raportami ESPI, strategiami IR oraz — w kluczowych epizodach — niezależnymi ustaleniami **NIK** (m.in. fuzja Orlen–Lotos, Elektrownia Ostrołęka C). Jednocześnie dominacja Skarbu Państwa w akcjonariacie części emitentów utrudnia czyste oddzielenie inklinacji menedżerskich od logiki agencyjnej i politycznej — co samo w sobie jest problemem badawczym, a nie tylko „zakłóceniem”.

## Luka badawcza

Luka, którą adresuje praca, jest podwójna. Po pierwsze, polskie badania finansów behawioralnych koncentrowały się w dużej mierze na **zachowaniach inwestorów** i anomaliach rynkowych, podczas gdy nurt BCF na poziomie **decyzji emitentów** pozostaje częściej opisem koncepcyjnym niż programem empirycznym na danych sprawozdawczo-emisyjnych. Po drugie, narzędzia analizy sentymentu dla rynku polskiego stosowane są zwykle na poziomie indeksów lub szerokiego rynku, rzadziej zaś w sprzężeniu z konkretnymi decyzjami korporacyjnymi (CAPEX, M&A, dywidenda, dezinwestycje) i z reakcją kursu wokół komunikatów ESPI.

Praca wypełnia obie luki **częściowo i świadomie**: łączy studia przypadku, event study i panel na materiale sektora o wysokiej intensywności decyzji strategicznych, przy czym ciężar dowodu rozkłada na triangulację filarów, a nie na jeden „główny” model panelowy siedmiu spółek. Warstwa newsowa (sentyment mediów) została w wersji bazowej **wyłączona** z braku stabilnych danych historycznych; hipotezy o luce tonu i kanale ton→CAPEX testowano w zakresie dostępnych proxy tekstowych, bez przeciążania ich rolą, której sparse słownikowy ton IR nie udźwignie.

## Cel główny i cele szczegółowe

**Cel główny:** zidentyfikować, zoperacjonalizować i empirycznie oszacować przejawy czynników behawioralnych w decyzjach inwestycyjno-finansowych wybranych spółek sektora energetyczno-paliwowego notowanych na GPW w latach 2020–2025 oraz zbadać, w jakim stopniu czynniki te współkształtowały krótkookresową reakcję rynku kapitałowego na te decyzje.

**Cele szczegółowe:**

1. Zbudować model pojęciowy BCF adekwatny do sektora regulowanego z istotną rolą właściciela państwowego.  
2. Opracować i zastosować proxy inklinacji w komunikacji zarządczej (ton, niepewność, pewność) w polskim korpusie IR — w wariancie słownikowym MVP.  
3. Udokumentować przejawy inklinacji w kluczowych decyzjach strategicznych (megaprojekty, M&A, dezinwestycje, dywidenda/FIZ, strategie) metodą wielokrotnego studium przypadku, z konfrontacją deklaracji i ustaleń NIK tam, gdzie dostępne.  
4. Oszacować krótkookresową reakcję rynku na zdarzenia ESPI (model rynkowy, CAR, testy BMP i znaku) według kategorii komunikatów i dat case.  
5. Zbadać eksploracyjnie, czy mierniki tonu poprzedzają intensywność CAPEX i zmiany zadłużenia w panelu spółka–kwartał.  
6. Porównać reakcje rynku między podokresami: pandemia (2020), kryzys energetyczny (2022–2023), normalizacja (2024–2025).  
7. Przeprowadzić triangulację wyników jakościowych i ilościowych oraz jawnie rozstrzygnąć status hipotez (wsparta / częściowo / nie / wyłączona).

## Pytania badawcze

| Kod | Pytanie |
|-----|---------|
| **P1** | Które czynniki behawioralne i w jakich typach decyzji ujawniały się w badanych spółkach najczęściej i najwyraźniej? |
| **P2** | Czy przebieg wielkich projektów inwestycyjnych był spójny z mechanizmami złudzenia planowania i eskalacji zaangażowania? |
| **P3** | Czy w komunikacji IR występują mierzalne wzorce tonu/pewności/niepewności i czy poprzedzają one agresywniejsze decyzje inwestycyjno-finansowe? |
| **P4** | Czy istnieje „luka tonu” względem fundamentów i czy rynek ją koryguje? *(w pracy: ograniczona operacjonalizacja)* |
| **P5** | Czy sentyment newsowy wzmacnia reakcję na ESPI? *(poza zakresem wersji bazowej)* |
| **P6** | Czy dominacja SP współwystępuje z innymi trajektoriami decyzji niż w spółkach prywatnych (kontrast ZEP, Unimot)? |
| **P7** | Czy okresy skrajnej niepewności wzmacniają przejawy badanych zależności (m.in. w CAR)? |

## Hipotezy badawcze

**Hipoteza główna (HG).** Czynniki behawioralne — inklinacje menedżerskie ujawniające się w decyzjach i komunikacji oraz (w pełnym brzmieniu konspektu) sentyment otoczenia informacyjnego — istotnie współwyjaśniają decyzje inwestycyjno-finansowe badanych spółek i reakcję rynku na te decyzje, po kontroli czynników fundamentalnych i szoków okresu 2020–2025.  
*W wersji zrealizowanej HG weryfikowano bez warstwy newsowej; komponent medialny HG uznano za wyłączony.*

**Blok A — decyzje strategiczne (filar case/dokumenty)**

| H | Treść skrócona | Główne kotwice |
|---|----------------|----------------|
| **H1** | Overconfidence / złudzenie planowania w megaprojektach | Olefiny III (rewizje CAPEX) |
| **H2** | Eskalacja zaangażowania i koszty utopione | Ostrołęka C; późny stop Olefin |
| **H3** | Hubris w M&A (przeszacowanie synergii, koszt remedium) | Orlen–Energa–Lotos–PGNiG; NIK Lotos |
| **H4** | Status quo / awersja do strat w dezinwestycjach węglowych | NABE vs ZE PAK |
| **H5** | Zachowania stadne w strategiach transformacji | publikacje strategii 2021–2025 |
| **H6** | Kotwiczenie i mentalne księgowanie w polityce finansowej | dywidenda Orlen; FIZ JSW |

**Blok B — komunikacja i panel**

| H | Treść skrócona |
|---|----------------|
| **H7** | Wyższy ton (i kategoryczność) → wyższy CAPEX i agresywniejsze finansowanie |
| **H8** | Przy wyższym tonie inwestycje silniej zależą od wewnętrznych przepływów (TONE×CFO) |
| **H9** | Luka tonu względem fundamentów generuje krótką dodatnią reakcję i późniejszą korektę |

**Blok C — otoczenie i kryzys**

| H | Treść skrócona |
|---|----------------|
| **H10** | Sentyment newsowy i uwaga medialna wzmacniają CAR/ATURN wokół ESPI — **wyłączona** |
| **H11** | Zależności są silniejsze w 2020 i 2022–2023 niż w 2024–2025 |

**Zasada rozstrzygania:** hipotezę blokową uznaje się za wspartą przy zbieżności **co najmniej dwóch filarów** (case, tekst, event study, panel). Wyniki panelu traktuje się eksploracyjnie.

## Metody, dane i zakres realizacji

Praca ma charakter **wielometodowy i sekwencyjny**.

1. **Studia przypadku (H1–H6)** — kalendaria decyzji, kody QUAL (overconfidence, escalation, hubris_ma, framing, status_quo, herding, mental_accounting), tabele deklaracja vs realizacja, materiały NIK i IR.  
2. **Event study** — raporty ESPI (okno zdarzeń 2019–2025, ok. 2,5 tys. komunikatów z CAR), model rynkowy OLS w oknie estymacji [−250, −11], CAR w oknach od [−1,+1] do [−20,+20], testy BMP i znaku, wrażliwość bez spółek o niskim \(R^2\), podokresy H11.  
3. **Panel kwartalny** — 7 spółek × 24 kwartały (168 komórek); dźwignia jako net debt/assets; eksploracyjne FE ton→CAPEX (H7) i interakcja TONE×CFO (H8).  
4. **Tekst IR** — słownikowy ton w stylu LM (MVP), pokrycie niepełne; bez pełnej anotacji i bez TONE_FUND_GAP w wersji finalnej wyników.

Próba główna obejmuje m.in. Orlen (PKN), PGE, Tauron (TPE), Enea (ENA), Unimot (UNT), ZE PAK (ZEP) i JSW; w warstwie rynkowej także LWB. Notowania Unimot oparto na serii **`UNT.WA`** (nie mylić z `UNI.WA` = Unibep). Day 0 w event study mapuje godzinę ESPI na sesję GPW; przy braku godziny (m.in. PKN) stosuje się regułę konserwatywną (następna sesja), z analizą wrażliwości w aneksie.

## Oczekiwany wkład

Praca wnosi: (i) empiryczne przeniesienie BCF na polskich emitentów sektora strategicznego z kotwicą NIK; (ii) replikowalny most ESPI–CAR–case; (iii) jawną mapę statusów hipotez, w tym wyników negatywnych (brak potwierdzenia H7, wyłączenie H10, przeformułowanie H11), które chronią przed selektywnym „storytellingiem” behawioralnym.

## Struktura pracy

| Część | Zawartość |
|-------|-----------|
| **Rozdz. 1** | Rama teoretyczna BCF: teoria perspektywy, inklinacje, dwa nurty (nieracjonalny rynek / nieracjonalny menedżer), ton i ujawnienia, przegląd badań i luka |
| **Rozdz. 2** | Sektor na GPW 2020–2025: struktura, szoki, rola SP, konsolidacja Orlenu, kalendarium decyzji |
| **Rozdz. 3** | Projekt badawczy i metodologia: próba, źródła, ESPI, NLP MVP, event study, panel, triangulacja, ograniczenia |
| **Rozdz. 4** | Wielokrotne studium przypadku (Olefiny, Ostrołęka, M&A Orlen, NABE, strategie, dywidenda/FIZ) i synteza kodów QUAL |
| **Rozdz. 5** | Analizy ilościowe: ton (opis), event study, panel eksploracyjny H7–H8, podokresy H11, odporność |
| **Rozdz. 6** | Dyskusja i weryfikacja hipotez; mechanizmy behawioralne vs agencyjne vs polityczne; implikacje |
| **Zakończenie** | Synteza, wkład, ograniczenia, kierunki badań |
| **Aneksy** | Słownik ESPI, korpus, księga kodów QUAL, tabele dodatkowe (Day 0, H11, H7) |

---


---

# Rozdział 1. Behawioralne finanse przedsiębiorstw jako rama analityczna

*Wersja robocza R1 (konspekt). Cytowania opierają się na pozycjach obecnych w `Bibliography/moje_pdfy/` oraz kanonie dziedziny; przed złożeniem zweryfikuj lata/strony w PDF i ujednolić styl bibliografii (APA/Harvard wg katedry).*

---

## 1.1. Od klasycznej do behawioralnej teorii finansów

Klasyczna teoria finansów przedsiębiorstw — od modelu M&M, przez teorię agencyjną i asymetrię informacji, po hipotezę efektywności rynku — zakłada, że decydenci maksymalizują wartość (lub własną użyteczność w ramach kontraktów), a ceny integrują publicznie dostępne informacje w sposób wolny od systematycznych błędów poznawczych. W takim świecie odchylenia od optymalnej polityki inwestycyjnej lub dywidendowej tłumaczy się głównie konfliktami interesów (menedżer–akcjonariusz, akcjonariusz–wierzyciel), ograniczeniami finansowania lub regulacją, a nie inklinacjami samego decydenta.

Program badań behawioralnych podważa to uproszczenie na dwóch poziomach. Po stronie **rynku** pokazuje, że inwestorzy podlegają heurystykom, limitowanej uwadze i sentymentowi, co może generować błędne wyceny i skłaniać emitentów do *market timing* lub *catering* (Baker i Wurgler, 2004; Barberis, Shleifer i Vishny, 1998). Po stronie **firmy** dokumentuje, że menedżerowie bywają nadmiernie pewni siebie, optymistyczni, podatni na eskalację zaangażowania i pychę w przejęciach — co zmienia CAPEX, strukturę kapitału i aktywność M&A nawet przy racjonalnych rynkach (Baker i Wurgler, 2013; Malmendier i Tate oraz literatura pokrewna, m.in. Ben-David, Graham i Harvey, 2013).

Dla niniejszej pracy kluczowe jest rozróżnienie: **wyjaśnienie agencyjne** („menedżer maksymalizuje prywatne korzyści”) i **wyjaśnienie behawioralne** („menedżer szczerze, lecz systematycznie myli się co do szans i kosztów”) nie wykluczają się, ale generują inne prognozy testowalne. W sektorze z dominującym akcjonariuszem państwowym dochodzi trzeci filar — **presja polityczna i regulacyjna** — który może naśladować status quo lub „empire building”, nie będąc czystą inklinacją poznawczą. Rama BCF służy więc do generowania **obserwowalnych przejawów** i hipotez, a nie do etykietowania każdej decyzji jako irracjonalnej.

## 1.2. Teoria perspektywy, heurystyki i inklinacje

Fundamentem psychologicznym pozostaje **teoria perspektywy** (Kahneman i Tversky, 1979): ocena wyników względem punktu odniesienia, wklęsłość w domenie zysków i wypukłość w domenie strat oraz większa wrażliwość na straty niż na równoważne zyski (*loss aversion*). W decyzjach korporacyjnych punkt odniesienia bywa budżetem projektu, poprzednim CAPEX, „obietnicą” dywidendy lub narracją strategii — co łączy się z kotwiczeniem i niechęcią do uznania straty księgowej lub politycznej.

Program heurystyk i błędów (Tversky i Kahneman oraz kontynuacje) dostarcza katalogu mechanizmów relewantnych dla H1–H6:

| Mechanizm | Istota | Powiązanie z pracą |
|-----------|--------|-------------------|
| Nadmierna pewność siebie / miscalibration | zawężone przedziały ufności, przeszacowanie kontroli | H1, H7–H8 |
| Złudzenie planowania | systematyczny optymizm co do czasu i kosztów | H1 (Olefiny) |
| Eskalacja / sunk cost | kontynuacja po negatywnym sygnale z powodu kosztów utopionych | H2 (Ostrołęka, stop CAPEX) |
| Hubris | przeszacowanie własnych zdolności w transakcjach | H3 (M&A) |
| Status quo / awersja do strat | odkładanie bolesnej zmiany | H4 (NABE, węgiel) |
| Herding / kaskady informacyjne | naśladownictwo w warunkach niepewności | H5 (strategie) |
| Mental accounting | niefungibilność „kont” pieniężnych | H6 (dywidenda, FIZ) |

**Sunk cost** w psychologii decyzyjnej (Arkes i Blumer, 1985) pokazuje, że ludzie uwzględniają nieodwracalne nakłady w decyzjach o kontynuacji — w korporacjach przekłada się to na opóźnione odpisy i „jeszcze jeden etap” projektu. **Overconfidence i wejście na rynek** (Camerer i Lovallo, 1999) ilustrują, że nadmierna pewność siebie może generować nadmierną aktywność inwestycyjną lub transakcyjną. Te mechanizmy nie wymagają założenia o złej wierze: menedżer może wierzyć, że działa optymalnie.

## 1.3. Dwa nurty *behavioral corporate finance*

Baker i Wurgler (2013) systematyzują BCF w dwóch nurtach, które w pracy są rozróżniane analitycznie, nawet jeśli w empirii trudno je w pełni oddzielić.

### 1.3.1. Nieracjonalny rynek, racjonalny menedżer

Jeśli ceny odchylają się od fundamentów, racjonalny zarząd może:

- emitować akcje przy przewartościowaniu i odkupywać przy niedowartościowaniu (*equity market timing*);
- dostosowywać dywidendy do preferencji inwestorów (*catering*) — Baker i Wurgler (2004);
- czasować komunikaty i oferty względem uwagi i sentymentu inwestorów (Barber i Odean, 2008 — uwaga; Antweiler i Frank, 2004 — treść dyskusji rynkowych).

W tym nurcie „przejaw behawioralny” leży po stronie **wyceny i popytu**, a decyzja firmy jest strategią na ten popyt. Event study w niniejszej pracy mierzy właśnie krótkookresową wycenę komunikatu; nie rozstrzyga jednak, czy odchylenie CAR wynika z nowej informacji fundamentalnej, czy z sentymentu — stąd ostrożność interpretacyjna i wyłączenie pełnej warstwy newsowej (H10) z wersji bazowej.

### 1.3.2. Nieracjonalny menedżer, (w przybliżeniu) racjonalny rynek

Drugi nurt zakłada, że rynek w horyzoncie średnim dyscyplinuje błędy, ale menedżerowie:

- przeszacowują NPV projektów i niedoszacowują ryzyka (overconfidence / optimism);
- preferują finansowanie wewnętrzne i „inwestowanie z własnej gotówki”;
- przejmują inne firmy z przeszacowaniem synergii (hubris);
- opóźniają uznanie strat i dezinwestycje.

Ben-David, Graham i Harvey (2013) dokumentują miscalibration menedżerów w prognozach; Bertrand i Schoar (2003) — trwałe „style” menedżerskie w polityce firm. W tym nurcie **studium przypadku i kalendarium decyzji** są naturalnym testem: jeśli budżet ex ante systematycznie odstaje od ex post, a wyjście następuje dopiero po skumulowanych stratach, wzorzec jest zgodny z overconfidence i eskalacją — nawet gdy CAR wokół pojedynczego ESPI jest bliski zera (informacja rozłożona w czasie, mieszana z innymi newsami).

**Mapa dla empirii pracy:** Blok A (H1–H6) operuje głównie w nurcie menedżerskim; Blok B–C (H7–H11) łączy komunikację i rynek, z panelem i event study jako mostami, nie jako jedynym dowodem.

## 1.4. Mechanizmy szczegółowe i prognozy empiryczne

### 1.4.1. Overconfidence, optimism i złudzenie planowania (H1)

Nadmierna pewność siebie w BCF oznacza zwykle zawężone przedziały błędów prognozy i przeszacowanie kontroli nad wynikami projektu. Złudzenie planowania to szczególny przypadek: **systematyczny optymizm co do harmonogramu i kosztów** przy niedoszacowaniu ryzyka implementacji. Prognozy testowalne:

- seria rewizji CAPEX/harmonogramu w górę;
- kategoryczny język komunikacji projektowej (wysoka CERTAINTY) na wczesnych etapach;
- ewentualnie wyższy CAPEX przy silniejszym tonie IR (H7) — test panelowy, w praktyce pracy słabo wspierany.

Kotwica empiryczna pracy: **Olefiny III / Nowa Chemia** — ścieżka od FID i budżetu ex ante do wielokrotnych rewizji i zatrzymania projektu.

### 1.4.2. Eskalacja zaangażowania i koszty utopione (H2)

Po negatywnym sygnale fundamentalnym racjonalny decydent aktualizuje NPV i wychodzi, gdy wartość opcji wyjścia przewyższa kontynuację. Przy eskalacji decydent **waży utopione nakłady** i reputację projektu. Prognozy:

- długi czas od pierwszego sygnału ostrzegawczego do odpisu/wyjścia (*time-to-impairment*);
- kontynuacja finansowania mimo pogorszenia parametrów;
- ujemna reakcja rynku na twarde sygnały wstrzymania/rozliczenia (event study na datach case).

Kotwice: **Ostrołęka C** (odpisy, NIK) oraz późny stop Olefin po skumulowanych nakładach.

### 1.4.3. Hubris w M&A (H3)

Hipoteza pychy Rolla (Roll, 1986) przewiduje, że przejmujący przeszacowują synergie i płacą zbyt wysokie premie; CAR akwizytora bywa ujemny. Literatura post-akwizycyjna (m.in. Agrawal, Jaffe i Mandelker, 1992) bada długookresowe stopy; w krótkim oknie event study (Brown i Warner, 1985; Brown i Warner, 1980) mierzy natychmiastową wycenę ogłoszeń. Prognozy:

- deklaracje synergii ex ante vs realizacja / audyt ex post (NIK);
- niekorzystne warunki remedium lub parytety;
- CAR wokół etapów transakcji — niekoniecznie jednolity znak na wszystkich datach.

Kotwica: konsolidacja **Orlen–Energa–Lotos–PGNiG**.

### 1.4.4. Status quo i awersja do strat (H4)

*Loss aversion* i bias status quo przewidują opóźnianie decyzji, które wymuszają uznanie straty (księgowej, politycznej, wizerunkowej). W elektroenergetyce SP oznacza to odkładanie dezinwestycji węglowych w oczekiwaniu na rozwiązanie systemowe (NABE). Prognoza porównawcza: **podmioty prywatne** (ZE PAK) szybciej realizują trajektorię odejścia od aktywów problemowych. Testem jest kalendarium, niekoniecznie średni CAR.

### 1.4.5. Herding (H5)

Modele kaskad informacyjnych i stadności (Bikhchandani, Hirshleifer i Welch, 1992) przewidują zbieżność decyzji przy niepewności. W strategiach transformacji: zbliżone cele OZE/neutralności, zbieżne daty aktualizacji, podobieństwo narracji. Wymaga miar podobieństwa tekstu lub struktury CAPEX — w wersji pracy częściowo tylko opisowo.

### 1.4.6. Mental accounting i polityka dywidendowa (H6)

Thaler (mental accounting) opisuje niefungibilność środków według etykiet kont. W korporacji: „dywidenda gwarantowana”, „fundusz stabilizacyjny”, „gotówka na transformację” jako osobne kubełki. Baker i Wurgler (2004) pokazują catering dywidend do popytu inwestorów — mechanizm rynkowy, komplementarny wobec kotwic menedżerskich. Prognozy: sztywność payout względem FCF; utrzymanie CAPEX/wypłat mimo pogorszenia wyniku przy jednoczesnym sięganiu do funduszy celowych (FIZ).

## 1.5. Ton, sentyment i tekst jako pomiar inklinacji

Ujawnienia tekstowe pozwalają budować proxy optymizmu, niepewności i ryzyka (Loughran i McDonald oraz kontynuacje; w polskim kontekście — adaptacje słownikowe i badania sentymentu, m.in. prace wykorzystujące polski rynek, np. Brzeszczyński i in. w zbiorze bibliografii). Antweiler i Frank (2004) oraz Barber i Odean (2008) łączą treść/uwagę z krótkimi stopami zwrotu.

W ramach BCF ton zarządu bywa traktowany jako:

- **sygnał inklinacji** (trwały optymizm menedżera) — wtedy powinien poprzedzać CAPEX i dźwignię (H7–H8);
- **sygnał informacyjny lub strategiczny** (impresja, *impression management*) — wtedy związek z realnymi decyzjami jest słaby lub pozorny;
- **źródło luki względem fundamentów** (H9) — rynek może początkowo podążać za tonem, potem korygować.

Ograniczenia pomiaru są fundamentalne dla interpretacji empirii pracy: słowniki ogólne są zawodne w polskim języku finansowym; korpus IR jest gatunkowo niejednorodny (list zarządu vs nota o odpisie); pokrycie kwartalne bywa sparse. Dlatego w projekcie ton jest **MVP i filarem uzupełniającym**, a nie jedynym testem BCF — zgodnie z zasadą, że negatywny wynik H7 nie unieważnia dokumentacyjnych H1–H6.

## 1.6. Event study jako most między decyzją a rynkiem

Analiza zdarzeń (Brown i Warner, 1980, 1985) pozostaje standardem pomiaru krótkookresowej treści informacyjnej komunikatów. Model rynkowy oddziela zwrot spółki od zwrotu benchmarku; CAR w oknach wokół Day 0 pozwala porównywać typy zdarzeń (M&A, wyniki, dywidenda, regulacje). W BCF CAR służy do:

- testowania, czy rynek „karze” lub „nagradza” etapy transakcji (H3);
- opisu reakcji na twarde sygnały wyjścia z projektu (H2);
- badania, czy ton lub newsy wzmacniają AR (H9–H10) — o ile dane są dostępne.

**Ograniczenie identyfikacyjne:** CAR ≠ dowód irracjonalności. Ujemny CAR przy zgodzie antymonopolowej może odzwierciedlać racjonalną wycenę kosztu remedium. Dlatego w pracy event study jest **filarem III triangulacji**, zawsze czytany łącznie z case i — tam gdzie jest — z NIK.

## 1.7. Przegląd empirii i luka (świat i Polska)

Międzynarodowa empiria BCF jest dojrzała w obszarach: overconfidence menedżerów i inwestycje; hubris i stopy po fuzjach; catering dywidend; sentyment i *equity issues*. Metodologicznie łączy ankiety menedżerów, cechy osobowe CEO, tekst 10-K/earnings calls oraz event study.

W Polsce silniejszy jest nurt **behawioralny po stronie inwestora** i analiz rynku; BCF na poziomie decyzji emitentów — zwłaszcza w sektorze regulowanym z SP — pozostaje rzadziej domknięty empirycznie na spójnym, wielometodowym materiale 2020–2025. Jednocześnie sektor dostarcza unikatowego identyfikatora: **kontrole NIK** jako zewnętrzny audyt narracji zarządów przy fuzjach i megaprojektach.

**Luka, którą domyka praca:** (1) operacjonalizacja przejawów inklinacji na kalendariach decyzji i ESPI polskich spółek energetyczno-paliwowych; (2) most do CAR; (3) ostrożny test panelowy ton→CAPEX; (4) jawna mapa statusów hipotez zamiast selekcji „istotnych” wyników.

## 1.8. Rama pojęciowa pracy: od inklinacji do obserwabli

Rysunek logiczny (do wstawienia jako schemat):

```text
Inklinacja (teoria)     →  Decyzja / komunikat     →  Obserwable w danych
─────────────────────────────────────────────────────────────────────
Overconfidence (H1)     →  FID, budżet CAPEX       →  rewizje ex post, CERTAINTY
Eskalacja (H2)          →  kontynuacja / odpis     →  time-to-exit, CAR na stop
Hubris M&A (H3)         →  ogłoszenie / remedium   →  NIK, CAR etapów
Status quo (H4)         →  odroczenie dezinwestycji→  kalendarium vs ZEP
Herding (H5)            →  strategie transformacji →  zbieżność dat/celów
Mental accounting (H6)  →  DPS, FIZ                →  payout vs FCF, ścieżka FIZ
Ton / optymizm (H7–H9)  →  listy, SZ, IR           →  TONE, CAPEX_t+1, CAR
Sentyment mediów (H10)  →  newsy wokół ESPI        →  (poza zakresem bazowym)
Kryzys (H11)            →  te same decyzje w 2020/22–23 vs 24–25 → CAR × podokres
```

**Implikacja metodologiczna:** żaden pojedynczy test nie „udowadnia BCF”. Wsparcie hipotezy wymaga zbieżności **co najmniej dwóch filarów** (case, tekst, event study, panel). Wyniki negatywne (np. brak H7) są informacyjne: ograniczają roszczenie, że słownikowy ton IR jest wystarczającym proxy inklinacji inwestycyjnych w tej próbie.

## 1.9. Podsumowanie rozdziału

Rozdział zarysował przejście od klasycznej racjonalności do BCF, dwa nurty (rynek vs menedżer), katalog inklinacji powiązanych z H1–H11 oraz rolę tonu i event study jako mostów pomiarowych. Kluczowa teza ramowa brzmi: w sektorze energetyczno-paliwowym GPW inklinacje menedżerskie, presja właścicielska i szoki regulacyjno-rynkowe współwystępują — empiria musi je **rozróżniać językiem prognoz i triangulacji**, a nie etykietą „irracjonalność”. Następny rozdział przenosi tę ramę na instytucjonalny i rynkowy kontekst sektora w latach 2020–2025.

---


---

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


---

# Rozdział 3. Dane i metody badawcze

*Wersja robocza rozdziału magisterki. Tytuł roboczy: „Behavioral Corporate Finance w sektorze energetyczno-paliwowym GPW w latach 2020–2025”. Liczby i reguły zgodne ze stanem pipeline’u empirycznego na 2026-07. Po wklejeniu do Word/LaTeX: ujednolicić numerację tabel z resztą pracy i dodać odwołania do rozdziałów z wynikami.*

---

Niniejszy rozdział opisuje konstrukcję próby, źródła danych oraz strategię empiryczną. Badanie łączy (i) klasyczną analizę zdarzeń (*event study*) na rynku akcji GPW, (ii) panel kwartalny spółka–czas z kontrolami rachunkowymi i makroekonomicznymi oraz (iii) jakościowo-ilościowe studia przypadków (m.in. inwestycje CAPEX, transakcje M&A, transformacja węglowa). Celem jest spójne powiązanie komunikatów emitentów (ESPI) z reakcją inwestorów i kontekstem finansowym spółki, przy jawnym sformułowaniu założeń identyfikacyjnych i ograniczeń pomiaru.

## 3.1. Okres badania i dobór próby

Okres docelowy analizy to lata **2020–2025**. Dla estymacji modelu rynkowego wykorzystano bufor notowań od **2018 r.**, tak aby dla zdarzeń z początku 2019–2020 dostępne było pełne okno estymacji. Zbiór zdarzeń roboczych obejmuje komunikaty z lat **2019–2025** (2 550 raportów po filtracji), z czego większość przypada na okno 2020–2025; wyniki CAR oszacowano dla **2 546** unikalnych zdarzeń (cztery komunikaty z przełomu 2025/2026 pominięto z powodu braku sesji w oknie post-event).

Próbę stanowią spółki sektora energetyczno-paliwowego notowane na GPW, dobrane według ról w badaniu:

| Ticker | Spółka | Rola |
|--------|--------|------|
| PKN | Orlen S.A. | rdzeń (główny podmiot) |
| PGE | PGE Polska Grupa Energetyczna S.A. | rdzeń |
| TPE | Tauron Polska Energia S.A. | rdzeń |
| ENA | Enea S.A. | rdzeń |
| UNT | Unimot S.A. | kontrast prywatny |
| ZEP | ZE PAK S.A. | rezerwa / kontrast płynności |
| JSW | Jastrzębska Spółka Węglowa S.A. | rezerwa / surowce |

Dodatkowo w warstwie rynkowej i ESPI dostępna jest Lubelski Węgiel Bogdanka (LWB) — wykorzystywana w rozszerzeniach event study, bez pełnego panelu rachunkowego w rdzeniu. Klasyfikacja ról odzwierciedla kapitalizację, płynność, kontrolę właścicielską (Skarb Państwa vs sektor prywatny) oraz przydatność do hipotez o M&A, CAPEX i transformacji.

## 3.2. Źródła danych

### 3.2.1. Notowania giełdowe

Dzienne kursy zamknięcia, wolumen oraz indeksy **WIG**, **WIG20**, **WIG-energia** i **WIG-paliwa** zebrano dla okresu 2018–2025. Zwroty zdefiniowano jako logarytmiczne stopy zmiany kursu zamknięcia w dniach z dodatnim wolumenem (sesje handlowe).

Unimot S.A. oznaczany jest w badaniu tickerem **UNT**. Kursy pochodzą z serii Yahoo Finance **`UNT.WA`**, z korektą o działania korporacyjne. Symbol **`UNI.WA` odpowiada innej spółce (Unibep S.A.)** i nie wchodzi do finalnych szacunków. Kapitalizację rynkową w panelu przybliżono jako iloczyn kursu na koniec kwartału i stałej liczby akcji (proxy; dla Unimot ok. 8,20 mln szt.). Liczby akcji dla pozostałych spółek ustalono na podstawie publicznie dostępnych metadanych rynkowych i traktowano jako stałe w próbie — nie modelowano pełnej historii emisji.

### 3.2.2. Raporty bieżące ESPI

Głównym źródłem dat zdarzeń są **raporty bieżące ESPI** ze stron relacji inwestorskich emitentów, scalone do jednolitego rejestru (ticker, data, godzina gdy dostępna, tytuł, URL, numer raportu). Zastosowano deduplikację po adresie URL oraz po parze tytuł–data w ramach spółki. Daty przyszłe względem dnia pobrania usunięto jako artefakty. Każdemu komunikatowi nadano unikalny identyfikator `event_id`.

### 3.2.3. Dokumenty okresowe, strategie i materiały case

Do panelu i studiów przypadków zebrano raporty roczne i śródroczne, prezentacje wynikowe oraz wybrane strategie (2020–2025), a także materiały NIK (m.in. fuzja Orlen–Lotos, Elektrownia Ostrołęka C) oraz kalendaria zdarzeń dla hipotez H1–H6 (Olefiny III, Ostrołęka C, M&A Orlen, NABE, dywidenda/FIZ, strategie). Mapowanie dat case na ESPI i CAR opisano w podrozdziale 3.6.

### 3.2.4. Dane rachunkowe

Panel kwartalny (spółka × rok × kwartał, 2020Q1–2025Q4) obejmuje **168** obserwacji (7 spółek × 24 kwartały). Zastosowano dwuwarstwową metodologię źródeł:

- **PKN** — skonsolidowane pakiety liczbowe ze strony IR Orlen (`pkn_xls`);  
- **pozostałe spółki** — kwartalne tabele BiznesRadar (`peer_br`), przeliczone z tys. PLN na mln PLN.

Kwoty bilansowe i wynikowe wyrażono w **milionach PLN**. Porównywalność między spółkami jest warunkowa: te same etykiety zmiennych nie oznaczają identycznej definicji w sprawozdaniu źródłowym; w regresjach uwzględniono lub rozdzielono warstwy `accounting_tier`.

### 3.2.5. Makroekonomia i sektor

Do panelu dołączono agregaty kwartalne: ropę Brent, kursy EUR/PLN i USD/PLN (NBP), stopę referencyjną NBP, proxy ceny energii day-ahead dla Polski, proxy ryzyka węglowego (ETF KRBN — **nie** kontrakt ICE EUA) oraz poziomy indeksów sektorowych. Dummy podokresów (COVID 2020, kryzys energetyczny 2022–2023, normalizacja 2024–2025, fuzje Orlen 2022/23) służą do analiz wrażliwości i kontroli tła rynkowego.

Jako **proxy stopy krótkoterminowej** przyjęto stopę referencyjną NBP, ponieważ publiczna seria miesięczna stopy rynkowej z zewnętrznej bazy nie była stabilnie dostępna przy budowie zbioru. **Nie interpretuje się tej zmiennej jako WIBOR/WIRON** — odzwierciedla nastawienie polityki pieniężnej. W regresjach unika się jednoczesnego włączania stopy ref. i jej proxy.

### 3.2.6. Tekst zarządu (warstwa uzupełniająca)

Z wybranych sprawozdań zarządu i listów wyodrębniono tekst i policzono proste wskaźniki leksykalne w stylu słowników Loughran–McDonald w wersji polskiej: ton (\(TONE\)), niepewność, pewność oraz proxy czytelności. Agregacja: dokumenty roczne mapowane na Q4, półroczne na Q2. Pokrycie jest **niepełne** (ok. 74 kwartałów spółek z niepustym tonem na 168 komórek panelu); warstwa NLP ma charakter uzupełniający (MVP) i nie stanowi głównego kanału identyfikacji.

Badanie **nie** wykorzystuje w wersji bazowej warstwy newsów medialnych (PAP i in.); ewentualne rozszerzenie pozostawiono poza zakresem.

## 3.3. Klasyfikacja zdarzeń ESPI

Każdemu tytułowi raportu bieżącego przypisano kategorię na podstawie reguł słów kluczowych (pierwsze dopasowanie wygrywa), m.in.: wyniki finansowe, dywidenda, prognoza, zmiany personalne, **transakcje M&A**, emisja/finansowanie, walne zgromadzenie, rating, regulacje, akcjonariat, umowy/kontrakty oraz reszta („inne”).

Reguły M&A obejmują m.in. przejęcie kontroli, wezwanie do zapisywania się na sprzedaż akcji, połączenie spółek, koncentrację oraz komunikaty związane z LOTOS, ENERGA i PGNiG w kontekście transakcyjnym. Transakcje menedżerskie typu „nabycie akcji Spółki przez członka zarządu” klasyfikowano jako **akcjonariat**, nie M&A. Wezwania do złożenia dokumentów akcji (dematerializacja) **nie** są traktowane jako wezwania przejęciowe.

W oknie 2019–2025 po klasyfikacji m.in. ok. 127 zdarzeń należy do `transakcje_MA`, a ok. 36% komunikatów pozostaje w koszu „inne” (tytuły formalne, operacyjne lub niejednoznaczne). Klasyfikacja automatyczna jest transparentna i powtarzalna, ale obarczona błędem reguł — w studiach przypadków daty kluczowe weryfikowano ręcznie względem kalendariów.

## 3.4. Analiza zdarzeń (event study)

### 3.4.1. Model rynkowy i okna

Dla każdego zdarzenia \(e\) spółki \(i\) oszacowano model rynkowy metodą najmniejszych kwadratów:

\[
R_{i,\tau}=\alpha_{i,e}+\beta_{i,e} R_{m,\tau}+\varepsilon_{i,\tau},
\]

w oknie estymacji \(\tau\in[-250,-11]\) dni sesyjnych względem Day 0, przy minimum **100** obserwacjach. \(R_m\) to zwrot wybranego benchmarku. Stopa nadzwyczajna:

\[
AR_{i,\tau}=R_{i,\tau}-\bigl(\hat\alpha_{i,e}+\hat\beta_{i,e} R_{m,\tau}\bigr),
\]

oraz skumulowana stopa nadzwyczajna w oknie \([t_1,t_2]\):

\[
CAR_i(t_1,t_2)=\sum_{\tau=t_1}^{t_2} AR_{i,\tau}.
\]

Raportowano m.in. okna \([-1,+1]\), \([-3,+3]\), \([-5,+5]\), \([-10,+10]\) i \([-20,+20]\).

**Benchmarki:** WIG-energia dla PGE, TPE i ENA; WIG-paliwa dla PKN; WIG dla UNT, ZEP, JSW i LWB. Wybór dla UNT i ZEP wynika z wyższego dopasowania modelu do WIG niż do indeksu sektorowego w oknie estymacji (mediana \(R^2\) dla UNT ok. 0,13, dla ZEP ok. 0,09 — wyraźnie niższa niż dla PKN/PGE).

### 3.4.2. Definicja Day 0

Day 0 to pierwszy dzień sesyjny, w którym publikacja ESPI może wpływać na ceny:

1. Jeżeli znana jest godzina publikacji **przed 17:00**, Day 0 to pierwsza sesja \(\ge\) dacie raportu.  
2. Jeżeli godzina jest **\(\ge\) 17:00** albo **godzina jest nieznana**, datę kalendarzową przesuwa się o jeden dzień, a następnie mapuje na najbliższą sesję.

Próg 17:00 odpowiada w przybliżeniu zamknięciu sesji ciągłej z buforem na publikacje po zamknięciu. W zebranym zbiorze godzina jest dostępna w zasadzie dla ENA, JSW i LWB oraz niemal w pełni dla PGE i TPE; dla **PKN i ZEP godzina nie występuje** (oraz jest rzadka dla UNT), stąd Day 0 opiera się na regule konserwatywnej (następna sesja).

W analizie wrażliwości porównano regułę bazową z wariantem „data raportu → najbliższa sesja bez automatycznego +1 dnia” przy braku godziny. Dla PKN w oknie \([-5,+5]\) korelacja CAR między regułami na poziomie zdarzenia jest wysoka (rzędu 0,9); w węższym oknie \([-1,+1]\) różnice bywają większe. Wyniki główne odnoszą się do reguły z przesunięciem przy braku godziny.

### 3.4.3. Wnioskowanie statystyczne

Dla średnich CAR w kategoriach stosowano:

- test **Boehmera, Musumeciego i Poulsena (1991)** (BMP) — standaryzacja CAR przez odchylenie reszt z okna estymacji;  
- **test znaku** (hipoteza \(P(CAR>0)=1/2\));  
- dla małych podprób (\(n<20\)) — **bootstrapowe** przedziały ufności dla średniej CAR.

Analiza wrażliwości obejmuje wykluczenie spółek o niskim dopasowaniu modelu rynkowego (UNT, ZEP) oraz — w aneksie — wariant Day 0.

## 3.5. Panel kwartalny i zmienne kontrolne

Jednostką panelu jest spółka–kwartał. Obok wielkości rachunkowych (aktywa, kapitał, przychody, EBIT/EBITDA, zysk netto, CF operacyjny, CAPEX) zdefiniowano:

\[
\mathrm{lev}_{i,t}=\frac{D^{\mathrm{net}}_{i,t}}{A_{i,t}},
\qquad
D^{\mathrm{net}}_{i,t}=D^{\mathrm{odsetkowe}}_{i,t}-\mathrm{Cash}_{i,t}.
\]

To **główna miara dźwigni** w modelach. Wskaźnik \(D^{\mathrm{net}}/\mathrm{EBITDA}\) (ew. EBIT) zachowano opisowo; przy ujemnym wyniku operacyjnym jest niestabilny i nie wchodzi do specyfikacji bazowych. W robustness stosowano winsoryzację \(\mathrm{lev}\) (1. i 99. percentyl).

Dodatkowo: wskaźniki zdarzeń w kwartale (m.in. flaga M&A, dywidendy, finansowania, liczby ESPI), zwrot kwartalny i zmienność zwrotów, proxy \(M/B\), oraz — gdy dostępne — wskaźniki tonu z tekstów zarządu (z opóźnieniem kwartalnym w analizach deskryptywnych CAR × ton).

## 3.6. Studia przypadków i mapowanie na ESPI

Dla hipotez jakościowych (m.in. overconfidence/CAPEX, eskalacja, hubris M&A, status quo/NABE, mental accounting dywidendy/FIZ, framing strategii) zbudowano kalendaria priorytetowych dat. Każdą datę starano się powiązać z komunikatem ESPI (dokładna data lub reguły dopasowania) oraz z oszacowanym CAR. Ze **52** wierszy mapy case **45** ma dopasowanie do ESPI w oknie 2019–2025; niedopasowania wynikają m.in. z dat poza oknem, braku osobnego ESPI lub niejednoznaczności dnia prawa do dywidendy. Zbiór analityczny łączy zdarzenia z CAR, flagami case i kowariantami panelu z tego samego oraz poprzedniego kwartału.

## 3.7. Ograniczenia metody

Po pierwsze, event study mierzy **krótkookresową reakcję rynku**, a nie długookresowy efekt realny inwestycji czy fuzji; wnioski behawioralne opierają się na współwystępowaniu narracji (ESPI, case) i CAR, a nie na eksperymencie naturalnym z losowym przydziałem. Po drugie, klasyfikacja tytułów ESPI jest regułowa i pozostawia duży udział kategorii „inne”. Po trzecie, brak godzin publikacji dla PKN systematyzuje Day 0; sensitivity łagodzi, ale nie eliminuje niepewności timing’u. Po czwarte, dualne źródła rachunkowe i stałe proxy liczby akcji ograniczają precyzję porównań między spółkami. Po piąte, warstwa tekstowa jest rzadka i słownikowa. Po szóste, niska \(R^2\) modelu rynkowego dla UNT i ZEP oznacza głośniejsze AR — stąd analizy wrażliwości bez tych spółek.

Mimo tych ograniczeń konstrukcja danych jest w pełni skryptowana i powtarzalna: od surowych ESPI i notowań, przez CAR i panel, po zbiory analityczne wykorzystywane w rozdziale z wynikami.

---

## Tabele pomocnicze (do wstawienia / aneksu)

### Tabela D.1. Źródła danych (skrót)

| Warstwa | Źródło | Jednostka |
|---------|--------|-----------|
| Notowania, indeksy | GPW / Yahoo (UNT.WA) | dzień |
| ESPI | IR emitentów | zdarzenie |
| Rachunkowość PKN | pakiety RI Orlen | kwartał |
| Rachunkowość peer | BiznesRadar | kwartał |
| FX, stopa ref. NBP | NBP / ścieżka RPP | dzień → kwartał |
| Brent | futures BZ=F | dzień → kwartał |
| Energia PL | energy-charts (proxy) | dzień → kwartał |
| Carbon proxy | KRBN | dzień → kwartał |
| Tekst zarządu | PDF IR → słownik PL | dokument → kwartał |
| Case / NIK | kalendaria, wystąpienia NIK | data case |

### Tabela D.2. Parametry event study

| Element | Wartość |
|---------|---------|
| Model | rynkowy, OLS |
| Okno estymacji | [−250, −11] sesji |
| Min. obserwacji | 100 |
| Okna CAR | [−1,+1] … [−20,+20] |
| Day 0 | sesja wg godziny ESPI; brak godziny → +1 sesja |
| Testy | BMP (1991), znak, bootstrap \(n<20\) |

### Tabela D.3. Benchmarki modelu rynkowego

| Ticker | Benchmark |
|--------|-----------|
| PGE, TPE, ENA | WIG-energia |
| PKN | WIG-paliwa |
| UNT, ZEP, JSW, LWB | WIG |

---


---

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


---

# Rozdział 5. Wyniki badań empirycznych

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


---

# Rozdział 6. Dyskusja wyników i weryfikacja hipotez

*Wersja robocza rozdziału 6 (konspekt). Opiera się na: `MAPA_HIPOTEZ.md`, `ROZDZIAL_Wyniki.md`, `ROZDZIAL_Dane_i_metody.md`, H7/H11. Zasada weryfikacji z konspektu: hipotezę uznaje się za wspartą przy **zbieżności co najmniej dwóch filarów** (I case/dokumenty, II tekst, III event study, IV panel).*

---

Celem dyskusji jest ocena, w jakim stopniu wyniki empiryczne pozwalają utrzymać, zawęzić lub odrzucić hipotezy sformułowane we wstępie, oraz umiejscowienie ich względem literatury *behavioral corporate finance* (BCF). Wnioskowanie świadomie unika silnych roszczeń przyczynowych: przy małej liczbie emitentów, dualnych źródłach rachunkowych i niepełnej warstwie tekstowej praca dokumentuje **przejawy** inklinacji i **współwystępowanie** z reakcją rynku, a nie identyfikuje czystego efektu behawioralnego oderwanego od logiki agencyjnej i politycznej.

## 6.1. Status hipotez w świetle triangulacji

### 6.1.1. Tabela zbiorcza

**Tabela D.1. Status hipotez (stan empiryczny pracy)**

| H | Treść skrócona | Filar I case | Filar II tekst | Filar III CAR | Filar IV panel | **Status** |
|---|----------------|:------------:|:--------------:|:-------------:|:--------------:|------------|
| **HG** | BCF współwyjaśnia decyzje i reakcję rynku | + | ± | + | ± | **Częściowo** |
| **H1** | Overconfidence / złudzenie planowania (megaprojekty) | **+** | ± | 0 | — | **Częściowo (I)** |
| **H2** | Eskalacja / sunk cost | **+** | — | **+** (Ostrołęka) | — | **Częściowo (I+III)** |
| **H3** | Hubris M&A (Orlen) | **+** (NIK) | — | ± (heterogen.) | — | **Częściowo (I)** |
| **H4** | Status quo / NABE vs ZEP | **+** | — | ± | — | **Częściowo≈I mocne** |
| **H5** | Herding strategii | ± opis | — | 0 | — | **Otwarte / słabe** |
| **H6** | Kotwiczenie dywidendy / FIZ | **+** | — | 0 | — | **Częściowo (I)** |
| **H7** | Ton → wyższy CAPEX | — | ± | — | **−** (n.s./−) | **Nie potwierdzona** |
| **H8** | TONE×CFO → inwestycje | — | ± | — | ± (p≈0,09) | **Nie potwierdzona wiarygodnie** |
| **H9** | TONE_FUND_GAP + korekta CAR | — | — | 0 (corr≈0) | — | **Nie potwierdzona / nie zbudowana** |
| **H10** | Sentyment newsowy | — | — | — | — | **Wyłączona** |
| **H11** | Silniejsze efekty w kryzysie | ± | — | ± (struktura, nie grand mean) | — | **Częściowo / przeformułowana** |

Legenda filarów: **+** wspiera hipotezę; **±** mieszane lub słabe; **0** brak efektu / neutralne; **−** przeciwne do hipotezy; **—** nie testowano.

### 6.1.2. Hipoteza główna (HG)

HG w pełnym brzmieniu konspektu zakłada, że inklinacje menedżerskie **oraz** sentyment otoczenia informacyjnego istotnie współwyjaśniają decyzje i reakcję rynku po kontroli fundamentów i szoków. W wersji zrealizowanej:

- **dokumentacja inklinacji w decyzjach** (Blok A, filar I) jest najmocniejszym filarem;
- **reakcja rynku na ESPI** (filar III) jest mierzalna i heterogeniczna, ale rzadko daje jednolity, „czysty” wzorzec behawioralny;
- **ton zarządu** (filar II/IV) nie potwierdza prostego kanału „optymizm → CAPEX” (H7);
- **newsy** (H10) wyłączono.

**Werdykt HG (ostrożny):** praca **częściowo wspiera** HG w węższym sformułowaniu: *w sektorze energetyczno-paliwowym GPW w latach 2020–2025 dają się udokumentować przejawy inklinacji menedżerskich w decyzjach strategicznych i komunikacji IR, a rynek reaguje na komunikaty ESPI w sposób zróżnicowany według typu zdarzenia i epizodu; pełna estymacja wkładu sentymentu medialnego oraz silnego panelowego kanału ton→inwestycje pozostaje poza zakresem wersji bazowej.*

### 6.1.3. Blok A (H1–H6) — inklinacje w decyzjach

**H1 (overconfidence / planning fallacy).** Materiał dokumentacyjny Olefin III (ścieżka budżetu ex ante → rewizje → zatrzymanie) jest spójny z niedoszacowaniem nakładów i kategorycznością narracji projektowej. Event study **nie** dostarcza serii silnie ujemnych CAR na każdym kamieniu milowym — średnie wokół FID, rewizji i stopu są bliskie zera w oknie [−1,+1]. Nie podważa to H1: hipoteza dotyczy **decyzji i planowania**, nie natychmiastowej kary rynkowej. Jaworzno 910 MW pozostaje kotwicą słabiej zoperacjonalizowaną w kalendarium. **Status: częściowo wsparta (głównie filar I).**

**H2 (eskalacja / sunk cost).** Ostrołęka C i łańcuch Olefin (późny stop po dużych nakładach i odpisach) tworzą spójny obraz opóźnionej rezygnacji. CAR wokół twardych sygnałów Ostrołęki jest przeciętnie ujemny (ok. −0,8% w [−1,+1]), silniejszy niż przy wieloletnim łańcuchu rewizji Olefin. Brak modeli *time-to-impairment* i interakcji ton×szok (filar IV) uniemożliwia pełną operacjonalizację z konspektu. **Status: częściowo wsparta (I + częściowo III).**

**H3 (hubris M&A).** Ustalenia NIK dotyczące remedium Lotosu oraz kalendarium Energa–Lotos–PGNiG wspierają tezę o agresywnej konsolidacji i kosztach transakcyjnych niedostatecznie wyeksponowanych ex ante. Rynkowo: kategoria M&A ma średni CAR bliski zeru (BMP nieistotny), przy istotnym teście znaku (więcej CAR>0), a ścieżka Orlen jest **heterogeniczna** (silnie ujemne CAR przy warunkowej zgodzie KE na Lotos; dodatnie przy rejestracji PGNiG). Nie wolno pisać, że „rynek systematycznie karze hubris”; wolno pisać, że **rynek różnicuje etapy transakcji**, a ocena *ex post* (NIK) jest surowsza niż przeciętna reakcja CAR. **Status: częściowo wsparta (silny I, mieszany III).**

**H4 (status quo / awersja do strat).** Kalendarium NABE (2021→rezygnacja 2025) i kontrast z trajektorią ZE PAK dają najczystszy argument o odkładaniu dezinwestycji w spółkach SP. CAR na nielicznych datach NABE jest mieszany (m.in. Enea+, PGE− na porozumieniu 2021). Główny dowód pozostaje **instytucjonalno-kalendarzowy**, nie event-study. **Status: częściowo wsparta z mocnym filarem I.**

**H5 (herding strategii).** Zebrano strategie i daty publikacji; brak formalnej miary podobieństwa tekstów (`STRAT_SIM`). CAR wokół publikacji strategii jest bliski zera. **Status: otwarte / jedynie opisowa zbieżność narracji — nie oznaczać jako potwierdzone.**

**H6 (kotwiczenie / mental accounting).** Epizody polityki dywidendowej Orlenu (ścieżki gwarantowanych DPS w strategiach) oraz FIZ JSW (umorzenia certyfikatów przy trudnej sytuacji wynikowej i utrzymanym CAPEX) wspierają tezę o „kubełkach” gotówki. Kategoria dywidenda w pełnej próbie ESPI nie daje istotnego średniego CAR; dni prawa do dywidendy często bez ESPI. **Status: częściowo wsparta (I); bez ekonometrii sztywności payout.**

### 6.1.4. Blok B–C (H7–H11)

**H7.** W FE z kontrolami i opóźnionym tonem współczynnik przy \(TONE\) dla \(\mathrm{capex}_{t+1}\) jest **ujemny i nieistotny** (n≈66, G=7). Korelacja \(TONE\)–CAPEX lead ≈ −0,20. **H7 w brzmieniu „wyższy ton → wyższe inwestycje” nie jest potwierdzona.** Ewentualny dodatni związek tonu z przyrostem długu netto (spec. finansowa) jest eksploracyjny i nie zastępuje kanału inwestycyjnego.

**H8.** Interakcja \(TONE \times CFO\) na granicy 10% (p≈0,09) przy niskiej mocy. **Nie potwierdzona wiarygodnie.**

**H9.** `TONE_FUND_GAP` nie zbudowano; prosta korelacja CAR–ton ≈ 0. **Nie potwierdzona.**

**H10.** Warstwa newsowa nie została zbudowana. **Wyłączona z wersji bazowej** (zgodnie z checklistą danych). HG należy czytać bez komponentu sentymentu medialnego.

**H11.** Grand mean CAR[−5,+5] **nie** jest najwyższy w 2022–2023 (≈ −0,07%); w 2020 M&A są istotnie ujemne; w kryzysie rośnie raczej **odsetek** CAR>0 w niektórych podpróbach i zmienia się struktura kategorii. **H11 w brzmieniu „silniejszy przeciętny CAR w kryzysie” — nie; w brzmieniu „kryzys moderuje kanały i heterogeniczność” — częściowo.**

## 6.2. Konfrontacja z literaturą

Wyniki wpisują się w dwa nurty BCF (Baker, Ruback, Wurgler; Malmendier, Tate i in.).

1. **Nieracjonalny menedżer.** Overconfidence i eskalacja (H1–H2) są klasycznie wiązane z nadmiernym inwestowaniem i opóźnionym *write-off*. Materiał case (Olefiny, Ostrołęka) jest z tym zgodny na poziomie faktów decyzyjnych. Brak panelowego potwierdzenia H7 oznacza, że **słownikowy ton IR nie jest w tej próbie dobrym proxy** agresji inwestycyjnej — co jest zgodne z ostrzeżeniami literatury o endogeniczności i szumie ujawnień (Loughran–McDonald: ton zależy od gatunku tekstu i regulacji).

2. **Hubris w M&A (Roll).** Literatura przewiduje ujemne CAR akwizytora przy przejęciach napędzanych pychą. W pełnej kategorii M&A średnia jest bliska zera; **epizody Orlen** pokazują ujemne CAR przy niepewności regulacyjnej i dodatnie przy domknięciu PGNiG. Pasuje to bardziej do **warunkowej wyceny ryzyk transakcji** niż do jednolitej premii/kary za „empire building”. NIK dostarcza niezależnego *ex post*, którego standardowy event study nie zastąpi.

3. **Status quo i strata.** Opóźnianie dezinwestycji węglowych (H4) rezonuje z awersją do realizacji strat i z literaturą o *state ownership* / polityce energetycznej; kontrast ZEP jest tu ważniejszy niż CAR.

4. **Sentyment i rynek.** H9–H10 w literaturze łączą media i luki tonu z krótkimi stopami zwrotu. W tej pracy brak newsów i słaba zależność CAR–ton oznaczają, że **wkład leży raczej po stronie decyzji i IR/ESPI**, nie po stronie media microstructure.

5. **Polska luka BCF korporacyjnego.** Konspekt wskazywał niedostatek empirii na emitentach GPW. Praca częściowo ją wypełnia: **replikowalny słownik ESPI + case + CAR**, przy świadomym ograniczeniu ambicji panelowo-medialnych.

## 6.3. Co jest behawioralne, co agencyjne, a co polityczne

Granice interpretacji są kluczowe przy dominacji Skarbu Państwa.

| Mechanizm | Przykład w materiale | Ryzyko nadinterpretacji |
|-----------|----------------------|-------------------------|
| **Behawioralny** (overconfidence, escalation, mental accounting) | Rewizje CAPEX Olefin; późny stop; FIZ JSW; gwarancja DPS | „Błąd poznawczy” tam, gdzie jest racjonalna gra o taryfy/subsydia |
| **Agencyjny** | Budowanie skali Orlen; premiowanie wzrostu vs FCF | Hubris vs mandat właściciela SP |
| **Polityczny / regulacyjny** | NABE, remedium KE, rotacje zarządów | Status quo jako *policy wait* nie *loss aversion* menedżera |

Kontrast **UNT / ZEP** (prywatni) częściowo oddziela SP od inklinacji „czysto menedżerskich”, ale niska płynność i niski \(R^2\) modelu rynkowego ograniczają siłę testów CAR. NIK (Lotos, Ostrołęka) jest najmocniejszym zewnętrznym kotwicowaniem narracji zarządów — **nie behawioralnym modelem, lecz audytem faktów**.

Rekomendacja redakcyjna: w tekście używać sformułowań typu *„wzorzec zgodny z X”*, *„trudny do odróżnienia od Y”*, unikać *„dowodzi irracjonalności zarządu”*.

## 6.4. Implikacje

**Dla zarządów i IR.** Rynek silniej reaguje na komunikaty o **akcjonariacie/progach** i **ratingach** niż na przeciętny „szum” wyników w wąskim oknie; przy M&A liczy się **etap** (niepewność KE vs domknięcie). Kalendaria CAPEX pokazują, że opóźnione *write-off* i reframing („Nowa Chemia”) nie zastępują wiarygodnego planu kosztów.

**Dla inwestorów i analityków.** Event study po kategoriach ESPI jest użyteczny deskryptywnie, ale **średnie CAR M&A ≈ 0** nie oznaczają braku ryzyka transakcyjnego — ścieżki case są silnie niejednorodne. Spółki o niskim \(R^2\) (UNT, ZEP) wymagają ostrożności w interpretacji AR.

**Dla nadzoru właścicielskiego i regulatora.** Materiał NABE i NIK wzmacnia argument o koszcie odkładania dezinwestycji i o asymentrii informacji przy remedium fuzji. Praca nie formułuje rekomendacji taryfowych; wskazuje na **wartość niezależnego audytu ex post** względem narracji IR.

## 6.5. Ograniczenia a wiarygodność wniosków

1. **Małe N spółek** — panel i klastry SE (G=7) mają niską moc; stąd priorytet zdarzeń ESPI (tysiące) i case.  
2. **Brak godzin ESPI dla PKN** — systematyczny shift Day 0; sensitivity w aneksie.  
3. **Klasyfikacja regułowa tytułów** — duży udział „inne”; M&A poprawione, ale nie idealne.  
4. **TONE sparse i słownikowy** — H7–H9 nie mogą dźwigać wkładu.  
5. **H10 wyłączone** — HG bez mediów.  
6. **H5 bez similarity** — herding tylko opisowo.  
7. **Dualne źródła rachunkowe** — porównywalność peer vs PKN ograniczona.

Ograniczenia te **nie unieważniają** Bloku A ani mapy CAR; wyznaczają, czego praca **nie** twierdzi.

## 6.6. Synteza: co praca wnosi

1. **Udowokumentowane przejawy** overconfidence, eskalacji, hubris (ex post NIK), status quo i mental accounting na materiale 2020–2025 sektora GPW.  
2. **Replikowalny most** ESPI → CAR → case (45/52 dat) z jawnymi regułami Day 0 i benchmarków.  
3. **Negatywne wyniki o wartości:** brak potwierdzenia H7 (ton→CAPEX), brak grand-mean H11, wyłączenie H10 — chronią przed nadmierną „storytelling” BCF.  
4. **Mapa hipotez z statusami** jako szkielet rozdziału dyskusji i ewentualnej obrony.

Wkład jest zatem **empiryczno-dokumentacyjny i metodologiczny** (triangulacja), nie „odkryciem uniwersalnego współczynnika behawioralnego” w panelu siedmiu spółek.

---


---

# Zakończenie

*Wersja robocza. Tytuł roboczy pracy: „Przejawy czynników behawioralnych w decyzjach inwestycyjno-finansowych wybranych spółek sektora energetyczno-paliwowego notowanych na GPW w latach 2020–2025”. Synteza rozdziałów danych, wyników i dyskusji (stan empiryczny 2026-07).*

---

## Podsumowanie celu i podejścia

Celem pracy było zidentyfikowanie, zoperacjonalizowanie i empiryczne oszacowanie **przejawów** czynników behawioralnych w decyzjach inwestycyjno-finansowych wybranych spółek sektora energetyczno-paliwowego na GPW w latach 2020–2025 oraz zbadanie, w jakim stopniu czynniki te współkształtowały **krótkookresową reakcję rynku** na komunikaty o tych decyzjach. Projekt celowo rozłożono na kilka filarów: wielokrotne studium przypadku z konfrontacją dokumentów IR i ustaleń NIK, analizę zdarzeń (ESPI → model rynkowy → CAR), panel kwartalny spółka–czas oraz uzupełniającą warstwę tekstową (słownikowy ton zarządu). Przy małej liczbie emitentów panel nie stanowił „modelu głównego”, lecz element triangulacji — zgodnie z założeniem, że tytułowe *przejawy* najpierw dokumentuje się w decyzjach i komunikacji, a dopiero potem ostrożnie mierzy ich siłę.

Okres 2020–2025 okazał się naturalnym laboratorium: pandemia i krach cen ropy, kryzys energetyczny i konsolidacja sektora wokół Orlenu, programy transformacji i dezinwestycji węglowych (NABE), wreszcie korekty strategiczne i normalizacja. Próba połączyła spółki z dominacją Skarbu Państwa z kontrastem prywatnym (Unimot, ZE PAK) oraz — w warstwie rynkowej — rozszerzeniem o podmioty rezerwowe.

## Najważniejsze ustalenia empiryczne

**Po pierwsze**, w materiale dokumentacyjnym dają się odtworzyć wzorce zgodne z kanonicznymi mechanizmami *behavioral corporate finance*: niedoszacowanie nakładów i złudzenie planowania (Olefiny III), eskalacja zaangażowania i koszty utopione (Ostrołęka C, późny stop projektów), hubris i koszty transakcyjne M&A w świetle NIK (konsolidacja Orlen–Lotos–PGNiG–Energa), odkładanie dezinwestycji węglowych w oczekiwaniu na rozwiązanie zewnętrzne (NABE vs trajektoria ZE PAK) oraz kotwiczenie polityki dywidendowej i „kubełkowanie” nadwyżek (polityka DPS Orlenu, FIZ JSW). Te ustalenia opierają się przede wszystkim na kalendariach, sprawozdaniach i kontrolach NIK, a nie na jednym współczynniku regresji.

**Po drugie**, event study na tysiącach komunikatów ESPI pokazuje, że rynek **różnicuje typy zdarzeń**. W oknie [−5,+5] najsilniejszy parametrycznie efekt w pełnej próbie dotyczy kategorii akcjonariatu/progów, przy czym wynik jest wrażliwy na skład próby (Unimot). Ratingi generują istotnie dodatni CAR w wąskim oknie przy małej liczebności. Transakcje M&A nie dają istotnej średniej CAR w teście BMP, ale charakteryzują się istotnie wyższym odsetkiem obserwacji z CAR > 0; ścieżka Orlen jest heterogeniczna — od silnie ujemnych reakcji przy niepewności regulacyjnej (m.in. Lotos/KE) po dodatnie przy domknięciu połączenia z PGNiG. Średni CAR wokół dat case CAPEX jest bliższy zeru dla wieloletniego łańcucha Olefin i wyraźniej ujemny dla twardych sygnałów Ostrołęki.

**Po trzecie**, warstwa panelowa i tekstowa **nie potwierdza** prostego kanału „wyższy ton zarządu → wyższy CAPEX” (H7): w estymacjach z efektami stałymi współczynnik przy opóźnionym tonie jest nieistotny, a surowa korelacja jest ujemna. Interakcja tonu z przepływami operacyjnymi (H8) pozostaje na granicy istotności przy niskiej mocy testu. Korelacja CAR z tonem jest bliska zeru; luki tonu względem fundamentów i warstwy newsowej nie zbudowano lub świadomie wyłączono (H9–H10).

**Po czwarte**, podział na podokresy niepewności (H11) **nie** wskazuje na wyższy przeciętny CAR w latach kryzysu 2022–2023 względem normalizacji 2024–2025. Różnice dotyczą raczej **struktury i znaku** reakcji (m.in. ujemne M&A w 2020, zmienny odsetek CAR dodatnich w wybranych oknach) niż uniwersalnej „silniejszej premii behawioralnej” w kryzysie.

## Weryfikacja hipotez — synteza

Hipoteza główna w pełnym brzmieniu konspektu (inklinacje menedżerskie **oraz** sentyment otoczenia medialnego współwyjaśniają decyzje i wycenę) została **częściowo** utrzymana w węższym sformułowaniu: praca dokumentuje przejawy inklinacji w decyzjach i komunikacji IR oraz heterogeniczną reakcję rynku na ESPI, bez estymacji przyczynowego wkładu newsów i bez silnego panelowego potwierdzenia kanału ton→inwestycje.

W bloku H1–H6 przeważa wsparcie **jakościowo-dokumentacyjne** (często z uzupełnieniem CAR na datach case), przy świadomym braku pełnej ekonometrii odpisów, herdingu tekstowego i sztywności payout. H7 nie została potwierdzona; H8–H9 nie stanowią wiarygodnego filaru; H10 wyłączono; H11 wymaga przeformułowania z „wyższego średniego CAR w kryzysie” na „moderację kanałów i heterogeniczność”.

Takie wyniki negatywne i zawężenia nie są porażką projektu: chronią przed nadinterpretacją BCF i pokazują, gdzie proxy tekstowe oraz mały panel przestają dźwigać ambicje „małej rozprawy”, a gdzie case i ESPI nadal niosą treść.

## Wkład pracy

1. **Empiryczny** — przeniesienie narzędzi BCF na konkretnych emitentów GPW w strategicznym sektorze, z unikatową możliwością konfrontacji narracji zarządów z ustaleniami NIK (Lotos, Ostrołęka).  
2. **Metodologiczny** — sekwencyjny, skryptowalny pipeline: ESPI → kategorie → Day 0 → CAR → panel → mapa case (45/52 dat), z jawnymi regułami benchmarków, dźwigni, korekty notowań Unimot (`UNT.WA`) i testów wrażliwości.  
3. **Poznawczy** — mapa statusów hipotez (wsparta / częściowo / nie / wyłączona) jako uczciwy bilans triangulacji, a nie selektywne eksponowanie „istotnych gwiazdek”.

## Ograniczenia

Wnioski ograniczają: mała liczba spółek i niska moc panelu; dualne źródła rachunkowe; brak godzin publikacji ESPI dla PKN (systematyczny shift Day 0); regułowa klasyfikacja tytułów z dużym udziałem kategorii „inne”; sparse i słownikowy charakter tonu; wyłączenie newsów; brak formalnej miary podobieństwa strategii (H5); niższe \(R^2\) modelu rynkowego dla spółek mniej płynnych. Event study mierzy krótkookresową wycenę, nie długookresowy efekt realny inwestycji. Mechanizmy behawioralne trudno w pełni oddzielić od agencyjnych i politycznych przy dominacji SP — stąd ostrożny język wniosków.

## Kierunki dalszych badań

Naturalne rozszerzenia obejmują: (i) historyczną warstwę newsową wokół top-ESPI (H10); (ii) pełniejszą operacjonalizację luki tonu i okien korekty CAR (H9); (iii) modele czasu do odpisu (H2) na szerszej próbie; (iv) miary podobieństwa strategii (H5); (v) porównanie z innymi sektorami regulowanymi GPW; (vi) wykorzystanie zbudowanej bazy zdarzeń i tekstów w replikacjach i aktualizacjach po 2025 r. Baza ESPI–CAR–case sama w sobie może stanowić produkt uboczny pracy o wartości dla kolejnych projektów.

## Zakończenie właściwe

W latach 2020–2025 polski sektor energetyczno-paliwowy na GPW był areną decyzji o skali rzadko spotykanej w jednym sektorze: megaprojekty petrochemiczne i energetyczne, fuzje systemowe, próby wydzielenia węgla, sztywne kotwice dywidendowe i fundusze stabilizacyjne. Praca pokazuje, że w tych decyzjach i w ich publicznej oprawie widać wzorce opisywane przez finanse behawioralne przedsiębiorstw — zwłaszcza po stronie **dokumentacji faktów decyzyjnych** — podczas gdy **rynek akcji** reaguje selektywnie, etapami i często bez jednolitego znaku „kary za irracjonalność”. Najuczciwszy wniosek nie brzmi więc, że menedżerowie „są nieracjonalni, a rynek to zawsze karze”, lecz że **przejawy inklinacji da się systematycznie opisać i częściowo zmierzyć**, o ile łączy się studia przypadku, niezależne audyty i dyscyplinę event study — oraz o ile nie przeciąża się małego panelu i niedoskonałego tonu IR rolą, której te dane nie udźwigną.

---


---

# Aneksy i materiały robocze (odsyłacze)

| Materiał | Ścieżka |
|----------|---------|
| Mapa hipotez H1–H11 | `data/processed/MAPA_HIPOTEZ.md` |
| Fragmenty metodologii | `data/processed/METODOLOGIA_fragmenty_dane.md` |
| H7 panel | `data/processed/h7_panel_summary.md` |
| H11 podokresy | `data/processed/h11_periods_summary.md` |
| Tabele | `data/processed/tables/` |
| Wykresy AAR | `data/processed/plots/` |
| Kalendaria case | `data/processed/case_studies/` |
| Audyt danych | `data/AUDIT_DANYCH_2026-07-21.md`, `AUDIT_P1_2026-07-21.md` |
| Bibliografia PDF | `Bibliography/moje_pdfy/` |
| Skrypty | `data/scripts/` |

---

*Koniec pliku scalonego. Przed oddaniem: (1) ujednolicić numerację sekcji, (2) skrócić powtórzenia CAR między R4 a R5, (3) dodać bibliografię i spis tabel/rysunków, (4) zweryfikować liczby NIK w PDF.*
