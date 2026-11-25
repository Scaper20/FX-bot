"""History of the order-block strategy's option for the live cards, from the spec v16 backtest
(H1, D1+H4 bias, limit at the order block's open, 3R, after Ore's spreads).

    python scripts/build_smc_stats.py      -> engine/data/smc_stats.json
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "engine" / "data" / "smc_stats.json"


def main() -> int:
    out = {}
    for pair in ("GBPUSD", "XAUUSD"):
        d = pd.read_csv(ROOT / "backtest" / "out" / f"smc_{pair}_H1.csv")
        d = d[d["bias_both"] & (d["entry"] == "E4")]
        t = pd.to_datetime(d["time"], unit="ns", utc=True)
        out[pair] = {"n": int(len(d)), "avg_R": round(float(d["R"].mean()), 3),
                     "win_rate": round(float((d["R"] > 0).mean()), 3), "first": t.min().isoformat(),
                     "last": t.max().isoformat(), "enough": bool(len(d) >= 30),
                     "score": round(float(d["R"].mean()), 3)}
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
