"""Spec v12b (docs/spec-v12b-fvg-fresh.md): the FVG-limit candidate, frozen, on EUR/USD and silver.

    python -m backtest.fvg_fresh
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest import run as engine_run  # noqa: E402
from backtest.pattern_stats import ore_rules  # noqa: E402
from engine import config as K  # noqa: E402

FRESH = {"EURUSD": {"spread": 0.00010, "pip": 0.0001, "file": "data/eurusd-m1-bid-2021-11-01-2026-11-19.zip"},
         "XAGUSD": {"spread": 0.025, "pip": 0.001, "file": "data/xagusd-m1-bid-2021-11-01-2026-11-19.zip"}}
YEARS = range(2022, 2027)


def main() -> int:
    K.PAIRS.update(FRESH)
    parts = []
    for pair in FRESH:
        for per in ("design", "check", "final"):
            df, _ = engine_run.run_pair(pair, per)
            parts.append(df)
    d = pd.concat(parts, ignore_index=True)
    d.to_csv(ROOT / "backtest" / "out" / "fvg_fresh_trades.csv", index=False)
    d = d[ore_rules(d) & (d["status"] == "filled") & (d["stop_type"] == "S1p") & (d["mgmt"] == "M2_T2")]
    d["year"] = pd.to_datetime(d["decision_time"], utc=True).dt.year
    out = {}
    for e in ("E3", "E2", "E1", "E4", "E5"):
        x = d[d["entry_type"] == e].sort_values("decision_time").drop_duplicates(["pair", "range_tf", "range_open", "direction"])
        r = x["R"]
        yr = x.groupby("year")["R"].mean()
        hit = (x["exit_reason"] == "target").mean() * 100          # far side reached (rest of position)
        ch = (1 / (1 + x["rr_T2"])).mean() * 100
        out[e] = {"setups": len(x), "avg": r.mean(), "t": r.mean() / (r.std() / np.sqrt(len(r))) if len(r) > 1 else np.nan,
                  "years+": int(sum(1 for y in YEARS if yr.get(y, np.nan) > 0)), "far hit%": hit, "chance%": ch,
                  "pairs": x.groupby("pair")["R"].mean().round(3).to_dict(), "years": yr.round(3).to_dict()}
        print(e, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in out[e].items()})
    e3 = out["E3"]
    ok = e3["avg"] > 0 and e3["years+"] >= 3 and e3["far hit%"] >= e3["chance%"] and e3["setups"] >= 40
    print(f"\nPASS RULE (E3): avg>0 {e3['avg'] > 0} | 3+ of 5 years {e3['years+'] >= 3} | far hit >= chance "
          f"{e3['far hit%'] >= e3['chance%']} | 40+ setups {e3['setups'] >= 40} -> {'PASS' if ok else 'FAIL'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
