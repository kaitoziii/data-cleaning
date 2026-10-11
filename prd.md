# PRD: Dataset Nilai Tukar Rupiah 1995–2026

## 1. Tujuan
Membangun tools scraping/pengumpulan data untuk menghasilkan dataset nilai tukar rupiah (IDR) terhadap mata uang asing dari **1995 sampai 2026**, dalam format **CSV**, di mana **setiap baris data wajib menyertakan sumbernya**.

## 2. Ruang Lingkup
**Termasuk**
- Pasangan utama: USD/IDR. Opsional tahap berikutnya: EUR, JPY, SGD, AUD.
- Data harian bila tersedia; bila hanya bulanan/tahunan, disimpan apa adanya dengan kolom `frequency`.
- Penggabungan beberapa sumber dengan aturan prioritas yang transparan.

**Tidak termasuk**
- Data intraday / tick.
- Prediksi atau analisis kurs.
- Redistribusi data dari sumber yang lisensinya melarang.

## 3. Sumber Data
Cakupan dan format tiap sumber **harus diverifikasi saat implementasi**; jangan berasumsi.

| Prioritas | Sumber | Kegunaan |
|---|---|---|
| 1 | Bank Indonesia (JISDOR, kurs transaksi BI) | Data resmi harian periode modern |
| 2 | Data historis BI/SEKI, IMF IFS, World Bank | Periode lama (1995–2000-an), kemungkinan bulanan/tahunan |
| 3 | Yahoo Finance (USDIDR=X) | Penambal celah harian periode 2000-an dst. |

Aturan: utamakan API/unduhan resmi; scraping HTML hanya bila tidak ada alternatif. Hormati `robots.txt` dan ketentuan penggunaan tiap situs.

## 4. Skema Dataset Final (`kurs_idr.csv`)

| Kolom | Tipe | Keterangan |
|---|---|---|
| `date` | date | YYYY-MM-DD (untuk data bulanan: tanggal akhir periode, tandai di `frequency`) |
| `pair` | string | Contoh `USD/IDR` |
| `rate_type` | string | `tengah`, `jual`, `beli`, `jisdor`, `close` |
| `rate` | decimal | Nilai kurs (IDR per 1 unit mata uang asing) |
| `frequency` | string | `daily`, `monthly`, `yearly` |
| `source_name` | string | **Wajib.** Contoh `Bank Indonesia` |
| `source_url` | string | **Wajib.** URL halaman/endpoint asal data |
| `retrieved_at` | datetime | **Wajib.** Waktu fetch (UTC, ISO 8601) |
| `is_filled` | bool | `true` bila nilai hasil forward-fill (hari libur/akhir pekan) |
| `filled_from_date` | date | Tanggal data asli bila `is_filled = true` |
| `notes` | string | Opsional, contoh "rezim band terkendali (sebelum 14 Agu 1997)" |

Tidak boleh ada baris tanpa `source_name`, `source_url`, dan `retrieved_at`.

## 5. Output Tambahan
- `kurs_idr_all_observations.csv`: satu baris per sumber per tanggal (tanpa penimpaan), skema sama dengan di atas.
- `raw/`: snapshot mentah tiap fetch, nama file memuat sumber dan tanggal unduh.
- `SOURCES.md`: daftar sumber, cakupan periode, lisensi/ketentuan penggunaan, dan tanggal terakhir diverifikasi.

## 6. Aturan Penggabungan
1. Semua observasi dari semua sumber masuk ke tabel `all_observations`.
2. Tabel final dibentuk dengan memilih satu observasi per (`date`, `pair`, `rate_type`) berdasarkan prioritas sumber pada bagian 3.
3. Jangan mencampur `rate_type` berbeda dalam satu seri tanpa penanda.
4. Bila dua sumber berbeda lebih dari ambang (default 1%) pada tanggal yang sama, catat ke `reports/discrepancies.csv` untuk ditinjau manual.

## 7. Validasi
- Tidak ada duplikat (`date`, `pair`, `rate_type`) di tabel final.
- Tidak ada nilai kosong/nol/negatif pada `rate`.
- Deteksi lonjakan harian tidak wajar (default > 15%) dan laporkan, jangan hapus otomatis. Krisis 1997–1998 adalah lonjakan nyata, jadi perlu ditinjau manual.
- Laporan celah tanggal (hari kerja tanpa data).
- Setiap baris lolos pengecekan kolom sumber wajib.

## 8. Persyaratan Non-Fungsional
- Dapat dijalankan ulang (idempoten) dan bisa dilanjutkan bila gagal di tengah (resume).
- Jeda antar request dan batas laju yang sopan; sertakan User-Agent yang jelas.
- Log setiap fetch: URL, status, waktu, jumlah baris.

## 9. Milestone
1. Riset & verifikasi sumber, isi `SOURCES.md`.
2. Fetcher per sumber + penyimpanan raw.
3. Normalisasi & skema.
4. Penggabungan + validasi + laporan.
5. Ekspor CSV final + dokumentasi.

## 10. Kriteria Sukses
- Cakupan USD/IDR dari 1995 sampai 2026 tanpa celah yang tidak terjelaskan.
- 100% baris memiliki sumber, URL, dan waktu retrieval.
- Semua celah/selisih antar sumber terdokumentasi.
- Dataset dapat direproduksi dari `raw/` dengan satu perintah.

## 11. Risiko
- Struktur situs sumber berubah atau memblokir scraping → simpan raw, siapkan sumber cadangan.
- Data periode lama hanya bulanan/tahunan → tandai lewat `frequency`, jangan diinterpolasi diam-diam.
- Lisensi sumber membatasi redistribusi → catat di `SOURCES.md` dan tinjau sebelum publikasi.
