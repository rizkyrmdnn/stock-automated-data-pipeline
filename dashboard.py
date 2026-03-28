import streamlit as st
import pandas as pd
import pandas_gbq
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

# --- 1. SETUP KUNCI GCP ---
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "kunci-gcp.json"

# --- 2. KONFIGURASI HALAMAN & CSS INJECTION ---
st.set_page_config(page_title="Dashboard Saham AI", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNGSI NARIK DATA ---
# PERHATIAN: Ganti pakai Project ID GCP lo yang asli
id_project_gcp = 'skripsi-pipeline-saham' 

@st.cache_data(ttl=3600) # Cache kedaluwarsa tiap 1 jam agar data fresh
def load_sentimen():
    # Gunakan DISTINCT agar berita dengan judul dan tanggal yang sama tidak muncul ganda di visualisasi
    query = f"SELECT DISTINCT * FROM `{id_project_gcp}.data_saham.tabel_sentimen` ORDER BY Tanggal DESC"
    return pandas_gbq.read_gbq(query, project_id=id_project_gcp)

@st.cache_data(ttl=3600)
def load_harga():
    query = f"SELECT * FROM `{id_project_gcp}.data_saham.tabel_harga` ORDER BY Date DESC"
    return pandas_gbq.read_gbq(query, project_id=id_project_gcp)

with st.spinner('Menghubungkan ke Google Cloud & AI...'):
    df_berita = load_sentimen()
    df_harga = load_harga()

# Konversi Format Tanggal
df_harga['Date'] = pd.to_datetime(df_harga['Date']).dt.date
df_berita['Tanggal'] = pd.to_datetime(df_berita['Tanggal']).dt.date

# --- 4. SIDEBAR FILTER AREA ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2942/2942813.png", width=80)
    st.title("⚙️ Kontrol Panel")
    st.markdown("Sistem Pendukung Keputusan")
    
    pilih_saham = st.selectbox("🎯 Pilih Saham:", ['GOOGL', 'NVDA', 'VZ', 'TSLA', 'AAPL'])
    
    # Ambil batas tanggal dari data harga
    min_date = df_harga['Date'].min()
    max_date = df_harga['Date'].max()
    
    rentang_tanggal = st.date_input(
        "📅 Rentang Waktu:",
        value=(min_date, max_date)
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

# --- 5. HEADER & KPI SCORECARD ---
st.title(f"📈 Analisis Saham: {pilih_saham}")
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

# --- 6. TABS LAYOUT INTERAKTIF ---
tab1, tab2, tab3 = st.tabs(["📊 Candlestick & Tren", "📰 Analisis NLP Berita", "🤖 Korelasi Harga vs Sentimen"])

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
        st.subheader("Distribusi Sentimen (VADER)")
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
            st.dataframe(df_b_filter[['Tanggal', 'Judul_Berita', 'Sentimen', 'Skor_Compound']], width='stretch', hide_index=True)
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
        fig_corr.add_trace(go.Scatter(x=df_korelasi['Date'], y=df_korelasi['Skor_Compound'], name='Skor NLP (VADER)', 
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