import yfinance as yf
import pandas as pd
import pandas_gbq
import os

# --- SETUP KUNCI GCP ---
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "kunci-gcp.json"

tickers = ['GOOGL', 'NVDA', 'VZ', 'TSLA', 'AAPL']
semua_data = []

print("Mulai narik data harga harian (Incremental Load)...")

# --- FASE EXTRACT ---
for ticker in tickers:
    saham = yf.Ticker(ticker)
    # Ubah ke 1d untuk ambil data hari perdagangan terakhir saja
    df_saham = saham.history(period="1d") 
    df_saham['Ticker'] = ticker
    df_saham = df_saham.reset_index()
    semua_data.append(df_saham)

final_df = pd.concat(semua_data, ignore_index=True)
# Rapihin format tanggal
final_df['Date'] = pd.to_datetime(final_df['Date']).dt.date

# --- FASE LOAD KE BIGQUERY ---
id_project_gcp = 'skripsi-pipeline-saham' 
tabel_tujuan = 'data_saham.tabel_harga'

print("\nMengirim data harga harian ke BigQuery...")
# KRUSIAL: Gunakan 'append' agar data baru ditambahkan ke bawah data lama, bukan ditimpa!
pandas_gbq.to_gbq(
    final_df, 
    destination_table=tabel_tujuan, 
    project_id=id_project_gcp, 
    if_exists='append'
)

print("\n--- DATA HARIAN SUKSES DITAMBAHKAN KE BIGQUERY! ---")