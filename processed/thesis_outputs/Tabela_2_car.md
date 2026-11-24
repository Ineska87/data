# Tabela 2. Reakcja rynku wokół zatwierdzonych komunikatów ESPI

CAR[−1,+1] w procentach, wariant podstawowy dnia 0, model rynkowy oparty na WIG. Wszystkie 33 zdarzenia mają pełne trzydniowe okno. Odchylenia standardowe obliczono z próby.

| Przekrój | Grupa | N | Średnia | Odch. std. | Mediana | Min. | Maks. | Ujemny CAR | t | p (t) | W | p (W) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Cała próba | Ogółem | 33 | −0,586 | 2,735 | −0,794 | −6,736 | 7,614 | 63,6% | −1,231 | 0,2274 | 183 | 0,0831 |
| Typ decyzji | `start` — Rozpoczęcie | 15 | −0,387 | 2,302 | −0,566 | −4,847 | 2,806 | 60,0% | −0,652 | 0,5251 | 48 | 0,5245 |
| Typ decyzji | `revision` — Rewizja | 13 | −0,272 | 3,124 | −1,008 | −3,169 | 7,614 | 69,2% | −0,314 | 0,7590 | 32 | 0,3757 |
| Typ decyzji | `suspension` — Wstrzymanie lub zakończenie | 5 | −1,997 | 3,005 | −1,036 | −6,736 | 0,485 | 60,0% | −1,486 | 0,2116 | 3 | 0,3125 |
| Ocena korekty | `yes` — Niekorzystna korekta | 13 | −1,035 | 2,651 | −0,514 | −6,736 | 4,279 | 61,5% | −1,408 | 0,1846 | 27 | 0,2163 |
| Ocena korekty | `no` — Grupa odniesienia | 15 | −0,387 | 2,302 | −0,566 | −4,847 | 2,806 | 60,0% | −0,652 | 0,5251 | 48 | 0,5245 |
| Ocena korekty | `unknown` — Kierunek nieustalony | 5 | −0,013 | 4,356 | −1,050 | −2,824 | 7,614 | 80,0% | −0,007 | 0,9949 | 5 | 0,6250 |

Test t Studenta jest dwustronnym testem jednej średniej względem zera (stopnie swobody N−1). W oznacza mniejszą z sum rang dodatnich i ujemnych w dwustronnym teście znakowanych rang Wilcoxona. Wartości p wyznaczono z dokładnego rozkładu W. W próbie nie było zerowych CAR ani remisów rang wartości bezwzględnych. Test Wilcoxona zakłada symetrię rozkładu wokół położenia testowanego względem zera. Wartości p mają charakter opisowy i nie są skorygowane z tytułu wielokrotnych porównań.

Przekroje według typu decyzji i kierunku korekty obejmują te same zdarzenia. W tej próbie grupa `no` pokrywa się z grupą `start`. W `car_results.csv` dostępne jest wyłącznie okno [−1,+1]. Oba warianty dnia 0 mają te same daty i CAR.

Źródło danych: `processed/event_study/car_results.csv` i zatwierdzony rejestr `metadata/espi_review.csv`.
