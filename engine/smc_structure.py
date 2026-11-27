"""External market structure (draft for Ore's review, 27 Nov 2026).

Replaces "every 5-bar fractal is structure". Only the swings that matter are tracked:

Uptrend:
- the **external high** = the highest point of the current leg, fixed once price pulls back from it
  (2 lower highs after it);
- the **protected low** = the lowest point between the previous external high and the candle that broke it
  (the higher low that launched the break).
- **BOS (bullish)** = price breaks the external high (close or wick, per teacher) → a new protected low and a
  new leg.
- **MSS (bearish)** = price breaks the protected low → the trend turns down. The top of the move = the external
  high (or the leg high if it was never fixed).
Downtrend = mirror. Small swings inside a leg (internal structure) are ignored here.

Everything is known at the close of the candle that makes the event (no look-ahead).
"""
from __future__ import annotations

import numpy as np

CONFIRM = 2          # lower highs after the leg high that fix it as the external high


def external_structure(o, h, l, c, mode: str = "close", warmup: int = 20) -> list[dict]:
    """Events in time order. Each: kind ('BOS'/'MSS'), dir (+1 bull / -1 bear), j (break candle),
    broken (index of the swing that was broken), protected (index of the new protected swing = origin of the
    move that broke), level (broken price)."""
    n = len(c)
    if n <= warmup + 2:
        return []
    up_px = c if mode == "close" else h
    dn_px = c if mode == "close" else l
    hi = int(np.argmax(h[:warmup]))
    lo = int(np.argmin(l[:warmup]))
    trend = 0
    hi_fixed, lo_fixed = True, True      # warm-up range edges act as fixed levels
    events = []
    for j in range(warmup, n):
        # extend the running leg extreme until it is fixed by a pullback
        if trend >= 0 and not hi_fixed:
            if h[j] >= h[hi]:
                hi = j
            elif j - hi >= CONFIRM and h[hi + 1:j + 1].max() < h[hi]:
                hi_fixed = True
        if trend <= 0 and not lo_fixed:
            if l[j] <= l[lo]:
                lo = j
            elif j - lo >= CONFIRM and l[lo + 1:j + 1].min() > l[lo]:
                lo_fixed = True
        bull_break = hi_fixed and up_px[j] > h[hi] and hi != j
        bear_break = lo_fixed and dn_px[j] < l[lo] and lo != j
        if bull_break and not bear_break:
            kind = "MSS" if trend == -1 else "BOS"
            prot = int(hi + np.argmin(l[hi:j + 1]))          # higher low that launched the break
            if trend == -1:
                prot = lo if l[lo] <= l[prot] else prot       # after an MSS the low of the move is the origin
            events.append({"kind": kind, "dir": 1, "j": j, "broken": hi, "protected": prot, "level": float(h[hi])})
            trend, lo, lo_fixed, hi, hi_fixed = 1, prot, True, j, False
        elif bear_break and not bull_break:
            kind = "MSS" if trend == 1 else "BOS"
            prot = int(lo + np.argmax(h[lo:j + 1]))
            if trend == 1:
                prot = hi if h[hi] >= h[prot] else prot
            events.append({"kind": kind, "dir": -1, "j": j, "broken": lo, "protected": prot, "level": float(l[lo])})
            trend, hi, hi_fixed, lo, lo_fixed = -1, prot, True, j, False
    return events


def trend_at(events: list[dict], t_close_ns, frame_close_ns) -> int:
    """External trend (+1/-1/0) known at time t from a list of events on another timeframe.
    frame_close_ns[j] = close time of candle j of that timeframe."""
    out = 0
    for ev in events:
        if frame_close_ns[ev["j"]] > t_close_ns:
            break
        out = ev["dir"]
    return out


def order_block(o, h, l, c, origin: int, direction: int, back: int = 5):
    """Order block at the origin of a move. direction=-1 (sell): the last up-close candle(s) at or just before
    the origin high (consecutive up-close candles count as one block, from the first). direction=+1: mirror.
    Returns dict(first, last, low, high, body_edge) where body_edge is the block's near body edge
    (sell: lowest open of the run; buy: highest open) or None."""
    up = (lambda k: c[k] > o[k]) if direction == -1 else (lambda k: c[k] < o[k])
    k = origin
    while k >= 0 and origin - k <= back and not up(k):
        k -= 1
    if k < 0 or origin - k > back:
        return None
    last = k
    while k - 1 >= 0 and up(k - 1):
        k -= 1
    first = k
    lo, hi = float(l[first:last + 1].min()), float(h[first:last + 1].max())
    edge = float(o[first:last + 1].min()) if direction == -1 else float(o[first:last + 1].max())
    return {"first": first, "last": last, "low": lo, "high": hi, "body_edge": edge}
