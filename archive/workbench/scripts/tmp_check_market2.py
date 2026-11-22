import pandas as pd

# istniejacy plik zbiorczy
df = pd.read_parquet(r'C:\Users\izabe\OneDrive - SGH\magisterka\data\raw\market_data\market_data_all.parquet')
print("Tickery w market_data_all:", sorted(df['Ticker'].unique()))
print("Zakres:", df['Date'].min().date(), "–", df['Date'].max().date())
print("Volume=0 rows:", (df['Volume'] == 0).sum())
print()

# sprawdz zakres w plikach CSV
import os
DATA = r'C:\Users\izabe\OneDrive - SGH\magisterka\data\raw\market_data'
for fname in sorted(os.listdir(DATA)):
    if not fname.endswith('.csv') or fname.startswith('market'):
        continue
    path = os.path.join(DATA, fname)
    # spółki mają Date, indeksy mają Data
    try:
        tmp = pd.read_csv(path, nrows=2)
        date_col = 'Date' if 'Date' in tmp.columns else 'Data'
        tmp = pd.read_csv(path, usecols=[date_col], parse_dates=[date_col])
        col = tmp.columns[0]
        print(f"  {fname:<22s}  {tmp[col].min().date()} – {tmp[col].max().date()}  ({len(tmp)} wierszy)")
    except Exception as e:
        print(f"  {fname}: BLAD {e}")
