# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
# pyrefly: ignore [missing-import]
import pandas_gbq
# pyrefly: ignore [missing-import]
import plotly.express as px
# pyrefly: ignore [missing-import]
import plotly.graph_objects as go
from datetime import timedelta
import base64
import json
import time
# pyrefly: ignore [missing-import]
from google.oauth2 import service_account
# pyrefly: ignore [missing-import]
from google import genai


# --- 1. SETUP KUNCI GCP (JURUS ULTIMATE) ---
if "GCP_JSON" in st.secrets:
    # Ambil teks JSON mentah dari Secrets dan jadikan dictionary Python
    gcp_secrets = json.loads(st.secrets["GCP_JSON"])
    creds = service_account.Credentials.from_service_account_info(gcp_secrets)
else:
    # Kalau di lokal, baca dari file biasa
    creds = service_account.Credentials.from_service_account_file("kunci-gcp.json")

# --- 2. SETUP GEMINI CLIENT ---
if "GEMINI_API_KEY" in st.secrets:
    gemini_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key Gemini tidak ditemukan di Secrets!")

# --- 3. KONFIGURASI HALAMAN & CSS INJECTION ---
st.set_page_config(page_title="Dashboard Saham AI", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 4. FUNGSI NARIK DATA ---
# PERHATIAN: Ganti pakai Project ID GCP lo yang asli
id_project_gcp = 'skripsi-pipeline-saham' 

@st.cache_data(ttl=3600) # Cache kedaluwarsa tiap 1 jam agar data fresh
def load_sentimen():
    # Gunakan DISTINCT agar berita dengan judul dan tanggal yang sama tidak muncul ganda di visualisasi
    query = f"SELECT DISTINCT * FROM `{id_project_gcp}.data_saham.tabel_sentimen` ORDER BY Tanggal DESC"
    # KRUSIAL: Masukkan variabel 'creds' ke dalam parameter credentials=
    return pandas_gbq.read_gbq(query, project_id=id_project_gcp, credentials=creds)

@st.cache_data(ttl=3600)
def load_harga():
    query = f"SELECT * FROM `{id_project_gcp}.data_saham.tabel_harga` ORDER BY Date DESC"
# KRUSIAL: Masukkan variabel 'creds' ke dalam parameter credentials=
    return pandas_gbq.read_gbq(query, project_id=id_project_gcp, credentials=creds)

with st.spinner('Menghubungkan ke Google Cloud & AI...'):
    df_berita = load_sentimen()
    df_harga = load_harga()

# Konversi Format Tanggal
df_harga['Date'] = pd.to_datetime(df_harga['Date']).dt.date
df_berita['Tanggal'] = pd.to_datetime(df_berita['Tanggal']).dt.date

# Hapus duplikat data harga untuk mencegah duplikasi (bar chart menumpuk/sum)
df_harga = df_harga.drop_duplicates(subset=['Date', 'Ticker'])

# --- 5. SIDEBAR FILTER AREA ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3126/3126489.png", width=80)
    st.title("⚙️ Panel Kontrol")
    
    
    with open("assets/icons/pilih-saham.png", "rb") as image_file:
        icon_saham = base64.b64encode(image_file.read()).decode()
    
    st.markdown(f'<div style="display: flex; align-items: center; margin-bottom: 5px;"><img src="data:image/png;base64,{icon_saham}" width="28" style="margin-right: 10px;"><b>Pilih Saham:</b></div>', unsafe_allow_html=True)
    pilih_saham = st.selectbox("Pilih Saham", ['GOOGL', 'NVDA', 'VZ', 'TSLA', 'AAPL'], label_visibility="collapsed")
    
    # Ambil batas tanggal dari data harga
    min_date = df_harga['Date'].min()
    max_date = df_harga['Date'].max()
    
    # Set default ke 1 bulan terakhir (30 hari)
    default_start_date = max(min_date, max_date - timedelta(days=60))
    
    with open("assets/icons/rentang-tanggal.png", "rb") as image_file:
        icon_tanggal = base64.b64encode(image_file.read()).decode()
        
    st.markdown(f'<div style="display: flex; align-items: center; margin-bottom: 5px;"><img src="data:image/png;base64,{icon_tanggal}" width="28" style="margin-right: 10px;"><b>Rentang Waktu:</b></div>', unsafe_allow_html=True)
    
    rentang_tanggal = st.date_input(
        "Rentang Waktu",
        value=(default_start_date, max_date),
        label_visibility="collapsed"
    )
    
    # Tambahkan ruang kosong agar kalender tidak terpotong atau lompat ke atas
    st.markdown("<div style='height: 380px;'></div>", unsafe_allow_html=True)

# Validasi jika user belum milih rentang waktu lengkap (start & end)
if len(rentang_tanggal) == 2:
    start_date, end_date = rentang_tanggal
else:
    start_date, end_date = rentang_tanggal[0], rentang_tanggal[0]

# Saring data sesuai pilihan ticker & tanggal
df_h_filter = df_harga[(df_harga['Ticker'] == pilih_saham) & 
                       (df_harga['Date'] >= start_date) & 
                       (df_harga['Date'] <= end_date)].sort_values('Date').copy()

df_b_filter = df_berita[(df_berita['Ticker'] == pilih_saham) & 
                        (df_berita['Tanggal'] >= start_date) & 
                        (df_berita['Tanggal'] <= end_date)].copy()

# Kalkulasi Moving Average (MA) 7 Hari untuk DSS
if not df_h_filter.empty:
    df_h_filter['MA_7'] = df_h_filter['Close'].rolling(window=7).mean()

# --- 6. FUNGSI AI SUMMARY ---
@st.cache_data(ttl=3600)
def dapatkan_ringkasan_gemini(nama_saham, df_berita):
    if df_berita.empty:
        return "Tidak ada berita untuk dianalisis saat ini."
    
    kumpulan_berita = "\n".join([f"- {row['Judul_Berita']}" for _, row in df_berita.head(10).iterrows()])
    
    prompt = f"""
    Kamu adalah seorang analis saham profesional. Berdasarkan berita-berita terbaru mengenai saham {nama_saham} berikut ini:
    
    {kumpulan_berita}
    
    Tolong berikan ringkasan eksekutif (maksimal 3 kalimat pendek) mengenai bagaimana sentimen pasar terhadap saham {nama_saham} saat ini berdasarkan berita di atas. 
    Gunakan bahasa Indonesia yang profesional namun mudah dipahami.
    """
    
    # Mekanisme Auto-Retry (Maksimal 3 kali percobaan)
    maksimal_coba = 3
    for percobaan in range(maksimal_coba):
        try:
            response = gemini_client.models.generate_content(
                model="gemini-3.1-flash-lite", 
                contents=prompt
            )
            return response.text
        except Exception as e:
            error_msg = str(e).lower()
            # Kalau error-nya karena server sibuk (503) atau quota habis (429)
            if "503" in error_msg or "429" in error_msg or "demand" in error_msg:
                if percobaan < maksimal_coba - 1:
                    time.sleep(2) # Tunggu 2 detik sebelum nyoba lagi
                    continue # Looping nyoba tembak API lagi
            
            # Kalau gagal terus sampai 3 kali, atau errornya beda
            return f"Sistem AI sedang sibuk. Mohon coba lagi nanti. (Error log: {e})"

# --- 7. HEADER & KPI SCORECARD ---
with open("assets/icons/analisis-saham.png", "rb") as image_file:
    icon_analisis = base64.b64encode(image_file.read()).decode()
st.title(f"![icon](data:image/png;base64,{icon_analisis}) Analisis Saham: {pilih_saham}")
st.markdown("*Analisis Prediktif & Sentimen Berita Menggunakan Natural Language Processing (NLP)*")

# Kalkulasi KPI
if not df_h_filter.empty and len(df_h_filter) >= 2:
    harga_terakhir = df_h_filter.iloc[-1]['Close']
    harga_kemarin = df_h_filter.iloc[-2]['Close']
    selisih = harga_terakhir - harga_kemarin
    persen = (selisih / harga_kemarin) * 100
else:
    harga_terakhir, selisih, persen = 0, 0, 0

sentimen_mayoritas = df_b_filter['Sentimen'].mode()[0] if not df_b_filter.empty else "Belum Ada Berita"
rata_skor_nlp = df_b_filter['Skor_Compound'].mean() if not df_b_filter.empty else 0
total_berita = len(df_b_filter)

# Warna metrik sentimen NLP
if rata_skor_nlp > 0.05:
    indikator_nlp = "Positif 🟢"
elif rata_skor_nlp < -0.05:
    indikator_nlp = "Negatif 🔴"
else:
    indikator_nlp = "Netral ⚪"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Harga Terakhir", f"${harga_terakhir:,.2f}", f"{selisih:,.2f} ({persen:.2f}%)")
col2.metric("Total Berita Ditarik", total_berita, "Sumber: Yahoo Finance")
col3.metric("Sentimen Mayoritas", sentimen_mayoritas)
col4.metric("Rata-rata Skor NLP", f"{rata_skor_nlp:.2f}", indikator_nlp)

st.markdown("---")

# Menambahkan Kolom AI Summary di bawah KPI
st.subheader("🤖 AI Executive Summary (Powered by Gemini)")
with st.spinner("Gemini sedang menganalisis berita..."):
    ringkasan = dapatkan_ringkasan_gemini(pilih_saham, df_b_filter)
    st.info(ringkasan)

st.markdown("---")

# --- 8. TABS LAYOUT INTERAKTIF ---
with open("assets/icons/candle-stick.png", "rb") as image_file:
    icon_candle = base64.b64encode(image_file.read()).decode()
with open("assets/icons/news.png", "rb") as image_file:
    icon_news = base64.b64encode(image_file.read()).decode()
with open("assets/icons/sentiment.png", "rb") as image_file:
    icon_sentiment = base64.b64encode(image_file.read()).decode()

tab1, tab2, tab3 = st.tabs([
    f"![icon](data:image/png;base64,{icon_candle}) Candlestick & Tren", 
    f"![icon](data:image/png;base64,{icon_news}) Analisis NLP Berita", 
    f"![icon](data:image/png;base64,{icon_sentiment}) Korelasi Harga vs Sentimen"
])

with tab1:
    st.subheader(f"Pergerakan Harga {pilih_saham} (Candlestick)")
    if not df_h_filter.empty:
        # Menggunakan Graph Objects untuk Candlestick
        fig_candle = go.Figure()
        
        # Tambah Candlestick
        fig_candle.add_trace(go.Candlestick(x=df_h_filter['Date'],
                        open=df_h_filter['Open'], high=df_h_filter['High'],
                        low=df_h_filter['Low'], close=df_h_filter['Close'],
                        name='Harga Saham'))
        
        # Tambah Garis MA-7
        fig_candle.add_trace(go.Scatter(x=df_h_filter['Date'], y=df_h_filter['MA_7'], 
                                        line=dict(color='orange', width=2), name='Moving Average (7 Hari)'))
        
        fig_candle.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark" if st.get_option("theme.base") == "dark" else "plotly_white")
        st.plotly_chart(fig_candle, width='stretch')
    else:
        st.warning("Data harga tidak tersedia untuk rentang waktu ini.")

with tab2:
    col_chart, col_data = st.columns([1, 1.5])
    
    with col_chart:
        st.subheader("Distribusi Sentimen")
        if not df_b_filter.empty:
            sentimen_count = df_b_filter['Sentimen'].value_counts().reset_index()
            sentimen_count.columns = ['Sentimen', 'Jumlah']
            color_map = {'Positif': '#00cc96', 'Negatif': '#ef553b', 'Netral': '#636efa'}
            fig_pie = px.pie(sentimen_count, values='Jumlah', names='Sentimen', hole=0.4,
                             color='Sentimen', color_discrete_map=color_map)
            st.plotly_chart(fig_pie, width='stretch')
        else:
            st.info("Tidak ada data berita di rentang waktu ini.")
            
    with col_data:
        st.subheader("Daftar Berita Terbaru")
        if not df_b_filter.empty:
            rows_list = []
            
            # Pastikan data terurut berdasarkan Tanggal dari yang terbaru
            df_b_filter_sorted = df_b_filter.sort_values(by='Tanggal', ascending=False)
            
            for tanggal, group in df_b_filter_sorted.groupby('Tanggal', sort=False):
                # Ambil data hari tersebut
                g = group[['Tanggal', 'Judul_Berita', 'Sentimen', 'Skor_Compound']].copy()
                g['Tanggal'] = g['Tanggal'].astype(str)
                rows_list.extend(g.to_dict('records'))
                
                # Hitung rata-rata skor harian
                rata_harian = group['Skor_Compound'].mean()
                if rata_harian > 0.05:
                    teks_sentimen = "🟢 SENTIMEN HARIAN POSITIF"
                elif rata_harian < -0.05:
                    teks_sentimen = "🔴 SENTIMEN HARIAN NEGATIF"
                else:
                    teks_sentimen = "⚪ SENTIMEN HARIAN NETRAL"
                
                # Buat row summary dengan teks tersebut di kolom Judul_Berita
                rows_list.append({
                    'Tanggal': '', 
                    'Judul_Berita': teks_sentimen, 
                    'Sentimen': '', 
                    'Skor_Compound': None
                })
                
            df_display = pd.DataFrame(rows_list)
            
            # Fungsi styling untuk mewarnai baris summary
            def row_style(row):
                teks = str(row['Judul_Berita'])
                if "SENTIMEN HARIAN POSITIF" in teks:
                    return ["background-color: rgba(40, 167, 69, 0.2); color: #4ade80; font-weight: bold;"] * len(row)
                elif "SENTIMEN HARIAN NEGATIF" in teks:
                    return ["background-color: rgba(220, 53, 69, 0.2); color: #f87171; font-weight: bold;"] * len(row)
                elif "SENTIMEN HARIAN NETRAL" in teks:
                    return ["background-color: rgba(108, 117, 125, 0.2); color: #9ca3af; font-weight: bold;"] * len(row)
                return [""] * len(row)
            
            # Karena tipe kolom Skor_Compound menjadi float dengan ada data None/NaN, gunakan style.format
            styled_df = df_display.style.apply(row_style, axis=1).format(na_rep="")
            
            st.dataframe(styled_df, width='stretch', hide_index=True)
        else:
            st.info("Tidak ada data berita.")

with tab3:
    st.subheader("Korelasi: Apakah Berita Positif Menaikkan Harga?")
    st.markdown("Grafik ini membandingkan rata-rata skor sentimen berita harian dengan harga penutupan saham.")
    
    if not df_h_filter.empty and not df_b_filter.empty:
        # Agregasi skor NLP rata-rata per hari
        df_b_harian = df_b_filter.groupby('Tanggal')['Skor_Compound'].mean().reset_index()
        # Gabung data harga dan sentimen
        df_korelasi = pd.merge(df_h_filter, df_b_harian, left_on='Date', right_on='Tanggal', how='left')
        
        # Bikin chart dengan dua axis (Y1 untuk harga, Y2 untuk skor NLP)
        fig_corr = go.Figure()
        
        # Axis 1: Harga Saham (Bar)
        fig_corr.add_trace(go.Bar(x=df_korelasi['Date'], y=df_korelasi['Close'], name='Harga Penutupan', opacity=0.6, marker_color='royalblue'))
        
        # Axis 2: Skor Sentimen (Line)
        fig_corr.add_trace(go.Scatter(x=df_korelasi['Date'], y=df_korelasi['Skor_Compound'], name='Skor NLP', 
                                      yaxis='y2', mode='lines+markers', line=dict(color='red', width=3)))
        
        fig_corr.update_layout(
            template="plotly_dark" if st.get_option("theme.base") == "dark" else "plotly_white",
            yaxis=dict(title='Harga Saham (USD)', side='left'),
            yaxis2=dict(title='Skor NLP (-1.0 s/d 1.0)', overlaying='y', side='right', range=[-1, 1]),
            legend=dict(x=0, y=1.1, orientation="h")
        )
        st.plotly_chart(fig_corr, width='stretch')
    else:
        st.warning("Data tidak mencukupi untuk melihat korelasi.")