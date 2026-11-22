"""
Dodaje kolumne event_type do events_master na podstawie slow kluczowych w tytule.
Wejscie:  data/processed/events_master.parquet
Wyjscie:  data/processed/events_master.parquet / .csv (nadpisuje)

Uwagi (audyt 2026-07):
  - M&A: reguły obejmują „przejęcie”, „wezwanie”, „kontroli nad”, „połączenie”,
    „koncentracja” oraz kontekst LOTOS / ENERGA / PGNiG przy sygnałach transakcyjnych.
  - Insider „Nabycie akcji Spółki przez [osobę]” → akcjonariat (nie M&A).
"""

from pathlib import Path
import re
import pandas as pd

BASE    = Path(__file__).parent.parent
IN_FILE = BASE / "processed" / "events_master.parquet"
OUT_DIR = BASE / "processed"

df = pd.read_parquet(IN_FILE)

# ---------------------------------------------------------------------------
# Reguly kategoryzacji (stosowane w kolejnosci — pierwszy dopasowany wygrywa)
# ---------------------------------------------------------------------------
RULES = [
    ("wyniki_finansowe", [
        r"wyniki?\s+finansow",
        r"wyniki?\s+za\s+(I|II|III|IV|Q[1-4]|\d)",
        r"szacunk(i|owe|owy)\s+wynik",
        r"wst[eę]pn\w+\s+wynik",
        r"skonsolidowane\s+wyniki?",
        r"jednostkowe\s+wyniki?",
        r"wynik\s+(netto|operacyjny|EBITDA)",
        r"raport\s+(roczny|p[oó][łl]roczny|kwartalny)",
        r"sprawozdanie\s+finansow",
        r"przychod\w+\s+(i\s+)?(koszt|wynik|zysk)",
        r"wyniki?\s+(grupy|skonsolidow)",
        r"przychody\s+(ze\s+sprzeda|grupy|skonsolidow)",
        r"^przychody\b",
        r"szacunek\w*\s+wybranych\s+danych",
        r"szacunki\s+wybranych\s+danych",
        r"dane\s+finansowe\b",
        r"wyniki\s+test[oó]w\s+na\s+utrat",
        r"odpis\w*\s+aktualizuj[aą]c",
    ]),
    ("dywidenda", [
        r"dywidend",
        r"wyp[łl]at[ae]\s+dywidend",
        r"zaliczk[ae]\s+na\s+dywidend",
        r"polityk[ae]\s+dywidend",
    ]),
    ("prognoza", [
        r"prognoz[ae]",
        r"korekta\s+prognozy",
        r"aktualizacja\s+prognozy",
        r"szacunk(i|owe)\s+(przychod|wynik|zysk|EBIT)",
        r"guidance",
        r"wst[eę]pn\w+\s+szacunk",
    ]),
    # zmiany_personalne — stemmy bez końcówek fleksyjnych (j.polski: powołanie/powołania/powołaniu)
    ("zmiany_personalne", [
        r"powo[łl]ani",           # powołanie, powołania, powołaniu, powołaniem
        r"odwo[łl]ani",           # odwołanie, odwołania, odwołaniu
        r"rezygnacj",             # rezygnacja, rezygnacji, rezygnację
        r"zmian[ay]\s+w\s+(sk[łl]adzie\s+)?(zarz[aą]d|rady?\s+nadzorcz)",
        r"zmiany\s+w\s+radzie",
        r"zmian[ay]\s+w\s+sk[łl]adzie",
        r"nowy\s+(prezes|wiceprezes|cz[łl]onek\s+zarz[aą]d)",
        r"wybor\s+cz[łl]onk[oó]w?\s+rady?\s+nadzorcz",
        r"zarz[aą]d\s+sp[oó][łl]k",
        r"sk[łl]ad\s+(zarz[aą]d|rady\s+nadzorcz)",
    ]),
    # Insider / managers' dealings — PRZED M&A (inaczej "Nabycie akcji Spółki przez Wiceprezesa" → M&A)
    ("akcjonariat", [
        r"nabycie\s+akcji\s+sp[oó][łl]ki\s+przez",
        r"zbycie\s+akcji\s+sp[oó][łl]ki\s+przez",
        r"transakcje\s+na\s+(akcjach|instrumentach)",
        r"transakcje\s+os[oó]b\s+(maj[aą]cych|pe[łl]ni[aą]cych|blisk)",
        r"osoba\s+pe[łl]ni[aą]ca\s+obowi[aą]zki\s+zarz[aą]dz",
        r"informacja\s+o\s+transakcjach\s+os[oó]b",
    ]),
    ("transakcje_MA", [
        # klasyczne
        r"nabycie\s+(pakietu|wi[eę]kszo[śs]ciowego|kontrolnego|projekt)",
        r"nabycie\s+przez\b",                        # "Nabycie przez JSW … pakietu"
        r"nabycie\s+(akcji|udzia[łl][oó]w|aktyw[oó]w|sp[oó][łl]k)",
        r"nabycie\s+kolejnych\s+sp",                 # spółek / spółki projektowych
        r"nabycie\s+sp[oó][łl]ek\s+projekt",
        r"decyzj\w*\s+o\s+nabyciu",
        r"na\s+nabycie\b",                           # "zgoda … na nabycie sieci stacji"
        r"zbycie\s+(akcji|udzia[łl][oó]w|aktyw[oó]w|sp[oó][łl]k)",
        r"przej[eę]ci",                              # przejęcie / przejęciem / przejęciu
        # wezwanie = tender offer (NIE dematerializacja "wezwanie do złożenia dokumentów akcji")
        r"wezwani\w*\s+do\s+zapisywania",
        r"wezwani\w*\s+do\s+sk[łl]adania\s+zapis",
        r"og[łl]oszeni\w*\s+wezwani",
        r"tre[śs]ci\s+wezwani",
        r"zmiana\s+ceny\s+w\s+wezwani",
        r"warunku\s+zastrze[żz]onego\s+w\s+wezwani",
        r"w\s+ramach\s+wezwani",
        r"kontroli\s+(kapita[łl]owej\s+)?nad",
        r"kontrol[eę]\s+(kapita[łl]ow[aąe]\s+)?nad",
        r"po[łl][aą]czeni",                          # połączenie / plan połączenia
        r"fuzj",
        r"akwizycj",
        r"koncentrac",                               # wniosek koncentracyjny
        r"sprzeda[żz]\s+(akcji|udzia[łl][oó]w|aktyw[oó]w|sp[oó][łl]k)",
        r"umowa\s+(sprzeda[żz]y|nabycia|zbycia)\s+(sp[oó][łl]k|aktyw|akcji|udzia)",
        r"transakcja\s+(nabycia|zbycia|kupna|sprzeda[żz]|po[łl][aą]czeni)",
        r"plan(?:u|em)?\s+po[łl][aą]czeni",
        r"projekt(?:u)?\s+planu\s+po[łl][aą]czeni",
        r"\bdemerger\b|\bspin[- ]?off\b",
        r"w[łl]a[śs]cicielem\s+ok\.\s+\d",           # "został właścicielem ok. 80% akcji"
        r"poszukiwania\s+potencjalnego\s+inwestora",
        # cele M&A + sygnał transakcyjny (nie czyste umowy handlowe z PGNiG)
        r"(?:lotos|pgnig|pgni g|energa).{0,80}(?:przej|naby|zby|po[łl][aą]cz|kontrol|wezw|transakc|akcj|udzia|koncentrac|fuzj|akwizyc|plan|w[łl]a[śs]ciciel)",
        r"(?:przej|naby|zby|po[łl][aą]cz|kontrol|wezw|transakc|koncentrac|fuzj|akwizyc|plan|w[łl]a[śs]ciciel).{0,80}(?:lotos|pgnig|pgni g|energa)",
        r"grup[ay]\s+lotos",
        r"\bLOTOS\s+S\.?A",
        r"\bENERGA\s+S\.?A",
        r"\bPGNiG\s+S\.?A",
        r"polskich\s+aktyw[oó]w\s+grupy\s+cez",
        r"ofert\w+\s+(?:niewi[aą][żz][aą]c|wi[aą][żz][aą]c).{0,40}naby",
    ]),
    ("emisja_finansowanie", [
        r"emisja\s+(akcji|obligacji|akcj)",
        r"obligacj[ae]",
        r"program\s+emisji",
        r"oferta\s+publiczna",
        r"subskrypcja",
        r"podwy[żz]szenie\s+kapita[łl][ua]",
        r"kredyt\w*\s+(bank|konsorcjaln|inwestycyjn)",
        r"umowa\s+(kredytow|finansow|po[żz]yczk)",
        r"refinansow",
        r"euroobligacj",
        r"d[łl]u[żz]n\w+\s+papier[oó]w?\s+warto[śs]ciow",
        r"rejestracja\s+(praw\s+do\s+|nowych\s+)?akcji",
        r"rejestracja\s+podwy[żz]szenia\s+kapita[łl][ua]",
        r"komunikat\s+KDPW",
        r"informacja\s+dot\.?\s+termin[oó]w?\s+oferty",
        r"aktualizacja\s+(tre[śs]ci\s+)?prospektu",
    ]),
    ("walne_zgromadzenie", [
        r"walne\s+zgromadzenie",
        r"\bWZA\b",
        r"\bNWZ\b",
        r"\bZWZ\b",
        r"zwo[łl]anie\s+(nadzwyczajnego|zwyczajnego|walnego)",
        r"uchwa[łl]\w+\s+(walnego|WZA|NWZ)",
        r"uchwa[łl]\w+\s+(Nadzwyczajnego|Zwyczajnego)",
        r"porz[aą]dek\s+obrad\s+(walnego|WZA|NWZ)",
        r"og[łl]oszenie\s+o\s+zwo[łl]aniu",
        r"wykaz\s+akcjonariuszy",
        r"przerwa\s+w\s+obradach",
        r"projekty\s+uchwa[łl]",
        r"tre[śs][ćc]\s+uchwa[łl]",
    ]),
    ("rating_rekomendacja", [
        r"rating",
        r"ocena\s+(kredytow|wiarygodno)",
        r"rekomendacj[ae]\s+(analityk|biur|domu\s+maklersk)",
        r"zmiana\s+ocen[ay]\s+kredytow",
        r"Moody|Fitch|S&P|Standard\s+&\s+Poor",
    ]),
    ("regulatory_prawne", [
        r"decyzja\s+(Prezesa\s+URE|UOKiK|KNF|Urz[eę]du|Regulato)",
        r"zgoda\s+(UOKiK|KNF|Prezesa|organu\s+antymonopolow)",
        r"postanowienie\s+s[aą]du",
        r"rejestracja\s+przez\s+s[aą]d",
        r"wyrok\s+s[aą]d",
        r"postepowanie\s+(regulacyjn|administracyjn|s[aą]dow)",
        r"\bKNF\b.*decyzj",
        r"\bUOKiK\b",
        r"zmiana\s+statut",
        r"statut\s+sp[oó][łl]k",
        r"taryf[ae]\s+(dla|zatwierdzon)",
        r"zatwierdzen\w+\s+taryf",
        r"rejestracja\s+zmian\s+(statutu|w\s+statut)",
        r"rejestracja\s+zmian\s+w\s+(KRS|rejestrze)",
        r"przyj[eę]cie\s+(jednolitego\s+tekstu|tekstu\s+jednolitego)",
        r"tekst\s+jednolity\s+statut",
    ]),
    # akcjonariat: progi, zawiadomienia (insider — reguły wyżej, przed M&A)
    ("akcjonariat", [
        r"progow[ae]\s+udzia[łl][oó]w",
        r"przekroczenie\s+prog",
        r"udzia[łl]\s+w\s+(og[oó]lnej\s+)?liczbie\s+g[łl]os",
        r"zawiadomienie\s+o\s+(nabyciu|zbyciu|przekroczeniu|zmian)",
        r"zmiana\s+udzia[łl][oó]w?\s+w\s+(og[oó]lnej\s+)?liczbie",
        r"akcjonariusz\s+(posiada|nabyw|zby)",
        r"zawiadomienie\s+akcjonariusz",
        r"^zawiadomienie\b",
        r"akcjonariusze?\s+posiadaj[aą]c",
        r"(zmniejszenie|zwi[eę]kszenie)\s+udzia[łl]u\s+w",
        r"zmiana\s+(stanu\s+)?posiadania",
    ]),
    # umowy_kontrakty: zawarcie/podpisanie kontraktów (nie-M&A)
    ("umowy_kontrakty", [
        r"zawarcie\b",           # "Zawarcie umowy/aneksu/przez Spółkę umowy..."
        r"podpisanie\b",         # "Podpisanie umowy/aneksu/listu intencyjnego"
        r"aneks\s+(do\s+umow|nr)",
        r"^umow[ay]\b",
        r"kontrakt\s+(z\s+|na\s+)",
        r"umowa\s+znacz[aą]c",
        r"umowa\s+o\s+wsp[oó][łl]prac",
        r"list\s+intencyjny",
        r"porozumienie\s+(z\s+|w\s+sprawie|o\s+)",
    ]),
]

LABEL_PL = {
    "wyniki_finansowe":   "Wyniki finansowe",
    "dywidenda":          "Dywidenda",
    "prognoza":           "Prognoza/szacunki",
    "zmiany_personalne":  "Zmiany personalne",
    "transakcje_MA":      "Transakcje M&A",
    "emisja_finansowanie":"Emisja/finansowanie",
    "walne_zgromadzenie": "Walne zgromadzenie",
    "rating_rekomendacja":"Rating/rekomendacja",
    "regulatory_prawne":  "Regulacyjne/prawne",
    "akcjonariat":        "Akcjonariat/progi",
    "umowy_kontrakty":    "Umowy/kontrakty",
    "inne":               "Inne",
}

def classify(title: str) -> str:
    t = title.lower()
    for label, patterns in RULES:
        for pat in patterns:
            if re.search(pat, t, re.IGNORECASE):
                return label
    return "inne"

df["event_type"]    = df["title"].apply(classify)
df["event_type_pl"] = df["event_type"].map(LABEL_PL)

# przenieś kolumny za has_time
cols = list(df.columns)
for col in ["event_type", "event_type_pl"]:
    if col in cols:
        cols.remove(col)
insert_after = cols.index("has_time") + 1
cols = cols[:insert_after] + ["event_type", "event_type_pl"] + cols[insert_after:]
df = df[cols]

# zapis
df.to_parquet(OUT_DIR / "events_master.parquet", index=False)
df.to_csv(OUT_DIR / "events_master.csv", index=False, encoding="utf-8-sig")

# podsumowanie
print("=" * 60)
print("KATEGORYZACJA ZDARZEN")
print("=" * 60)
counts = df["event_type"].value_counts()
total = len(df)
for cat, n in counts.items():
    label = LABEL_PL.get(cat, cat)
    bar = "#" * (n // 50)
    print(f"  {label:<28s} {n:5d}  ({100*n//total:2d}%)  {bar}")
print("-" * 60)
print(f"  Lacznie: {total}")
print()

# pokrycie per ticker
print("Pokrycie kategorii 'inne' per ticker:")
inne = df[df["event_type"] == "inne"].groupby("ticker").size()
total_per = df.groupby("ticker").size()
for ticker in sorted(total_per.index):
    n_inne = inne.get(ticker, 0)
    n_all  = total_per[ticker]
    pct = 100 * n_inne // n_all
    bar = "#" * (pct // 5)
    print(f"  {ticker:5s}  inne: {n_inne:4d}/{n_all:4d} ({pct:2d}%)  {bar}")
