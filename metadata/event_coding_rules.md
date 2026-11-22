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

Obecne wpisy obejmują udokumentowany pilotaż Olefin III. Katalog i wynik
pilotażowy nie stanowią kompletnej próby sześciu emitentów.
