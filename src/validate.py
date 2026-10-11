"""Validation + reports (PRD bagian 7). Tidak menghapus outlier; hanya melaporkan."""
from __future__ import annotations

import pandas as pd

from .config import COLUMNS, REPORTS_DIR


def _write(df: pd.DataFrame, name: str) -> str:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / name
    df.to_csv(path, index=False)
    return str(path)


def _write_issues(final: pd.DataFrame, jumps: pd.DataFrame, gaps: pd.DataFrame) -> str:
    """Lokasi tiap masalah: file, baris (nomor baris di file CSV, header = 1), kolom,
    jenis masalah, keterangan (kriteria tugas 4)."""
    recs: list[tuple] = []
    src = "data/kurs_idr.csv"

    # missing value: kolom J filled_from_date (diizinkan kosong oleh PRD §4).
    # Di memori nilainya "" (string), di CSV terbaca NaN — keduanya dihitung.
    empty = final["filled_from_date"].fillna("").astype(str).str.strip() == ""
    for line, is_missing in enumerate(empty, start=2):
        if is_missing:
            recs.append((src, line, "filled_from_date", "missing_value",
                         "kosong karena tidak ada forward-fill (PRD §4)"))

    key_to_line = {
        (d, p, rt): i
        for i, (d, p, rt) in enumerate(
            zip(final["date"], final["pair"], final["rate_type"]), start=2
        )
    }

    # outlier lonjakan harian
    if not jumps.empty:
        for _, h in jumps.iterrows():
            line = key_to_line.get((str(h["date"]), h["pair"], h["rate_type"]))
            recs.append((src, line, "rate", "outlier_lonjakan",
                         f"{h['pct_change']:+.1%} vs hari sebelumnya (ambang 15%)"))

    # nilai konstan mencurigakan (identik di >10 tanggal berbeda)
    daily = final[final["frequency"] == "daily"]
    vc = daily["rate"].round(2).value_counts()
    hot = set(vc[vc > 10].index)
    if hot:
        for line, (fr, rate) in enumerate(
            zip(final["frequency"], final["rate"]), start=2
        ):
            v = round(float(rate), 2)
            if fr == "daily" and v in hot:
                recs.append((src, line, "rate", "nilai_konstan",
                             f"nilai {v} identik di {int(vc[v])} tanggal berbeda"))

    # celah hari kerja (barisnya tidak ada; posisi dicatat via tanggal)
    if not gaps.empty:
        for _, g in gaps.iterrows():
            recs.append((src, "", "date", "celah_data",
                         f"hari kerja {g['date']} tanpa data harian"))

    issues = pd.DataFrame(recs, columns=["file", "baris", "kolom", "jenis_masalah", "keterangan"])
    return _write(issues, "issues.csv")


def check(observations: pd.DataFrame, final: pd.DataFrame, *, jump_pct: float = 0.15,
          discrepancy_pct: float = 0.01) -> dict:
    findings: dict = {}

    # 1. kolom sumber wajib tidak boleh kosong (berlaku untuk semua baris final)
    missing = final[["source_name", "source_url", "retrieved_at"]].isna().any(axis=1)
    findings["missing_source_rows"] = int(missing.sum())

    # 2. rate kosong / nol / negatif
    bad_rate = final["rate"].isna() | (final["rate"] <= 0)
    findings["invalid_rate_rows"] = int(bad_rate.sum())

    # 3. duplikat kunci di tabel final
    dup = final.duplicated(subset=["date", "pair", "rate_type"]).sum()
    findings["duplicate_keys"] = int(dup)

    # 4. celah hari kerja pada seri harian
    daily = final[final["frequency"] == "daily"].copy()
    gaps = pd.DataFrame(columns=["date", "pair"])
    jumps = pd.DataFrame(columns=["date", "pair", "rate_type", "rate", "prev_rate", "pct_change"])
    if not daily.empty:
        daily["date"] = pd.to_datetime(daily["date"])
        all_days = pd.date_range(daily["date"].min(), daily["date"].max(), freq="B")
        present = pd.DatetimeIndex(sorted(daily["date"].unique()))
        missing_days = all_days.difference(present)
        gaps = pd.DataFrame({"date": missing_days.date, "pair": "USD/IDR"})

        for (pair, rt), grp in daily.sort_values("date").groupby(["pair", "rate_type"]):
            grp = grp.drop_duplicates("date")
            grp["pct_change"] = grp["rate"].pct_change()
            hits = grp[grp["pct_change"].abs() > jump_pct]
            for _, h in hits.iterrows():
                jumps.loc[len(jumps)] = [
                    h["date"].date(), pair, rt, h["rate"], h["rate"] / (1 + h["pct_change"]),
                    round(h["pct_change"], 4),
                ]
    findings["gaps"] = len(gaps)
    findings["jumps"] = len(jumps)

    # 5. selisih antar sumber pada tanggal yang sama (harian, lintas rate_type).
    # Sumber punya rate_type berbeda (jisdor vs close), jadi bandingkan per
    # (date, pair) di antara observasi harian saja.
    disc = pd.DataFrame(columns=["date", "pair", "rate_types", "sources", "min_rate", "max_rate", "pct_diff"])
    daily_obs = observations[observations["frequency"] == "daily"] if not observations.empty else observations
    if not daily_obs.empty:
        for (day, pair), grp in daily_obs.groupby(["date", "pair"]):
            if grp["source_name"].nunique() < 2:
                continue
            lo, hi = grp["rate"].min(), grp["rate"].max()
            pct = (hi - lo) / lo
            if pct > discrepancy_pct:
                disc.loc[len(disc)] = [day, pair, ",".join(grp["rate_type"].unique()),
                                       ",".join(grp["source_name"].unique()), lo, hi, round(pct, 4)]
    findings["discrepancies"] = len(disc)

    findings["gap_report"] = _write(gaps, "gaps.csv")
    findings["jump_report"] = _write(jumps, "jumps.csv")
    findings["discrepancy_report"] = _write(disc, "discrepancies.csv")
    findings["issues_report"] = _write_issues(final, jumps, gaps)
    return findings
