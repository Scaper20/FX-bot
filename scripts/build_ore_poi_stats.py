"""Card history for the live Ore's-model strategy (spec v26) from backtest/out/v26_trades.csv
(python -m backtest.ore_v26 first): the exact live rules, entry chosen at decision time.

    python scripts/build_ore_poi_stats.py     -> 'ore_poi' in engine/data/smc_v22_stats.json
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.ore_v26 import OUT  # noqa: E402
from backtest.patterns import FRESH, MAIN  # noqa: E402
from backtest.smc_v22 import STATS  # noqa: E402

x = pd.read_csv(OUT)
x = x[x["filled"].astype(bool)]
fr = x[x["pair"].isin(FRESH)]
st = json.loads(STATS.read_text())
st["ore_poi"] = {}
for pair, g in x[x["pair"].isin(MAIN)].groupby("pair"):
    st["ore_poi"][pair] = {"n": int(len(g)), "avg_R": round(float(g["R"].mean()), 3),
                           "win_rate": round(float((g["R"] > 0).mean()), 3),
                           "first": pd.Timestamp(int(g["t_dec"].min()), tz="UTC").isoformat(),
                           "last": pd.Timestamp(int(g["t_dec"].max()), tz="UTC").isoformat(),
                           "enough": bool(len(g) >= 30), "score": round(float(g["R"].mean()), 3),
                           "fresh_avg_R": round(float(fr["R"].mean()), 3), "fresh_n": int(len(fr))}
STATS.write_text(json.dumps(st, indent=1))
print(json.dumps(st["ore_poi"], indent=1))
