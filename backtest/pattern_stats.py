"""Historical result of every entry option, for the website's ranking (spec v1.3).

Uses Design + Check trades (Nov 2021 - Dec 2024) with Ore's rules applied
(London/NY sessions, no Friday-late, with daily direction or HTF-backed).
2025-2026 is never read.

    python -m backtest.pattern_stats   -> engine/data/pattern_stats.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "engine" / "data" / "pattern_stats.json"
KEYS = ["pair", "range_tf", "entry_tf", "trigger", "entry_type", "stop_type", "mgmt"]


def ore_rules(d: pd.DataFrame) -> pd.Series:
    backed = d["htf_fvg"].astype(bool) | d["htf_ob"].astype(bool)
    return (d["session"].fillna("").isin(["london", "newyork", "overlap"]) & ~d["friday_late"].astype(bool)
            & ((d["trend_struct"] == "with") | backed))


def key(row) -> str:
    return "|".join(str(row[k]) for k in KEYS)


def main() -> int:
    parts = []
    for per in ("design", "check"):
        d = pd.read_csv(ROOT / "backtest" / "out" / f"trades_{per}.csv", low_memory=False,
                        parse_dates=["decision_time"])
        d = d[(d["status"] == "filled") & d["R"].notna()]
        parts.append(d[ore_rules(d)])
    t = pd.concat(parts, ignore_index=True)
    risk = (t["stop"] - t["entry"]).abs()
    tgt = np.where(t["mgmt"].str.endswith("T3"), t["T3_px"], t["T2_px"])
    t["p_chance"] = risk / (risk + (t["entry"] - tgt).abs())
    out = {}
    for k, g in t.groupby(KEYS):
        out["|".join(map(str, k))] = {
            "n": int(len(g)),
            "avg_R": round(float(g["R"].mean()), 3),
            "win_rate": round(float((g["R"] > 0).mean()), 3),
            "target_rate": round(float((g["exit_reason"] == "target").mean()), 3),
            "chance_rate": round(float(g["p_chance"].mean()), 3),
            "first": g["decision_time"].min().strftime("%Y-%m-%d"),
            "last": g["decision_time"].max().strftime("%Y-%m-%d"),
        }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    meta = {"_meta": {"period": "2021-11-01 to 2024-12-31", "rules": "spec v1.3 recommended filters, body-close CRT (v1.4)",
                      "trades": int(len(t)), "setups": int(t.groupby(["pair", "decision_time"]).ngroups)}}
    OUT.write_text(json.dumps({**meta, **out}, indent=0))
    print(f"{len(out)} option patterns from {len(t)} trades -> {OUT.relative_to(ROOT)}")
    best = sorted(((v["avg_R"], k, v["n"]) for k, v in out.items() if v["n"] >= 30), reverse=True)[:8]
    for r, k, n in best:
        print(f"  {k}: avg {r:+.3f} R over {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
