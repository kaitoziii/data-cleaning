"""Yahoo Finance chart API untuk USDIDR=X. Prioritas 3, penambal celah harian.
Rate_type = close (harga penutupan pasar). API tidak resmi.
"""
from __future__ import annotations

import datetime as dt
import json

from .. import http
from ..normalize import row

SOURCE = "yahoo"
NAME = "Yahoo Finance"
TICKER = "USDIDR=X"
PAIR = "USD/IDR"
START = dt.datetime(1995, 1, 1, tzinfo=dt.timezone.utc)
ENDPOINT = f"https://query1.finance.yahoo.com/v8/finance/chart/{TICKER}"


def _url() -> str:
    p1 = int(START.timestamp())
    p2 = int(dt.datetime.now(dt.timezone.utc).timestamp())
    return f"{ENDPOINT}?period1={p1}&period2={p2}&interval=1d"


def parse(payload: bytes, retrieved_at: str) -> list[dict]:
    body = json.loads(payload)
    result = (body.get("chart") or {}).get("result") or []
    if not result:
        return []
    res = result[0]
    stamps = res.get("timestamp") or []
    closes = ((res.get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
    out: list[dict] = []
    for ts, close in zip(stamps, closes):
        if close is None:
            continue
        when = dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc).date().isoformat()
        out.append(
            row(
                date=when,
                pair=PAIR,
                rate_type="close",
                rate=close,
                frequency="daily",
                source_name=NAME,
                source_url=ENDPOINT,
                retrieved_at=retrieved_at,
                notes=f"{TICKER} daily close",
            )
        )
    return out


def fetch(from_raw: bool = False) -> list[dict]:
    raw, retrieved_at = http.fetch(SOURCE, _url(), ext="json", from_raw=from_raw)
    return parse(raw, retrieved_at)
