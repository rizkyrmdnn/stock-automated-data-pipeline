import yfinance as yf
import pandas as pd
import os

tickers = ['GOOGL', 'NVDA', 'VZ', 'TSLA', 'AAPL']
semua_data = []

print("Mulai narik data harga harian (Incremental Load)...")

# --- EXTRACT FUNCTION ---
for ticker in tickers:
    saham = yf.Ticker(ticker)
    # get data from 1d
    df_saham = saham.history(period="1d") 
    df_saham['Ticker'] = ticker
    df_saham = df_saham.reset_index()
    semua_data.append(df_saham)

final_df = pd.concat(semua_data, ignore_index=True)
# set date format
final_df['Date'] = pd.to_datetime(final_df['Date']).dt.date

# --- TRANSFORM FUNCTION ---
final_df = final_df.drop(columns=['Dividends', 'Stock Splits'], errors='ignore')

# --- LOAD TO JSON FUNCTION ---
json_file = 'data_harga.json'

print(f"\nMengirim data harga harian ke {json_file}...")

if os.path.exists(json_file):
    try:
        existing_df = pd.read_json(json_file)
        existing_df = existing_df.drop(columns=['Dividends', 'Stock Splits'], errors='ignore')
        final_df = pd.concat([existing_df, final_df], ignore_index=True)
    except Exception as e:
        print(f"Gagal membaca file JSON lama: {e}. Membuat file baru.")

# Convert dates/datetimes to string so they serialize cleanly as strings in the JSON file
final_df['Date'] = final_df['Date'].astype(str)

final_df.to_json(
    json_file, 
    orient='records', 
    indent=4
)

print(f"\n--- DATA HARIAN SUKSES DITAMBAHKAN KE {json_file}! ---")
