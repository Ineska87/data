# Dane pracy magisterskiej

Zakres badania i benchmark WIG określa `metadata/study_scope.json`. Katalog
`raw/` przechowuje źródła i ich metadane, a `processed/` dane przetworzone.
`raw/context/` przechowuje materiały porównawcze, w tym ESPI Bogdanki.
Niezatwierdzone eksporty scrapera trafiają do `staging/`. Plik
`metadata/espi_snapshots.json` określa, które zrzuty uwzględni potok.

## Odtwarzanie wyników

Polecenia można wykonać z katalogu projektu. Przy uruchamianiu z innego
katalogu wskaż pełną ścieżkę do każdego skryptu. Dane domyślnie są obok
`scripts/`. Dla innej kopii danych ustaw `MAGISTERKA_DATA_ROOT` na katalog
z `raw/` i `metadata/`.

Użyj Pythona 3.13 oraz polecenia `python -m pip install -r data/requirements.txt`.
Do odczytu archiwów 7z TAURONU potrzebny jest `bsdtar` w PATH. W systemie
Windows sprawdzono systemowy `tar.exe` oparty na libarchive. Scraper korzysta
z oddzielnego `ir-scraper/requirements.txt`.

```powershell
python -B data/scripts/build_master.py
python -B data/scripts/build_events.py
python -B data/scripts/map_case_events.py
python -B data/scripts/merge_indices.py
python -B data/scripts/build_returns.py
python -B data/scripts/compute_car.py
python -B data/scripts/sensitivity_day0.py
python -B data/scripts/build_corpus_sentiment.py
python -B data/scripts/build_analytical.py
```

`build_events.py` stosuje decyzje zapisane w `metadata/espi_review.csv`.
Do weryfikacji służą kolejka `processed/events/espi_review_queue.csv`,
odrębny plik rozbieżności katalogu oraz [zasady kodowania](metadata/event_coding_rules.md).
Rejestr zawiera kwalifikujące się zdarzenia z zakończoną weryfikacją treści.
Oznaczenia w tytule ustalają kolejność przeglądu. Zatwierdzony rejestr może
przechować nieustaloną podgrupę korekty, która pozostaje poza modelem, ale
może być opisana i mieć policzony CAR.

Korpus korzysta z rejestru dat publikacji i wskazanych fragmentów. Instrukcja
doboru fragmentów i walidacji znajduje się w [opisie korpusu](processed/corpus/README.md).
`processed/analytical/investment_analysis_status.json` pokazuje pokrycie,
stan weryfikacji i dostępność modelu. `processed/market/coverage.json` opisuje
źródła, sposób liczenia zwrotów i zasięg notowań. Bieżące pliki CAR znajdują
się w `processed/event_study/`. Eksport CSV i Parquet powstają w tym samym
przebiegu.

`metadata/market_sources.json` wskazuje zapisaną migawkę skorygowanych cen
zamknięcia sześciu spółek. Manifesty w `raw/market_data/snapshots/` przechowują
adresy źródeł i sumy kontrolne. Oficjalne eksporty GPW uzupełniają serię WIG
i trzy pozostałe indeksy do 8 stycznia 2026 r. Przedział kwalifikacji
komunikatów określa `metadata/study_scope.json`.

## Materiały historyczne

`archive/previous_scope/` zawiera historyczny rękopis, wyniki i część narzędzi.
Pozostawiono historyczne wartości CAR w postaci, w jakiej istniały przed
migracją, w tym różnice między starymi wersjami CSV i Parquet.
`archive/workbench/` przechowuje wcześniejsze skrypty diagnostyczne bez roli
w obecnym potoku. Archiwalne narzędzia importujące `data_paths` można uruchomić
po dodaniu bezwzględnej ścieżki `data/scripts` do `PYTHONPATH`.
