"""Normalization helpers + canonical row schema (PRD bagian 4)."""
from __future__ import annotations

import pandas as pd

from .config import COLUMNS


def row(
    *,
    date: str,
    pair: str,
    rate_type: str,
    rate: float,
    frequency: str,
    source_name: str,
    source_url: str,
    retrieved_at: str,
    notes: str = "",
    is_filled: bool = False,
    filled_from_date: str = "",
) -> dict:
    """One observation. Source provenance is stamped here at fetch time, never later."""
    return {
        "date": date,
        "pair": pair,
        "rate_type": rate_type,
        "rate": float(rate),
        "frequency": frequency,
        "source_name": source_name,
        "source_url": source_url,
        "retrieved_at": retrieved_at,
        "is_filled": bool(is_filled),
        "filled_from_date": filled_from_date,
        "notes": notes,
    }


def frame(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=COLUMNS)
    if df.empty:
        return df
    df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
    return df
