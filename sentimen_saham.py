import yfinance as yf
import pandas as pd
import pandas_gbq
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import os

# --- 1. SETTING KUNCI GOOGLE CLOUD ---
# Pastiin nama file json ini udah bener dan ada di folder utama (sejajar sama script ini)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "kunci-gcp.json"

nltk.download('vader_lexicon', quiet=True)
sia = SentimentIntensityAnalyzer()

tickers = ['GOOGL', 'NVDA', 'VZ', 'TSLA', 'AAPL']

# Dictionary keyword untuk memfilter berita supaya nggak salah masuk
company_keywords = {
    'GOOGL': ['google', 'alphabet', 'googl'],
    'NVDA': ['nvidia', 'nvda'],
    'VZ': ['verizon', 'vz'],
    'TSLA': ['tesla', 'tsla'],
    'AAPL': ['apple', 'aapl']
}

data_berita = []

print("Mulai narik dan analisis berita...\n")

# --- 2. FASE EXTRACT & TRANSFORM ---
for ticker in tickers:
    print(f"Lagi proses berita untuk saham: {ticker}")
    saham = yf.Ticker(ticker)
    berita_list = saham.news
    
    # Ambil keyword yang relevan buat saham ini
    keywords = company_keywords.get(ticker, [ticker.lower()])
    
    for berita in berita_list:
        content = berita.get('content', {})
        judul = content.get('title', '')
        ringkasan = content.get('summary', '')
        tanggal = content.get('pubDate', '')
        
        teks_analisis = f"{judul}. {ringkasan}"
        
        # FILTER: Pastikan ada keyword perusahaan di judul atau ringkasan
        if not any(kw in teks_analisis.lower() for kw in keywords):
            continue # Skip berita ini
        
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
df_berita['Tanggal'] = pd.to_datetime(df_berita['Tanggal']).dt.date

# --- 3. FASE LOAD (KIRIM KE BIGQUERY) ---
print("\nMulai siap-siap kirim data ke Google Cloud BigQuery...")


id_project_gcp = 'skripsi-pipeline-saham' 
tabel_tujuan = 'data_saham.tabel_sentimen'

# Perintah untuk ngelempar dataframe ke Cloud
# if_exists='append' artinya tiap script ini jalan besok-besok, datanya bakal nambah di bawahnya (nggak nimpa data lama)
# Pakai pandas_gbq langsung sesuai saran dari warning-nya
pandas_gbq.to_gbq(
    df_berita, # dataframe-nya dimasukin ke dalem kurung ini
    destination_table=tabel_tujuan, 
    project_id=id_project_gcp, 
    if_exists='append'
)

print("\n--- YEAAY! DATA SUKSES MENDARAT DI BIGQUERY! ---")
