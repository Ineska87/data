import pandas as pd
from collections import Counter
import re

df = pd.read_parquet(r'C:\Users\izabe\OneDrive - SGH\magisterka\data\processed\events_master.parquet')
inne = df[df['event_type'] == 'inne']['title'].dropna()

# najczestsze pierwsze slowo
first_words = inne.str.lower().str.split().str[0]
print("Najczestsze pierwsze slowo w 'inne':")
for w, n in Counter(first_words).most_common(20):
    print(f"  {n:5d}  {w}")

print()

# przykladowe tytuly dla najczestszych wzorcow
patterns = [
    r'^zawarcie',
    r'^podpisanie',
    r'^informacja',
    r'^umowa',
    r'^ogłoszenie|^ogloszenie',
    r'^komunikat',
    r'^zmiana',
    r'^realizacja',
    r'^aneks',
    r'^sprzedaz|^sprzedaż',
]
for pat in patterns:
    matches = inne[inne.str.contains(pat, case=False, regex=True)]
    if len(matches):
        print(f"Pattern '{pat}': {len(matches)} rekordow")
        for t in matches.head(3):
            print(f"    {t[:90]}")
        print()
