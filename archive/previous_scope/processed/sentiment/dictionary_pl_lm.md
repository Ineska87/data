# Polski słownik tonu (adaptacja stylu Loughran–McDonald)

MVP do scoringu `TONE_MGR` / `UNCERTAINTY` / `CERTAINTY` na tekstach zarządu.
Listy **nie** są automatycznym tłumaczeniem LM EN — dobór pod PL prozę IR (energia/paliwa).

Matching: normalizacja bez polskich znaków + prefix stem (min. 4 znaki).

## Positive (n=122)

akcjonariusz, ambitn, bezpiecz, buduje, dekarbon, dochod, dochodow, dochód, dynamiczn, dywidend, ebitda, efektywn, efektywno, ekspans, emisyjnosc, innowac, innowacyj, integrac, inwestowan, inwestycj, konsolidac, korzystn, korzystna, korzystne, korzystny, lider, marza, marzy, marż, marża, mocn, modernizac, mozliwosc, możliwości, możliwość, nadwyzk, nadwyzka, nadwyżk, nadwyżka, najlepsz, niezawodn, niskoweglow, odnawialn, odpornos, odporność, optymaliz, osiagn, osiąg, oszczedn, oszczednosc, oszczędn, oszczędność, oze, popraw, poprawa, poprawia, poprawie, poprawy, postep, postęp, postępu, potencjal, potencjał, powodzen, pozytywn, produktywn, przejrzyst, przekrocz, przyrost, przyspiesz, redukcja_koszt, rekord, rekordow, rentown, resilient, rosn, rosną, rosnące, rosnący, rozszerz, rozwija, rozwoj, rozwojow, rozwoju, rozwój, satysfakc, siln, solidn, stabiliz, stabiln, sukces, synerg, szansa, szanse, szansę, transformac, transparent, udane, udany, udanym, ulepsz, umacnia, umocn, wiarygodn, wiodac, wiodąc, wyplat, wypłat, wzmacnia, wzmocn, wzmocnienia, wzmocnienie, wzrosn, wzrost, zaufan, zielon, zrealizow, zrealizowani, zrealizowano, zysk, zyski, zyskown

## Negative (n=119)

anulow, awari, awaria, awarii, bankruct, ciecia, cięcia, cięcie, deficyt, deficytu, grozb, groźb, grzywn, impairment, incydent, kara, kary, karze, korupc, kryzys, kryzysow, kryzysu, likwidac, nadmiern, naduzyc, nadużyc, negatywn, niedoszacow, niekorzystn, niepowodzen, nieprawidlow, nieprawidł, niewyplacaln, niewypłacaln, obnizen, obnizk, obniżen, obniżk, odpis, odpisow, odpisy, odpisów, odstapien, odstąpien, opoznien, opoznion, opóźnien, opóźnion, pogorszen, pogorszenia, pogorszenie, pogorszy, porazk, porażk, postepowanie_sadow, pozew, pozwy, problem, problemem, problemy, przekroczenie_termin, przeszacow, recesj, restrukturyzac, rezygnac, roszczen, sankcj, skazen, skażen, slab, slaba, slabe, slaby, spadek, spadk, spadki, spadku, spor, spory, spór, stracie, strata, stratn, straty, stratę, szkod, szkoda, szkodliw, szkody, słab, słaba, słabe, słaby, trudnos, trudności, trudność, turbulenc, upadlosc, upadłość, utracie, utrata, utraty, utraty_wartosci, utratę, write-off, writeoff, wstrzyman, wyciek, wypadek, zadluzen, zadłużen, zagrozen, zagrożen, zaklocen, zakłócen, zanieczyszcz, zawiesz, zwolnien, zwolnienia

## Uncertainty (n=72)

ewentualn, fluktuac, hipotetyczn, istnieje_ryzyko, jesli, jezeli, jeśli, jeżeli, mniej_wiecej, moga, mogą, moze, moze_wplynac, mozliw, może, może_wpłynąć, możliw, nie_mozna_wykluczyc, nie_można_wykluczyć, niejasn, nieokreslon, nieokreślon, niepew, niepewnosc, niepewnosci, niepewności, niepewność, nieprzewidywaln, niezdefiniow, o_ile, oczekiwan, oczekuje, okolo, około, orientacyjn, potencjaln, potencjalnie, prawdopodobn, prognoz, prognoza, prognozy, przybliz, przyblizony, przybliż, przybliżony, risk, ryzyk, ryzyka, ryzykiem, ryzyko, ryzykown, ryzyku, scenariusz, szacowan, szacuje, szacunk, trudno_ocenic, trudno_przewidziec, uncertainty, w_razie, w_zaleznosci, wahania, warunkow, warunków, zalezne, zalezy, zależne, zależy, zmiennosc, zmiennosci, zmienności, zmienność

## Certainty (n=50)

bez_watpienia, bez_wątpienia, bezspornie, bezsporny, definitywn, gwarant, jasno, jednoznacz, niepodwazaln, niepodważaln, niewatpliwie, niewątpliwie, niezmiennie, oczywist, ostateczn, pewn, pewna, pewne, pewnie, pewnosc, pewność, pewny, potwierdz, potwierdzamy, potwierdzono, realizujemy, realizujemy_plan, rozstrzygn, stal, stala, stale, stała, stałe, stały, wedlug_planu, wyraznie, wyraźnie, zamkniety, zamknięty, zapewnia, zapewniamy, zawsze, zdecydowan, zdecydowanie, zgodnie_z_planem, zobowiaz, zobowiazanie, zobowiazujemy, zobowiąz, zobowiązujemy

## Formuły

- `TONE_MGR` = (n_pos − n_neg) / n_words
- `UNCERTAINTY` = n_unc / n_words
- `CERTAINTY` = n_cer / n_words
- `READABILITY` = 0.4 × (średnia długość zdania + % słów z ≥4 „sylabami” proxy)

Agregacja kwartalna: średnia ważona liczbą słów dokumentów w ticker×year×quarter.
AR → Q4; H1 → Q2.
