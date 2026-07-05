import yfinance as yf
import pandas as pd
import pandas_gbq
import os

# --- GCP AUTHENTICATION ---
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "kunci-gcp.json"

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
    df_saham = df_saham.dropna(subset=['Close'])
    df_saham = df_saham.drop_duplicates(subset=['Date', 'Ticker'])
    semua_data.append(df_saham)

final_df = pd.concat(semua_data, ignore_index=True)
# set date format
final_df['Date'] = pd.to_datetime(final_df['Date']).dt.date

# --- TRANSFORM FUNCTION ---
final_df = final_df.drop(columns=['Dividends', 'Stock Splits'], errors='ignore')

# --- LOAD TO BIGQUERY FUNCTION ---
id_project_gcp = 'skripsi-pipeline-saham' 
tabel_tujuan = 'data_saham.tabel_harga'

print("\nMengirim data harga harian ke BigQuery...")
# append to existing table
pandas_gbq.to_gbq(
    final_df, 
    destination_table=tabel_tujuan, 
    project_id=id_project_gcp, 
    if_exists='append'
)

print("\n--- DATA HARIAN SUKSES DITAMBAHKAN KE BIGQUERY! ---")