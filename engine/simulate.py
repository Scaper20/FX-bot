"""Simulate one order on 1-minute candles.

Works in "short space": for a real short, prices are as-is; for a real long,
prices are mirrored (negated), so a long also looks like a short. Data is BID.
Spread handling:
  real short: sells at bid (fill when bid high >= entry); exits buy at ask,
              so stop/target trigger when bid is within one spread of them.
  real long:  buys at ask (fill when bid low <= entry - spread); exits sell at bid.
In short space that becomes: fill when high >= entry + fill_shift,
stop when high >= stop - exit_shift, target when low <= target - exit_shift,
where (fill_shift, exit_shift) = (0, spread) for shorts and (spread, 0) for longs.

Conventions (CLAUDE.md): if stop and target fall in the same candle, the stop
counts; on the candle that fills a limit order only the stop is checked; an
order not filled by expiry is cancelled; a pending order is also cancelled if
price reaches the 50% level (T1) first.
"""
from __future__ import annotations

import numpy as np

from .structure import first_true


def _first(mask_src: np.ndarray, a: int, b: int) -> int:
    if a >= b:
        return -1
    i = first_true(mask_src[a:b])
    return a + i if i >= 0 else -1


def simulate(h, l, c, start: int, pend_end: int, hold_end_fn, *, entry: float, market: bool,
             stop: float, targets: dict, t1: float, fill_shift: float, exit_shift: float) -> dict:
    """h, l, c: 1-minute arrays in short space.
    start: first 1-minute candle after the decision.
    pend_end: first 1-minute candle after the order expires (exclusive).
    hold_end_fn(fill_idx) -> exclusive index where the time stop closes the trade.
    targets: name -> price (short space). t1: the 50% level, used to cancel pending orders
    and for the half-off management.
    Returns fill info and, per management name, a dict(R, exit, reason)."""
    n = len(h)
    pend_end = min(pend_end, n)
    if market:
        fill = start - 1
        entry_px = entry - fill_shift          # long market buy pays the spread
        a_stop, a_tgt = start, start
    else:
        if start >= pend_end:
            return {"status": "expired"}
        fill = _first(h >= entry + fill_shift, start, pend_end)
        if fill < 0:
            return {"status": "expired"}
        cancel = _first(l <= t1 - exit_shift, start, fill)
        if cancel >= 0:
            return {"status": "cancelled"}
        entry_px = entry
        a_stop, a_tgt = fill, fill + 1
    risk = stop - entry_px
    if risk <= 0:
        return {"status": "bad_risk"}
    end = min(hold_end_fn(max(fill, start - 1)), n)
    stop_i = _first(h >= stop - exit_shift, a_stop, end)

    def time_exit():
        px = c[end - 1] + exit_shift if end - 1 >= a_stop else entry_px
        return px

    res = {}
    for name, tgt in targets.items():
        if tgt is None:
            continue
        t_i = _first(l <= tgt - exit_shift, a_tgt, end)
        if stop_i >= 0 and (t_i < 0 or stop_i <= t_i):
            res[f"M1_{name}"] = {"R": (entry_px - stop) / risk, "exit": stop_i, "reason": "stop"}
        elif t_i >= 0:
            res[f"M1_{name}"] = {"R": (entry_px - tgt) / risk, "exit": t_i, "reason": "target"}
        else:
            res[f"M1_{name}"] = {"R": (entry_px - time_exit()) / risk, "exit": end - 1, "reason": "time"}

    # M2: half off at T1, stop to breakeven, rest to T2 / T3
    if t1 < entry_px:
        h1 = _first(l <= t1 - exit_shift, a_tgt, end)
        for name in ("T2", "T3"):
            tgt = targets.get(name)
            if tgt is None:
                continue
            key = f"M2_{name}"
            if stop_i >= 0 and (h1 < 0 or stop_i <= h1):
                res[key] = {"R": (entry_px - stop) / risk, "exit": stop_i, "reason": "stop"}
                continue
            if h1 < 0:
                res[key] = {"R": (entry_px - time_exit()) / risk, "exit": end - 1, "reason": "time"}
                continue
            half = 0.5 * (entry_px - t1) / risk
            be_i = _first(h >= entry_px - exit_shift, h1 + 1, end)
            t_i = _first(l <= tgt - exit_shift, h1 + 1, end)
            if be_i >= 0 and (t_i < 0 or be_i <= t_i):
                rest, ex, why = 0.0, be_i, "breakeven"
            elif t_i >= 0:
                rest, ex, why = 0.5 * (entry_px - tgt) / risk, t_i, "target"
            else:
                rest, ex, why = 0.5 * (entry_px - time_exit()) / risk, end - 1, "time"
            res[key] = {"R": half + rest, "exit": ex, "reason": why}
    return {"status": "filled", "fill": fill, "entry_px": entry_px, "risk": risk, "results": res}
