import streamlit as st
import pandas as pd
import pandas_gbq
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
import base64
import json
import time
from google.oauth2 import service_account
from google import genai


# --- 1. GCP AUTHENTICATION  ---
if "gcp_service_account" in st.secrets:
    # streamlit cloud credentials
    creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
else:
    # local credentials
    creds = service_account.Credentials.from_service_account_file("kunci-gcp.json")

# --- 2. GEMINI CLIENT SETUP ---
if "GEMINI_API_KEY" in st.secrets:
    gemini_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key Gemini tidak ditemukan di Secrets!")

# --- 3. PAGE CONFIGURATION & CSS INJECTION ---
st.set_page_config(page_title="Dashboard Saham AI", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 4. LOAD DATA FUNCTION ---
id_project_gcp = 'skripsi-pipeline-saham' 

@st.cache_data(ttl=3600) # expired cache every hour
def load_sentimen():
    query = f"SELECT DISTINCT * FROM `{id_project_gcp}.data_saham.tabel_sentimen` ORDER BY Tanggal DESC"
    return pandas_gbq.read_gbq(query, project_id=id_project_gcp, credentials=creds)

@st.cache_data(ttl=3600)
def load_harga():
    query = f"SELECT * FROM `{id_project_gcp}.data_saham.tabel_harga` ORDER BY Date DESC"
    return pandas_gbq.read_gbq(query, project_id=id_project_gcp, credentials=creds)

with st.spinner('Menghubungkan ke Google Cloud & AI...'):
    df_berita = load_sentimen()
    df_harga = load_harga()

# date conversion
df_harga['Date'] = pd.to_datetime(df_harga['Date']).dt.date
df_berita['Tanggal'] = pd.to_datetime(df_berita['Tanggal']).dt.date

# remove duplicate data
df_harga = df_harga.drop_duplicates(subset=['Date', 'Ticker'])

# --- 5. SIDEBAR FILTER CONFIGURATION ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3126/3126489.png", width=80)
    st.title("⚙️ Panel Kontrol")
    
    
    with open("assets/icons/pilih-saham.png", "rb") as image_file:
        icon_saham = base64.b64encode(image_file.read()).decode()
    
    st.markdown(f'<div style="display: flex; align-items: center; margin-bottom: 5px;"><img src="data:image/png;base64,{icon_saham}" width="28" style="margin-right: 10px;"><b>Pilih Saham:</b></div>', unsafe_allow_html=True)
    pilih_saham = st.selectbox("Pilih Saham", ['GOOGL', 'NVDA', 'VZ', 'TSLA', 'AAPL'], label_visibility="collapsed")
    
    # get date range from stock data
    min_date = df_harga['Date'].min()
    max_date = df_harga['Date'].max()
    
    # default to 60 days
    default_start_date = max(min_date, max_date - timedelta(days=60))
    
    with open("assets/icons/rentang-tanggal.png", "rb") as image_file:
        icon_tanggal = base64.b64encode(image_file.read()).decode()
        
    st.markdown(f'<div style="display: flex; align-items: center; margin-bottom: 5px;"><img src="data:image/png;base64,{icon_tanggal}" width="28" style="margin-right: 10px;"><b>Rentang Waktu:</b></div>', unsafe_allow_html=True)
    
    rentang_tanggal = st.date_input(
        "Rentang Waktu",
        value=(default_start_date, max_date),
        label_visibility="collapsed"
    )
    
    # Jumping calendar fix
    st.markdown("<div style='height: 380px;'></div>", unsafe_allow_html=True)

# Validate if user haven't choose start & end date
if len(rentang_tanggal) == 2:
    start_date, end_date = rentang_tanggal
else:
    start_date, end_date = rentang_tanggal[0], rentang_tanggal[0]

# Filter data according to ticker & date range
df_h_filter = df_harga[(df_harga['Ticker'] == pilih_saham) & 
                       (df_harga['Date'] >= start_date) & 
                       (df_harga['Date'] <= end_date)].sort_values('Date').copy()

df_b_filter = df_berita[(df_berita['Ticker'] == pilih_saham) & 
                        (df_berita['Tanggal'] >= start_date) & 
                        (df_berita['Tanggal'] <= end_date)].copy()

# Calculate Moving Average (MA) 7 Days for DSS
if not df_h_filter.empty:
    df_h_filter['MA_7'] = df_h_filter['Close'].rolling(window=7).mean()

# --- 6. AI SUMMARY FUNCTION ---
@st.cache_data(ttl=3600)
def dapatkan_ringkasan_gemini(nama_saham, df_harga, df_berita):
    if df_harga.empty or df_berita.empty:
        return "Data harga atau berita tidak mencukupi untuk dianalisis saat ini."
    
    # Agregasi skor NLP rata-rata per hari
    df_b_harian = df_berita.groupby('Tanggal')['Skor_Compound'].mean().reset_index()
    df_korelasi = pd.merge(df_harga, df_b_harian, left_on='Date', right_on='Tanggal', how='inner').sort_values('Date')
    
    if df_korelasi.empty:
        return "Tidak ditemukan irisan tanggal antara data harga dan berita untuk menghitung korelasi."
    
    # Hitung metrik ringkasan harga & sentimen
    harga_awal = df_korelasi.iloc[0]['Close']
    harga_akhir = df_korelasi.iloc[-1]['Close']
    perubahan_harga = ((harga_akhir - harga_awal) / harga_awal) * 100
    rata_sentimen = df_korelasi['Skor_Compound'].mean()
    
    # Hitung koefisien korelasi Pearson jika data mencukupi
    corr_text = "N/A (data tidak cukup)"
    if len(df_korelasi) >= 2 and df_korelasi['Close'].std() > 0 and df_korelasi['Skor_Compound'].std() > 0:
        r_val = df_korelasi['Close'].corr(df_korelasi['Skor_Compound'])
        if pd.notna(r_val):
            corr_text = f"{r_val:.2f}"
    
    # Ringkasan data harian (maksimal 15 titik data terbaru untuk konteks model)
    data_list = []
    for _, row in df_korelasi.tail(15).iterrows():
        data_list.append(f"- Tanggal: {row['Date']}, Harga Penutupan: ${row['Close']:.2f}, Rata-rata Skor NLP: {row['Skor_Compound']:.2f}")
    data_table_str = "\n".join(data_list)
    
    prompt = f"""
    Kamu adalah seorang analis pasar modal kuantitatif profesional.
    Berikut adalah data korelasi antara Harga Penutupan Saham (Close Price) dan Rata-rata Skor Sentimen Berita NLP (-1.0 s/d 1.0) untuk saham {nama_saham}:
    
    Ringkasan Periode ({df_korelasi.iloc[0]['Date']} s/d {df_korelasi.iloc[-1]['Date']}):
    - Harga Awal vs Akhir: ${harga_awal:.2f} -> ${harga_akhir:.2f} ({perubahan_harga:+.2f}%)
    - Rata-rata Skor NLP: {rata_sentimen:.2f}
    - Koefisien Korelasi Pearson (r): {corr_text}
    
    Riwayat Data Harian (Harga vs Skor NLP):
    {data_table_str}
    
    Tolong berikan ringkasan eksekutif (maksimal 3-4 kalimat) mengenai:
    1. Bagaimana hubungan/korelasi antara fluktuasi skor sentimen berita dengan pergerakan harga penutupan saham {nama_saham}.
    2. Apakah tren kenaikan/penurunan harga saham sejalan atau bertolak belakang dengan sentimen pemberitaan pada periode ini.
    3. Insight atau kesimpulan singkat bagi investor mengenai dampak sentimen terhadap pergerakan harga saham tersebut saat ini.
    Gunakan bahasa Indonesia yang profesional, lugas, dan mudah dipahami.
    """
    
    # Auto-Retry (Max 3 attempts)
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
            # If error is server is busy (503) or quota is full (429)
            if "503" in error_msg or "429" in error_msg or "demand" in error_msg:
                if percobaan < maksimal_coba - 1:
                    time.sleep(2) # Wait 2 seconds before trying again
                    continue # Looping trying to hit the API again
            
            # If failed 3 times
            return f"Sistem AI sedang sibuk. Mohon coba lagi nanti. (Error log: {e})"

# --- 7. HEADER & KPI SCORECARD ---
with open("assets/icons/analisis-saham.png", "rb") as image_file:
    icon_analisis = base64.b64encode(image_file.read()).decode()
st.title(f"![icon](data:image/png;base64,{icon_analisis}) Analisis Saham: {pilih_saham}")
st.markdown("")

# KPI Calculation
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

# AI Sentiment Metric Color
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

# Add AI Summary in the KPI section
st.subheader(" AI Executive Summary (Powered by Gemini)")
with st.spinner("Gemini sedang menganalisis korelasi harga & sentimen..."):
    ringkasan = dapatkan_ringkasan_gemini(pilih_saham, df_h_filter, df_b_filter)
    st.info(ringkasan)

st.markdown("---")

# --- 8. INTERACTIVE TABS LAYOUT ---
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
        # using go for candlestick
        fig_candle = go.Figure()
        
        # add candlestick
        fig_candle.add_trace(go.Candlestick(x=df_h_filter['Date'],
                        open=df_h_filter['Open'], high=df_h_filter['High'],
                        low=df_h_filter['Low'], close=df_h_filter['Close'],
                        name='Harga Saham'))
        
        # add MA-7
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
            
            # sort to newest
            df_b_filter_sorted = df_b_filter.sort_values(by='Tanggal', ascending=False)
            
            for tanggal, group in df_b_filter_sorted.groupby('Tanggal', sort=False):
                # get today's data
                g = group[['Tanggal', 'Judul_Berita', 'Sentimen', 'Skor_Compound']].copy()
                g['Tanggal'] = g['Tanggal'].astype(str)
                rows_list.extend(g.to_dict('records'))
                
                # median score of the day
                rata_harian = group['Skor_Compound'].mean()
                if rata_harian > 0.05:
                    teks_sentimen = "🟢 SENTIMEN HARIAN POSITIF"
                elif rata_harian < -0.05:
                    teks_sentimen = "🔴 SENTIMEN HARIAN NEGATIF"
                else:
                    teks_sentimen = "⚪ SENTIMEN HARIAN NETRAL"
                
                # summary row of the day
                rows_list.append({
                    'Tanggal': '', 
                    'Judul_Berita': teks_sentimen, 
                    'Sentimen': '', 
                    'Skor_Compound': None
                })
                
            df_display = pd.DataFrame(rows_list)
            
            # summary row styling
            def row_style(row):
                teks = str(row['Judul_Berita'])
                if "SENTIMEN HARIAN POSITIF" in teks:
                    return ["background-color: rgba(40, 167, 69, 0.2); color: #4ade80; font-weight: bold;"] * len(row)
                elif "SENTIMEN HARIAN NEGATIF" in teks:
                    return ["background-color: rgba(220, 53, 69, 0.2); color: #f87171; font-weight: bold;"] * len(row)
                elif "SENTIMEN HARIAN NETRAL" in teks:
                    return ["background-color: rgba(108, 117, 125, 0.2); color: #9ca3af; font-weight: bold;"] * len(row)
                return [""] * len(row)
            
            # using style.format because it's a float data
            styled_df = df_display.style.apply(row_style, axis=1).format(na_rep="")
            
            st.dataframe(styled_df, width='stretch', hide_index=True)
        else:
            st.info("Tidak ada data berita.")

with tab3:
    st.subheader("Korelasi: Apakah Berita Positif Menaikkan Harga?")
    st.markdown("Grafik ini membandingkan rata-rata skor sentimen berita harian dengan harga penutupan saham.")
    
    if not df_h_filter.empty and not df_b_filter.empty:
        # median nlp score
        df_b_harian = df_b_filter.groupby('Tanggal')['Skor_Compound'].mean().reset_index()
        # merge stock and nlp data
        df_korelasi = pd.merge(df_h_filter, df_b_harian, left_on='Date', right_on='Tanggal', how='left')
        
        # create chart with two axis (Y1 for stock price, Y2 for nlp score)
        fig_corr = go.Figure()
        
        # Axis 1: stock price (Bar)
        fig_corr.add_trace(go.Bar(x=df_korelasi['Date'], y=df_korelasi['Close'], name='Harga Penutupan', opacity=0.6, marker_color='royalblue'))
        
        # Axis 2: nlp score (Line)
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