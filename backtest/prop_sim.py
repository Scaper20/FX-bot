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


V34_FX = ("AUDJPY", "GBPCHF", "GBPNZD", "GBPAUD", "AUDCHF", "NZDCHF", "GBPCAD", "CADJPY", "CADCHF", "EURCAD",
          "EURNZD", "AUDCAD")


@dataclass
class Rules:
    balance: float = 5000.0
    target: float = 0.08          # profit target (of the starting balance)
    daily: float = 0.03           # max loss in one day, from that day's starting balance
    trailing: float = 0.05        # max loss below the highest balance reached
    lock_at_start: bool = False   # True: the trailing floor stops rising once it reaches the starting balance
    min_days: int = 2             # trading days needed before a pass counts
    day_tz: str = "Europe/London"  # Equity Edge: the daily limit resets at 22:00 London time
    day_start_h: int = 22
    equity_trailing: bool = True  # Equity Edge: the trailing floor follows the highest balance OR equity
    leverage: dict = field(default_factory=lambda: {"GBPUSD": 30, "EURUSD": 30, "AUDUSD": 30, "USDJPY": 30,
                                                     "XAUUSD": 10, "XAGUSD": 10, "XPTUSD": 10, "GBPJPY": 30,
                                                     "EURJPY": 30, "USDCAD": 30, "USDCHF": 30, "NZDUSD": 30,
                                                     "EURGBP": 30,
                                                     # spec v34 candidates; BTC 1:2 = crypto leverage assumed (unverified)
                                                     **{p: 30 for p in V34_FX}, "BTCUSD": 2})
    contract: dict = field(default_factory=lambda: {"GBPUSD": 100_000, "EURUSD": 100_000, "AUDUSD": 100_000,
                                                    "USDJPY": 100_000, "XAUUSD": 100, "XAGUSD": 5000,
                                                    "XPTUSD": 100, "GBPJPY": 100_000, "EURJPY": 100_000,
                                                    "USDCAD": 100_000, "USDCHF": 100_000, "NZDUSD": 100_000,
                                                    "EURGBP": 100_000, **{p: 100_000 for p in V34_FX}, "BTCUSD": 1})
    no_hedge: bool = True         # hedging is prohibited: skip a trade opposite an open one on the same pair
    payout_days: int | None = None  # funded stage: pay out profit every N days (no target)
    split: float = 0.8


@dataclass
class Plan:
    risk: float = 0.005                     # risk per trade, fraction of the starting balance
    strategies: tuple = ()                  # () = all
    daily_stop: float | None = None         # no new trades today once today's P&L <= -daily_stop
    max_open: int | None = None             # skip new trades while this many are open
    dd_halve: float | None = None           # halve the risk while the balance is this far below its high
    taper: bool = False                     # near the target, risk only what one 3R win needs (min 0.25%)
    label: str = field(default="")


FX_USD = {"JPY": 1 / 150, "GBP": 1.30, "EUR": 1.10,   # fixed rates for crosses (spec v33; only the leverage cap uses them)
          "AUD": 0.65, "NZD": 0.59, "CAD": 0.72, "CHF": 1.13}   # spec v34


def _usd_per_move(pair: str, price: float, contract: float) -> float:
    """Dollars per 1.0 price move per lot: XXX/USD pays in dollars; USD/XXX pays in XXX, converted at the price;
    crosses pay in the quote currency, converted at a fixed rate."""
    if pair.endswith("USD"):
        return contract
    if pair.startswith("USD"):
        return contract / price
    return contract * FX_USD[pair[3:]]


def _notional_per_lot(pair: str, price: float, contract: float) -> float:
    """Dollar value of one lot (for margin): USD/XXX = contract dollars; XXX/USD = contract x price; crosses =
    contract x the base currency's fixed dollar rate."""
    if pair.startswith("USD"):
        return contract
    if pair.endswith("USD"):
        return contract * price
    return contract * FX_USD[pair[:3]]


def load(paths, candles_dir: str | None = None) -> pd.DataFrame:
    """Filled orders from replay files, plus each trade's best point (MFE, in R) between fill and exit, for the
    equity-based trailing floor. 1-minute Dukascopy data where it exists, else <candles_dir>/{PAIR}_M5.pkl."""
    parts = []
    for p in paths:
        d = pd.read_csv(p)
        d = d[d["order_placed"].astype(bool) & (d["status"] == "filled") & d["R"].notna() & d["exit_time"].notna()]
        parts.append(d[["strategy", "pair", "direction", "entry", "stop", "fill_time", "exit_time", "R"]])
    d = pd.concat(parts, ignore_index=True)
    d["fill"] = pd.to_datetime(d["fill_time"], utc=True)
    d["exit"] = pd.to_datetime(d["exit_time"], utc=True)
    d = d.drop_duplicates(["strategy", "pair", "fill"]).sort_values("fill").reset_index(drop=True)
    d["mfe"] = 0.0
    from backtest.patterns import EXTRA, MARKETS
    from engine.candles import clean, load_m1_csv
    files = {**MARKETS, **EXTRA}
    for pair, g in d.groupby("pair"):
        m1 = clean(load_m1_csv(ROOT / files[pair]["file"]))[0]
        src = [m1]
        if candles_dir and (Path(candles_dir) / f"{pair}_M5.pkl").exists():
            m5 = pd.read_pickle(Path(candles_dir) / f"{pair}_M5.pkl")
            src.append(m5[m5.index > m1.index[-1]])
        px = pd.concat([x[["high", "low"]] for x in src]).sort_index()
        t = px.index.as_unit("ns").asi8
        H, L = px["high"].to_numpy(float), px["low"].to_numpy(float)
        for i, r in g.iterrows():
            a = int(np.searchsorted(t, r["fill"].value)); b = int(np.searchsorted(t, r["exit"].value, side="right"))
            risk = abs(r["entry"] - r["stop"])
            if b > a and risk > 0:
                fav = (H[a:b].max() - r["entry"]) if r["direction"] == "long" else (r["entry"] - L[a:b].min())
                d.at[i, "mfe"] = max(0.0, fav / risk)
    return d


def run(trades: pd.DataFrame, rules: Rules, plan: Plan, start: pd.Timestamp, horizon_days: int = 182) -> dict:
    """One challenge from `start`. Returns {result: pass/fail/open, days, why, trades}."""
    end = start + pd.Timedelta(days=horizon_days)
    t = trades[(trades["fill"] >= start) & (trades["fill"] < end)]
    if plan.strategies:
        t = t[t["strategy"].isin(plan.strategies)]
    shift = pd.Timedelta(hours=24 - rules.day_start_h)
    day = lambda ts: (ts.tz_convert(rules.day_tz) + shift).date()
    target_bal = rules.balance * (1 + rules.target)
    events = []                                   # (time, kind, idx): kind 0 = exit before 1 = fill at the same time
    for i, r in enumerate(t.itertuples()):
        events.append((r.fill, 1, i))
        events.append((r.exit, 0, i))
    events.sort()
    bal, peak, open_, size = rules.balance, rules.balance, set(), {}
    side = t["direction"].to_numpy() if "direction" in t else np.array(["long"] * len(t))
    pair = t["pair"].to_numpy()
    entry = t["entry"].to_numpy(float) if "entry" in t else np.ones(len(t))
    stopd = np.abs(t["entry"].to_numpy(float) - t["stop"].to_numpy(float)) if "stop" in t else np.ones(len(t))
    mfe = t["mfe"].to_numpy(float) if "mfe" in t else np.zeros(len(t))
    at_fill, lots_open = {}, {}
    paid, n_pay, next_pay = 0.0, 0, None
    taken, days_traded = set(), set()
    cur_day, day_start, day_pnl = None, bal, 0.0
    R = t["R"].to_numpy(float)
    for ts, kind, i in events:
        d = day(ts)
        if d != cur_day:
            cur_day, day_start, day_pnl = d, bal, 0.0
        if rules.payout_days and next_pay is not None and ts >= next_pay and not open_:
            if bal > rules.balance:                           # funded payout: profit above the start, then reset
                paid += rules.split * (bal - rules.balance)
                n_pay += 1
                bal, peak = rules.balance, rules.balance
            next_pay = next_pay + pd.Timedelta(days=rules.payout_days)
        if kind == 1:
            if plan.daily_stop is not None and day_pnl <= -plan.daily_stop * rules.balance:
                continue
            if plan.max_open is not None and len(open_) >= plan.max_open:
                continue
            if rules.no_hedge and any(pair[j] == pair[i] and side[j] != side[i] for j in open_):
                continue
            r_usd = plan.risk * rules.balance
            if plan.dd_halve is not None and peak - bal >= plan.dd_halve * rules.balance:
                r_usd /= 2
            if plan.taper:
                r_usd = min(r_usd, max((target_bal - bal) / 3, 0.0025 * rules.balance))
            usd_move = _usd_per_move(pair[i], entry[i], rules.contract.get(pair[i], 1))   # $ per 1.0 move per lot
            lots = r_usd / (stopd[i] * usd_move) if stopd[i] > 0 else 0.0
            used = sum(lots_open[j] * _notional_per_lot(pair[j], entry[j], rules.contract.get(pair[j], 1))
                       / rules.leverage.get(pair[j], 30) for j in open_)
            free_margin = bal - used
            max_lots = max(0.0, free_margin) * rules.leverage.get(pair[i], 30) / _notional_per_lot(
                pair[i], entry[i], rules.contract.get(pair[i], 1))
            if lots > max_lots:                                  # leverage caps the size: less risk on this trade
                lots = max_lots
                r_usd = lots * stopd[i] * usd_move
            lots_open[i] = lots
            if r_usd <= 0.0005 * rules.balance:
                continue
            size[i] = r_usd
            at_fill[i] = bal
            if rules.payout_days and next_pay is None:
                next_pay = ts + pd.Timedelta(days=rules.payout_days)
            open_.add(i)
            taken.add(i)
            days_traded.add(d)
            continue
        if i not in open_:
            continue
        open_.discard(i)
        if rules.equity_trailing:                             # the trade's best point lifted the equity high
            peak = max(peak, at_fill[i] + mfe[i] * size[i])
        pnl = R[i] * size[i]
        bal += pnl
        day_pnl += pnl
        floor = peak - rules.trailing * rules.balance
        if rules.lock_at_start:
            floor = min(floor, rules.balance)
        if bal - day_start <= -rules.daily * rules.balance:
            return {"result": "fail", "why": "daily", "days": (ts - start).days, "trades": len(taken),
                    "paid": round(paid, 2), "payouts": n_pay}
        if bal <= floor:
            return {"result": "fail", "why": "trailing", "days": (ts - start).days, "trades": len(taken),
                    "paid": round(paid, 2), "payouts": n_pay}
        peak = max(peak, bal)
        if not rules.payout_days and bal >= target_bal and len(days_traded) >= rules.min_days and not open_:
            return {"result": "pass", "why": "", "days": (ts - start).days, "trades": len(taken)}
    if rules.payout_days and bal > rules.balance and not open_:
        paid += rules.split * (bal - rules.balance)
        n_pay += 1
    return {"result": "open", "why": "", "days": horizon_days, "trades": len(taken), "paid": round(paid, 2),
            "payouts": n_pay}


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
    ap.add_argument("--candles", help="folder with {PAIR}_M5.pkl for days after the Dukascopy data ends")
    ap.add_argument("--only", help="run one strategy set (by name) and write prop_sim_v29_<n>.csv")
    a = ap.parse_args()
    trades = load(a.files, a.candles)
    rules = Rules()
    print(f"{len(trades)} trades {trades['fill'].min().date()} -> {trades['fill'].max().date()}\n")
    rows = []
    sets = {"all six": (), "CRT only": ("crt",), "smart-money (5)": ("smc_ob", "irl_erl", "toni", "lingard", "ore_poi"),
            "Ore + IRL/ERL + Lingard": ("ore_poi", "irl_erl", "lingard"), "Toni only": ("toni",)}
    mgmt = {"plain": {}, "daily stop 1.5%": {"daily_stop": 0.015}, "halve after -2.5%": {"dd_halve": 0.025},
            "taper near target": {"taper": True}, "halve + taper": {"dd_halve": 0.025, "taper": True}}
    for k, (name, strats) in enumerate(sets.items()):
        if a.only is not None and str(k) != a.only:
            continue
        for risk in (0.0025, 0.005, 0.0075, 0.01, 0.015, 0.02):
            for mname, kw in mgmt.items():
                plan = Plan(risk, strats, label=f"{name} | {risk:.2%} | {mname}", **kw)
                r = evaluate(trades, rules, plan)
                r.update({f"{k}_1y": v for k, v in evaluate(trades, rules, plan, horizon_days=364).items()
                          if k in ("pass", "still_open", "median_days_to_pass")})
                r.update(bootstrap(trades, rules, plan, n_paths=300, weeks=52))
                r.update({"set": name, "risk": risk, "mgmt": mname})
                rows.append(r)
                print(r["plan"], r["pass"], r["boot_pass"], flush=True)
    out = ROOT / "backtest" / "out" / (f"prop_sim_v29_{a.only}.csv" if a.only is not None else "prop_sim_v29.csv")
    pd.DataFrame(rows).to_csv(out, index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



def funded_value(trades, rules, plan, horizon_days=182):
    """Average payout over the funded stage started on every Monday (same limits, payouts every 14 days)."""
    fr = Rules(**{**rules.__dict__, "payout_days": 14})
    first, last = trades["fill"].min().floor("D"), trades["fill"].max()
    starts = pd.date_range(first - pd.Timedelta(days=first.dayofweek), last - pd.Timedelta(days=horizon_days), freq="7D")
    res = pd.DataFrame([run(trades, fr, plan, s0, horizon_days) for s0 in starts])
    return {"funded_avg_paid": round(res["paid"].mean(), 1), "funded_any_payout": round((res["paid"] > 0).mean(), 3),
            "funded_breached": round((res["result"] == "fail").mean(), 3)}
