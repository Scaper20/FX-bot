"""Run the backtest for one period and write every simulated trade to a CSV.

    python -m backtest.run --period design
    python -m backtest.run --period check
    python -m backtest.run --period final --i-understand-this-runs-once

Data after the period's end is never loaded, so nothing later can leak in.
One row per (setup, entry, stop, management). Analysis is in backtest/stats.py.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import config as K  # noqa: E402
from engine.candles import clean, load_m1_csv  # noqa: E402
from engine.setups import Market, find_orders, simulate_order  # noqa: E402

OUT = ROOT / "backtest" / "out"
FINAL_LOG = ROOT / "backtest" / "FINAL_RUNS.log"


def run_pair(pair: str, period: str, spread_mult: float = 1.0, m1: pd.DataFrame | None = None,
             verbose: bool = True) -> tuple[pd.DataFrame, dict]:
    start, end = (pd.Timestamp(x, tz="UTC") for x in K.PERIODS[period])
    if m1 is None:
        m1, _ = clean(load_m1_csv(ROOT / K.PAIRS[pair]["file"]))
    spread = K.PAIRS[pair]["spread"] * spread_mult
    mkt = Market(m1, data_end=end)
    rows, reasons = [], {}
    for range_tf, entry_tfs in K.RANGE_TO_ENTRY.items():
        R = mkt.view[(range_tf, False)]
        idx = [i for i in range(len(R.o)) if R.t_open[i] >= start.value]
        for entry_tf in entry_tfs:
            for mirrored in (False, True):
                for i in idx:
                    for k in (1, 2):
                        orders, why = find_orders(mkt, range_tf, entry_tf, i, k, mirrored, spread)
                        reasons[why] = reasons.get(why, 0) + 1
                        for o in orders:
                            sim = simulate_order(mkt, o, range_tf, mirrored, spread)
                            rows.extend(_rows(pair, range_tf, entry_tf, mirrored, o, sim))
    df = pd.DataFrame(rows)
    if verbose:
        print(f"{pair} {period}: {reasons}  -> {len(df)} rows")
    return df, reasons


def _rows(pair, range_tf, entry_tf, mirrored, o, sim):
    base = {k: v for k, v in o.items() if k not in ("targets", "rr", "t_end", "t_dec")}
    base.update(pair=pair, range_tf=range_tf, entry_tf=entry_tf, direction="long" if mirrored else "short",
                status=sim["status"])
    sign = -1 if mirrored else 1
    base["entry"], base["stop"] = sign * o["entry"], sign * o["stop"]
    for t, p in o["targets"].items():
        base[f"{t}_px"] = sign * p if p is not None else None
    for t, v in o["rr"].items():
        base[f"rr_{t}"] = v
    base["fill_time"] = pd.Timestamp(sim["fill_time"], tz="UTC") if sim["status"] == "filled" else None
    base["filled_by_exp1"] = bool(sim["status"] == "filled" and sim["fill_time"] <= o["t_end"][1])
    out = []
    mgmts = ("M1_T1", "M1_T2", "M1_T3", "M2_T2", "M2_T3")
    for m in mgmts:
        final_t = m.split("_")[1]
        rr = o["rr"].get(final_t)
        if rr is None or rr < K.MIN_RR:
            continue                       # this management doesn't meet 1:3, not a trade
        r = dict(base, mgmt=m)
        if sim["status"] == "filled" and m in sim["results"]:
            res = sim["results"][m]
            r.update(R=res["R"], exit_reason=res["reason"], exit_time=pd.Timestamp(res["exit_time"], tz="UTC"))
        elif sim["status"] == "filled":
            continue                       # management not applicable (e.g. entry already past T1)
        out.append(r)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", required=True, choices=list(K.PERIODS))
    ap.add_argument("--spread-mult", type=float, default=1.0)
    ap.add_argument("--i-understand-this-runs-once", action="store_true")
    a = ap.parse_args()
    if a.period == "final":
        if not a.i_understand_this_runs_once:
            print("The final period runs once. Add --i-understand-this-runs-once.")
            return 2
        prior = FINAL_LOG.read_text().strip().splitlines() if FINAL_LOG.exists() else []
        if prior:
            print(f"WARNING: final period already run {len(prior)} time(s). This result is CONTAMINATED.")
        with FINAL_LOG.open("a") as f:
            f.write(json.dumps({"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "spread_mult": a.spread_mult}) + "\n")
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    parts = [run_pair(p, a.period, a.spread_mult)[0] for p in K.PAIRS]
    df = pd.concat(parts, ignore_index=True)
    tag = f"{a.period}" + ("" if a.spread_mult == 1 else f"_x{a.spread_mult:g}")
    df.to_csv(OUT / f"trades_{tag}.csv", index=False)
    print(f"wrote {len(df)} rows to backtest/out/trades_{tag}.csv in {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
