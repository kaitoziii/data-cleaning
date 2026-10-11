"""Minimal self-checks (PRD kriteria sukses). Run: pytest -q"""
import json

import pandas as pd

from src import merge, validate
from src.fetchers import bank_indonesia, worldbank, yahoo

JISDOR_HTML = b"""
<table>
  <tr><th>Date</th><th>Rates</th></tr>
  <tr><td>9 October 2026</td><td>Rp17,884.00</td></tr>
  <tr><td>8 October 2026</td><td>Rp17,890.00</td></tr>
</table>
"""

WB_JSON = json.dumps([{}, [
    {"date": "1998", "value": 10013.6225},
    {"date": "1997", "value": 2909.38},
    {"date": "1996", "value": None},
]]).encode()

YF_JSON = json.dumps({"chart": {"result": [{
    "timestamp": [1009843200, 1010016000],
    "indicators": {"quote": [{"close": [9575.0, None]}]},
}]}}).encode()


def test_all_fetchers_stamp_required_source_columns():
    rows = (
        bank_indonesia.parse(JISDOR_HTML, "2026-10-11T00:00:00Z")
        + worldbank.parse(WB_JSON, "2026-10-11T00:00:00Z")
        + yahoo.parse(YF_JSON, "2026-10-11T00:00:00Z")
    )
    assert rows, "expected parsed rows"
    for r in rows:
        assert r["source_name"] and r["source_url"] and r["retrieved_at"]
        assert r["rate"] > 0


def test_parsers_skip_empty_values():
    assert len(worldbank.parse(WB_JSON, "2026-10-11T00:00:00Z")) == 2
    assert len(yahoo.parse(YF_JSON, "2026-10-11T00:00:00Z")) == 1


def test_merge_priority_prefers_lower_rank():
    rows = [
        {"date": "2026-10-09", "pair": "USD/IDR", "rate_type": "tengah", "rate": 1.0,
         "frequency": "daily", "source_name": "Yahoo Finance", "source_url": "u",
         "retrieved_at": "t", "is_filled": False, "filled_from_date": "", "notes": ""},
        {"date": "2026-10-09", "pair": "USD/IDR", "rate_type": "tengah", "rate": 2.0,
         "frequency": "daily", "source_name": "Bank Indonesia", "source_url": "u",
         "retrieved_at": "t", "is_filled": False, "filled_from_date": "", "notes": ""},
    ]
    obs = merge.all_observations(rows)
    assert len(obs) == 2  # no overwrite across sources
    fin = merge.final(obs)
    assert len(fin) == 1 and fin.iloc[0]["source_name"] == "Bank Indonesia"


def test_validate_flags_missing_source():
    df = pd.DataFrame([{
        "date": "2026-10-09", "pair": "USD/IDR", "rate_type": "close", "rate": 17800.0,
        "frequency": "daily", "source_name": None, "source_url": "u",
        "retrieved_at": "t", "is_filled": False, "filled_from_date": "", "notes": "",
    }])
    findings = validate.check(df, df)
    assert findings["missing_source_rows"] == 1


def test_issues_report_records_file_baris_column():
    df = pd.DataFrame([{
        "date": "2026-10-09", "pair": "USD/IDR", "rate_type": "close", "rate": 17800.0,
        "frequency": "daily", "source_name": "Yahoo Finance", "source_url": "u",
        "retrieved_at": "t", "is_filled": False, "filled_from_date": "", "notes": "",
    }])
    findings = validate.check(df, df)
    iss = pd.read_csv(findings["issues_report"])
    assert list(iss.columns) == ["file", "baris", "kolom", "jenis_masalah", "keterangan"]
    # kolom filled_from_date kosong -> tercatat sebagai missing_value
    assert (iss.jenis_masalah == "missing_value").any()


def _fake_final(n: int) -> pd.DataFrame:
    from src.config import COLUMNS
    row = {"date": "2026-01-01", "pair": "USD/IDR", "rate_type": "close", "rate": 17000.0,
           "frequency": "daily", "source_name": "Yahoo Finance", "source_url": "u",
           "retrieved_at": "t", "is_filled": False, "filled_from_date": "", "notes": ""}
    return pd.DataFrame([{**row, "date": f"2026-01-{(i % 28) + 1:02d}"} for i in range(n)],
                        columns=COLUMNS)


def test_dirty_demo_contains_four_problem_types(tmp_path):
    from src.export import dirty_demo

    path = dirty_demo(_fake_final(1600), path=tmp_path / "demo.csv")
    d = pd.read_csv(path)

    assert d.duplicated().sum() >= 2, "harus ada baris duplikat persis"
    assert d.rate.isna().sum() >= 1, "harus ada missing value"
    # inkonsistensi kategori: tiap kategori punya varian kapitalisasi/senar
    assert d.pair.nunique() >= 2, "varian pair"
    assert d.rate_type.nunique() >= 2, "varian rate_type"
    assert d.frequency.nunique() >= 2, "varian frequency"
    assert d.source_name.nunique() >= 2, "varian source_name"
    assert d.iloc[998]["rate"] == "17,884.00", "rate berupa teks (tipe data salah)"
    assert d.iloc[1098]["date"] == "09/10/2026", "format tanggal berbeda (tipe data salah)"
    # label sintetis harus terbaca
    assert d.notes.astype(str).str.contains("DEMO SINTETIS").any()
