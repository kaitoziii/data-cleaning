"""One-command pipeline (PRD, AGENT "Alur Kerja").

    python -m src.run              # fetch all sources, then build dataset
    python -m src.run --from-raw   # rebuild from raw/ snapshots only (reproducible)
"""
from __future__ import annotations

import argparse
import sys

from . import export, merge, validate
from .fetchers import bank_indonesia, worldbank, yahoo

FETCHERS = [bank_indonesia, worldbank, yahoo]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build USD/IDR dataset 1995-2026")
    ap.add_argument("--from-raw", action="store_true", help="use raw/ snapshots, no network")
    args = ap.parse_args(argv)

    rows: list[dict] = []
    for mod in FETCHERS:
        try:
            got = mod.fetch(from_raw=args.from_raw)
        except Exception as exc:  # keep going: another source may cover the gap
            print(f"[warn] {mod.NAME}: {exc}", file=sys.stderr)
            continue
        print(f"[ok] {mod.NAME}: {len(got)} observations")
        rows.extend(got)

    obs = merge.all_observations(rows)
    fin = merge.final(obs)
    findings = validate.check(obs, fin)
    paths = export.export(fin, obs)

    print(f"\nfinal rows      : {len(fin)} -> {paths['final']}")
    print(f"all observations: {len(obs)} -> {paths['all']}")
    print(f"missing source  : {findings['missing_source_rows']}")
    print(f"invalid rate    : {findings['invalid_rate_rows']}")
    print(f"duplicate keys  : {findings['duplicate_keys']}")
    print(f"gaps (weekdays) : {findings['gaps']} -> {findings['gap_report']}")
    print(f"jumps >15%      : {findings['jumps']} -> {findings['jump_report']}")
    print(f"discrepancies   : {findings['discrepancies']} -> {findings['discrepancy_report']}")

    if findings["missing_source_rows"] or findings["invalid_rate_rows"]:
        print("\n[FAIL] provenance/rate validation failed; not a clean export", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
