import yfinance as yf
import pandas as pd

# 1. Daftar saham yang mau ditarik (bisa ditambahin nanti)
tickers = ['GOOGL', 'NVDA', 'VZ']

# Bikin list kosong buat nampung data
semua_data = []

# 2. Proses Extract (Narik data satu-satu)
for ticker in tickers:
    print(f"Lagi narik data historis: {ticker}...")
    
    # Ambil data dari Yahoo Finance (kita ambil data 1 bulan terakhir dulu buat test)
    saham = yf.Ticker(ticker)
    df_saham = saham.history(period="1mo")
    
    # Tambahin kolom 'Ticker' biar kita tau ini data saham apa pas digabung
    df_saham['Ticker'] = ticker
    
    # Reset index biar kolom 'Date' jadi kolom biasa, bukan index
    df_saham = df_saham.reset_index()
    
    # Masukin ke list
    semua_data.append(df_saham)

# 3. Gabungin semua data jadi satu tabel rapi
final_df = pd.concat(semua_data, ignore_index=True)

# Format ulang kolom Date biar lebih rapi (hilangin zona waktu)
final_df['Date'] = pd.to_datetime(final_df['Date']).dt.date

print("\n--- PENARIKAN DATA SUKSES ---")
print(final_df[['Date', 'Ticker', 'Open', 'Close', 'Volume']].head())

# 4. Simpan ke CSV dulu sebagai bukti lokal
final_df.to_csv("data_saham_mentah.csv", index=False)
print("\nData berhasil disimpen ke 'data_saham_mentah.csv'")