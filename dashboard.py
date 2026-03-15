import streamlit as st
import pandas as pd
import pandas_gbq
import os
import plotly.express as px

# --- 1. SETUP KUNCI GCP ---
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "kunci-gcp.json"

# --- 2. KONFIGURASI HALAMAN & CSS INJECTION ---
st.set_page_config(page_title="Dashboard Saham AI", page_icon="📈", layout="wide")

# CSS rahasia buat ngilangin menu default Streamlit biar kelihatan kayak Web App beneran
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("📈 Dashboard Analisis Sentimen & Harga Saham")
st.markdown("Sistem Pendukung Keputusan Berbasis Cloud & Natural Language Processing (NLP)")

# PERHATIAN: Ganti pakai Project ID GCP lo yang asli
id_project_gcp = 'skripsi-pipeline-saham' 

# --- 3. FUNGSI NARIK DATA ---
@st.cache_data
def load_sentimen():
    query = f"SELECT * FROM `{id_project_gcp}.data_saham.tabel_sentimen` ORDER BY Tanggal DESC"
    return pandas_gbq.read_gbq(query, project_id=id_project_gcp)

@st.cache_data
def load_harga():
    query = f"SELECT * FROM `{id_project_gcp}.data_saham.tabel_harga` ORDER BY Date DESC"
    return pandas_gbq.read_gbq(query, project_id=id_project_gcp)

with st.spinner('Menghubungkan ke Google BigQuery...'):
    df_berita = load_sentimen()
    df_harga = load_harga()

# Konversi kolom tanggal biar formatnya kebaca bener sama Plotly
df_harga['Date'] = pd.to_datetime(df_harga['Date'])
df_berita['Tanggal'] = pd.to_datetime(df_berita['Tanggal']).dt.date

# --- 4. AREA FILTER ---
st.markdown("---")
pilih_saham = st.selectbox("🎯 Pilih Saham untuk Dianalisis:", ['GOOGL', 'NVDA', 'VZ'])

# Saring data sesuai pilihan
df_b_filter = df_berita[df_berita['Ticker'] == pilih_saham]
df_h_filter = df_harga[df_harga['Ticker'] == pilih_saham].sort_values('Date') # Sortir urut tanggal

# --- 5. SCORECARD / KPI METRICS (Ngitung otomatis) ---
# Kalkulasi pergerakan harga
if not df_h_filter.empty and len(df_h_filter) >= 2:
    harga_terakhir = df_h_filter.iloc[-1]['Close']
    harga_kemarin = df_h_filter.iloc[-2]['Close']
    selisih = harga_terakhir - harga_kemarin
    persen = (selisih / harga_kemarin) * 100
else:
    harga_terakhir, selisih, persen = 0, 0, 0

# Kalkulasi sentimen
sentimen_mayoritas = df_b_filter['Sentimen'].mode()[0] if not df_b_filter.empty else "N/A"
total_berita = len(df_b_filter)

# Nampilin 3 Kotak KPI Berjejer
col1, col2, col3 = st.columns(3)
col1.metric("Harga Penutupan Terakhir", f"${harga_terakhir:,.2f}", f"{selisih:,.2f} ({persen:.2f}%)")
col2.metric("Total Berita Dianalisis", total_berita)
col3.metric("Sentimen Mayoritas AI", sentimen_mayoritas)

st.markdown("---")

# --- 6. TABS LAYOUT INTERAKTIF ---
tab1, tab2 = st.tabs(["📊 Analisis Harga Saham", "📰 Analisis Sentimen Berita"])

with tab1:
    st.subheader("Pergerakan Harga Saham (1 Bulan Terakhir)")
    # Bikin Line Chart interaktif pakai Plotly
    fig_harga = px.line(df_h_filter, x='Date', y='Close', markers=True, 
                        title=f"Tren Harga {pilih_saham}",
                        labels={'Date': 'Tanggal', 'Close': 'Harga Penutupan (USD)'})
    
    # Warna chart otomatis nyesuain tema web (Dark/Light mode)
    fig_harga.update_layout(template="plotly_dark" if st.get_option("theme.base") == "dark" else "plotly_white")
    st.plotly_chart(fig_harga, width='stretch')

with tab2:
    col_chart, col_data = st.columns([1, 1.5]) # Kolom kanan dibikin lebih lebar buat tabel
    
    with col_chart:
        st.subheader("Distribusi Sentimen")
        # Bikin Pie Chart interaktif (Donut Chart)
        sentimen_count = df_b_filter['Sentimen'].value_counts().reset_index()
        sentimen_count.columns = ['Sentimen', 'Jumlah']
        
        # Mapping warna biar Positif = Ijo, Negatif = Merah
        color_map = {'Positif': '#00cc96', 'Negatif': '#ef553b', 'Netral': '#636efa'}
        fig_pie = px.pie(sentimen_count, values='Jumlah', names='Sentimen', hole=0.4,
                         color='Sentimen', color_discrete_map=color_map)
        st.plotly_chart(fig_pie, width='stretch')
        
    with col_data:
        st.subheader("Daftar Berita Terbaru")
        st.dataframe(df_b_filter[['Tanggal', 'Judul_Berita', 'Sentimen']], width='stretch', hide_index=True)