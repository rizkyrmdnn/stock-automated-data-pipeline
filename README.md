# Automated Stock News Sentiment Analysis & Price Correlation System

### *An End-to-End Cloud Data Pipeline, Lexicon NLP & Hybrid Generative AI Decision Support System (DSS)*

Dashboard Saham AI

---

## 📌 1. Project Overview & Problem Statement

### 🎯 Problem Statement

In modern capital markets, novice retail investors often suffer from behavioral finance biases, emotional decision-making, and Fear of Missing Out (FOMO). The massive daily influx of unstructured financial news headlines creates information overload and market noise. Manual news sentiment tracking is subjective, error-prone, and time-consuming, leading retail traders to execute impulsive trades rather than objective, data-backed investment strategies.

### 💡 Solution

This project delivers a **cloud-native, automated Decision Support System (DSS)** that bridges data engineering, Natural Language Processing (NLP), and Generative AI. Built upon the **CRISP-DM** engineering framework, the system continuously ingests US equity market data, quantifies news sentiment into mathematical metrics, synthesizes daily price-sentiment co-movement via interactive dual-axis visual dashboards, and generates zero-hallucination executive summaries using Large Language Models (LLMs).

---

## 🏗️ 2. Key Features & End-to-End Architecture

!data flow architecture with legend.png

### ⚙️ Core System Modules

1. **Automated Cloud ETL Data Engineering Pipeline**
    - **Extract**: Ingests daily historical stock prices (\(Open, High, Low, Close, Volume\)) and news metadata across 5 key US tech equities (**GOOGL, NVDA, VZ, TSLA, AAPL**) via the `yfinance` API.
    - **Transform & DQA**: Applies Data Quality Assurance (DQA) including ticker-specific keyword filtering (`company_keywords`), title deduplication (`drop_duplicates`), missing value elimination, timestamp standardization, and feature concatenation.
    - **Load**: Performs daily incremental loads (`if_exists='append'`) into Google BigQuery Cloud Data Warehouse partitioned tables.
2. **Dual-Path AI & NLP Modeling**
    - **Quantitative Path (NLTK VADER)**: Computes a normalized Compound Sentiment Score (\(-1.0 \text{ to } +1.0\)) for news text using rule-based heuristics. Standard thresholds classify polarity into **Positive** (\(\ge 0.05\)), **Negative** (\(\le -0.05\)), and **Neutral**.
    - **Qualitative Path (Gemini 3.1 Flash-Lite API)**: Utilizes advanced Prompt Engineering to ingest 15-day aggregated time-series data points (Date, Close Price, VADER Compound Score) alongside overall Pearson correlation (\(r\)) coefficients. Generates concise, professional 3-sentence executive summaries detecting market divergence.
3. **CI/CD Automation & Security**
    - **Orchestration**: Fully automated back-end workflow executed via GitHub Actions cron jobs (`0 22 * * *` / 5:00 AM WIB daily UTC trigger) running on headless Ubuntu runners.
    - **Zero-Trust Security**: Secure credential injection using GitHub Secrets (`GCP_CREDENTIALS`) and Streamlit Secrets (`secrets.toml`) to prevent API key exposure.
4. **Interactive Analytics Dashboard**
    - Renders **Dual Y-Axis Charts** overlaying Close Price bar charts against VADER Compound Score trend lines.
    - Features Candlestick price action with 7-day Moving Averages (MA-7), sentiment distribution Donut Charts, KPI Scorecards, and real-time LLM-generated market summaries.

---

## 🛠️ 3. Technical Stack

| Layer | Technologies & Tools |
| --- | --- |
| **Language & Environment** | Python 3.14 / 3.10, Linux (Ubuntu Latest) |
| **Data Extraction & Manipulation** | `yfinance` API, Pandas, `pandas-gbq` |
| **Cloud Infrastructure & Data Warehouse** | Google Cloud Platform (GCP), Google BigQuery |
| **Automation & CI/CD** | GitHub Actions, YAML, Cron Schedulers, GitHub Secrets |
| **AI, NLP & Large Language Models** | NLTK VADER (`vader_lexicon`), Gemini 3.1 Flash-Lite API (`google-genai`) |
| **Data Visualization & Front-End** | Streamlit, Plotly Express, Plotly Graph Objects (`go.Bar`, `go.Scatter`) |
| **Deployment Platform** | Streamlit Community Cloud |

---

## 🧪 4. Performance Evaluation & Results

### 📊 VADER Sentiment Model Evaluation (Confusion Matrix)

Model performance was rigorously benchmarked using a 100-sample test set extracted from BigQuery (covering volatile tech news cycles from July 1–5, 2026) and cross-validated against human domain expert labeling (*ground truth*).

!image.png

| Class / Metric | Precision | Recall | F1-Score | Support |
| --- | --- | --- | --- | --- |
| **Negative Sentiment** | **0.95 (95%)** | 0.82 (82%) | 0.88 | 22 |
| **Neutral Sentiment** | **0.93 (93%)** | 0.67 (67%) | 0.78 | 21 |
| **Positive Sentiment** | 0.83 (83%) | **0.96 (96%)** | 0.89 | 57 |
| **Overall Accuracy** |  |  | **87.00%** | **100** |
| **Weighted Average** | **0.88 (88%)** | **0.87 (87%)** | **0.87** | **100** |

#### Key Analytical Insights:

- **High Overall Accuracy (87.00%)**: Proves that zero-shot lexicon-based VADER is highly reliable for short-text financial news without expensive retraining.
- **Negative Class Precision (95%)**: Minimizes False Positives in risk detection, giving investors high assurance when a negative warning is flagged.
- **Positive Class Recall (96%)**: Extremely sensitive to good news, ensuring traders never miss bullish market momentum.
- **Neutral Class Trade-off**: Lower recall on neutral headlines (67%) stems from financial news containing compound positive adjectives (e.g., *"expansion"*, *"partnership"*), causing VADER's sum-based score to cross the positive threshold.

### 📉 Visual Co-Movement & Divergence Discovery

In a case study analyzing NVIDIA (NVDA) for June 2026:

- **Pearson Correlation Coefficient (\(r\))**: Calculated at \(0.14\), indicating a very weak linear relationship.
- **Market Divergence**: NVDA stock price dropped by **12.76%** while average news sentiment remained positive (**0.47**).
- **AI Executive Summary Insight**: Gemini 3.1 Flash-Lite correctly synthesized this anomaly, warning investors that macro-fundamental or technical factors dominated price action, preventing retail traders from falling into a positive news trap.

---


## 🌐 5. Live Production & Author Information

- 🔗 **Live Production Dashboard**: korelasi-harga-sentimen-saham.streamlit.app
- 👤 **Author**: **Rizky Ramdhani Koswara** (NPM: 11122300)
- 🎓 **Degree Program**: B.S. in Information Systems, Faculty of Computer Science & Information Technology, Gunadarma University (Graduated August 2026)
- 👨‍🏫 **Thesis Advisor**: Dr. Sutresna Wati, ST., MMSI
- 📄 **Academic Thesis Title**: *Sistem Analisis Sentimen Berita Saham Otomatis dan Visualisasi Korelasi Harga Berbasis NLTK VADER dan Generative AI Gemini API untuk Mendukung Keputusan Investasi*
