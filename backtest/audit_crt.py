"""Audit every practice setup against the candles drawn on its chart: range candle, sweep, middle candle,
levels, trigger timing, order levels, and that higher timeframes match the lower ones they are built from.

    python -m backtest.audit_crt
"""
from __future__ import annotations

from collections import Counter

import pandas as pd

from web import chartdata, service

SEC = {"M5": 300, "M15": 900, "H1": 3600, "H4": 14400, "D1": 86400}


def _s(t):
    return int(pd.Timestamp(t).value // 1_000_000_000)


def audit_item(it) -> list[str]:
    c = it["card"]
    ch = chartdata.practice_chart(it["id"]) or {}
    bars = {tf: {b[0]: b for b in rows} for tf, rows in (ch.get("before") or {}).items()}
    after = {tf: {b[0]: b for b in rows} for tf, rows in (ch.get("after") or {}).items()}
    allb = {tf: {**bars.get(tf, {}), **after.get(tf, {})} for tf in SEC}
    errs = []
    tol = 1e-6 if c["pair"] == "GBPUSD" else 1e-3
    R = allb.get(c["range_tf"], {})
    r = R.get(_s(c["range_open"]))
    sw = R.get(_s(c["sweep_open"]))
    if r is None:
        return ["range candle not on the chart"]
    if sw is None:
        return ["sweep candle not on the chart"]
    _, ro, rh, rl, rc = r
    _, so, sh, sl, sc = sw
    if abs(rh - c["range_high"]) > tol or abs(rl - c["range_low"]) > tol:
        errs.append("range high/low differ from the drawn range candle")
    if abs(c["range_mid"] - (rh + rl) / 2) > tol:
        errs.append("50% level wrong")
    # sweep candle is k candles after the range candle, with no candle missing in between
    keys = sorted(R)
    i, s = keys.index(_s(c["range_open"])), keys.index(_s(c["sweep_open"]))
    if s - i != c["k"]:
        errs.append(f"sweep is {s - i} candles after the range on the chart, card says k={c['k']}")
    if c["direction"] == "short":
        if not sh > rh:
            errs.append("short: sweep candle did not go above the range high")
        if sl < rl:
            errs.append("short: sweep candle also broke the range low")
        if abs(sh - c["sweep_extreme"]) > tol:
            errs.append("sweep extreme differs from the sweep candle high")
    else:
        if not sl < rl:
            errs.append("long: sweep candle did not go below the range low")
        if sh > rh:
            errs.append("long: sweep candle also broke the range high")
        if abs(sl - c["sweep_extreme"]) > tol:
            errs.append("sweep extreme differs from the sweep candle low")
    if not rl < sc < rh:
        errs.append("sweep candle did not close back inside the range")
    if c["k"] == 2:
        mid = R.get(keys[i + 1])
        if mid[2] > rh or mid[3] < rl:
            errs.append("k=2: middle candle broke out of the range")
    # timing
    if _s(c["sweep_close"]) - _s(c["sweep_open"]) != SEC[c["range_tf"]] and c["range_tf"] == "H4":
        errs.append("H4 sweep candle is not 4 hours long")
    for op in c["options"]:
        dt = _s(op["decision_time"])
        friday_close = pd.Timestamp(c["sweep_open"]).dayofweek == 4     # market shuts ~22:00 UTC, before midnight
        if dt < _s(c["sweep_close"]) and not (friday_close and _s(c["sweep_close"]) - dt <= 4 * 3600):
            errs.append(f"{op['id']}: decided before the sweep candle closed")
        if dt > _s(c["window_end"]):
            errs.append(f"{op['id']}: decided after the window ended")
        e, st, tg = op["entry"], op["stop"], op["target"]
        ok = (st > e > tg) if c["direction"] == "short" else (st < e < tg)
        if not ok:
            errs.append(f"{op['id']}: stop/entry/target in the wrong order")
        beyond = st >= c["sweep_extreme"] - tol if c["direction"] == "short" else st <= c["sweep_extreme"] + tol
        if op["stop_type"] != "S2" and not beyond:
            errs.append(f"{op['id']}: stop not beyond the sweep extreme")
    # higher timeframes must equal the lower-timeframe candles inside them (where both are drawn)
    for hi_tf, lo_tf in (("H4", "H1"), ("H1", "M15"), ("M15", "M5"), ("D1", "H1")):
        H, L = allb.get(hi_tf, {}), allb.get(lo_tf, {})
        if not H or not L:
            continue
        lo_keys = sorted(L)
        for t, b in H.items():
            if hi_tf == "D1" and t < lo_keys[0]:
                continue
            inside = [L[x] for x in lo_keys if t <= x < t + SEC[hi_tf]]
            if len(inside) * SEC[lo_tf] < SEC[hi_tf] * 0.5 or t < lo_keys[0] or t + SEC[hi_tf] > lo_keys[-1] + SEC[lo_tf]:
                continue                                  # only fully covered candles
            if abs(max(x[2] for x in inside) - b[2]) > tol or abs(min(x[3] for x in inside) - b[3]) > tol:
                errs.append(f"{hi_tf} candle {pd.Timestamp(t, unit='s')} does not match its {lo_tf} candles")
                break
    return errs


def main() -> int:
    items = service.practice_items()
    bad, kinds = {}, Counter()
    sunday = 0
    for it in items:
        e = audit_item(it)
        if pd.Timestamp(it["card"]["range_open"]).dayofweek == 6:
            sunday += 1
        if e:
            bad[it["id"]] = e
            kinds.update(x.split(":")[-1].strip() if ":" in x else x for x in e)
    print(f"{len(items)} practice setups audited, {len(bad)} with problems")
    for k, n in kinds.most_common():
        print(f"  {n:4d}  {k}")
    print(f"range candle is the short Sunday candle: {sunday}")
    for pid, e in list(bad.items())[:8]:
        print(pid, e[:3])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
