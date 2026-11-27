"""Prop-firm challenge simulator (spec v29, docs/spec-v29-prop-eval.md).

Plays the live scanner's real trade sequence (fills and exits in time order, overlapping trades included)
through a one-step challenge: profit target, daily loss limit from the day's starting balance, trailing maximum
loss from the highest balance, minimum trading days. Each challenge starts on a Monday; every Monday of the record
is one start. Also a week-block bootstrap for a smoother estimate.

    python -m backtest.prop_sim backtest/out/replay_setups.csv [more.csv ...]
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@dataclass
class Rules:
    balance: float = 5000.0
    target: float = 0.08          # profit target (of the starting balance)
    daily: float = 0.03           # max loss in one day, from that day's starting balance
    trailing: float = 0.05        # max loss below the highest balance reached
    lock_at_start: bool = False   # True: the trailing floor stops rising once it reaches the starting balance
    min_days: int = 2             # trading days needed before a pass counts
    day_offset_h: int = 0         # the firm's day starts at 00:00 UTC + this many hours


@dataclass
class Plan:
    risk: float = 0.005                     # risk per trade, fraction of the starting balance
    strategies: tuple = ()                  # () = all
    daily_stop: float | None = None         # no new trades today once today's P&L <= -daily_stop
    max_open: int | None = None             # skip new trades while this many are open
    dd_halve: float | None = None           # halve the risk while the balance is this far below its high
    taper: bool = False                     # near the target, risk only what one 3R win needs (min 0.25%)
    label: str = field(default="")


def load(paths) -> pd.DataFrame:
    parts = []
    for p in paths:
        d = pd.read_csv(p)
        d = d[d["order_placed"].astype(bool) & (d["status"] == "filled") & d["R"].notna() & d["exit_time"].notna()]
        parts.append(d[["strategy", "pair", "fill_time", "exit_time", "R"]])
    d = pd.concat(parts, ignore_index=True)
    d["fill"] = pd.to_datetime(d["fill_time"], utc=True)
    d["exit"] = pd.to_datetime(d["exit_time"], utc=True)
    return d.drop_duplicates(["strategy", "pair", "fill"]).sort_values("fill").reset_index(drop=True)


def run(trades: pd.DataFrame, rules: Rules, plan: Plan, start: pd.Timestamp, horizon_days: int = 182) -> dict:
    """One challenge from `start`. Returns {result: pass/fail/open, days, why, trades}."""
    end = start + pd.Timedelta(days=horizon_days)
    t = trades[(trades["fill"] >= start) & (trades["fill"] < end)]
    if plan.strategies:
        t = t[t["strategy"].isin(plan.strategies)]
    off = pd.Timedelta(hours=rules.day_offset_h)
    day = lambda ts: (ts - off).floor("D")
    target_bal = rules.balance * (1 + rules.target)
    events = []                                   # (time, kind, idx): kind 0 = exit before 1 = fill at the same time
    for i, r in enumerate(t.itertuples()):
        events.append((r.fill, 1, i))
        events.append((r.exit, 0, i))
    events.sort()
    bal, peak, open_, size = rules.balance, rules.balance, set(), {}
    taken, days_traded = set(), set()
    cur_day, day_start, day_pnl = None, bal, 0.0
    R = t["R"].to_numpy(float)
    for ts, kind, i in events:
        d = day(ts)
        if d != cur_day:
            cur_day, day_start, day_pnl = d, bal, 0.0
        if kind == 1:
            if plan.daily_stop is not None and day_pnl <= -plan.daily_stop * rules.balance:
                continue
            if plan.max_open is not None and len(open_) >= plan.max_open:
                continue
            r_usd = plan.risk * rules.balance
            if plan.dd_halve is not None and peak - bal >= plan.dd_halve * rules.balance:
                r_usd /= 2
            if plan.taper:
                r_usd = min(r_usd, max((target_bal - bal) / 3, 0.0025 * rules.balance))
            size[i] = r_usd
            open_.add(i)
            taken.add(i)
            days_traded.add(d)
            continue
        if i not in open_:
            continue
        open_.discard(i)
        pnl = R[i] * size[i]
        bal += pnl
        day_pnl += pnl
        floor = peak - rules.trailing * rules.balance
        if rules.lock_at_start:
            floor = min(floor, rules.balance)
        if bal - day_start <= -rules.daily * rules.balance:
            return {"result": "fail", "why": "daily", "days": (ts - start).days, "trades": len(taken)}
        if bal <= floor:
            return {"result": "fail", "why": "trailing", "days": (ts - start).days, "trades": len(taken)}
        peak = max(peak, bal)
        if bal >= target_bal and len(days_traded) >= rules.min_days and not open_:
            return {"result": "pass", "why": "", "days": (ts - start).days, "trades": len(taken)}
    return {"result": "open", "why": "", "days": horizon_days, "trades": len(taken)}


def evaluate(trades, rules, plan, horizon_days=182):
    first, last = trades["fill"].min().floor("D"), trades["fill"].max()
    starts = pd.date_range(first - pd.Timedelta(days=first.dayofweek), last - pd.Timedelta(days=horizon_days), freq="7D")
    res = [run(trades, rules, plan, s, horizon_days) for s in starts]
    df = pd.DataFrame(res)
    n = len(df)
    p = df[df.result == "pass"]
    return {"plan": plan.label or f"{plan.risk:.2%}", "starts": n, "pass": round((df.result == "pass").mean(), 3),
            "fail_daily": round(((df.result == "fail") & (df.why == "daily")).mean(), 3),
            "fail_trailing": round(((df.result == "fail") & (df.why == "trailing")).mean(), 3),
            "still_open": round((df.result == "open").mean(), 3),
            "median_days_to_pass": float(p.days.median()) if len(p) else np.nan,
            "fee_per_pass": round(19 / max((df.result == "pass").mean(), 1e-9), 0)}


def bootstrap(trades, rules, plan, n_paths=2000, weeks=26, seed=29):
    """Week-block bootstrap: shuffle whole weeks of real trades into new 26-week paths."""
    rng = np.random.default_rng(seed)
    t = trades if not plan.strategies else trades[trades["strategy"].isin(plan.strategies)]
    wk = t["fill"].dt.to_period("W-SUN")
    blocks = [g for _, g in t.groupby(wk)]
    all_weeks = pd.period_range(t["fill"].min(), t["fill"].max(), freq="W-SUN")
    empty = len(all_weeks) - len(blocks)
    pool = blocks + [None] * max(0, empty)                       # quiet weeks count too
    base = pd.Timestamp("2030-01-07", tz="UTC")
    out = []
    for _ in range(n_paths):
        rows = []
        for w in range(weeks):
            b = pool[rng.integers(len(pool))]
            if b is None:
                continue
            fmin = b["fill"].min()
            shift = base + pd.Timedelta(weeks=w) - (fmin - pd.Timedelta(days=int(fmin.dayofweek))).floor("D")
            rows.append(b.assign(fill=b["fill"] + shift, exit=b["exit"] + shift))
        if not rows:
            out.append("open")
            continue
        path = pd.concat(rows).sort_values("fill")
        out.append(run(path, rules, Plan(plan.risk, (), plan.daily_stop, plan.max_open, plan.dd_halve, plan.taper),
                       base, weeks * 7)["result"])
    s = pd.Series(out)
    return {"boot_pass": round((s == "pass").mean(), 3), "boot_fail": round((s == "fail").mean(), 3)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    trades = load(a.files)
    rules = Rules()
    print(f"{len(trades)} trades {trades['fill'].min().date()} -> {trades['fill'].max().date()}\n")
    rows = []
    sets = {"all six": (), "CRT only": ("crt",), "smart-money (5)": ("smc_ob", "irl_erl", "toni", "lingard", "ore_poi"),
            "Ore + IRL/ERL + Lingard": ("ore_poi", "irl_erl", "lingard"), "Toni only": ("toni",)}
    mgmt = {"plain": {}, "daily stop 1.5%": {"daily_stop": 0.015}, "halve after -2.5%": {"dd_halve": 0.025},
            "taper near target": {"taper": True}, "halve + taper": {"dd_halve": 0.025, "taper": True}}
    for name, strats in sets.items():
        for risk in (0.0025, 0.005, 0.0075, 0.01, 0.015, 0.02):
            for mname, kw in mgmt.items():
                plan = Plan(risk, strats, label=f"{name} | {risk:.2%} | {mname}", **kw)
                r = evaluate(trades, rules, plan)
                r.update(bootstrap(trades, rules, plan, n_paths=300))
                r.update({"set": name, "risk": risk, "mgmt": mname})
                rows.append(r)
                print(r["plan"], r["pass"], r["boot_pass"], flush=True)
    pd.DataFrame(rows).to_csv(ROOT / "backtest" / "out" / "prop_sim_v29.csv", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
