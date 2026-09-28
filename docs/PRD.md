# Product Requirements Document (PRD)

## 1. Problem Statement and Scope
- **Problem Statement**: Riwayat mutasi rekening bank dan dompet digital di Indonesia (BCA, Mandiri, QRIS, GoPay, ShopeePay) menggunakan format teks yang tidak terstandarisasi dan penuh singkatan acak (`TRF KANTIN RAYA`, `QRIS KOPI HOJA`, `WD ATM MANDIRI`). Akibatnya, pemilahan pengeluaran bulanan memerlukan rekapitulasi manual yang memakan waktu.
- **Goal**: Mengotomatiskan klasifikasi mutasi transaksi dari input CSV mentah hingga visualisasi grafik bulanan, mengurangi waktu rekap manual menjadi di bawah 3 detik.
- **Target Audience**: Individu, pekerja lepas, dan pemilik UMKM yang membutuhkan rekap pengeluaran tanpa ketergantungan pada aplikasi berbayar.
- **Scope**:
  - **In-Scope**:
    - Validasi schema mutasi debit/kredit menggunakan kontrak data Pandera.
    - Pembersihan teks keterangan transaksi dan filter khusus mutasi debit (pengeluaran).
    - Pipeline kategorisasi dua tahap: Heuristik Regex (Tier-1) dan Batch Gemini 3.5 Flash Lite (Tier-2).
    - Generator data sintetis untuk 150+ baris mutasi bank Indonesia.
    - Agregasi analitik lokal menggunakan DuckDB dan penyimpanan cloud via Supabase PostgreSQL.
    - Dashboard visualisasi interaktif menggunakan Streamlit.
  - **Out-of-Scope**:
    - Integrasi langsung ke API perbankan (Open Banking berlisensi BI).
    - Training model NLP custom dari nol.

---

## 2. Solution Strategy
- **Pendekatan**: Pipeline analitik hybrid (Rule-Based Heuristic + LLM Batch).
- **Alasan**:
  - Sekitar 40–60% transaksi bulanan memiliki pola berulang yang pasti (`PLN`, `SPOTIFY`, `ATM`, `CARWASH`). Memanggil LLM untuk transaksi ini memperlambat pemrosesan dan membuang kuota API.
  - Transaksi dengan merchant lokal spesifik atau singkatan ambigu (misal kedai kopi via QRIS) membutuhkan penalaran semantik dari LLM.
- **Dampak Arsitektur**: Heuristik lokal menyelesaikan sebagian besar transaksi dalam <1ms tanpa biaya API, sementara Gemini hanya menangani transaksi yang tidak cocok dengan aturan regex.

---

## 3. Success Metrics
- **Akurasi**: >= 95% transaksi terklasifikasi ke kategori yang tepat.
- **Efisiensi Kuota**: Minimal 40% transaksi ditangani oleh Tier-1 Heuristics tanpa memanggil API Gemini.
- **Validasi Kontrak Data**: 100% data lolos verifikasi skema Pandera tanpa nilai negatif atau format tanggal rusak.
- **Cakupan Kategori**: 100% baris transaksi mendapatkan label kategori definitif (tanpa nilai null/NaN).
- **Latensi Pemrosesan**:
  - Pipeline pembersihan dan inferensi selesai dalam < 3 detik untuk 150 baris transaksi.
  - Kueri agregasi dashboard via DuckDB selesai dalam < 10 milidetik.

---

## 4. Data Strategy
- **Format Input**: CSV tabular standar mutasi bank (`Date`, `Amount`, `Type`, `Raw_Description`).
- **Data Generator**: Modul generator berbasis Faker dan daftar merchant lokal Indonesia untuk menghasilkan 150+ baris transaksi realistis (F&B, Utilitas, Transportasi, Hiburan, Belanja, dan Transfer/Tarik Tunai).

---

## 5. Potential Pitfalls and Mitigation
<details>
<summary>Daftar jebakan teknis dan mitigasi</summary>

- **Rate Limiting dan N+1 Query pada LLM**:
  - *Risiko*: Memanggil API per baris dalam loop `for` menimbulkan error 429 dan latensi jaringan yang tinggi.
  - *Mitigasi*: Kelompokkan seluruh deskripsi unik ke dalam satu request batch array JSON ke Gemini.
- **Kerusakan Skema Data (Schema Drift)**:
  - *Risiko*: Kolom nominal terbaca sebagai teks karena pemisah ribuan, atau terdapat nilai minus pada mutasi debit.
  - *Mitigasi*: Validasi data menggunakan Pandera di awal pipeline. Tolak data yang tidak sesuai kontrak sebelum masuk ke tahap pembersihan atau AI.
- **Kredensial Bocor ke Git**:
  - *Risiko*: Menyimpan kunci API atau kredensial database di kode sumber.
  - *Mitigasi*: Simpan seluruh kunci rahasia di file `.env`, daftarkan `.env` ke `.gitignore`, dan sediakan template `.env.example`.
</details>

---

## 6. Data Governance and Taxonomy
- **Privasi Data**: Hapus nomor referensi unik, nomor invoice, dan format hashtag dari teks sebelum dikirim ke prompt LLM untuk melindungi identitas transaksi.
- **Taksonomi Kategori Standar**:
  1. F&B (Food & Beverages)
  2. Belanja (Groceries & Shopping)
  3. Transportasi
  4. Utilitas & Tagihan
  5. Hiburan & Langganan
  6. Kesehatan
  7. Pendidikan
  8. Transfer Keluar
  9. Biaya Admin & Pajak
  10. Lainnya
