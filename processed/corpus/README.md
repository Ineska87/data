# Korpus wypowiedzi zarządów o inwestycjach

`build_corpus_sentiment.py` tworzy `report_manifest.csv`. Identyfikator `report_id`
oznacza wydanie raportu okresowego, a `document_id` identyfikuje konkretny dokument
z jego pakietu. Manifest śledzi plik źródłowy, tekst, część archiwum i wynik
ekstrakcji. Dokumenty JSW mają status kandydata do walidacji.

`document_type` wskazuje sprawozdanie zarządu (`management_report`),
komentarz zarządu (`management_commentary`), tekst objaśniający z not
finansowych (`financial_notes`), pełne sprawozdanie finansowe
(`financial_statement`), prezentację (`presentation`), list prezesa
(`ceo_letter`) lub raport zintegrowany (`integrated_report`). Pola
`is_narrative` i `is_supplementary` określają rolę tekstu przy doborze
raportu odniesienia. Uzupełniające materiały z niezależną dystrybucją
wymagają własnego potwierdzenia daty, a ich identyfikatory pozostają osobne.
Gdy `publication_precision` wynosi `date`, dokument może poprzedzać
komunikat ESPI tylko wtedy, gdy jego data jest wcześniejsza od daty zdarzenia.
Sufiks `_ocr_pl` w `text_basis` wskazuje tekst materiału dodatkowego
odczytany przez zainstalowany polski OCR Windows. Cytaty z takiego tekstu
sprawdzaj w źródłowym PDF-ie.

1. W `data/metadata/report_publications.csv` zapisz potwierdzoną datę
   udostępnienia raportu wraz z adresem źródła. Pole `published_at` wypełniaj
   tylko dla potwierdzonej godziny, podając ISO 8601 ze strefą czasową.
   Manifest wyświetla tę godzinę w czasie warszawskim w polu
   `publication_time`. Gdy plik ma własną datę lub gdy dotyczy go inna
   publikacja, zapisz potwierdzenie pod `document_id` w
   `data/metadata/report_document_publications.csv`. Przykładem jest raport
   zintegrowany udostępniony po raporcie rocznym ESPI. Rok i okres
   sprawozdawczy same nie określają daty udostępnienia.
2. W `data/metadata/investment_passages.csv` wskaż zweryfikowany fragment
   wypowiedzi o planie inwestycyjnym. Podaj ten sam `project_id` co w rejestrze
   zdarzeń, stronę lub lokalizator w źródle oraz zakres znaków w tekście z
   manifestu. Indeksy zaczynają się od zera i nie obejmują znaku końcowego.
   Wersję tekstu należy zachować po zapisaniu odwołań.
3. W `data/metadata/sentiment_validation_pool.csv` wskaż niezależne fragmenty
   w podzbiorach `calibration` i `holdout`. Z pulą co najmniej 100 fragmentów
   z różnych spółek i lat skrypt losuje 100 pozycji deterministycznie.
   Raporty holdout muszą być odrębne od kalibracji i od raportów użytych w
   rejestrze fragmentów inwestycyjnych. W plikach `*_blind.csv` zapisz
   oceny `negative`, `neutral` albo `positive`. Pliki do oceny zawierają
   teksty bez wyników słownika.

Przy pustym rejestrze ręcznym potok tworzy pulę roboczą
`processed/sentiment/validation/validation_pool_auto.csv`. Fragmenty wybiera
na podstawie języka inwestycyjnego, niezależnie od punktacji słownika, z
pominięciem raportów przypisanych zdarzeniom. Pula obejmuje JSW, a podział
na kalibrację i próbę testową jest rozłączny na poziomie raportu.

Próg neutralności jest dobierany na danych kalibracyjnych według średniej F1
dla trzech klas. Raport walidacji podaje liczebność, precyzję, czułość i F1 po
uzupełnieniu 100 niezależnych ocen. Słownik roboczy w
`data/metadata/investment_tone_lexicon.json` korzysta z dopasowania fraz od
najdłuższej i uwzględnia dwuwyrazowe okno negacji w obrębie zdania. Wynik to
różnica liczby dopasowań dodatnich i ujemnych na 100 słów. Przy braku
adnotacji status pozostaje `pending_review`.

Zachowane pliki `manifest.csv` i `texts/` dokumentują starszą ekstrakcję.
Archiwa roczne TAURONU zawierają dokumenty XHTML. Skrypt odczytuje właściwy
raport zarządu bez zapisywania plików z archiwum. Trzy raporty kwartalne ORLENU
użyte w próbie pilotażowej są odczytywane bezpośrednio z pobranych pakietów ZIP.
