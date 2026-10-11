"""Merge (PRD bagian 6). Semua observasi masuk all_observations; tabel final
memilih satu observasi per (date, pair, rate_type) menurut prioritas sumber."""
from __future__ import annotations

import pandas as pd

from .config import COLUMNS, SOURCE_PRIORITY
from .normalize import frame


def all_observations(rows: list[dict]) -> pd.DataFrame:
    df = frame(rows)
    if df.empty:
        return df
    # satu baris per sumber per (date, pair, rate_type) — jangan menimpa antar sumber
    return df.drop_duplicates(subset=["date", "pair", "rate_type", "source_name"], keep="last")


def final(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    ranked = df.copy()
    ranked["_prio"] = ranked["source_name"].map(SOURCE_PRIORITY).fillna(99)
    ranked = ranked.sort_values(["_prio", "retrieved_at"])
    ranked = ranked.drop_duplicates(subset=["date", "pair", "rate_type"], keep="first")
    ranked = ranked.drop(columns="_prio")
    return ranked[COLUMNS].sort_values(["date", "pair", "rate_type"]).reset_index(drop=True)
