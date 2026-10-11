"""Bank Indonesia JISDOR (Jakarta Interbank Spot Dollar Rate). Prioritas 1.

BI menutup endpoint JSON publik di balik WAF (302). Halaman JISDOR merender
tabel ~10 hari kerja terakhir, jadi HTML scraping dipakai karena tidak ada
alternatif resmi yang bisa diakses (PRD bagian 3: scraping hanya bila perlu).
"""
from __future__ import annotations

import datetime as dt
import re

from bs4 import BeautifulSoup

from .. import http
from ..normalize import row

SOURCE = "bank_indonesia"
NAME = "Bank Indonesia"
URL = "https://www.bi.go.id/en/statistik/informasi-kurs/jisdor/Default.aspx"

_ROW = re.compile(r"^\s*(?P<date>\d{1,2} \w+ \d{4})\s+Rp\s*(?P<rate>[\d.,]+)\s*$")


def parse(html: bytes, retrieved_at: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[dict] = []
    for tr in soup.find_all("tr"):
        text = " ".join(tr.get_text(" ", strip=True).split())
        m = _ROW.match(text)
        if not m:
            continue
        when = dt.datetime.strptime(m.group("date"), "%d %B %Y").date().isoformat()
        rate = float(m.group("rate").replace(",", ""))
        out.append(
            row(
                date=when,
                pair="USD/IDR",
                rate_type="jisdor",
                rate=rate,
                frequency="daily",
                source_name=NAME,
                source_url=URL,
                retrieved_at=retrieved_at,
                notes="JISDOR BI",
            )
        )
    return out


def fetch(from_raw: bool = False) -> list[dict]:
    raw, retrieved_at = http.fetch(SOURCE, URL, ext="html", from_raw=from_raw)
    return parse(raw, retrieved_at)
