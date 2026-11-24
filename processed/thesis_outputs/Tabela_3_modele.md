# Tabela 3. Zależność między tonem wcześniejszego raportu a CAR[−1,+1]

| Miara | M1 · bazowy | M2 · oszczędny | M3a · kontekst CAPEX | M3b · CAPEX + efekty stałe |
| --- | --- | --- | --- | --- |
| Próba zdarzeń | Ścisłe dopasowanie | Ścisłe dopasowanie | Ścisłe dopasowanie + kontekst CAPEX | Ścisłe dopasowanie + kontekst CAPEX |
| Efekty stałe spółki i typu decyzji | Tak | Nie | Nie | Tak |
| Liczba zdarzeń | 17 | 17 | 28 | 28 |
| Niekorzystne korekty (yes) | 12 | 12 | 13 | 13 |
| Pozostałe zdarzenia (no) | 5 | 5 | 15 | 15 |
| Liczba odrębnych raportów | 17 | 17 | 25 | 25 |
| Stopnie swobody reszt | 9 | 14 | 24 | 19 |
| Rząd macierzy / liczba kolumn | 8/9 | 3/4 | 4/4 | 9/9 |
| Pełny rząd w bootstrapie, liczba na 1000 | 0 | 0 | 579 | 482 |
| Pełny rząd w bootstrapie, odsetek (%) | 0,0 | 0,0 | 57,9 | 48,2 |
| Niekorzystne korekty (yes) · współczynnik tonu (p.p.) | -3,1322 | -0,8334 | -0,6657 | -0,4465 |
| Niekorzystne korekty (yes) · błąd standardowy HC3 (p.p.) | — | — | — | — |
| Niekorzystne korekty (yes) · p-value HC3 | — | — | — | — |
| Niekorzystne korekty (yes) · identyfikowalne losowania na 1000 | 389 | 629 | 653 | 595 |
| Niekorzystne korekty (yes) · dolna granica 95% PU bootstrap (p.p.) | — | — | — | — |
| Niekorzystne korekty (yes) · górna granica 95% PU bootstrap (p.p.) | — | — | — | — |
| Pozostałe zdarzenia (no) · współczynnik tonu (p.p.) | — | — | -0,4242 | -0,1502 |
| Pozostałe zdarzenia (no) · błąd standardowy HC3 (p.p.) | — | — | 0,8711 | 2,096 |
| Pozostałe zdarzenia (no) · p-value HC3 | — | — | 0,6307 | 0,9436 |
| Pozostałe zdarzenia (no) · identyfikowalne losowania na 1000 | 0 | 0 | 891 | 860 |
| Pozostałe zdarzenia (no) · dolna granica 95% PU bootstrap (p.p.) | — | — | -2,0602 | -3,3833 |
| Pozostałe zdarzenia (no) · górna granica 95% PU bootstrap (p.p.) | — | — | 0,816 | 2,9864 |
| Wyraz wolny · współczynnik (p.p.) | — | 0,7391 | -0,3327 | — |
| Wyraz wolny · błąd HC3 (p.p.) | — | 1,1464 | 0,7121 | — |
| Wskaźnik niekorzystnej korekty · współczynnik (p.p.) | — | -1,9595 | -0,7456 | — |
| Wskaźnik niekorzystnej korekty · błąd HC3 (p.p.) | — | 1,4587 | 1,0962 | — |
| Spearman ρ w grupie yes (n = 12) | — | -0,0437 | — | — |
| Spearman · p-value dokładne permutacyjne | — | 1,0 | — | — |
| Kendall τ-b w grupie yes (n = 12) | — | -0,0371 | — | — |
| Kendall · p-value dokładne permutacyjne | — | 1,0 | — | — |

**Uwagi.** Zmienną zależną jest CAR[−1,+1] względem WIG w podstawowym wariancie dnia 0. Współczynniki i błędy wyrażono w punktach procentowych CAR na jednostkę tonu. Jednostka tonu to jedno dodatnie dopasowanie netto na 100 słów. M1 odtwarza model z pliku `processed/analytical/investment_analysis_status.json`, sekcja `models.baseline_all`. Efekty typu decyzji w M1 i M3b obejmują wskaźnik grupy korekty z uwagi na współliniowość. Grupa `unknown` pozostaje poza modelami.

Bootstrap par losuje z powtórzeniami 1000 prób całych raportów przy stałym ziarnie 42. Pełny rząd wymaga identyfikacji wszystkich kolumn oryginalnej specyfikacji. Osobno zliczono losowania identyfikujące dany współczynnik mimo zależności pozostałych kolumn. Przedział percentylowy 95% podano przy co najmniej 800 z 1000 identyfikowalnych losowań oraz gdy po usunięciu dowolnego pojedynczego raportu parametr pozostaje identyfikowalny. HC3 przy dźwigni równej jeden jest nieokreślony dla parametrów zależnych od tej obserwacji. W kolumnie M1 pokazano wniosek bazowej diagnostyki bootstrapu, a błędy HC3 podano dla wariantów M2, M3a i M3b z p-value względem rozkładu t o stopniach swobody reszt.

P-wartości korelacji rangowych są dwustronne, permutacyjne i dokładne przy jednej obserwacji o niezerowym tonie. Enumeracja obejmuje 12 możliwych przypisań tej wartości do obserwowanego CAR.

M3 zachowuje 17 ścisłych dopasowań i rozszerza próbę o 11 powiązań z ogólną narracją inwestycyjną z 9 raportów odniesienia. Ten sam fragment w jednym raporcie ma ten sam ton dla wszystkich zdarzeń uzupełnianych z tego raportu. Uzupełnienia mierzą tło inwestycyjne spółki, a zatem rozszerzenie zmienia zakres mierzonej narracji i skład próby. Raport może obejmować inne projekty niż komunikat, do którego przypisano kontekst.

Pięć uzupełnień ORLENU pochodzi z czterech raportów w manifeście korpusu. Pozostałe sześć pochodzi z pięciu oficjalnych załączników do raportów okresowych. Kolumna `fragment_tekstu` w `extended_capex_passages.csv` zawiera tekst przekazany do słownika. Początek zakresu liczy się od zera, a koniec wyłącza znak końcowy. Przy pliku z manifestu znaki liczy się od początku pełnego tekstu. Przy załączniku znaki liczy się od początku tekstu jednej strony PDF, odczytanego w kolejności wizualnej przez PyMuPDF `get_text(sort=True)`. Kolumna `pdf_page` numeruje strony pliku od 1. Wstawione przez ekstraktor złamania wierszy i wcięcia zachowano w fragmencie. Funkcja słownika v0.2 wykonuje własną normalizację podczas pomiaru tonu.
