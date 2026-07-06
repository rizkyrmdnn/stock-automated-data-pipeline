import os
from google.cloud import bigquery

print("Memulai proses perpanjangan umur tabel BigQuery...")

# 1. -- GCP AUTHENTICATION --
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "kunci-gcp.json"

# 2. -- INITIALIZE BIG QUERY CLIENT --
client = bigquery.Client()

# project id & dataset
project_id = "skripsi-pipeline-saham"
dataset = "data_saham"

# 3. -- QUERY TO REPLACE TABLE WITH ITS OWN CONTENT (RESET TIMER) --
queries = [
    f"""
    CREATE OR REPLACE TABLE `{project_id}.{dataset}.tabel_sentimen` AS 
    SELECT DISTINCT * FROM `{project_id}.{dataset}.tabel_sentimen`
    """,
    f"""
    CREATE OR REPLACE TABLE `{project_id}.{dataset}.tabel_harga` AS 
    SELECT DISTINCT * FROM `{project_id}.{dataset}.tabel_harga`
    """
]

# 4. -- EXECUTE QUERY --
for query in queries:
    print(f"Mengeksekusi query...")
    query_job = client.query(query)
    query_job.result()  # wait.
    print("Tabel berhasil di-refresh dan umurnya kembali jadi 60 hari!")

print("Proses selesai, aman sentosa!")