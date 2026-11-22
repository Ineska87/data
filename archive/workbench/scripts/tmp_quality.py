import pandas as pd

df = pd.read_parquet(r'C:\Users\izabe\OneDrive - SGH\magisterka\data\processed\espi_master.parquet')
today = pd.Timestamp('2026-06-25')

# 1. daty przyszle (po dacie scrapowania)
future = df[df['data_pub'] > today][['ticker','numer','data_str','data_pub','tytul']]
print(f'Daty przyszle (po 2026-06-25): {len(future)}')
if len(future):
    print(future[['ticker','data_str','tytul']].to_string())

print()

# 2. 14 rekordow DD-MM-YYYY — ktory ticker?
import re
mask = df['data_str'].apply(lambda s: bool(re.match(r'\d{2}-\d{2}-\d{4}$', s)))
print(f'Rekordy DD-MM-YYYY ({mask.sum()}):')
print(df[mask][['ticker','data_str','tytul']].head(5).to_string())
