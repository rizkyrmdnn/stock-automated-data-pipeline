import yfinance as yf
import pandas as pd
import pandas_gbq
import os

# FUNCTION TO PULL DATA FROM 5 YEARS BACK. RUN ONCE.
# --- 1. GCP AUTHENTICATION ---
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "kunci-gcp.json"

tickers = ['GOOGL', 'NVDA', 'VZ', 'TSLA', 'AAPL']
semua_data = []

print("Mulai narik data harga historis (5 TAHUN TERAKHIR)...")

# --- 2. EXTRACT FUNCTION ---
for ticker in tickers:
    saham = yf.Ticker(ticker)
    # get data from 5 years back
    df_saham = saham.history(period="5y")
    df_saham['Ticker'] = ticker
    df_saham = df_saham.reset_index()
    semua_data.append(df_saham)

final_df = pd.concat(semua_data, ignore_index=True)
# set date format
final_df['Date'] = pd.to_datetime(final_df['Date']).dt.date

# --- 3. LOAD FUNCTION TO BIGQUERY ---
id_project_gcp = 'skripsi-pipeline-saham' 
tabel_tujuan = 'data_saham.tabel_harga'

print("\nMengirim data historis 5 tahun ke BigQuery (Mungkin butuh waktu agak lama)...")
# use 'replace' only for first time to reset the table
pandas_gbq.to_gbq(
    final_df, 
    destination_table=tabel_tujuan, 
    project_id=id_project_gcp, 
    if_exists='replace'
)

print("\n--- DATA HISTORIS 5 TAHUN SUKSES MENDARAT DI BIGQUERY! ---")