"""Export CSV (PRD bagian 4-5). UTF-8, header baris pertama, koma, titik desimal.

Juga membuat `kurs_idr_dirty_demo.csv`: salinan sengaja dikotori untuk tugas
pembelajaran (kriteria "masalah data"). File ini SINTETIS dan dilabeli di kolom
`notes`; `kurs_idr.csv` tetap bersih.
"""
from __future__ import annotations

import pandas as pd

from .config import COLUMNS, DATA_DIR, REPORTS_DIR

# (baris di file, kolom, nilai_baru, jenis_masalah)
DEMO_INJECTIONS = [
    (500, "rate", "", "missing_value"),
    (1500, "source_url", "", "missing_value"),
    (600, "pair", "usd/idr", "inkonsistensi_kategori"),
    (700, "rate_type", "Close", "inkonsistensi_kategori"),
    (800, "source_name", "yahoo finance", "inkonsistensi_kategori"),
    (900, "frequency", "Daily", "inkonsistensi_kategori"),
    (1000, "rate", "17,884.00", "tipe_data_salah"),
    (1100, "date", "09/10/2026", "tipe_data_salah"),
]
DEMO_DUPLICATES = [200, 300]


def _write(df: pd.DataFrame, name: str) -> str:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / name
    df.to_csv(path, index=False, encoding="utf-8")
    return str(path)


def dirty_demo(final: pd.DataFrame, path=None) -> str:
    df = final[COLUMNS].copy()
    for col in ("date", "pair", "rate_type", "rate", "frequency",
                "source_name", "source_url"):
        df[col] = df[col].astype(object)

    issues: list[tuple] = []
    name = "kurs_idr_dirty_demo.csv"

    for line, col, val, kind in DEMO_INJECTIONS:
        i = line - 2
        if not 0 <= i < len(df):
            continue
        df.at[i, col] = val
        df.at[i, "notes"] = f"DEMO SINTETIS [{kind}] kolom {col}: {df.at[i, 'notes']}"
        issues.append((f"data/{name}", line, col, kind, "disuntik sengaja, bukan data asli"))

    n_before = len(df)
    for k, line in enumerate(DEMO_DUPLICATES):
        i = line - 2
        if not 0 <= i < n_before:
            continue
        # salinan persis (tanpa label apa pun) supaya terdeteksi df.duplicated().
        # Lokasinya dicatat di reports/issues.csv.
        df = pd.concat([df, df.iloc[[i]]], ignore_index=True)
        issues.append((f"data/{name}", n_before + k + 2, "(baris utuh)", "duplikat",
                       f"salinan identik dari baris {line}"))

    if path is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        path = DATA_DIR / name
    df.to_csv(path, index=False, encoding="utf-8")

    if issues:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        out = REPORTS_DIR / "issues.csv"
        header = not out.exists() or out.stat().st_size == 0
        with out.open("a", encoding="utf-8") as fh:
            if header:
                fh.write("file,baris,kolom,jenis_masalah,keterangan\n")
            for row in issues:
                fh.write(",".join('"' + str(c).replace('"', '""') + '"' for c in row) + "\n")
    return str(path)


def export(final: pd.DataFrame, observations: pd.DataFrame) -> dict:
    return {
        "final": _write(final[COLUMNS], "kurs_idr.csv"),
        "all": _write(observations[COLUMNS], "kurs_idr_all_observations.csv"),
        "demo": dirty_demo(final),
    }
