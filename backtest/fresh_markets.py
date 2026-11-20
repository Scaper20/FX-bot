"""Spec v10 (docs/spec-v10-fresh-markets.md): the frozen v9 candidate on EUR/USD and silver.

    python -m backtest.fresh_markets
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.breaker_filters import FRESH, run_pair  # noqa: E402

OUT = ROOT / "backtest" / "out"
RULE = ["F1L", "F2L", "F3L", "msnr"]


def rowstats(x):
    r = x["R"].dropna()
    y = x[x["hit_T2"].notna()]
    p = y["p_T2"]
    yr = x.assign(year=pd.to_datetime(x["time"], utc=True).dt.year).groupby("year")["R"].mean()
    return {"trades": len(r), "avg R": r.mean() if len(r) else np.nan,
            "T2 hit%": y["hit_T2"].mean() * 100 if len(y) else np.nan, "T2 chance%": p.mean() * 100 if len(y) else np.nan,
            "z T2": (y["hit_T2"].sum() - p.sum()) / np.sqrt((p * (1 - p)).sum()) if len(y) else np.nan,
            **{str(k): v for k, v in yr.items()}}


def main() -> int:
    rows = []
    for pair in FRESH:
        rows += run_pair(pair, FRESH)
        print(pair, "done", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "fresh_markets_trades.csv", index=False)
    m = np.logical_and.reduce([df[f].astype(bool) for f in RULE]) & (df["tf"] == "H4")
    out = []
    for stop in ("classic", "tight"):
        for entry in ("edge", "confirm", "mid"):
            x = df[m & (df["entry"] == entry) & (df["stop"] == stop)]
            out.append({"row": f"H4 {entry} {stop}", "market": "both", **rowstats(x)})
            for pair in FRESH:
                out.append({"row": f"H4 {entry} {stop}", "market": pair, **rowstats(x[x["pair"] == pair])})
    t = pd.DataFrame(out)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 20)
    print(t.round(3).to_string(index=False))
    both = t[(t["market"] == "both") & t["row"].str.endswith("classic")].set_index("row")
    edge = both.loc["H4 edge classic"]
    c1 = edge["avg R"] > 0
    c2 = int((both["avg R"] > 0).sum()) >= 2
    c3 = edge["T2 hit%"] >= edge["T2 chance%"]
    print(f"\nPASS rule: edge classic avg>0: {c1} | 2 of 3 classic rows >0: {c2} | edge T2 >= chance: {c3} "
          f"| trades edge {int(edge['trades'])} -> {'PASS' if c1 and c2 and c3 else 'FAIL'}")
    t.to_csv(OUT / "fresh_markets_summary.csv", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
