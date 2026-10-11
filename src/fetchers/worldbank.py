"""World Bank, indikator PA.NUS.FCRF (Official exchange rate, LCU per US$, period
average). Prioritas 2 untuk periode lama. API terbuka (CC-BY 4.0), tahunan.
"""
from __future__ import annotations

import json

from .. import http
from ..normalize import row

SOURCE = "worldbank"
NAME = "World Bank"
YEAR_START, YEAR_END = 1995, 2026
URL = (
    "https://api.worldbank.org/v2/country/IDN/indicator/PA.NUS.FCRF"
    f"?format=json&per_page=200&date={YEAR_START}:{YEAR_END}"
)


def parse(payload: bytes, retrieved_at: str) -> list[dict]:
    body = json.loads(payload)
    observations = body[1] if len(body) > 1 else []
    out: list[dict] = []
    for obs in observations:
        if obs.get("value") is None:
            continue
        year = int(obs["date"])
        out.append(
            row(
                date=f"{year}-12-31",
                pair="USD/IDR",
                rate_type="tengah",
                rate=obs["value"],
                frequency="yearly",
                source_name=NAME,
                source_url=URL,
                retrieved_at=retrieved_at,
                notes="World Bank PA.NUS.FCRF, official exchange rate period average",
            )
        )
    return out


def fetch(from_raw: bool = False) -> list[dict]:
    raw, retrieved_at = http.fetch(SOURCE, URL, ext="json", from_raw=from_raw)
    return parse(raw, retrieved_at)
