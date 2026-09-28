# AI-Augmented Expense Categorizer - Product Requirements Document (PRD)

## 1. Executive Summary & Problem Statement
- **Problem Statement**: Mutasi rekening bank dan dompet digital di Indonesia (BCA, Mandiri, QRIS, GoPay, ShopeePay) menghasilkan riwayat transaksi dengan format deskripsi yang tidak terstruktur, penuh singkatan acak (contoh: `TRF KANTIN RAYA`, `QRIS KOPI HOJA`, `WD ATM MANDIRI`), sehingga menyulitkan pelacakan pengeluaran pribadi dan analisis keuangan bulanan.
- **Business / Personal Impact**: Mengotomatiskan kategorisasi mutasi pengeluaran dari hitungan jam kerja manual menjadi hitungan detik, memberikan visibilitas penuh terhadap arus kas bulanan, dan mendeteksi pemborosan secara instan.
- **Target Audience / Stakeholders**: Individu pencatat keuangan pribadi, profesional, dan Business Owners/SMEs yang memerlukan rekapitulasi pengeluaran instan tanpa bergantung pada aplikasi berbayar.
- **Scope Boundaries**:
  - **In-Scope**:
    - Validasi kontrak data mutasi debit/kredit (*Data Contract*).
    - Pipeline pembersihan data dan pemfilteran mutasi debit (pengeluaran).
    - Mesin kategorisasi *Hybrid*: Heuristik Regex (Tier-1) + Gemini 3.5 Flash Lite Batching (Tier-2).
    - Generator data mutasi perbankan Indonesia sintetis (100–200 baris realistis).
    - Database analitik lokal berkecepatan tinggi (DuckDB) dan sinkronisasi cloud (Supabase PostgreSQL).
    - Dashboard interaktif modern berbasis Streamlit.
  - **Out-of-Scope**:
    - Koneksi API perbankan langsung (Open Banking API berlisensi BI) karena regulasi perbankan.
    - Pelatihan model Deep Learning NLP dari nol (kita memanfaatkan LLM pre-trained yang jauh lebih hemat biaya dan adaptif).

---

## 2. Solution Strategy & Track
- **Selected Track**: **Rule-Based Heuristic + LLM Hybrid Analytics Pipeline**
- **Rationale**: 
  - Sebanyak 40–60% transaksi bulanan memiliki pola kata kunci berulang (contoh: `PLN`, `SPOTIFY`, `ATM`, `CARWASH`). Memanggil LLM untuk pola deterministik ini adalah pemborosan latensi dan kuota token.
  - Sebaliknya, pola transaksi unik (seperti nama kafe/warung lokal via QRIS) membutuhkan penalaran semantik (*semantic reasoning*) yang hanya bisa dipahami secara fleksibel oleh LLM.
- **Complexity Justification**: Pendekatan hybrid memberikan *best of both worlds*: latensi sub-detik untuk transaksi umum dan kecerdasan adaptif LLM untuk *edge cases*, dengan biaya 0 rupiah pada tier gratis.

---

## 3. Success Metrics
- **Business KPI**:
  - **Kategorisasi Akurat**: >= 95% transaksi terpetakan ke kategori finansial yang tepat.
  - **Cost & Quota Efficiency**: Minimal 40% transaksi ditangani oleh Tier-1 Heuristics tanpa mengonsumsi kuota token Gemini.
- **Technical Metrics**:
  - **Data Contract Pass Rate**: 100% data yang diproses lolos validasi Pandera tanpa anomali tipe data atau nilai negatif.
  - **Batch Coverage**: 100% baris transaksi mendapatkan label kategori (tidak ada nilai `null`/`NaN`).
- **Operational SLA**:
  - **End-to-End Processing Time**: < 3 detik untuk pemrosesan 150 baris transaksi mutasi.
  - **Dashboard Query Latency**: < 10 milidetik untuk kueri agregasi grafik analitik via DuckDB.

---

## 4. Data Strategy & Acquisition
- **Data Availability**: Synthetic Required & Extensible to Real CSVs.
- **Sources & Formats**: Format tabular CSV standar mutasi perbankan Indonesia (`Date`, `Amount`, `Type`, `Raw_Description`).
- **Acquisition / Bootstrapping Plan**:
  - **Strategy**: Generator Sintetis Tabular berbasis Faker & kamus merchant lokal Indonesia.
  - **Details**: Menghasilkan 150 transaksi pengeluaran realistis mencakup merchant F&B (Kopi Kenangan, Mixue, Kantin), Utilitas (PLN, PDAM, Indihome), Transportasi (KAI, Grab, Gojek), Hiburan (Spotify, Netflix), Belanja (Shopee, Tokopedia), dan Transfer/Tarik Tunai.

---

## 5. Proactive Pitfall Warnings & Risk Mitigation
*(Educational Mentorship Section - Baca sebelum eksekusi)*
<details>
<summary>💡 Klik untuk melihat daftar Jebakan Data Science & Mitigasinya pada proyek ini</summary>

- **Potential Pitfall 1: Rate Limiting & N+1 Query Loop pada LLM**:
  - *Bahaya*: Melakukan loop `for index, row in df.iterrows()` dan memanggil LLM 1 per 1 akan langsung memicu error `429 Too Many Requests` serta delay puluhan detik.
  - *Mitigasi*: Wajib menggunakan pola **Batch Prompting** (mengirim array JSON berisi seluruh deskripsi unik sekaligus dalam 1 request prompt).
- **Potential Pitfall 2: Silent Data Corruption (Schema Drift)**:
  - *Bahaya*: Kolom `Amount` terbaca sebagai string karena pemisah ribuan titik/koma (misal: `"150.000"`), atau ada nominal minus pada mutasi debit.
  - *Mitigasi*: Terapkan *Data Contract* menggunakan `Pandera` sebelum proses data cleaning dimulai. Jika ada data kotor, sistem langsung menolak (*fail-fast*) dengan pesan error yang jelas.
- **Potential Pitfall 3: Leaking Credentials on GitHub**:
  - *Bahaya*: Menyimpan `API_KEY` atau password Supabase langsung di dalam script/notebook.
  - *Mitigasi*: Enforce penggunaan file `.env` yang terdaftar di `.gitignore`, dan gunakan `load_dotenv(override=True)`.
</details>

---

## 6. Data Governance, Ethics & Fairness Assessment
- **Privacy & PII Protection**: Data mutasi riil sering kali memuat nomor rekening, nomor referensi transfer, atau nama pengirim. Sebelum deskripsi dikirim ke LLM, lakukan *regex masking* pada nomor rekening/invoice untuk mematuhi regulasi perlindungan data pribadi (UU PDP).
- **Fairness & Algorithmic Bias**: Memastikan taksonomi kategori finansial seimbang dan mencakup pengeluaran esensial (*Needs*) vs non-esensial (*Wants*).
- **Taxonomy Standards**: Kategori baku: `[F&B, Transportasi, Utilitas, Hiburan, Belanja, Perawatan Kendaraan, Transfer/Tarik Tunai, Kebutuhan Rumah Tangga, Lainnya]`.
