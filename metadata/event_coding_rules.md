# Kodowanie komunikatów inwestycyjnych

Punktem wyjścia jest `processed/events/espi_review_queue.csv`. Wskazanie w tytule
pomaga ustalić kolejność odczytu. Nie przesądza o kwalifikacji. Każdą pozycję oceń
na podstawie treści źródłowego raportu, przed sprawdzeniem CAR.

W `metadata/espi_review.csv` dodaj jeden rekord dla identyfikatora `event_id`.
Wpisz `include`, gdy komunikat ogłasza rzeczywiste rozpoczęcie, zmianę lub
wstrzymanie inwestycji, `exclude` po wykluczeniu na podstawie źródła albo
`needs_review`, jeśli źródło lub interpretacja są niepewne. Dla decyzji uwzględnionej
podaj projekt, źródło i datę poprzedniego publicznego planu oraz uzasadnienie.
Brak wpisu oznacza `needs_review`.

Decyzje mają kody `start`, `revision` i `suspension`.
Oznacz korektę jako `yes` przy wzroście kosztów dla porównywalnego zakresu lub
opóźnieniu realizacji, także przy wstrzymaniu. Jeśli podstawa porównania jest
niepewna, użyj `unknown`. Koszty prognozowane dla kontynuacji, wykonane nakłady
i szacunek dla zmienionego zakresu zapisuj osobno. Godzinę podawaj w czasie
lokalnym GPW wyłącznie na podstawie zidentyfikowanego źródła publikacji.

## Dane porównawcze

- `old_capex_mn` i `new_capex_mn` zawierają prognozy w milionach waluty
  zapisanej w `capex_currency`. `old_capex_scope` i `new_capex_scope`
  opisują zakres każdej prognozy. Użyj `base_installation`,
  `supporting_infrastructure`, `base_and_support`, `redesigned_project`,
  `programme`, `other` albo `unknown`. Uzasadnij porównanie w
  `capex_scope_note` i podaj źródło w `comparison_source_url`.
- `old_milestone_type` i `new_milestone_type` rozróżniają koniec budowy
  (`construction_completion`), rozruch (`commissioning`), uruchomienie
  komercyjne (`commercial_operation`), inny cel (`other`) i niepewny typ
  (`unknown`). Pola `*_milestone_target` przechowują termin o precyzji
  podanej w źródle. `milestone_comparable=yes` wymaga dwóch terminów
  odnoszących się do tego samego rodzaju kamienia milowego.
- `actual_spend_mn`, `actual_spend_currency` i `actual_spend_to`
  przechowują wykonane nakłady narastająco do wskazanego dnia.
  `impairment_mn`, `impairment_currency` i `impairment_period`
  przechowują odpis dotyczący wskazanego okresu. Zapisz zakres w uzasadnieniu.
- Pola `first_public_plan_*` przechowują najwcześniejszy udokumentowany
  plan i jego zakres. Pola `previous_plan_*` identyfikują zaktualizowany
  plan odniesienia. Komunikaty z tego samego dnia zachowują odrębne
  identyfikatory. Relacja do wcześniejszego planu z tego samego dnia
  wymaga godzin ze źródeł pozwalających ustalić ścisłą kolejność.
- Wartość `adverse_revision=unknown` daje status
  `revision_subgroup=undetermined`. Zatwierdzone zdarzenie z tym statusem
  ma CAR i pozostaje poza główną próbą regresji.

Obecne wpisy obejmują udokumentowany pilotaż Olefin III. Katalog i wynik
pilotażowy nie stanowią kompletnej próby sześciu emitentów.
