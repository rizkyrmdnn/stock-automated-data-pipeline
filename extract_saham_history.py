import yfinance as yf
import pandas as pd
import pandas_gbq
import os

# INI BUAT NARIK DATA 5 TAHUN TERAKIR - JALANIN SEKALI AJA.
# --- SETUP KUNCI GCP ---
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "kunci-gcp.json"

tickers = ['GOOGL', 'NVDA', 'VZ', 'TSLA', 'AAPL']
semua_data = []

print("Mulai narik data harga historis (5 TAHUN TERAKHIR)...")

# --- FASE EXTRACT ---
for ticker in tickers:
    saham = yf.Ticker(ticker)
    # Ambil data 5 tahun
    df_saham = saham.history(period="5y")
    df_saham['Ticker'] = ticker
    df_saham = df_saham.reset_index()
    semua_data.append(df_saham)

final_df = pd.concat(semua_data, ignore_index=True)
# Rapihin format tanggal
final_df['Date'] = pd.to_datetime(final_df['Date']).dt.date

# --- FASE LOAD KE BIGQUERY ---
id_project_gcp = 'skripsi-pipeline-saham' 
tabel_tujuan = 'data_saham.tabel_harga'

print("\nMengirim data historis 5 tahun ke BigQuery (Mungkin butuh waktu agak lama)...")
# Gunakan 'replace' HANYA untuk inisialisasi awal ini, agar tabel ter-reset dengan data 5 tahun
pandas_gbq.to_gbq(
    final_df, 
    destination_table=tabel_tujuan, 
    project_id=id_project_gcp, 
    if_exists='replace'
)

print("\n--- DATA HISTORIS 5 TAHUN SUKSES MENDARAT DI BIGQUERY! ---")