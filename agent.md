# AGENT.md

Panduan untuk agen/AI coding yang mengerjakan proyek **Dataset Nilai Tukar Rupiah 1995–2026**. Baca `PRD.md` terlebih dahulu; dokumen itu adalah sumber kebenaran untuk skema dan aturan.

## Aturan Utama (tidak boleh dilanggar)
1. **Setiap baris data harus punya `source_name`, `source_url`, dan `retrieved_at`.** Sumber ditempel saat fetch pertama, bukan ditambahkan belakangan.
2. **Jangan mengarang atau menginterpolasi data diam-diam.** Nilai hasil isi-ulang harus ditandai `is_filled = true` beserta `filled_from_date`.
3. **Jangan menimpa observasi antar sumber.** Semua observasi disimpan di `all_observations`; tabel final diturunkan dengan aturan prioritas.
4. **Simpan data mentah** di `raw/` untuk setiap fetch sebelum diolah.
5. **Jangan mencampur `rate_type`** (tengah/jual/beli/jisdor/close) dalam satu seri tanpa penanda.
6. Jangan menghapus outlier otomatis; laporkan ke `reports/`.

## Etika Scraping
- Utamakan API atau unduhan resmi daripada scraping HTML.
- Cek `robots.txt` dan ketentuan penggunaan sebelum menambah sumber baru.
- Beri jeda antar request, gunakan retry dengan backoff, dan sertakan User-Agent yang jelas.
- Cache respons agar tidak mengunduh ulang tanpa perlu.

## Stack yang Disarankan
- Python 3.11+, `requests` (atau `httpx`), `beautifulsoup4`, `pandas`, `pytest`.
- Tidak wajib mengikuti persis; ubah bila ada alasan jelas dan catat di README.

## Struktur Proyek
```
.
├── PRD.md
├── AGENT.md
├── SOURCES.md              # sumber, cakupan, lisensi, tanggal verifikasi
├── src/
│   ├── fetchers/           # satu modul per sumber
│   ├── normalize.py
│   ├── merge.py
│   ├── validate.py
│   └── export.py
├── raw/                    # snapshot mentah: <sumber>_<tanggal-unduh>.<ext>
├── data/
│   ├── kurs_idr.csv
│   └── kurs_idr_all_observations.csv
├── reports/                # celah tanggal, lonjakan, selisih antar sumber
└── tests/
```

## Alur Kerja
1. Tambah/ubah fetcher di `src/fetchers/` (satu sumber = satu modul, mengembalikan baris dengan kolom sumber sudah terisi).
2. Normalisasi: format tanggal ke ISO, angka (pemisah ribuan/desimal), nama kolom, tipe data.
3. Gabungkan sesuai prioritas di PRD bagian 3 dan 6.
4. Jalankan validasi (PRD bagian 7); jangan lanjut ekspor bila ada pelanggaran aturan sumber wajib.
5. Ekspor CSV (UTF-8, header baris pertama, pemisah koma, titik sebagai desimal).

## Definisi Selesai untuk Setiap Perubahan
- Tes lulus, termasuk tes bahwa tidak ada baris tanpa kolom sumber wajib.
- `SOURCES.md` diperbarui bila ada sumber baru atau perubahan cakupan.
- Proses dapat dijalankan ulang dan menghasilkan CSV yang sama dari `raw/`.
- Perubahan dijelaskan singkat di pesan commit atau catatan PR.

## Hal yang Perlu Ditanyakan ke Pemilik Proyek
- Menambah pasangan mata uang di luar USD/IDR.
- Mengubah aturan prioritas sumber atau ambang selisih/lonjakan.
- Menambah sumber yang lisensinya tidak jelas atau melarang scraping.
