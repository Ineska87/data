# Fragmenty metodologii — dane i konstrukcja zmiennych

*Język: akademicki PL. Do wklejenia do rozdziału „Dane” / „Strategia empiryczna”.*  
*Źródło kontroli jakości: audyty `AUDIT_DANYCH_2026-07-21.md`, `AUDIT_P1_2026-07-21.md`.*

Spis:

1. [Unimot — notowania `UNT.WA`](#1-unimot--notowania-untwa)
2. [Dźwignia finansowa](#2-dźwignia-finansowa)
3. [Dzień 0 w event study (godzina ESPI)](#3-dzień-0-w-event-study-godzina-espi)
4. [Stopa krótka / polityka pieniężna](#4-stopa-krótka--polityka-pieniężna)
5. [Blok scalony (opcjonalnie — jeden podrozdział)](#5-blok-scalony--opcjonalnie)

---

## 1. Unimot — notowania `UNT.WA`

### Skrót

Dzienne notowania spółek z próby oraz indeksów WIG, WIG20, WIG-energia i WIG-paliwa pochodzą z publicznych serii giełdowych (GPW). W badaniu Unimot S.A. oznaczany jest tickerem **UNT**. Kursy zamknięcia Unimot pobrano z serii Yahoo Finance **`UNT.WA`** (dostosowane o dywidendy i splity, `auto_adjust`), za okres obejmujący bufor estymacji 2018–2019 oraz okno analizy 2020–2025. Ticker Yahoo **`UNI.WA` odpowiada innej spółce (Unibep S.A.)** i nie był wykorzystywany w finalnych szacunkach. Na podstawie skorygowanych kursów obliczono logarytmiczne stopy zwrotu, parametry modelu rynkowego oraz skumulowane stopy nadzwyczajne (CAR); kapitalizację rynkową przybliżono jako iloczyn kursu zamknięcia na koniec kwartału i stałej liczby akcji (ok. 8,20 mln szt.).

### Pełny akapit

Źródłem dziennych kursów zamknięcia, wolumenu oraz indeksów referencyjnych jest zbiór notowań GPW scalony w pliku roboczym (okres 2018-01–2025-12, z buforem przed 2020 r. na potrzeby okna estymacji modelu rynkowego). Spółki energetyczno-paliwowe z próby rdzeniowej i rezerwowej identyfikowane są tickerami GPW: PKN, PGE, TPE, ENA, ZEP, JSW oraz — jako kontrast prywatny — **Unimot S.A. (UNT)**.

W przypadku Unimot ostateczna seria kursów pochodzi z Yahoo Finance pod symbolem **`UNT.WA`**, z korektą o działania korporacyjne. Zwroty dzienne zdefiniowano jako logarytmiczne stopy zmiany kursu zamknięcia w dniach z dodatnim wolumenem (sesje handlowe). Model rynkowy dla UNT szacowano względem indeksu **WIG** (wybór podyktowany wyższym dopasowaniem R² niż dla WIG-paliwa w oknie estymacji [−250, −11] dni sesyjnych przed dniem zdarzenia). Kapitalizację rynkową w panelu kwartalnym obliczono jako \(P_{i,t}\times N_i\), gdzie \(N_i\) to przybliżona liczba akcji w mln szt. (dla Unimot \(N_{\mathrm{UNT}}\approx 8{,}198\)), traktowana jako stała w próbie — proxy, a nie pełna historia emisji.

### Przypis (opcjonalny)

W wersji roboczej wystąpiła pomyłka mapowania tickera UNT na symbol Yahoo `UNI.WA` (Unibep S.A.). Błąd wykryto przy audycie spójności kapitalizacji i kursów; serię zastąpiono `UNT.WA` (Unimot), a wyniki event study i panel przeliczono. W finalnej pracy wykorzystano wyłącznie skorygowaną serię Unimot.

---

## 2. Dźwignia finansowa

### Skrót

W panelu spółka–kwartał **główną miarą dźwigni** jest stosunek **zadłużenia netto do aktywów ogółem** (\(\mathrm{lev}_{i,t}=D^{\mathrm{net}}_{i,t}/A_{i,t}\)). Zadłużenie netto zdefiniowano jako oprocentowane zobowiązania pomniejszone o środki pieniężne (w mln PLN). Alternatywna miara operacyjna \(D^{\mathrm{net}}/\mathrm{EBITDA}\) (ew. EBIT) bywa niestabilna przy ujemnym lub bliskim zeru wyniku operacyjnym i **nie stanowi zmiennej bazowej** w regresjach; w analizie wrażliwości stosowano także wersję \(\mathrm{lev}\) poddaną winsoryzacji na poziomie 1. i 99. percentyla w całej próbie.

### Pełny akapit

Zmienne bilansowe i wynikowe w panelu kwartalnym wyrażono w milionach PLN. Dla Orlen (PKN) źródłem są skonsolidowane pakiety liczbowe ze strony IR; dla pozostałych spółek — kwartalne tabele BiznesRadar (po konwersji z tys. PLN). **Dźwignię finansową** zdefiniowano jako:

\[
\mathrm{lev}_{i,t} \equiv \frac{D^{\mathrm{net}}_{i,t}}{A_{i,t}},
\qquad
D^{\mathrm{net}}_{i,t} = D^{\mathrm{odsetkowe}}_{i,t} - \mathrm{Cash}_{i,t},
\]

gdzie \(A_{i,t}\) to aktywa razem na koniec kwartału. Tak zdefiniowany wskaźnik jest porównywalny między spółkami i nie eksploduje przy ujemnej EBITDA.

Dla diagnostyki zachowano także dźwignię operacyjną \(\mathrm{lev}^{\mathrm{op}}_{i,t}=D^{\mathrm{net}}_{i,t}/\mathrm{EBITDA}_{i,t}\) (przy braku EBITDA: EBIT). Przy stratach operacyjnych lub EBITDA bliskiej zeru miara ta przyjmuje wartości ekstremalne i **nie jest wykorzystywana w specyfikacjach głównych**. W testach odporności stosowano \(\mathrm{lev}\) po winsoryzacji (1.–99. percentyl w przekroju panelu).

### Tabela (aneks zmiennych)

| Symbol w danych | Definicja | Rola |
|-----------------|-----------|------|
| `lev` / `lev_assets` | net_debt / total_assets | **główna** |
| `lev_assets_w` | jw., winsor 1–99% | robustness |
| `lev_op` | net_debt / EBITDA (else EBIT) | tylko opis / nie w bazie |
| `net_debt` | debt_interest_bearing − cash | mln PLN |
| `cash_ratio` | cash / total_assets | kontrola płynności |

### EN (1 zdanie)

Leverage is measured as net interest-bearing debt over total assets; an EBITDA-based ratio is reported only descriptively because it is unstable when operating earnings are near zero or negative.

---

## 3. Dzień 0 w event study (godzina ESPI)

### Skrót

Dzień 0 (efektywny dzień oddziaływania na rynek) wyznaczono na kalendarzu **sesji GPW**. Jeżeli raport ESPI zawiera godzinę publikacji **przed zamknięciem sesji** (przyjęto próg 17:00), Day 0 to ta sama sesja (lub najbliższa sesja ≥ dacie, gdy dzień niehandlowy). Jeżeli godzina to **17:00 lub później**, albo **godzina jest niedostępna**, Day 0 to **następna sesja** po dacie raportu. W próbie godzina publikacji jest w pełni dostępna m.in. dla ENA, JSW i LWB, niemal pełna dla PGE i TPE, natomiast dla **PKN i ZEP godzina w zbiorze ESPI nie występuje** — w ich przypadku reguła konserwatywnie przesuwa Day 0 na następną sesję. W analizie wrażliwości porównano tę regułę z wariantem „data kalendarzowa raportu → najbliższa sesja bez automatycznego +1 dnia” przy braku godziny; wyniki CAR pozostają silnie skorelowane w szerszych oknach, a reguła bazowa jest raportowana jako główna.

### Pełny akapit + lista reguł

Analiza zdarzeń opiera się na modelu rynkowym:

\[
R_{i,\tau}=\alpha_i+\beta_i R_{m,\tau}+\varepsilon_{i,\tau},
\]

szacowanym metodą OLS w oknie estymacji \(\tau\in[-250,-11]\) dni sesyjnych względem Day 0 (wymagane minimum 100 obserwacji). Stopa nadzwyczajna w dniu \(\tau\) to \(AR_{i,\tau}=R_{i,\tau}-(\hat\alpha_i+\hat\beta_i R_{m,\tau})\), a CAR to suma AR w zadanym oknie (m.in. [−1,+1], [−5,+5]).

**Mapowanie daty ESPI na Day 0:**

1. Znormalizowano datę publikacji raportu bieżącego (ESPI).  
2. Jeżeli dostępna jest godzina publikacji i jest ona **wcześniejsza niż 17:00**, za Day 0 przyjmuje się **pierwszy dzień sesyjny ≥ dacie** publikacji.  
3. Jeżeli godzina jest **≥ 17:00** albo **brak godziny**, datę kalendarzową przesuwa się o **+1 dzień**, a następnie mapuje na najbliższą sesję ≥ tej dacie.  
4. Benchmark rynkowy: WIG-energia (PGE, TPE, ENA), WIG-paliwa (PKN), WIG (UNT, ZEP, JSW, LWB).

Dla Orlen (PKN) i ZE PAK (ZEP) w zebranych komunikatach ESPI **nie ma pola godziny** (`has_time = 0`), stąd Day 0 jest systematycznie oparty na regule „następna sesja”. W aneksie przedstawiono test wrażliwości: wariant bez automatycznego +1 dnia przy braku godziny. Dla PKN w oknie [−5,+5] korelacja CAR między regułami na poziomie zdarzenia wynosi ok. **0,90**; różnice średnich CAR po kategoriach są zwykle rzędu ułamków punktu procentowego, choć w wybranych kategoriach (np. krótkie okno [−1,+1]) mogą być większe — dlatego regułę Day 0 opisano jawnie, a wyniki bazowe odnoszą się do wariantu konserwatywnego (przesunięcie przy braku godziny).

### Przypis

Próg 17:00 odpowiada w przybliżeniu zamknięciu sesji ciągłej na GPW z buforem na publikacje po zamknięciu; nie modeluje się tu mikrostruktury otwarcia/fixingu.

### EN (2 zdania)

Event day 0 is the first trading session on which the ESPI release can affect prices: same session if the timestamp is before 17:00, otherwise the next session. For PKN and ZEP timestamps are missing, so the baseline always uses the next session; a same-calendar-day alternative is reported in the robustness appendix.

---

## 4. Stopa krótka / polityka pieniężna

### Skrót

W panelu kwartalnym kontrolowano **stopę referencyjną NBP** (ścieżka decyzji RPP, interpolacja schodkowa do dni i agregacja do kwartału: średnia oraz poziom na koniec kwartału). Jako **proxy stopy krótkoterminowej** (`pl_short_rate_m`) przyjęto tę samą stopę referencyjną NBP, ponieważ publiczna seria miesięczna krótkoterminowej stopy rynkowej z FRED (IRSTCI01PLM156N) nie była stabilnie dostępna w momencie budowy zbioru. **Nie należy interpretować tej zmiennej jako WIBOR/WIRON**; odzwierciedla ona nastawienie polityki pieniężnej, a nie kwotowanie rynku międzybankowego. W regresjach wystarczy jedna z serii (ref. NBP), aby uniknąć współliniowości z proxy.

### Pełny akapit

Zmienne makroekonomiczne i sektorowe dołączono do panelu spółka–kwartał po agregacji z częstotliwości dziennej lub miesięcznej. Kursy EUR/PLN i USD/PLN pochodzą z tabeli A NBP; ropę Brent — z notowań futures (BZ=F); ceny energii day-ahead dla Polski — z publicznego API energy-charts (proxy, nie komercyjny feed TGE); proxy ryzyka węglowego — ETF KRBN (nie kontrakt ICE EUA).

**Stopę referencyjną NBP** zakodowano na podstawie oficjalnej ścieżki decyzji RPP (seria schodkowa od daty obowiązywania). Próba uzyskania miesięcznej stopy krótkoterminowej Polski z bazy FRED kończyła się timeoutami API; w związku z tym pole przeznaczone na stopę krótką wypełniono **proxy = stopa referencyjna NBP**. W tekście i tabelach zmienną tę opisano jako *proxy stopy polityki pieniężnej*, nie jako rynkowy WIBOR. Jeżeli w przyszłej wersji pracy dostępny będzie WIBOR 3M lub WIRON, można zastąpić proxy bez zmiany reszty pipeline’u makro.

### Tabela (aneks)

| Zmienna | Źródło | Interpretacja |
|---------|--------|----------------|
| `nbp_ref_rate_*` | ścieżka RPP / NBP | stopa referencyjna |
| `pl_short_rate_m_*` | **proxy = NBP ref** (gdy brak FRED) | nie WIBOR |
| `eurpln_*`, `usdpln_*` | NBP tabela A | FX |
| `brent_usd_*` | yfinance BZ=F | ropa |
| `eua_proxy_krbn_*` | yfinance KRBN | proxy carbon |
| `power_pl_eur_mwh_*` | energy-charts bzn=PL | day-ahead PL |

### EN (1 zdanie)

The short-rate control is a policy-rate proxy equal to the NBP reference rate when market short-rate series are unavailable; it should not be read as WIBOR.

---

## 5. Blok scalony (opcjonalnie)

*Jeśli w pracy chcesz jeden spójny podrozdział „Konstrukcja zmiennych rynkowych i panelowych”:*

Notowania dzienne (2018–2025) obejmują spółki z próby oraz indeksy WIG, WIG20, WIG-energia i WIG-paliwa. Unimot (UNT) oparto na serii Yahoo **`UNT.WA`** (nie mylić z `UNI.WA` = Unibep). Zwroty logarytmiczne policzono w dniach handlowych; CAR z modelu rynkowego (okno estymacji [−250, −11]) względem benchmarku sektorowego lub WIG. **Day 0** to sesja, na którą przypada oddziaływanie ESPI: ta sama sesja przy godzinie &lt; 17:00, w przeciwnym razie — oraz przy braku godziny (PKN, ZEP) — następna sesja. W panelu kwartalnym dźwignię zdefiniowano jako **zadłużenie netto / aktywa**; miary oparte o EBITDA zachowano jedynie opisowo. Wśród kontrolek makro wykorzystano m.in. stopę referencyjną NBP; proxy stopy krótkiej odpowiada tej stopie polityki (nie WIBOR), ceny energii day-ahead PL oraz proxy EUA (KRBN).

---

## Mapa: gdzie wkleić w strukturze pracy

| Fragment | Sugerowana sekcja |
|----------|-------------------|
| §1 Unimot + notowania | Dane → źródła rynkowe |
| §3 Day 0 + model rynkowy | Strategia empiryczna → event study |
| §2 Dźwignia | Dane → panel / zmienne kontrolne |
| §4 Stopa NBP | Dane → makro |
| §5 Blok scalony | zamiast §1–4, jeśli mało miejsca |

---

## Pliki robocze (nie cytować w tekście głównym)

| Temat | Plik |
|-------|------|
| Unimot korekta | `data/raw/market_data/UNT_PRICE_CORRECTION.md` |
| Day 0 sensitivity | `data/processed/sensitivity/day0_pkn_summary.md` |
| Codebook panel | `data/processed/panel/codebook.md` |
| Makro źródła | `data/raw/macro/sources.md` |
