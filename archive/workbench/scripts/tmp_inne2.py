"""
Glębsza analiza kategorii 'inne' - grupuje wedlug wzorcow i pokazuje przyklady.
"""
import pandas as pd
import re
from collections import Counter

df = pd.read_parquet(r'C:\Users\izabe\OneDrive - SGH\magisterka\data\processed\events_master.parquet')
inne = df[df['event_type'] == 'inne'][['ticker', 'title', 'event_date']].copy()
titles = inne['title'].dropna()

# --- bigrams z tytulu (pierwsze 2 slowa) ---
def first_words(t, n=3):
    words = re.sub(r'[^\w\s]', '', t.lower()).split()
    return ' '.join(words[:n])

bigrams = titles.apply(first_words)
top_bigrams = Counter(bigrams).most_common(40)

print(f"KATEGORIA 'INNE': {len(inne)} rekordow\n")
print("Najczestsze pierwsze 3 slowa:\n")
for phrase, count in top_bigrams:
    pct = 100 * count // len(inne)
    bar = '#' * (count // 10)
    print(f"  {count:4d} ({pct:2d}%)  {phrase:<40s}  {bar}")

print("\n" + "="*70)
print("SZCZEGOLOWE GRUPY Z PRZYKLADAMI")
print("="*70)

GROUPS = [
    ("Informacja o ...",          r"^informacj[ae]\b"),
    ("Zmiana daty/terminu",       r"zmiana\s+(daty|terminu|harmonogram)"),
    ("Zmiana ratingu/rekomend.",  r"zmiana\s+(rating|ocen|rekomend)"),
    ("Zmiana strategii/planu",    r"zmiana\s+(strateg|plan\b|cel[oó]w)"),
    ("Korekta raportu/komunikatu",r"(korekta|uzupe[łl]nienie|sprostowanie)\s+(raportu|komunikatu|informacji|do\s+raportu)"),
    ("Terminy publikacji raportow",r"termin[y]?\s+(publikacji|przekazania)\s+(raport|wynik)"),
    ("Aktualizacja (inne)",       r"^aktualizacja\b"),
    ("Projekty inwestycyjne",     r"(projekt|budow[ae]|realizacj[ae]|inwestycj[ae])"),
    ("Sprzedaz (nie-MA)",         r"^sprzeda[żz]\b"),
    ("Strategia / CSR / ESG",     r"(strategia|esg\b|csr\b|zr[oó]wnowa[żz]on|odpowiedzia|spo[łl]eczn)"),
    ("Umowa dostawy energii/paliw",r"(dostaw[ay]\s+(energii|w[eę]gla|paliw|gaz)|umowa\s+sprzeda[żz]y\s+energii)"),
    ("Rating/rekomendacja analityk",r"(rekomendacj[ae]\s+do\s+akcji|zmiana\s+rekomendacj)"),
    ("Zdarzenie jednorazowe",     r"(odpis|utrata\s+warto[śs]ci|impairment|rezerw[ae])"),
    ("PKN Orlen - headline",      r"^pkn\b"),
    ("Nagrody/rankingi",          r"(nagroda|ranking|wyroznienie|certyfikat)"),
]

for label, pat in GROUPS:
    mask = titles.str.contains(pat, case=False, regex=True, na=False)
    n = mask.sum()
    if n == 0:
        continue
    examples = titles[mask].head(4).tolist()
    print(f"\n[{label}] — {n} rekordow")
    for ex in examples:
        print(f"    {ex[:95]}")

# --- catch-all: co pozostaje bez zadnego wzorca? ---
all_pats = [p for _, p in GROUPS]
combined = '|'.join(f'(?:{p})' for p in all_pats)
unmatched = titles[~titles.str.contains(combined, case=False, regex=True, na=False)]
print(f"\n\nBEZ WZORCA: {len(unmatched)} rekordow")
print("Pierwsze slowo (top 20):")
first = unmatched.str.lower().str.split().str[0]
for w, n in Counter(first).most_common(20):
    print(f"  {n:4d}  {w}")

print("\nPrzykladowe tytuly bez wzorca (losowe 15):")
sample = unmatched.sample(min(15, len(unmatched)), random_state=42)
for t in sample:
    print(f"    {t[:95]}")
