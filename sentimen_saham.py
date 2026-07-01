import yfinance as yf
import pandas as pd
import pandas_gbq
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import os
import time

# --- 1. GCP AUTHENTICATION ---
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "kunci-gcp.json"

nltk.download('vader_lexicon', quiet=True)
sia = SentimentIntensityAnalyzer()

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

print("Mulai narik dan analisis berita...\n")

# --- 2. EXTRACT & TRANSFORM FUNCTION ---
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
        
        skor = sia.polarity_scores(teks_analisis)
        skor_akhir = skor['compound']
        
        if skor_akhir >= 0.05:
            kategori = 'Positif'
        elif skor_akhir <= -0.05:
            kategori = 'Negatif'
        else:
            kategori = 'Netral'
            
        data_berita.append({
            'Ticker': ticker,
            'Tanggal': tanggal,
            'Judul_Berita': judul,
            'Skor_Compound': skor_akhir,
            'Sentimen': kategori
        })

df_berita = pd.DataFrame(data_berita)

#Data Quality Assurance
df_berita.replace('', pd.NA, inplace=True)
df_berita = df_berita.dropna(subset=['Judul_Berita', 'Tanggal'])

df_berita = df_berita.drop_duplicates(subset=['Judul_Berita'])

df_berita['Tanggal'] = pd.to_datetime(df_berita['Tanggal']).dt.date

print(f"Jeda 5 detik biar ga kena rate limit Yahoo Finance...")
time.sleep(5)

# --- 3. LOAD FUNCTION ---
print("\nMulai siap-siap kirim data ke Google Cloud BigQuery...")

id_project_gcp = 'skripsi-pipeline-saham' 
tabel_tujuan = 'data_saham.tabel_sentimen'

# function to throw dataframe to cloud
pandas_gbq.to_gbq(
    df_berita, 
    destination_table=tabel_tujuan, 
    project_id=id_project_gcp, 
    if_exists='append'
)

print("\n--- YEAAY! DATA SUKSES MENDARAT DI BIGQUERY! ---")
