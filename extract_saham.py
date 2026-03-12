import yfinance as yf
import pandas as pd
import pandas_gbq
import os

# --- SETUP KUNCI GCP ---
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "kunci-gcp.json"

tickers = ['GOOGL', 'NVDA', 'VZ']
semua_data = []

print("Mulai narik data harga historis (1 bulan terakhir)...")

# --- FASE EXTRACT ---
for ticker in tickers:
    saham = yf.Ticker(ticker)
    df_saham = saham.history(period="1mo")
    df_saham['Ticker'] = ticker
    df_saham = df_saham.reset_index()
    semua_data.append(df_saham)

final_df = pd.concat(semua_data, ignore_index=True)
# Rapihin format tanggal
final_df['Date'] = pd.to_datetime(final_df['Date']).dt.date

# --- FASE LOAD KE BIGQUERY ---
# PERHATIAN: Ganti dengan Project ID GCP lo yang asli
id_project_gcp = 'skripsi-pipeline-saham' 
tabel_tujuan = 'data_saham.tabel_harga'

print("\nMengirim data harga ke BigQuery...")
# Kita pakai if_exists='replace' biar setiap jalan, dia nge-refresh data sebulan terakhir
pandas_gbq.to_gbq(
    final_df, 
    destination_table=tabel_tujuan, 
    project_id=id_project_gcp, 
    if_exists='replace'
)

print("\n--- DATA HARGA SUKSES MENDARAT DI BIGQUERY! ---")