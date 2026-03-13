import streamlit as st
import pandas as pd
import pandas_gbq
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "kunci-gcp.json"

st.set_page_config(page_title="Dashboard Saham AI", layout="wide")
st.title("📈 Dashboard Analisis Sentimen & Harga Saham")

# Ganti pakai Project ID lo
id_project_gcp = 'skripsi-pipeline-saham' 

# Fungsi narik data Sentimen
@st.cache_data
def load_sentimen():
    query = f"SELECT * FROM `{id_project_gcp}.data_saham.tabel_sentimen` ORDER BY Tanggal DESC"
    return pandas_gbq.read_gbq(query, project_id=id_project_gcp)

# Fungsi narik data Harga
@st.cache_data
def load_harga():
    query = f"SELECT * FROM `{id_project_gcp}.data_saham.tabel_harga` ORDER BY Date DESC"
    return pandas_gbq.read_gbq(query, project_id=id_project_gcp)

with st.spinner('Menarik data dari BigQuery...'):
    df_berita = load_sentimen()
    df_harga = load_harga()

st.success("Data berhasil ditarik secara Real-Time!")

# --- FITUR FILTER SAHAM ---
pilih_saham = st.selectbox("Pilih Saham untuk dianalisis:", ['GOOGL', 'NVDA', 'VZ'])

# Saring data sesuai saham yang dipilih
df_berita_filter = df_berita[df_berita['Ticker'] == pilih_saham]
df_harga_filter = df_harga[df_harga['Ticker'] == pilih_saham]

# --- TAMPILAN GRAFIK HARGA ---
st.subheader(f"Grafik Pergerakan Harga Penutupan (Close) - {pilih_saham}")
st.line_chart(data=df_harga_filter, x='Date', y='Close', width='stretch')

st.divider() # Garis pembatas

# --- TAMPILAN SENTIMEN ---
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"Tabel Berita Terbaru - {pilih_saham}")
    st.dataframe(df_berita_filter[['Tanggal', 'Judul_Berita', 'Sentimen']], width='stretch')

with col2:
    st.subheader("Distribusi Sentimen AI")
    st.bar_chart(df_berita_filter['Sentimen'].value_counts(), color="#34b4eb")