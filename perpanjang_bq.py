import os
# pyrefly: ignore [missing-import]
from google.cloud import bigquery

print("Memulai proses perpanjangan umur tabel BigQuery...")

# 1. Setup Kredensial GCP
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "kunci-gcp.json"

# 2. Inisialisasi Client BigQuery
client = bigquery.Client()

# Project ID dan Dataset
project_id = "skripsi-pipeline-saham"
dataset = "data_saham"

# 3. Daftar Query untuk me-replace tabel dengan isinya sendiri (Reset Timer)
queries = [
    f"""
    CREATE OR REPLACE TABLE `{project_id}.{dataset}.tabel_sentimen` AS 
    SELECT * FROM `{project_id}.{dataset}.tabel_sentimen`
    """,
    f"""
    CREATE OR REPLACE TABLE `{project_id}.{dataset}.tabel_harga` AS 
    SELECT * FROM `{project_id}.{dataset}.tabel_harga`
    """
]

# 4. Eksekusi Query
for query in queries:
    print(f"Mengeksekusi query...")
    query_job = client.query(query)
    query_job.result()  # Tunggu sampai selesai
    print("Tabel berhasil di-refresh dan umurnya kembali jadi 60 hari!")

print("Proses selesai, aman sentosa!")