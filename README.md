# Dane pracy magisterskiej

Zakres badania i benchmark WIG określa `metadata/study_scope.json`. Katalog
`raw/` przechowuje źródła i ich metadane, a `processed/` dane przetworzone.
`raw/context/` przechowuje materiały porównawcze, w tym ESPI Bogdanki.
Niezatwierdzone eksporty scrapera trafiają do `staging/`. Plik
`metadata/espi_snapshots.json` określa, które zrzuty uwzględni potok.

## Aktualizacja indeksu ESPI

Z katalogu projektu uruchom następujące polecenia. Z katalogu `data/`
usuń prefiks `data/` w ścieżkach. Tryb `--study` używa emitentów i dat
z `metadata/study_scope.json`.

```powershell
python -B data/ir-scraper/scripts/scrape_ir_firecrawl.py --study --seed-cache
python -B data/ir-scraper/scripts/scrape_ir_firecrawl.py --study --dry-run
python -B data/ir-scraper/scripts/scrape_ir_firecrawl.py --study --max-uncached 0
```

Cache w `raw/firecrawl_cache/` przechowuje znormalizowane adresy pod
skrótem SHA-256. Zachowane odpowiedzi archiwalne można odzyskać bez API.
Podgląd pokazuje strony dostępne w cache, strony do odzyskania lokalnie
i adresy wymagające pobrania. `--verify-public` dodatkowo porównuje
wyniki z publicznym HTML emitenta tam, gdzie jest parser.

Nowe strony pobierane są z Firecrawl w standardowych formatach Markdown
i HTML, po jednym kredycie za URL. Odpowiedź jest zapisywana na dysku przed
lokalnym wydobyciem rekordów. `--max-uncached` ogranicza liczbę nowych URL-i.
Przy HTTP 429 scraper czeka zgodnie z `Retry-After` lub ponawia z rosnącym
odstępem. Gdy wynik rozliczenia jest niepewny, cache zachowuje blokadę URL-a.

Zrzuty trafiają do `staging/espi/`. Po sprawdzeniu pokrycia dopisz je do
`metadata/espi_snapshots.json`. Można zachować poprzedni zrzut jako
pierwszy wpis listy. Pole `complete_period` zapisuj po zweryfikowaniu
pełnego okresu i zastąpieniu starego zakresu przez nowy. Korekty mają
własne identyfikatory i wskazują raport, którego dotyczą. Jednostkowe
rozstrzygnięcia oparte na źródle są zapisane w
`metadata/espi_source_overrides.json`.

### Pełne treści ESPI

Skrypt `data/ir-scraper/scripts/scrape_espi_details.py --dry-run` liczy
unikalne adresy komunikatów bez zapisanej odpowiedzi. Opcje
`--fetch-only --batch` pobierają standardowe Markdown i HTML. Dziennik
przyjętych partii można podać w `--resume-batch`, aby odebrać wyniki bez
ponownego wysyłania adresów. `--parse-only --download-report-pdfs` rozpoznaje
treść lokalnie i pobiera dokumenty źródłowe dostępne wyłącznie jako PDF.

Surowe odpowiedzi Firecrawl zostają w cache. Indeks treści, źródła GPW,
załączniki i dowody kwalifikacji zapisują się w `raw/espi/detail_evidence/`.
`data/scripts/espi_investment_evidence.py --download` wyszukuje kandydatów
oraz zapisuje powiązania ze wcześniejszymi raportami i plikami PDF.
Status kandydata nie zastępuje decyzji zapisanej w `metadata/espi_review.csv`.

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
