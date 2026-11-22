import pandas as pd

from data_paths import EVENTS

df = pd.read_parquet(EVENTS / "espi_catalog.parquet")

print("=== PODSTAWOWE INFORMACJE ===")
print(f"Liczba rekordów: {len(df):,}")
print(f"Liczba kolumn:   {df.shape[1]}")
print(f"\nKolumny: {df.columns.tolist()}")

print("\n=== LICZBA RAPORTÓW NA SPÓŁKĘ ===")
print(df['ticker'].value_counts().sort_index())

print("\n=== ZAKRES DAT ===")
print(f"Od: {df['data_str'].min()}")
print(f"Do: {df['data_str'].max()}")

print("\n=== PRZYKŁADOWE DANE ===")
print(df[['ticker', 'numer', 'data_str', 'godzina', 'tytul']].head(10))

print("\n=== ILE RAPORTÓW MA GODZINĘ? ===")
print(df['godzina'].notna().value_counts())