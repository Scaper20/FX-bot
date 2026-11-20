"""SMT test (docs/spec-v2-smt.md): GBP/USD vs EUR/USD, gold vs silver.

    python -m backtest.smt              # Design (2021-11 .. 2023-12)
    python -m backtest.smt --check      # 2024, only if Design passed
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.search import scan, stats  # noqa: E402
from engine import config as K  # noqa: E402
from engine.candles import clean, load_m1_csv  # noqa: E402

PARTNER = {"GBPUSD": "data/eurusd-m1-bid-2021-11-01-2026-11-19.zip",
           "XAUUSD": "data/xagusd-m1-bid-2021-11-01-2026-11-19.zip"}
START, END = pd.Timestamp("2021-11-01", tz="UTC"), pd.Timestamp("2025-01-01", tz="UTC")   # 2025+ never loaded


def load(path):
    m1, _ = clean(load_m1_csv(ROOT / path))
    return m1[(m1.index >= START - pd.Timedelta("150D")) & (m1.index < END)]


def table(df, period_end):
    d = df[(df["time"] < period_end) & df["smt_known"]]
    out = []
    for (base, tf), g in d.groupby(["base", "tf"]):
        hit, p, R = (np.array(g[k], dtype=float) for k in ("hit_T1", "p_T1", "R"))
        for label, m in (("SMT", g["smt"].to_numpy(bool)), ("no SMT", ~g["smt"].to_numpy(bool)),
                         ("SMT + HTF bias", (g["smt"] & g["htf_bias"]).to_numpy(bool))):
            n, z, r = stats(hit, p, R, m)
            x = g[m & ~np.isnan(hit)]
            out.append({"entry": base, "tf": tf, "group": label, "trades": n,
                        "T1 hit%": x["hit_T1"].mean() * 100 if n else np.nan,
                        "T1 chance%": x["p_T1"].mean() * 100 if n else np.nan, "z": z, "avg R after spread": r,
                        "GBPUSD z": stats(hit, p, R, m & (g["pair"] == "GBPUSD").to_numpy())[1],
                        "XAUUSD z": stats(hit, p, R, m & (g["pair"] == "XAUUSD").to_numpy())[1]})
    return pd.DataFrame(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    rows = []
    for pair in K.PAIRS:
        m1, _ = clean(load_m1_csv(ROOT / K.PAIRS[pair]["file"]))
        m1 = m1[(m1.index >= START - pd.Timedelta("150D")) & (m1.index < END)]
        rows += scan(m1, pair, partner=load(PARTNER[pair]))
    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df.to_csv(ROOT / "backtest" / "out" / "smt_trades.csv", index=False)
    pd.set_option("display.width", 220)
    if a.check:
        d = df[df["time"] >= pd.Timestamp("2024-01-01", tz="UTC")]
        print("CHECK 2024"); print(table(d, END).round(2).to_string(index=False))
    else:
        print("DESIGN Nov 2021 - Dec 2023")
        print(table(df, pd.Timestamp("2024-01-01", tz="UTC")).round(2).to_string(index=False))
        known = df[df["time"] < pd.Timestamp("2024-01-01", tz="UTC")]
        print(f"\nSMT found on {known['smt'].mean():.0%} of CRTs (partner candle matched on {known['smt_known'].mean():.0%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
