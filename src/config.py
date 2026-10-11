from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw"
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

USER_AGENT = "idr-dataset-bot/1.0 (research dataset; contact: project-owner)"
REQUEST_DELAY = 1.5

# PRD bagian 3. Angka kecil = prioritas lebih tinggi.
SOURCE_PRIORITY = {
    "Bank Indonesia": 1,
    "World Bank": 2,
    "Yahoo Finance": 3,
}

COLUMNS = [
    "date",
    "pair",
    "rate_type",
    "rate",
    "frequency",
    "source_name",
    "source_url",
    "retrieved_at",
    "is_filled",
    "filled_from_date",
    "notes",
]
