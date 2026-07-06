import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# 1. Load Data
nama_file = 'bq-results-20260706-142852-1783348154407.csv'
df = pd.read_csv(nama_file)

# 2. Normalisasi Teks (Menghapus spasi berlebih & memastikan format huruf kapital seragam)
df['Sentimen'] = df['Sentimen'].str.strip().str.title()
df['Sentimen_manual'] = df['Sentimen_manual'].str.strip().str.title()

y_pred = df['Sentimen']        # Tebakan Model VADER
y_true = df['Sentimen_manual'] # Kunci Jawaban Manusia

# 3. Kalkulasi Metrik Evaluasi
akurasi = accuracy_score(y_true, y_pred)
print("=== HASIL EVALUASI MODEL NLP VADER ===")
print(f"Akurasi Total: {akurasi * 100:.2f}%\n")
print("Detail Presisi, Recall, dan F1-Score per Kelas:")
print(classification_report(y_true, y_pred))

# 4. Pembuatan Visualisasi Confusion Matrix
label_kelas = ['Positif', 'Netral', 'Negatif']
cm = confusion_matrix(y_true, y_pred, labels=label_kelas)

plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=label_kelas, yticklabels=label_kelas,
            annot_kws={"size": 14})

plt.title('Confusion Matrix - VADER vs Manual Labeling', fontsize=15, pad=15)
plt.xlabel('Prediksi Model (VADER)', fontsize=12)
plt.ylabel('Kondisi Aktual (Manual)', fontsize=12)

# Simpan luaran sebagai gambar PNG beresolusi tinggi
nama_output = 'Skripsi-Confusion-Matrix.png'
plt.savefig(nama_output, dpi=300, bbox_inches='tight')
print(f"\n[SUKSES] Visualisasi matriks berhasil diekspor menjadi: {nama_output}")