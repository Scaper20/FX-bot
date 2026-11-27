"""Spec v32 (docs/spec-v32-more-pairs.md): does adding pairs to the prop plan raise the pass rate?

    python -m backtest.more_pairs_v32 --candles DIR REPLAY.csv [REPLAY.csv ...]  -> backtest/out/v32_more_pairs.csv
"""
from __future__ import annotations

import argparse
import sys
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.prop_sim import Plan, Rules, bootstrap, evaluate, funded_value, load  # noqa: E402

PLAN = ("ore_poi", "irl_erl")
START, END = pd.Timestamp("2022-06-01", tz="UTC"), pd.Timestamp("2026-11-18", tz="UTC")
BASE = ("GBPUSD", "XAUUSD")
_T: dict = {}


def _one(args):
    name, pairs, risk = args
    t = _T["t"][_T["t"]["pair"].isin(pairs)].reset_index(drop=True)
    rules, plan = Rules(), Plan(risk, PLAN, label=f"{name} | {risk:.1%}")
    r = {"basket": name, "risk": risk, "trades": len(t), "net_R": round(t["R"].sum(), 1),
         **evaluate(t, rules, plan), **bootstrap(t, rules, plan, n_paths=2000, weeks=26), **funded_value(t, rules, plan)}
    return r


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--candles")
    ap.add_argument("--extra", default="EURUSD,XAGUSD")
    a = ap.parse_args()
    t = load(a.files, a.candles)
    t = t[t["strategy"].isin(PLAN) & (t["fill"] >= START) & (t["fill"] < END)].reset_index(drop=True)
    _T["t"] = t
    print(t.groupby(["pair", "strategy"])["R"].agg(["count", "sum"]).round(1).to_string(), "\n")
    extra = [x for x in a.extra.split(",") if x]
    baskets = {"A: GBP/USD + gold": BASE, **{f"A + {p}": BASE + (p,) for p in extra}}
    if len(extra) > 1:
        baskets["A + " + " + ".join(extra)] = BASE + tuple(extra)
    jobs = [(n, p, r) for n, p in baskets.items() for r in (0.01, 0.015, 0.02)]
    with Pool(6, initializer=_T.update, initargs=({"t": t},)) as pool:
        rows = pool.map(_one, jobs)
    d = pd.DataFrame(rows)[["basket", "risk", "trades", "net_R", "starts", "pass", "fail_daily", "fail_trailing",
                            "still_open", "median_days_to_pass", "boot_pass", "funded_avg_paid", "funded_breached"]]
    out = ROOT / "backtest" / "out" / f"v32_more_pairs_{'_'.join(extra)}.csv"
    d.to_csv(out, index=False)
    print(d.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
