"""Spec v1.2 selection (docs/spec-v1.2.md). Stages A and B use Design data only.

    python -m backtest.select_v12            # stages A + B, writes finalists
    python -m backtest.select_v12 --check    # stage C on 2024 (run backtest.run --period check first)
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.stats import load, path_stats  # noqa: E402

OUT = ROOT / "backtest" / "out"
REPORTS = ROOT / "backtest" / "reports"
SESSIONS = {"all": {"london", "newyork", "overlap"}, "london": {"london", "overlap"},
            "newyork": {"newyork", "overlap"}, "overlap": {"overlap"}}
SWEEPS = ("none", "ratio<=1", "depth>=0.1", "both")
VKEYS = ["range_tf", "entry_tf", "trigger", "entry_type", "stop_type", "min_risk", "mgmt"]


def prepare(path) -> pd.DataFrame:
    d = load(path)
    d = d[(d["expiry"] == 2) & d["trade"]].copy()
    d["session"] = d["session"].fillna("").astype(str)
    d["friday_late"] = d["friday_late"].astype(bool)
    d["backed"] = d["htf_fvg"] | d["htf_ob"]
    return d


def base_and_filter(d: pd.DataFrame, trend: str, sess: str, sweep: str) -> pd.DataFrame:
    tcol = "trend_struct" if trend == "struct" else "trend_ema"
    m = d["session"].isin(SESSIONS[sess]) & ~d["friday_late"]
    m &= (d[tcol] == "with") | d["backed"]                 # against / unclear only with HTF backing
    if sweep in ("ratio<=1", "both"):
        m &= d["sweep_ratio"] <= 1.0
    if sweep in ("depth>=0.1", "both"):
        m &= d["sweep_depth_atr"] >= 0.1
    return d[m]


def with_min_risk(d: pd.DataFrame) -> pd.DataFrame:
    a = d.assign(min_risk="none")
    b = d[d["risk_spreads"] >= 10].assign(min_risk=">=10")
    return pd.concat([a, b], ignore_index=True)


def stage_a(d: pd.DataFrame) -> dict:
    rows = []
    for pair in sorted(d["pair"].unique()):
        x = d[d["pair"] == pair]
        for trend, sess, sweep in itertools.product(("struct", "ema"), SESSIONS, SWEEPS):
            f = base_and_filter(x, trend, sess, sweep)
            rows.append({"pair": pair, "trend": trend, "session": sess, "sweep": sweep,
                         "trades": len(f), "setups": f["decision_time"].nunique(), "avg_R": f["R"].mean()})
    a = pd.DataFrame(rows)
    best = (a[a["trades"] >= 300].sort_values("avg_R", ascending=False).groupby("pair").head(1))
    return {"table": a, "best": best}


def variants(x: pd.DataFrame) -> pd.DataFrame:
    g = with_min_risk(x).groupby(VKEYS)["R"]
    v = pd.DataFrame({"n": g.size(), "avg_R": g.mean(), "win_rate": g.apply(lambda r: (r > 0).mean()),
                      "total_R": g.sum(), "sd": g.std()}).reset_index()
    v["t"] = v["avg_R"] / (v["sd"] / np.sqrt(v["n"]))
    return v.replace([np.inf, -np.inf], np.nan)


def stage_b(d1: pd.DataFrame, d2: pd.DataFrame, best: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    fins, tried = [], 0
    for _, b in best.iterrows():
        x1 = base_and_filter(d1[d1["pair"] == b.pair], b.trend, b.session, b.sweep)
        x2 = base_and_filter(d2[d2["pair"] == b.pair], b.trend, b.session, b.sweep)
        v1, v2 = variants(x1), variants(x2)
        tried += len(v1)
        v = v1.merge(v2[VKEYS + ["avg_R"]], on=VKEYS, how="left", suffixes=("", "_x2"))
        ok = v[(v["n"] >= 40) & (v["avg_R"] > 0) & (v["avg_R_x2"] > 0)]
        top = ok.sort_values("t", ascending=False).head(10).assign(
            pair=b.pair, trend=b.trend, session=b.session, sweep=b.sweep, qualified=len(ok), eligible=int((v["n"] >= 40).sum()))
        fins.append(top)
    return pd.concat(fins, ignore_index=True), tried


def evaluate(d: pd.DataFrame, fin: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, f in fin.iterrows():
        x = with_min_risk(base_and_filter(d[d["pair"] == f.pair], f.trend, f.session, f.sweep))
        for k in VKEYS:
            x = x[x[k] == f[k]]
        x = x.sort_values("exit_time")
        ps = path_stats(x["R"]) if len(x) else {"worst_losing_run": 0, "max_dd_R": 0}
        rows.append({"n": len(x), "avg_R": x["R"].mean() if len(x) else np.nan,
                     "win_rate": (x["R"] > 0).mean() if len(x) else np.nan, "total_R": x["R"].sum(), **ps})
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    if not a.check:
        d1, d2 = prepare(OUT / "trades_design.csv"), prepare(OUT / "trades_design_x2.csv")
        A = stage_a(d1)
        A["table"].to_csv(REPORTS / "v12_stage_a.csv", index=False)
        print("STAGE A: best filter per pair (all 32 combos in reports/v12_stage_a.csv)")
        print(A["best"].round(3).to_string(index=False))
        fin, tried = stage_b(d1, d2, A["best"])
        ev = evaluate(d1, fin)
        fin = pd.concat([fin.reset_index(drop=True), ev[["worst_losing_run", "max_dd_R"]]], axis=1)
        fin.to_csv(REPORTS / "v12_finalists.csv", index=False)
        print(f"\nSTAGE B: {tried} variants tried; qualified per pair:",
              fin.groupby("pair")["qualified"].first().to_dict())
        print(fin[["pair"] + VKEYS + ["n", "win_rate", "avg_R", "avg_R_x2", "t", "worst_losing_run", "max_dd_R"]]
              .round(3).to_string(index=False))
    else:
        fin = pd.read_csv(REPORTS / "v12_finalists.csv")
        fin["min_risk"] = fin["min_risk"].astype(str)
        dc = prepare(OUT / "trades_check.csv")
        ev = evaluate(dc, fin)
        res = pd.concat([fin[["pair"] + VKEYS + ["n", "avg_R"]].rename(columns={"n": "n_design", "avg_R": "avgR_design"}),
                         ev.add_suffix("_2024")], axis=1)
        res["pass"] = (res["n_2024"] >= 20) & (res["avg_R_2024"] > 0)
        res.to_csv(REPORTS / "v12_check.csv", index=False)
        print(res.round(3).to_string(index=False))
        print("\npassed:", int(res["pass"].sum()), "of", len(res))
        json.dump({"passed": int(res["pass"].sum()), "finalists": len(res)}, open(REPORTS / "v12_check_summary.json", "w"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
