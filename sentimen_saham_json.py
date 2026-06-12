import yfinance as yf
import pandas as pd
import os
import time

tickers = ['GOOGL', 'NVDA', 'VZ', 'TSLA', 'AAPL']

# dictionary keyword for filter news
company_keywords = {
    'GOOGL': ['google', 'alphabet', 'googl'],
    'NVDA': ['nvidia', 'nvda'],
    'VZ': ['verizon', 'vz'],
    'TSLA': ['tesla', 'tsla'],
    'AAPL': ['apple', 'aapl']
}

data_berita = []

print("Mulai narik berita...\n")

# --- EXTRACT & TRANSFORM FUNCTION ---
for ticker in tickers:
    print(f"Lagi proses berita untuk saham: {ticker}")
    saham = yf.Ticker(ticker)
    berita_list = saham.news
    
    # get relevant keyword for the company
    keywords = company_keywords.get(ticker, [ticker.lower()])
    
    for berita in berita_list:
        content = berita.get('content', {})
        judul = content.get('title', '')
        ringkasan = content.get('summary', '')
        tanggal = content.get('pubDate', '')
        
        teks_analisis = f"{judul}. {ringkasan}"
        
        # FILTER: make sure the keyword in the title or summary
        if not any(kw in teks_analisis.lower() for kw in keywords):
            continue # skip this news
            
        data_berita.append({
            'Ticker': ticker,
            'pubDate': tanggal,
            'title': judul
        })

df_berita = pd.DataFrame(data_berita)
df_berita['pubDate'] = pd.to_datetime(df_berita['pubDate']).dt.date

print(f"Jeda 5 detik biar ga kena rate limit Yahoo Finance...")
time.sleep(5)

# --- LOAD FUNCTION ---
json_file = 'data_sentimen.json'
print(f"\nMulai siap-siap kirim data ke {json_file}...")

if os.path.exists(json_file):
    try:
        existing_df = pd.read_json(json_file)
        # Filter existing columns to match the new schema in case the old JSON had extra columns
        if not existing_df.empty:
            existing_df = existing_df.rename(columns={'Tanggal': 'pubDate', 'Judul_Berita': 'title'})
            existing_df = existing_df[['Ticker', 'pubDate', 'title']]
        df_berita = pd.concat([existing_df, df_berita], ignore_index=True)
    except Exception as e:
        print(f"Gagal membaca file JSON lama: {e}. Membuat file baru.")

# Convert dates to string so they serialize cleanly
df_berita['pubDate'] = df_berita['pubDate'].astype(str)

df_berita.to_json(
    json_file, 
    orient='records', 
    indent=4
)

print(f"\n--- DATA SUKSES MENDARAT DI {json_file}! ---")
