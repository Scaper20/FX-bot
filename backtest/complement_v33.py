"""Spec v33 (docs/spec-v33-complement-pairs.md): two pairs to go with GBP/USD, gold, EUR/USD (and silver).

    python -m backtest.complement_v33 --candles DIR REPLAY.csv [...]  -> backtest/out/v33_complement.csv

Baselines: B = GBP/USD + gold + EUR/USD + silver (Ore's plan); B' = without silver (what runs live on the free plan).
At 1.5% risk: each candidate's own net R, B(+X) and B'(+X) pass rate and funded payout; then every two-pair
combination of the qualifying candidates. Selection follows the spec's rule.
"""
from __future__ import annotations

import argparse
import itertools
import sys
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backtest.prop_sim import Plan, Rules, evaluate, funded_value, load  # noqa: E402

PLAN = ("ore_poi", "irl_erl")
START, END = pd.Timestamp("2022-06-01", tz="UTC"), pd.Timestamp("2026-11-18", tz="UTC")
BASES = {"B": ("GBPUSD", "XAUUSD", "EURUSD", "XAGUSD"), "B'": ("GBPUSD", "XAUUSD", "EURUSD")}
RISK = 0.015
_T: dict = {}


def _one(args):
    base, extra = args
    pairs = BASES[base] + tuple(extra)
    t = _T["t"][_T["t"]["pair"].isin(pairs)].reset_index(drop=True)
    rules, plan = Rules(), Plan(RISK, PLAN)
    e, f = evaluate(t, rules, plan), funded_value(t, rules, plan)
    return {"base": base, "added": " + ".join(extra) or "-", "trades": len(t), "net_R": round(t["R"].sum(), 1),
            "pass": e["pass"], "fail_trailing": e["fail_trailing"], "still_open": e["still_open"],
            "median_days_to_pass": e["median_days_to_pass"], "funded_avg_paid": f["funded_avg_paid"],
            "funded_breached": f["funded_breached"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--candles")
    a = ap.parse_args()
    t = load(a.files, a.candles)
    t = t[t["strategy"].isin(PLAN) & (t["fill"] >= START) & (t["fill"] < END)].reset_index(drop=True)
    own = t.groupby("pair")["R"].agg(["count", "sum"]).round(1)
    print(t.groupby(["pair", "strategy"])["R"].agg(["count", "sum"]).round(1).to_string(), "\n")
    cands = [p for p in own.index if p not in BASES["B"]]
    jobs = [(b, ()) for b in BASES] + [(b, (p,)) for b in BASES for p in cands]
    with Pool(4, initializer=_T.update, initargs=({"t": t},)) as pool:
        rows = pool.map(_one, jobs)
        r = pd.DataFrame(rows)
        picks = {}
        for b in BASES:
            base = r[(r.base == b) & (r.added == "-")].iloc[0]
            ok = [p for p in cands if own.loc[p, "sum"] > 0
                  and (x := r[(r.base == b) & (r.added == p)].iloc[0])["pass"] >= base["pass"]
                  and x["funded_avg_paid"] >= base["funded_avg_paid"]]
            picks[b] = (base, ok)
        combos = sorted({(b, c) for b, (_, ok) in picks.items() for c in itertools.combinations(sorted(ok), 2)})
        r2 = pd.DataFrame(pool.map(_one, combos)) if combos else pd.DataFrame(columns=r.columns)
    d = pd.concat([r, r2], ignore_index=True)
    out = ROOT / "backtest" / "out" / "v33_complement.csv"
    d.to_csv(out, index=False)
    print(d.to_string(index=False), "\n")
    for b, (base, ok) in picks.items():
        print(f"{b}: qualifying candidates {ok or 'none'}")
        two = r2[(r2.base == b) & (r2["pass"] >= base["pass"]) & (r2.funded_avg_paid >= base.funded_avg_paid)] if len(r2) else r2
        if len(two):
            best = two.sort_values(["pass", "funded_avg_paid"], ascending=False).iloc[0]
            print(f"  chosen pair of two: {best.added} (pass {best['pass']}, funded ${best.funded_avg_paid})")
        elif ok:
            one = r[(r.base == b) & r.added.isin(ok)].sort_values(["pass", "funded_avg_paid"], ascending=False).iloc[0]
            print(f"  chosen single pair: {one.added} (pass {one['pass']}, funded ${one.funded_avg_paid})")
        else:
            print("  nothing added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
