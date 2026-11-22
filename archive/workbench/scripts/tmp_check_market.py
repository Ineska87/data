import pandas as pd
p = r'C:\Users\izabe\OneDrive - SGH\magisterka\data\raw\market_data\market_data_all.parquet'
df = pd.read_parquet(p)
print("Kolumny:", df.columns.tolist())
print("Shape:", df.shape)
print("Dtype:\n", df.dtypes)
print("\nPierwsze 3:")
print(df.head(3).to_string())
print("\nOstatnie 3:")
print(df.tail(3).to_string())
print("\nUnikalne tickery:", sorted(df['ticker'].unique()) if 'ticker' in df.columns else "brak kolumny ticker")
print("Zakres dat:", df.index.min() if df.index.dtype == 'datetime64[ns]' else df.iloc[:,0].min(), "–", df.index.max() if df.index.dtype == 'datetime64[ns]' else df.iloc[:,0].max())
