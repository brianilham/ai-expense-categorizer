# AI-Augmented Expense Categorizer - System Architecture & Data Flow

## 1. High-Level Data Flow Architecture

```mermaid
flowchart TD
    A[Data Ingestion: CSV Mutasi / Faker Generator] --> B[Data Contract Validation: Pandera Schema]
    B --> C[Data Preprocessing: Filter Debit & Normalize Text]
    C --> D{Hybrid Categorization Engine}
    
    D -->|Tier 1: Keyword/Regex Match| E[Deterministic Rules Engine: <1ms]
    D -->|Tier 2: Ambiguous/Unique Merchants| F[Gemini 3.5 Flash Lite: Batch JSON Array]
    
    E --> G[Merge Results & Compute Confidence]
    F --> G
    
    G --> H[(DuckDB: Local In-Memory OLAP)]
    G --> I[(Supabase: PostgreSQL Cloud Retention)]
    
    H --> J[Streamlit Analytics Dashboard]
    J --> K[Interactive KPIs, Plotly Visualizations & CSV Export]
```

---

## 2. Selected Tech Stack & Tooling

| Komponen | Tools Pilihan | Alasan Pemilihan & Justifikasi |
| :--- | :--- | :--- |
| **Data Acquisition** | **Faker + Custom Indonesian Bank Lexicon** | Generasi 150+ mutasi realistis (BCA, Mandiri, GoPay, QRIS) tanpa ketergantungan API pihak ketiga. |
| **Data Contract** | **Pandera** | Deklaratif, validasi tipe data dan rentang nilai ketat (*strict checks*), mencegah *silent bugs*. |
| **Heuristic Engine** | **Python Regex / Trie Map** | Deterministic matching instan (<1ms), 0 rupiah biaya API, menyerap 40–60% transaksi umum. |
| **AI Inference** | **Google Gemini 3.5 Flash Lite (REST)** | Model LLM tercepat dan paling efisien untuk ekstraksi teks terstruktur dengan kuota free tier. |
| **Analytics Engine** | **DuckDB** | Zero-dependency embedded OLAP, kueri SQL agregasi <5ms untuk visualisasi dashboard. |
| **Cloud Storage** | **Supabase PostgreSQL (Session Pooler)** | Penyimpanan data permanen cloud yang andal via driver `psycopg2-binary` pada port 5432. |
| **Frontend / Delivery**| **Streamlit** | Dashboard interaktif modern berbasis Python murni untuk visualisasi dan storytelling portofolio. |
| **Testing Suite** | **pytest** | Pengujian unit dan validasi kualitas klasifikasi otomatis (*Test-Driven Development*). |

---

## 3. Trade-offs & Decision Rationale (ADR)
*(Educational Mentorship Section - Mengapa arsitektur ini dipilih?)*
<details>
<summary>💡 Klik untuk Penjelasan Rationale & Trade-offs Teknis</summary>

* **Mengapa Hybrid (Rules + LLM) dan Bukan Full LLM?**
  Mengirim 100% transaksi ke LLM itu mahal dan lambat. Transaksi seperti `"PAYMENT PLN TOKEN"` atau `"SPOTIFY PREMIUM"` memiliki kepastian deterministik 100%. Dengan menyaringnya di Tier-1 menggunakan Regex/Rules lokal, kita menghemat waktu roundtrip jaringan dan menghemat kuota request API secara drastis.
* **Mengapa DuckDB bersama Supabase?**
  Supabase adalah database transaksional (OLTP). Jika dashboard Streamlit sering melakukan kueri agregasi berat (`GROUP BY category`, `SUM(amount)`, `AVG(...)`), koneksi cloud akan menimbulkan latensi jaringan bolak-balik. DuckDB bertindak sebagai mesin analitik lokal (OLAP) di memori RAM, mengeksekusi kalkulasi metrik dalam hitungan milidetik.
* **Mengapa Pandera di Pintu Depan (*Fail-Fast Principle*)?**
  Jika ada nominal pengeluaran bernilai negatif, kolom tanggal yang formatnya rusak, atau nilai kosong di deskripsi, proses ETL seharusnya tidak boleh dilanjutkan. Pandera memastikan integritas data terjamin sebelum data menyentuh AI atau database.
</details>

---

## 4. Data Contract & Schema Specifications (Contract-First)

### A. Raw Ingestion Schema (`schemas.py` via Pandera)
```python
import pandera as pa
from pandera.typing import Series

class RawTransactionSchema(pa.DataFrameModel):
    Date: Series[str] = pa.Field(nullable=False, description="Tanggal transaksi format YYYY-MM-DD")
    Amount: Series[float] = pa.Field(ge=0, nullable=False, description="Nominal transaksi positif")
    Type: Series[str] = pa.Field(isin=["Debit", "Credit"], nullable=False, description="Tipe mutasi")
    Raw_Description: Series[str] = pa.Field(nullable=False, str_length={"min_value": 3}, description="Keterangan transaksi")
```

### B. Cleaned & Categorized Schema
```python
class CategorizedTransactionSchema(pa.DataFrameModel):
    Date: Series[pa.DateTime] = pa.Field(nullable=False)
    Amount: Series[float] = pa.Field(ge=0, nullable=False)
    Raw_Description: Series[str] = pa.Field(nullable=False)
    Clean_Description: Series[str] = pa.Field(nullable=False)
    Category: Series[str] = pa.Field(isin=[
        "F&B", "Transportasi", "Utilitas", "Hiburan", 
        "Belanja", "Perawatan Kendaraan", "Transfer/Tarik Tunai", 
        "Kebutuhan Rumah Tangga", "Lainnya"
    ])
    Source: Series[str] = pa.Field(isin=["Heuristic_Rules", "Gemini_AI"])
```

---

## 5. Reliability, Reliability & Failure Mode Mitigation
- **Graceful API Fallback**: Jika kuota Gemini habis (HTTP 429) atau koneksi internet terputus, sistem secara otomatis menandai transaksi yang belum terpetakan sebagai `"Lainnya (Perlu Review)"` tanpa memutus jalannya pipeline.
- **Deduplication Engine**: Hash unik `MD5(Date + Amount + Raw_Description)` untuk mencegah duplikasi data transaksi saat file mutasi diunggah berulang kali ke database.
- **SQLAlchemy Session Pooler Protection**: Menggunakan `override=True` pada `.env` dan parameter `sslmode=require` untuk menjamin koneksi PostgreSQL Supabase selalu stabil.
