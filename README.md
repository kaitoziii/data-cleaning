# Dataset Nilai Tukar Rupiah 1995–2026

Pipeline pengumpulan/normalisasi USD/IDR. Skema & aturan: lihat `prd.md`.
Panduan kontribusi: `agent.md`. Daftar sumber: `SOURCES.md`.

## Struktur
```
src/
  config.py     # path, User-Agent, prioritas sumber, skema kolom
  http.py       # fetch sopan + cache raw + log fetch
  normalize.py  # skema baris + stamping sumber
  fetchers/     # bank_indonesia.py, worldbank.py, yahoo.py
  merge.py      # all_observations + final (prioritas sumber)
  validate.py   # celah, lonjakan, selisih antar sumber
  export.py     # CSV final
  run.py        # satu perintah
raw/            # snapshot mentah: <sumber>_<YYYYMMDD>.<ext>
data/
  kurs_idr.csv                        # FINAL (bersih, 6.427 baris)
  kurs_idr_all_observations.csv       # semua observasi, tanpa penimpaan
  kurs_idr_dirty_demo.csv             # SINTETIS, sengaja dikotori (lihat bawah)
reports/
  gaps.csv, jumps.csv, discrepancies.csv, fetch_log.csv
  issues.csv                          # lokasi tiap masalah: file,baris,kolom,jenis
  jisdor_snapshot.json                # hasil konversi HTML BI -> JSON
tests/
```

## Gunanya tiap file di `src/`

| File | Gunanya |
|---|---|
| `config.py` | Semua pengaturan di satu tempat: path folder, User-Agent, jeda antar request, prioritas sumber (BI=1, World Bank=2, Yahoo=3), dan daftar 11 kolom skema PRD. Mau ubah ambang/nama folder? Cukup ubah di sini. |
| `http.py` | "Tangan" yang pegang internet. Kirim request sopan (UA jelas, jeda 1,5 detik, retry + backoff), **simpan jawaban server mentah ke `raw/`** sebelum diolah, sediakan cache untuk `--from-raw`, dan catat log ke `fetch_log.csv`. |
| `normalize.py` | Bikin 1 baris data dengan skema yang benar. Fungsi `row()` juga tempat **provenance ditempel** (`source_name`, `source_url`, `retrieved_at`) — inilah alasan 100% baris punya sumber. |
| `fetchers/` (folder) | Satu sumber = satu file: `bank_indonesia.py`, `worldbank.py`, `yahoo.py`. Masing-masing tahu cara mengunduh + membaca sumbernya lalu mengubahnya jadi baris seragam. |
| `fetchers/__init__.py` | **File kosong.** Penanda supaya folder `fetchers/` dikenali Python sebagai *package*. Tidak ada kode di dalamnya. |
| `merge.py` | Aturan penggabungan (PRD §6). `all_observations()` mengumpulkan semua tanpa menimpa antar sumber; `final()` memilih satu baris terbaik per tanggal menurut prioritas. |
| `validate.py` | Pemeriksa kualitas: kolom sumber wajib, `rate` tidak valid, duplikat, celah hari kerja, lonjakan >15%, selisih antar sumber. Semuanya **dilaporkan ke `reports/`, tidak ada yang dihapus**. |
| `export.py` | Menulis file CSV hasil ke `data/`: final, semua observasi, dan file demo sintetis yang sengaja dikotori untuk tugas. |
| `run.py` | Satu perintah penyambung semua: fetch → gabung → validasi → ekspor → cetak ringkasan. **Ini satu-satunya file yang dijalankan.** |
| `src/__pycache__/` | **Bukan kode.** Folder cache otomatis Python (file `.pyc`) supaya script lebih cepat. Aman dihapus kapan saja, dibuat ulang sendiri. Jangan dimasukkan ke laporan/Git. |

Alurnya:
```
run.py → http.py (unduh ke raw/) → fetchers/ (baca) → normalize.py (bentuk baris)
       → merge.py (gabung + pilih) → validate.py (periksa) → export.py (tulis CSV)
       ↑ semua aturan/path berasal dari config.py
```

## Jalankan
```bash
pip install -r requirements.txt
python -m src.run              # fetch semua sumber lalu bangun dataset
python -m src.run --from-raw   # bangun ulang dari raw/ (tanpa jaringan, reproduksi)
pytest -q
```

## Desain singkat
- **Provenance di-stamp saat fetch** (`normalize.row`), bukan belakangan.
- **Antar sumber tidak saling menimpa**: semua observasi di `all_observations`,
  tabel final dipilih per `(date, pair, rate_type)` menurut `SOURCE_PRIORITY`.
- **`rate_type` tidak dicampur**: JISDOR (BI) / `close` (Yahoo) / `tengah`
  (World Bank) hidup sebagai baris terpisah.
- **Idempoten & resume**: respons di-cache di `raw/<sumber>_<tanggal>.<ext>`;
  re-run di hari yang sama memakai cache; `--from-raw` untuk reproduksi.
- **Tidak ada data karang-karangan**: tidak ada interpolasi diam-diam; kolom
  `is_filled`/`filled_from_date` disimpan untuk pengisian yang ditandai.

## Catatan
- BI JISDOR hanya ~10 hari kerja terakhir (API JSON diblokir WAF) — lihat `SOURCES.md`.
- Celah hari kerja dilaporkan di `reports/gaps.csv`, bukan diisi otomatis.
- Perubahan pasangan mata uang/aturan prioritas/ambang: tanyakan dulu (agent.md).

## Kolom `filled_from_date` (sengaja kosong)
PRD bagian 4 mensyaratkan kolom `filled_from_date` tetap ada; nilainya hanya diisi
bila `is_filled = true`. Pipeline ini **tidak melakukan forward-fill apa pun**, jadi
seluruh isi kolom kosong dan `is_filled` seluruhnya `false` — ini kondisi yang benar,
bukan kehilangan data. Celah justru dilaporkan di `reports/gaps.csv`.

## `data/kurs_idr_dirty_demo.csv` — SINTETIS
Salinan `kurs_idr.csv` yang **sengaja dikotori** untuk tugas pembelajaran
(kriteria "minimal 4 jenis masalah data"). Isinya:

| Jenis | Jumlah | Lokasi |
|---|---|---|
| `missing_value` (NaN) | 2 | baris 500 (`rate`), 1500 (`source_url`) |
| `duplikat` (baris persis) | 2 | baris 6429, 6430 (salinan baris 200, 300) |
| `inkonsistensi_kategori` | 4 | baris 600 `usd/idr`, 700 `Close`, 800 `yahoo finance`, 900 `Daily` |
| `tipe_data_salah` | 2 | baris 1000 `rate` = "17,884.00", 1100 `date` = "09/10/2026" |

Semua baris yang disuntik ditandai di kolom `notes` (`DEMO SINTETIS [...]`), **kecuali
duplikat** yang harus identik persis agar terdeteksi `df.duplicated()`.
Lokasi lengkap: `reports/issues.csv`.

⚠️ File ini **bukan hasil scraping**. Dataset asli ada di `data/kurs_idr.csv`
dan tetap bersih (0 duplikat, 0 nilai kosong pada `rate`).
