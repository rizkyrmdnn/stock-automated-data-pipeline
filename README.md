# 🎬 Popular Movies & TV Series in Indonesia: Business Intelligence & Regional Content Curation Dashboard

### *An End-to-End ETL Pipeline Processing 9+ Million IMDb Records, CRISP-DM Framework & Interactive Web Analytics*

Dashboard Film & Serial TV Populer di Indonesia

---

## 📌 1. Project Overview & Problem Statement

### 🎯 Problem Statement

The exponential growth of video-on-demand (VOD) streaming platforms (such as Netflix, Disney+ Hotstar, Amazon Prime Video, HBO GO, and Vidio) has created massive content fragmentation and information overload for Indonesian entertainment consumers. Viewers face significant friction when trying to discover relevant, high-quality movies and TV series tailored to local market preferences.

Furthermore, while official global platforms like IMDb host millions of public entertainment records, these raw datasets lack localized demographic context out of the box. Extracting regional insights requires engineering a robust data pipeline capable of ingesting multi-million row datasets, applying strict regional scoping, and normalizing complex multi-genre structures.

### 💡 Solution

This project delivers a web-deployed, interactive **Business Intelligence (BI) Analytics Dashboard** that curates and visualizes popular movies and TV series specifically registered and localized for the Indonesian market. Guided by the **CRISP-DM** engineering framework, the system ingests **over 9 million raw records** from official IMDb bulk datasets through a multi-stage **ETL (Extract, Transform, Load)** pipeline in **Power BI Desktop**, calculates custom weighted rating metrics to resolve multi-genre data duplication in **Looker Studio**, and deploys a responsive web dashboard globally via **GitHub Pages**.

---

## 🏗️ 2. Data Engineering: Processing 9+ Million IMDb Records (CRISP-DM)

The system architecture and data engine follow the six iterative phases of the **Cross-Industry Standard Process for Data Mining (CRISP-DM)** framework:

```
+-----------------------------------------------------------------------------------+
|                                1. BUSINESS UNDERSTANDING                          |
|  - Objective: Uncover popular titles & genre preferences for the Indonesian market|
|  - Scope: Regional content curation for Indonesian VOD audiences & curators       |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                                2. DATA UNDERSTANDING                              |
|  - Ingest 9M+ raw records from official IMDb bulk TSV files:                      |
|    * title.basics.tsv (9M+ global metadata, genres, release years)                |
|    * title.akas.tsv   (Multi-million localized alternate titles - Region 'ID')    |
|    * title.ratings.tsv (Global user average ratings & total vote counts)          |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                            3. DATA PREPARATION (ETL ENGINE)                       |
|  - Extract: Bulk stream raw TSVs into Power Query Editor (Power BI Desktop)       |
|  - Transform: Region 'ID' filter (slashes 9M+ rows), content type filtering,      |
|    '\N' null handling, year scope (1970–2025) & numVotes > 25,000 threshold,     |
|    multi-table Left Outer Joins, and genre delimiter splitting                    |
|  - Data Bridge: Memory optimization, Google Sheets weighted helper calculation,   |
|    and Looker Studio connection                                                   |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                                   4. MODELLING                                    |
|  - Construct Looker Studio interactive dashboard layout                           |
|  - Formulate custom 'Accurate Average Rating' calculated measure                  |
|  - Build KPI Scorecards, Line Charts, Bar Charts, Pie Charts & Scatter Plots      |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                                   5. EVALUATION                                   |
|  - Validate KPI calculations, genre distributions, & regional title accuracy     |
|  - Conduct Quality vs. Popularity quadrant analysis & Movie vs. TV rating comparison|
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                                   6. DEPLOYMENT                                   |
|  - Embed Looker Studio responsive report into custom HTML/Tailwind template       |
|  - Deploy live web portfolio to production via GitHub Pages                       |
+-----------------------------------------------------------------------------------+
```

### ⚙️ Detailed Breakdown of the 9M+ Record ETL Pipeline

Processing a dataset exceeding **9 million raw records** required a memory-efficient and structured ETL strategy executed inside **Power BI Desktop (Power Query Editor)** on a hardware setup of an Intel Core i5 processor with 16 GB RAM:

#### 📥 1. Extract Phase (Bulk Data Ingestion)

Raw, non-commercial IMDb bulk datasets were ingested directly in Tab-Separated Values (`.tsv`) format from official IMDb developer endpoints:

- **`title.basics.tsv`**: The primary catalog containing **over 9+ million global records** holding technical IDs (`tconst`), title classifications (`titleType`), canonical names (`primaryTitle`), release years (`startYear`), runtimes (`runtimeMinutes`), and genre strings (`genres`).
- **`title.akas.tsv`**: A massive relational table containing **millions of localized alternate title records** across global territories, featuring the critical `region` attribute.
- **`title.ratings.tsv`**: The global user feedback table containing `averageRating` (1.0–10.0 scale) and total user vote counts (`numVotes`).

#### 🔄 2. Transform Phase (Slashing & Cleaning 9M+ Rows)

To transform this massive unorganized global dataset into an agile regional database, a series of high-performance transformation steps were applied in Power Query Editor:

- **Regional Scoping (`region == 'ID'`)**: The pipeline filtered `title.akas.tsv` strictly for `region == 'ID'`. This single strategic step **instantaneously slashed the multi-million row global dataset down to titles specifically localized, registered, or distributed for the Indonesian market**, eliminating gigabytes of irrelevant global overhead.
- **Content Type Filtering**: Filtered `titleType` within `title.basics.tsv` to retain only `movie`, `tvMovie`, `tvSeries`, and `tvMiniSeries`. Short films, single TV episodes, video games, and promotional clips were systematically purged.
- **Data Cleansing & Type Casting**:
    - Replaced IMDb's default null marker string (`\N`) with true system `null` values across release years, runtimes, and genres.
    - Cast `startYear`, `endYear`, and `runtimeMinutes` into `Whole Number` data types.
- **Temporal & Popularity Thresholding**:
    - Scoped release years (`startYear`) between **1970 and 2025** to focus on modern entertainment history.
    - Applied a popularity filter threshold (`numVotes > 25,000`) to isolate mainstream popular titles and purge low-engagement records.
- **Relational Joins & Column Refactoring**:
    - Merged the scoped `title.akas` table with `title.basics` using a **Left Outer Join** on foreign keys (`titleId` / `tconst`).
    - Joined the resulting dataset with `title.ratings.tsv` on `tconst`.
    - Expanded required attributes while dropping redundant technical columns (`tconst`, `isAdult`, `originalTitle`, `ordering`).
    - Purged unrated records using `Remove Empty` on `averageRating` and `numVotes`.
- **Genre Delimiter Normalization**: Applied `Split Column by Delimiter (Comma)` on the comma-separated `genres` attribute, expanding multi-genre titles into individual genre rows to enable granular per-genre analytics.

#### 📤 3. Load Phase & Data Bridge Engine

- **Memory Optimization**: Executed `Close & Apply` in Power Query Editor. Data loading for raw staging tables (`title.akas`, `title.basics`, `title.ratings`) was explicitly disabled in the Power BI model view to prevent RAM overload.
- **Weighted Rating Calculation (Google Sheets Data Bridge)**:
    - Splitting multi-genre titles created duplicate title rows, which would artificially inflate average rating calculations if aggregated directly.
    - To resolve this, the clean dataset was exported to Google Sheets, where a custom helper column `Rating_Bobot` was engineered:
    \[\text{Rating_Bobot} = \frac{\text{Rating}}{\text{COUNTIF}(\text{ID_Column}, \text{ID_Row})}\]
- **Looker Studio Engine Connection**: Connected Looker Studio to the cleaned Google Sheets bridge, defining a custom calculated measure `Rata-rata Rating Akurat`:
\[\text{Accurate Average Rating} = \frac{\sum(\text{Rating_Bobot})}{\text{COUNT_DISTINCT}(\text{Title ID})}\]
This mathematical formula completely neutralized rating duplication, ensuring 100% metric accuracy across all visual scorecards.

---

## 📊 3. Key Analytical Insights & Highlights

### 📈 Core Catalog KPIs (2020–2025 Focus Scope)

- **Total Movies Analyzed**: **572 titles** (\(70.9%\) of catalog share).
- **Total TV Series & Miniseries Analyzed**: **235 titles** (\(29.1%\) of catalog share).
- **Overall Catalog Average Rating**: **68.24 / 100** (or **6.82 / 10** IMDb scale).
- **Total Unique Genres Tracked**: **23 distinct genres**.

### 🎭 Genre Preference Distribution

- **Dominant Genres**: **Drama** and **Action** lead the Indonesian market by a substantial margin, proving that emotionally compelling character arcs and high-octane spectacle represent the primary drivers for local audience engagement.
- **Secondary Favorites**: **Comedy** and **Adventure** occupy the second tier, showing consistent demand for lighthearted, escapist entertainment.
- **Niche Powerhouses**: **Crime**, **Thriller**, **Mystery**, and **Horror** maintain strong, dedicated viewership shares in Indonesia.

### 🔬 Comparative Analysis: Movies vs. TV Series

- **Significant Rating Gap**: TV Series achieved a noticeably higher average rating (**75.66**) compared to Movies (**65.19**)—a performance gap exceeding 10 points.
- **Prestige TV Phenomenon**: Indonesian audiences grant higher critical acclaim to long-form episodic narratives due to deeper character development and cinematic production budgets invested by streaming networks in titles like *The Last of Us*, *The Queen's Gambit*, and *Arcane*.

### 🌌 Quality vs. Popularity Quadrant Analysis (Scatter Chart)

- **Popular & High Quality (Top-Right Quadrant)**: Blockbusters achieving both critical acclaim and mass engagement (e.g., *Oppenheimer* [Rating: 83, Votes: 901K], *The Queen's Gambit* [Rating: 85, Votes: 621K], *The Last of Us* [Rating: 86, Votes: 676K]).
- **Popular & Lower Quality (Bottom-Right Quadrant)**: High-vote titles with moderate critical ratings (e.g., *Doctor Strange in the Multiverse of Madness* [Rating: 69, Votes: 518K], *Barbie* [Rating: 68, Votes: 612K]), proving that massive marketing and star power drive popularity independent of critical consensus.
- **Hidden Gems (Top-Left Quadrant)**: Highly acclaimed titles (\(>85\) rating) with moderate vote counts, heavily populated by anime and mini-series (e.g., *Frieren: Beyond Journey's End* [Rating: 89, Votes: 44K], *Bleach: Thousand-Year Blood War* [Rating: 90, Votes: 62K]).

---

## 🛠️ 4. Technical Stack & Architecture

| Layer | Tools & Technologies |
| --- | --- |
| **Data Source** | Official IMDb Non-Commercial Bulk Datasets (`title.basics.tsv`, `title.akas.tsv`, `title.ratings.tsv`) |
| **ETL & 9M+ Data Transformation** | Microsoft Power BI Desktop, Power Query Editor |
| **Data Bridge & Formula Normalization** | Google Sheets (Weighted Rating Helper Calculation) |
| **Visualization & Dashboard Engine** | Looker Studio (Calculated Fields, Scorecards, Custom Controls, Scatter Charts) |
| **Front-End & Web Deployment** | HTML5, CSS3 (Tailwind CSS, Inter font), Git, GitHub Repositories, GitHub Pages |
| **Methodology & Framework** | CRISP-DM (Cross-Industry Standard Process for Data Mining) |

---

## 🌐 5. Live Demo & Author Credentials

- 🔗 **Live Interactive Dashboard**: rizkyrmdnn.github.io/Dashboard-Film-Populer/
- 👨‍💻 **Author**: **Rizky Ramdhani Koswara** (NPM: 11122300)
- 🎓 **Degree Program**: Information Systems, Faculty of Computer Science and Information Technology, Gunadarma University (2025)
- 👨‍🏫 **Academic Advisor**: Kuwat Setiyanto, SKom., MMSI
- 📜 **Scientific Paper Title**: *Visualisasi Data Film dan Serial TV Populer di Indonesia Berdasarkan IMDb Menggunakan Power BI dan Looker Studio*
