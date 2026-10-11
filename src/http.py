"""Polite HTTP layer: clear User-Agent, delay, retry/backoff, raw snapshot cache,
and per-fetch logging (PRD bagian 8)."""
from __future__ import annotations

import datetime as dt
import time
from pathlib import Path

import requests

from .config import RAW_DIR, REPORTS_DIR, REQUEST_DELAY, USER_AGENT

FETCH_LOG = REPORTS_DIR / "fetch_log.csv"


def _today() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")


def _log(source: str, url: str, status, rows: int, path: Path) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    header = not FETCH_LOG.exists()
    with FETCH_LOG.open("a", encoding="utf-8") as fh:
        if header:
            fh.write("retrieved_at,source,url,status,rows,raw_file\n")
        fh.write(
            f"{dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')},"
            f"{source},{url},{status},{rows},{path.name}\n"
        )


def raw_path(source: str, ext: str) -> Path:
    return RAW_DIR / f"{source}_{_today()}.{ext}"


def _snapshot_iso(path: Path) -> str:
    """retrieved_at diturunkan dari waktu snapshot raw, bukan waktu re-run,
    agar --from-raw menghasilkan CSV yang identik (reproducible)."""
    ts = dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc)
    return ts.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def cached(source: str, ext: str) -> Path | None:
    """Newest snapshot for a source, if any. Enables --from-raw / resume."""
    if not RAW_DIR.exists():
        return None
    files = sorted(RAW_DIR.glob(f"{source}_*.{ext}"))
    return files[-1] if files else None


def fetch(
    source: str,
    url: str,
    *,
    params: dict | None = None,
    ext: str = "json",
    from_raw: bool = False,
    retries: int = 4,
) -> tuple[bytes, str]:
    path = raw_path(source, ext)
    if path.exists():
        data = path.read_bytes()
        _log(source, url, 200, data.count(b"\n"), path)
        return data, _snapshot_iso(path)

    if from_raw:
        old = cached(source, ext)
        if old is None:
            raise FileNotFoundError(f"raw/{source}_*.{ext} not found (--from-raw)")
        return old.read_bytes(), _snapshot_iso(old)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    last = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=30)
            if resp.status_code == 200:
                path.write_bytes(resp.content)
                _log(source, resp.url, 200, resp.content.count(b"\n"), path)
                time.sleep(REQUEST_DELAY)
                return resp.content, _snapshot_iso(path)
            last = f"HTTP {resp.status_code}"
        except requests.RequestException as exc:  # network hiccup -> backoff
            last = str(exc)
        time.sleep(REQUEST_DELAY * (2**attempt))
    _log(source, url, last, 0, path)
    raise RuntimeError(f"fetch failed for {source}: {last}")
