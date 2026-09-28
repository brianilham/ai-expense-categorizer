# AI-Augmented Expense Categorizer - Implementation Plan & Checklist

> **⚠️ Aturan SDD (Iterative State Machine)**:
> Jangan mulai Phase N+1 jika Phase N belum diselesaikan (ceklis `[x]`). Jika saat pengujian ditemukan kendala atau kegagalan logika, Anda **diizinkan (dan diwajibkan) untuk melakukan backtracking** (menghapus tanda ceklis) untuk merevisi fase sebelumnya.
> 
> **Traceability**: Setiap fungsi Python yang dibuat wajib menyertakan ID referensi PRD/Arsitektur di docstring-nya (contoh: `Ref: PRD-REQ-01`).

---

## Phase 1: Environment Setup & Data Contracts (Pandera-First)
- [x] **Dependencies Installation**: Update `requirements.txt` dan install pustaka baru (`pandera`, `duckdb`, `streamlit`, `plotly`, `pytest`, `faker`).
- [x] **Data Contract Module (`src/schemas.py`)**: Implementasikan skema validasi `RawTransactionSchema` dan `CategorizedTransactionSchema` menggunakan Pandera. *(Ref: ARCH-SCHEMA-01)*
  <details><summary>💡 Educational Note: Mengapa Contract-First?</summary>
  Dalam Spec-Driven Development, kita mendikte spesifikasi kolom, tipe data, dan batasan validitas (misal nominal >= 0) di awal. Hal ini memastikan data yang cacat langsung ditolak sebelum menyentuh AI atau database.
  </details>
- [x] **Data Generator Module (`src/data_generator.py`)**: Buat generator transaksi sintetis perbankan Indonesia (BCA/Mandiri/QRIS) menghasilkan 150+ baris data realistis untuk pengujian skala besar.

---

## Phase 2: Test-Driven Data Science (TDDS) & Preprocessing Pipeline
- [x] **Test Stubs Definition (`tests/test_pipeline.py`)**: Tulis unit test awal menggunakan `pytest` untuk memverifikasi:
  - Validasi data contract berhasil menolak data rusak.
  - Filter hanya menyisakan mutasi `Debit` dan mengonversi nominal menjadi integer/float positif.
  - Normalisasi teks deskripsi transaksi (pembersihan nomor referensi/noise). *(Ref: PRD-METRIC-01)*
  <details><summary>💡 Educational Note: Mengapa Test-Driven di Data Science?</summary>
  Menulis tes assert sebelum mengimplementasikan logika membersihkan data menjamin kode kita memenuhi spesifikasi bisnis tanpa ada asumsi bias yang tersembunyi.
  </details>
- [x] **Data Cleaner Implementation (`src/preprocessing.py`)**: Implementasikan fungsi `clean_and_filter_expenses()` yang lolos semua pengujian unit di atas.

---

## Phase 3: Hybrid Categorization Engine (Heuristics + Gemini Batching)
- [x] **Heuristics Matcher (`src/rules_engine.py`)**:
  - Bangun kamus kata kunci & regex deterministik untuk merchant umum Indonesia (PLN, PDAM, Spotify, Netflix, BPJS, ATM, dll.).
  - Return `(category, "Heuristic_Rules")` dengan latensi < 1 milidetik.
- [x] **LLM Batch Categorizer (`src/llm_categorizer.py`)**:
  - Implementasikan pemanggilan batching Gemini 3.5 Flash Lite untuk menangani sisa transaksi yang tidak cocok dengan aturan Tier-1.
  - Gunakan `transport='rest'` dan output format JSON array ketat.
- [x] **Hybrid Orchestrator (`src/categorizer.py`)**:
  - Gabungkan hasil Tier-1 dan Tier-2, pastikan 100% baris terlabeli. *(Ref: PRD-SOL-01)*
  - Tambahkan unit test untuk memastikan integritas penggabungan data.

---

## Phase 4: Dual Storage Layer (DuckDB OLAP + Supabase Cloud)
- [x] **DuckDB Local Engine (`src/db_duckdb.py`)**:
  - Buat fungsi in-memory / persistent DuckDB untuk kueri analitik cepat (`SELECT category, SUM(amount)...`).
- [x] **Supabase Cloud Sync (`src/db_supabase.py`)**:
  - Modul pengiriman data ke PostgreSQL Supabase menggunakan Session Pooler (port 5432) dan Session pooling protection.
- [x] **Test Database Roundtrip**: Pastikan kedua database dapat menyimpan dan membaca DataFrame secara presisi tanpa distorsi tipe tanggal.

---

## Phase 5: Streamlit Interactive Dashboard & Portfolio Polish
- [x] **Core Dashboard Layout (`app.py`)**:
  - Sidebar: File Uploader (dukungan upload CSV mutasi bank pengguna) & tombol Generate Data Sintetis.
  - Header: KPI Cards (Total Pengeluaran, Jumlah Transaksi, Rata-rata Harian, Efisiensi Heuristik AI).
  - Main Panel:
    - Grafik Pie / Donut Breakdown Pengeluaran per Kategori (Plotly).
    - Grafik Bar Pengeluaran Harian / Tren Waktu.
    - Filter interaktif berdasarkan Kategori dan Rentang Tanggal.
    - Tabel Data Interaktif dengan tombol Export CSV & Sinkronisasi ke Supabase.
- [x] **Repository Documentation**: Perbarui `README.md` dengan arsitektur diagram, cara instalasi, dan panduan menjalankan dashboard.
