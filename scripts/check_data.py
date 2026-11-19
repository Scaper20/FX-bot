"""Check 1-minute candle files and build all timeframes.

Usage (from the project folder):
    python scripts/check_data.py data/raw            # report only
    python scripts/check_data.py data/raw --save     # also write data/clean/<SYMBOL>_<TF>.csv
    python scripts/check_data.py data/raw --day-close utc0

Prints, per file: date range, duplicates, bad rows, weekday gaps, candle counts
per timeframe, and candles with fewer 1-minute candles than expected.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import candles as C  # noqa: E402

TFS = ["M5", "M15", "H1", "H4", "D1"]


def symbol_from_name(p: Path) -> str:
    name = p.stem.upper()
    for s in ("GBPUSD", "XAUUSD"):
        if s in name:
            return s
    return name.split("-")[0].split("_")[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--day-close", default="ny17", choices=C.DAY_CLOSES)
    ap.add_argument("--save", action="store_true")
    a = ap.parse_args()

    files = sorted(Path(a.folder).glob("*.csv"))
    if not files:
        print(f"No .csv files in {a.folder}")
        return 1
    out_dir = Path(__file__).resolve().parents[1] / "data" / "clean"
    for f in files:
        sym = symbol_from_name(f)
        print(f"\n===== {f.name}  ({sym}, day close {a.day_close})")
        raw = C.load_m1_csv(f)
        print(C.check(raw).summary())
        m1, info = C.clean(raw)
        print(f"clean: {info}")
        for tf in TFS:
            bars = C.resample(m1, tf, a.day_close)
            full = C.TF_MINUTES[tf]
            thin = bars[bars["m1_count"] < 0.5 * full]
            print(f"  {tf:>3}: {len(bars):>7,} candles, {len(thin):>5,} with under half the expected minutes")
            if a.save:
                out_dir.mkdir(parents=True, exist_ok=True)
                bars.to_csv(out_dir / f"{sym}_{tf}_{a.day_close}.csv")
        if a.save:
            m1.to_csv(out_dir / f"{sym}_M1.csv")
    if a.save:
        print(f"\nSaved to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
