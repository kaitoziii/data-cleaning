# SOURCES.md

Sumber data dataset nilai tukar Rupiah (USD/IDR). Cakupan/format diverifikasi
saat implementasi (PRD bagian 3). Status verifikasi: **2026-10-11**.

| Prioritas | Sumber | Endpoint | Cakupan | Frekuensi | `rate_type` | Lisensi / ketentuan |
|---|---|---|---|---|---|---|
| 1 | Bank Indonesia (JISDOR) | `https://www.bi.go.id/en/statistik/informasi-kurs/jisdor/Default.aspx` | ~10 hari kerja terakhir (JISDOR mulai 2013) | daily | `jisdor` | Data publik BI. HTML scraping (tanpa alternatif API yang dapat diakses). |
| 2 | World Bank (PA.NUS.FCRF) | `https://api.worldbank.org/v2/country/IDN/indicator/PA.NUS.FCRF` | 1995–2026 (tahunan) | yearly | `tengah` | API terbuka, data CC-BY 4.0 |
| 3 | Yahoo Finance (USDIDR=X) | `https://query1.finance.yahoo.com/v8/finance/chart/USDIDR=X` | ±2003–sekarang | daily | `close` | API tidak resmi, hanya untuk penggunaan pribadi/riset. |

## Catatan verifikasi
- **Bank Indonesia API JSON** (`/api_public/exchangerate/harian`, `/apilist/...`)
  mengembalikan HTTP 302 (di balik WAF), tidak dapat dipakai tanpa browser.
  Halaman JISDOR dirender server-side dan memuat tabel tanggal–kurs, sehingga
  dipakai sebagai fallback. Risiko: struktur halaman dapat berubah.
- **World Bank** `PA.NUS.FCRF` = "Official exchange rate (LCU per US$, period
  average)" — rata-rata periode (bukan kurs harian). Karena itu `rate_type =
  tengah` dan `frequency = yearly`, tidak dicampur dengan seri harian.
- **Yahoo Finance** mengembalikan JSON OHLC harian; hanya `close` yang dipakai.
  Memerlukan User-Agent jelas. Data historis lama (1995–2000) umumnya kosong,
  peran World Bank di situ.

## Lisensi & redistribusi
Tinjau ketentuan tiap sumber sebelum publikasi (PRD bagian 11). World Bank
CC-BY 4.0 (atribusi). BI dan Yahoo: gunakan sesuai ketentuan situs masing-masing;
jangan redistribusikan data yang melanggar ketentuan sumber.
