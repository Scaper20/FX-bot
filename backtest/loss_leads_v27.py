"""Spec v27 (docs/spec-v27-loss-leads.md): CRT overlap test and order-block D1-only test.

    python -m backtest.loss_leads_v27
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.pattern_stats import ore_rules  # noqa: E402

OUT = ROOT / "backtest" / "out"
COLS = ["pair", "range_tf", "range_open", "k", "direction", "decision_time", "session", "status", "R",
        "htf_fvg", "htf_ob", "trend_struct", "friday_late"]


def crt_setups(files, pairs):
    parts = []
    for f in files:
        for ch in pd.read_csv(OUT / f, usecols=COLS, chunksize=500_000, low_memory=False):
            ch = ch[ch["pair"].isin(pairs)]
            parts.append(ch[ore_rules(ch) & (ch["status"] == "filled") & ch["R"].notna()])
    d = pd.concat(parts, ignore_index=True)
    d["decision_time"] = pd.to_datetime(d["decision_time"], utc=True)
    g = d.groupby(["pair", "range_tf", "range_open", "k", "direction"]).agg(R=("R", "mean"), session=("session", "first"),
                                                                           t=("decision_time", "first")).reset_index()
    return g


def crt_test():
    a = crt_setups(["trades_design.csv", "trades_check.csv"], ["GBPUSD", "XAUUSD"])
    a = a[a["t"] < pd.Timestamp("2025-01-01", tz="UTC")]
    b = crt_setups(["fvg_fresh_trades.csv"], ["EURUSD", "XAGUSD"])
    rows, ok = [], True
    for name, g in (("A: GBP/USD + gold 2021-24", a), ("B: EUR/USD + silver", b)):
        ov, rest = g[g["session"] == "overlap"], g[g["session"] != "overlap"]
        passed = len(ov) >= 30 and ov["R"].mean() < 0 and ov["R"].mean() <= rest["R"].mean() - 0.10
        ok &= passed
        rows.append({"set": name, "overlap_n": len(ov), "overlap_avgR": round(ov["R"].mean(), 3),
                     "other_n": len(rest), "other_avgR": round(rest["R"].mean(), 3), "pass": passed})
    return pd.DataFrame(rows), ok


def ob_test():
    d = pd.concat([pd.read_csv(OUT / f"v22_{p}.csv") for p in ("GBPUSD", "XAUUSD", "EURUSD", "XAGUSD")])
    d = d[(d["model"] == "smc_ob") & (d["tf"] == "H1") & (d["target"] == "3R")]
    rows, ok = [], True
    for name, pairs in (("A: GBP/USD + gold", ["GBPUSD", "XAUUSD"]), ("B: EUR/USD + silver", ["EURUSD", "XAGUSD"])):
        g = d[d["pair"].isin(pairs)]
        d1, d1h4 = g[g["d1"].astype(bool)], g[g["d1h4"].astype(bool)]
        passed = len(d1) >= 30 and d1["R"].mean() > 0 and d1["R"].mean() >= d1h4["R"].mean()
        ok &= passed
        rows.append({"set": name, "d1_n": len(d1), "d1_avgR": round(d1["R"].mean(), 3), "d1_win": round((d1["R"] > 0).mean(), 3),
                     "d1h4_n": len(d1h4), "d1h4_avgR": round(d1h4["R"].mean(), 3), "pass": passed})
    return pd.DataFrame(rows), ok


if __name__ == "__main__":
    t, ok = crt_test()
    print("CRT: skip the London/New York overlap\n", t.to_string(index=False), "\n=> PASS" if ok else "\n=> FAIL")
    t, ok = ob_test()
    print("\nOrder block: D1 only vs D1 + H4\n", t.to_string(index=False), "\n=> PASS" if ok else "\n=> FAIL")
