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
    try:
        saham = yf.Ticker(ticker)
        berita_list = saham.news or []
    except Exception as e:
        print(f"  Gagal mengambil berita untuk {ticker}: {e}")
        berita_list = []
    
    # get relevant keyword for the company
    keywords = company_keywords.get(ticker, [ticker.lower()])
    count_ticker = 0
    
    for berita in berita_list:
        if not isinstance(berita, dict):
            continue

        # Support both nested 'content' structure and root-level/flat structure
        content = berita.get('content')
        if not isinstance(content, dict):
            content = berita
        
        judul = content.get('title') or berita.get('title') or ''
        ringkasan = content.get('summary') or berita.get('summary') or ''
        
        # Support both pubDate string and providerPublishTime timestamp
        tanggal_raw = content.get('pubDate') or content.get('providerPublishTime') or berita.get('providerPublishTime') or ''
        
        if isinstance(tanggal_raw, (int, float)):
            try:
                tanggal = pd.to_datetime(tanggal_raw, unit='s')
            except Exception:
                tanggal = tanggal_raw
        else:
            tanggal = tanggal_raw
        
        # Skip if title is missing
        if not judul:
            continue
        
        teks_analisis = f"{judul}. {ringkasan}".strip()
        
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
        count_ticker += 1
        
    print(f"  -> {count_ticker} berita relevan diambil untuk {ticker}.")

kolom_standar = ['Ticker', 'Tanggal', 'Judul_Berita', 'Skor_Compound', 'Sentimen']
df_berita = pd.DataFrame(data_berita, columns=kolom_standar)

# Data Quality Assurance
if df_berita.empty:
    print("\nTidak ada berita yang ditemukan atau lolos filter.")
else:
    # 1. replace empty string to NA
    df_berita.replace('', pd.NA, inplace=True)
    # 2. drop missing value
    df_berita = df_berita.dropna(subset=['Judul_Berita', 'Tanggal'])
    # 3. drop duplicate rows based on 'Judul_Berita'
    df_berita = df_berita.drop_duplicates(subset=['Judul_Berita'])
    
    if not df_berita.empty:
        df_berita['Tanggal'] = pd.to_datetime(df_berita['Tanggal']).dt.date

print(f"\nJeda 5 detik biar ga kena rate limit Yahoo Finance...")
time.sleep(5)

# --- 3. LOAD FUNCTION ---
id_project_gcp = 'skripsi-pipeline-saham' 
tabel_tujuan = 'data_saham.tabel_sentimen'

if not df_berita.empty:
    # Deduplicate against existing BigQuery data (Approach B)
    print("Memeriksa berita yang sudah ada di BigQuery untuk menghindari duplikasi...")
    try:
        # Query titles from the last 10 days to check against
        query_existing = f"""
        SELECT DISTINCT Judul_Berita 
        FROM `{id_project_gcp}.{tabel_tujuan}` 
        WHERE Tanggal >= DATE_SUB(CURRENT_DATE(), INTERVAL 10 DAY)
        """
        df_existing = pandas_gbq.read_gbq(query_existing, project_id=id_project_gcp)
        
        if not df_existing.empty:
            existing_titles = set(df_existing['Judul_Berita'].tolist())
            initial_count = len(df_berita)
            df_berita = df_berita[~df_berita['Judul_Berita'].isin(existing_titles)]
            new_count = len(df_berita)
            print(f"Ditemukan {new_count} berita baru dari total {initial_count} berita yang ditarik.")
        else:
            print("Tabel BigQuery kosong atau tidak ada data dalam 10 hari terakhir.")
    except Exception as e:
        print(f"Gagal memeriksa duplikasi ke BigQuery (mungkin tabel belum ada atau kosong): {e}")

# function to throw dataframe to cloud
if not df_berita.empty:
    print("\nMulai siap-siap kirim data ke Google Cloud BigQuery...")
    pandas_gbq.to_gbq(
        df_berita, 
        destination_table=tabel_tujuan, 
        project_id=id_project_gcp, 
        if_exists='append'
    )
    print("\n--- YEAAY! DATA SUKSES MENDARAT DI BIGQUERY! ---")
else:
    print("\n--- TIDAK ADA DATA BARU UNTUK DIKIRIM KE BIGQUERY ---")
