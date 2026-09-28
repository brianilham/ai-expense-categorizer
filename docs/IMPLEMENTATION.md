# Implementation Plan and Checklist

> **Aturan Eksekusi**:
> Selesaikan setiap fase secara berurutan. Jangan lanjut ke fase berikutnya sebelum fase saat ini selesai dan terverifikasi melalui pengujian.
> 
> **Traceability**: Setiap fungsi menyertakan ID referensi PRD atau Arsitektur di docstring (contoh: `Ref: PRD-REQ-01`).

---

## Phase 1: Environment Setup and Data Contracts
- [x] **Dependencies**: Tambahkan pustaka baru (`pandera`, `duckdb`, `streamlit`, `plotly`, `pytest`, `faker`) ke `requirements.txt` dan lakukan instalasi.
- [x] **Data Contracts (`src/schemas.py`)**: Tulis skema validasi `RawTransactionSchema`, `CleanedExpenseSchema`, dan `CategorizedExpenseSchema` menggunakan Pandera. *(Ref: ARCH-SCHEMA-01)*
  <details><summary>Mengapa contract-first?</summary>
  Spesifikasi kolom, tipe data, dan batasan nilai (misal nominal >= 0) didefinisikan di awal agar data yang tidak valid langsung ditolak sebelum menyentuh AI atau database.
  </details>
- [x] **Data Generator (`src/data_generator.py`)**: Buat generator transaksi sintetis perbankan Indonesia (BCA, Mandiri, QRIS) untuk menghasilkan 150+ baris data pengujian realistis.

---

## Phase 2: Preprocessing Pipeline and Unit Testing
- [x] **Unit Tests (`tests/test_pipeline.py`)**: Tulis unit test awal menggunakan `pytest` untuk memverifikasi:
  - Penolakan data yang melanggar kontrak skema.
  - Pemfilteran mutasi debit dan konversi nominal menjadi nilai positif.
  - Normalisasi teks deskripsi transaksi (menghapus nomor referensi dan hashtag). *(Ref: PRD-METRIC-01)*
  <details><summary>Mengapa test-driven data science?</summary>
  Menulis tes assert sebelum logika pembersihan data menjamin implementasi memenuhi spesifikasi tanpa asumsi tersembunyi.
  </details>
- [x] **Data Cleaner (`src/preprocessing.py`)**: Implementasikan fungsi `clean_and_filter_expenses()` yang lolos seluruh pengujian unit di atas.

---

## Phase 3: Hybrid Categorization Engine
- [x] **Heuristics Matcher (`src/rules_engine.py`)**:
  - Susun kamus kata kunci dan regex untuk merchant umum (PLN, PDAM, Spotify, Netflix, BPJS, ATM).
  - Kembalikan `(category, "Heuristic_Rules")` dengan latensi di bawah 1 milidetik.
- [x] **LLM Batch Categorizer (`src/llm_categorizer.py`)**:
  - Implementasikan pemanggilan batch Gemini 3.5 Flash Lite untuk sisa transaksi yang tidak cocok dengan aturan Tier-1.
  - Gunakan `transport='rest'` dan format output array JSON terstruktur.
- [x] **Hybrid Orchestrator (`src/categorizer.py`)**:
  - Gabungkan hasil Tier-1 dan Tier-2, pastikan seluruh baris terlabeli. *(Ref: PRD-SOL-01)*
  - Tambahkan unit test untuk memverifikasi integritas hasil penggabungan.

---

## Phase 4: Dual Storage Layer
- [x] **DuckDB Local Engine (`src/db_duckdb.py`)**:
  - Buat fungsi query in-memory DuckDB untuk kalkulasi agregasi cepat (`SELECT category, SUM(amount)...`).
- [x] **Supabase Cloud Sync (`src/db_supabase.py`)**:
  - Buat fungsi pengiriman data ke PostgreSQL Supabase melalui Session Pooler (port 5432).
- [x] **Database Roundtrip Tests**: Pastikan kedua database menyimpan dan membaca DataFrame secara presisi tanpa distorsi format tanggal.

---

## Phase 5: Streamlit Dashboard and Documentation
- [x] **Dashboard Layout (`app.py`)**:
  - Sidebar: Uploader file CSV dan tombol generator data sintetis.
  - Header: Kartu metrik pengeluaran, volume transaksi, rasio heuristik, dan inferensi AI.
  - Panel utama:
    - Grafik breakdown kategori dan tabel ringkasan (asymmetric 70:30).
    - Grafik area pengeluaran harian.
    - Filter kategori dan sumber klasifikasi.
    - Tabel transaksi interaktif dengan tombol sinkronisasi ke Supabase.
- [x] **Dokumentasi Proyek**: Tulis `README.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, dan perbarui checklist implementasi.
