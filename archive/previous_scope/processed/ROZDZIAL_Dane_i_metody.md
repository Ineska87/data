# Dane i metody badawcze

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

## Nota dla autora (usuń przed oddaniem)

- Plik: `data/processed/ROZDZIAL_Dane_i_metody.md`  
- Numery rozdziału „3.x” dostosuj do spisu treści pracy (może być rozdz. 4).  
- W rozdziale wyników odwołaj się do: `tabela1_model`, `tabela2_car_tests`, `tabela3_wrazliwosc`, wykresów AAR, `case_events_enriched`.  
- Fragmenty składowe: `METODOLOGIA_fragmenty_dane.md`.  
- Po zmianie danych: zaktualizuj liczby 2550 / 2546 / 168 / 45/52.
