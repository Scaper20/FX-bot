"""Price-structure building blocks on plain numpy arrays.

Everything is written for the BEARISH case (high swept, trade down). Bullish
setups are found by running the same code on mirrored prices (see mirror()).
Indexes are candle positions. A function only reads candles up to the `end`
it is given, so callers control what is "the past".
"""
from __future__ import annotations

import numpy as np


def mirror(o, h, l, c):
    """Flip prices upside down: a bullish pattern becomes a bearish one."""
    return -o, -l, -h, -c


def first_true(mask: np.ndarray) -> int:
    """Index of the first True, or -1."""
    if mask.size == 0:
        return -1
    i = int(np.argmax(mask))
    return i if mask[i] else -1


# ------------------------------------------------------------ swings

def is_swing_low(l: np.ndarray, t: int, n: int) -> bool:
    if t - n < 0 or t + n >= len(l):
        return False
    return bool(l[t] < l[t - n:t].min() and l[t] < l[t + 1:t + n + 1].min())


def is_swing_high(h: np.ndarray, t: int, n: int) -> bool:
    if t - n < 0 or t + n >= len(h):
        return False
    return bool(h[t] > h[t - n:t].max() and h[t] > h[t + 1:t + n + 1].max())


def last_swing_low(l: np.ndarray, known_by: int, n: int, lookback: int) -> int:
    """Latest swing low that is CONFIRMED by candle `known_by` (needs n candles
    after it, so t + n <= known_by). Returns index or -1."""
    for t in range(known_by - n, max(known_by - lookback, n) - 1, -1):
        if is_swing_low(l, t, n):
            return t
    return -1


# ------------------------------------------------------------ fair value gaps

def bear_fvg_at(h, l, a: int) -> tuple[float, float] | None:
    """Bearish FVG made by candles a, a+1, a+2: candle a+2's high is below
    candle a's low. Returns (bottom, top) or None."""
    if a < 0 or a + 2 >= len(h):
        return None
    if h[a + 2] < l[a]:
        return float(h[a + 2]), float(l[a])
    return None


# ------------------------------------------------------------ CISD and MSS

def cisd_level(o, c, top: int, max_back: int = 10) -> tuple[float, int] | None:
    """Open of the first candle in the run of up-close candles that made the
    high at `top` (the run may end at `top` or just before it).
    Returns (level, index of the last up-close candle in the run)."""
    j = top
    while j >= 0 and top - j <= max_back and not (c[j] > o[j]):
        j -= 1
    if j < 0 or top - j > max_back:
        return None
    last_up = j
    while j - 1 >= 0 and c[j - 1] > o[j - 1]:
        j -= 1
    return float(o[j]), last_up


def first_cisd(o, c, top: int, end: int) -> int:
    """First candle at/after the high whose close is below the CISD level. -1 if none before `end`."""
    got = cisd_level(o, c, top)
    if got is None:
        return -1
    level, last_up = got
    start = max(last_up + 1, top)
    if start >= end:
        return -1
    i = first_true(c[start:end] < level)
    return start + i if i >= 0 else -1


def first_mss(l, c, top: int, end: int, n: int, lookback: int = 60) -> int:
    """First candle after the high that closes below the latest swing low that
    was confirmed before the high. -1 if none before `end`."""
    t = last_swing_low(l, top, n, lookback)
    if t < 0:
        return -1
    start = top + 1
    if start >= end:
        return -1
    i = first_true(c[start:end] < l[t])
    return start + i if i >= 0 else -1


# ------------------------------------------------------------ order block

def bear_order_block(o, h, l, c, top: int, decision: int, search: int):
    """Last up-close candle at or shortly before the high. Valid (per Ore's
    reference) only if (1) it or the next candle took liquidity: a high above
    the previous 3 candles' highs, and (2) the move away left a bearish FVG
    before `decision`, and (3) no close above its high since.
    Returns dict(idx, open, mean, high) or None."""
    b = top
    while b >= 0 and top - b <= search and not (c[b] > o[b]):
        b -= 1
    if b < 3 or top - b > search:
        return None
    took = max(h[b], h[min(b + 1, top)]) > h[b - 3:b].max()
    if not took:
        return None
    gap = any(bear_fvg_at(h, l, a) is not None for a in range(b, decision - 1))
    if not gap:
        return None
    if decision > b and c[b + 1:decision + 1].max() > h[b]:
        return None
    return {"idx": b, "open": float(o[b]), "mean": float((o[b] + c[b]) / 2), "high": float(h[b])}


def latest_open_bear_fvg(h, l, first: int, decision: int):
    """Most recent bearish FVG with first candle >= `first` and completed by
    `decision`, not yet traded through (no high above its top since)."""
    for a in range(decision - 2, first - 1, -1):
        g = bear_fvg_at(h, l, a)
        if g is None:
            continue
        bottom, top = g
        if a + 3 <= decision and h[a + 3:decision + 1].max() >= top:
            continue
        return {"a": a, "bottom": bottom, "top": top, "mid": (bottom + top) / 2}
    return None


# ------------------------------------------------------------ higher-timeframe zones

def htf_zone_overlap(o, h, l, c, i_range: int, lo: float, hi: float, lookback: int):
    """Do bearish FVGs / order blocks that formed by candle `i_range` (and are
    still intact at its close) overlap the price band [lo, hi]?
    Returns (fvg_overlap, ob_overlap)."""
    fvg_hit = ob_hit = False
    start = max(0, i_range - lookback)
    for a in range(start, i_range - 1):
        g = bear_fvg_at(h, l, a)
        if g is None:
            continue
        bottom, top = g
        intact = a + 3 > i_range or h[a + 3:i_range + 1].max() < top
        if intact and hi >= bottom and lo <= top:
            fvg_hit = True
        # order block = up-close candle right before this gap's first candle (or the first candle itself)
        for b in (a - 1, a):
            if b >= 0 and c[b] > o[b]:
                zb, zt = o[b], h[b]
                ok = b + 1 > i_range or c[b + 1:i_range + 1].max() <= zt
                if ok and hi >= zb and lo <= zt:
                    ob_hit = True
                break
    return fvg_hit, ob_hit


# ------------------------------------------------------------ MSnR

def fresh_a_levels(o, h, l, c, i_range: int, lookback: int) -> list[float]:
    """A-levels (close of an up candle followed by a down candle) that are still
    fresh at the close of candle `i_range`. A wick touch makes a level unfresh;
    a body crossing it makes it fresh again."""
    out = []
    for t in range(max(0, i_range - lookback), i_range):
        if not (c[t] > o[t] and c[t + 1] < o[t + 1]):
            continue
        lvl = c[t]
        fresh = True
        for j in range(t + 2, i_range + 1):
            if min(o[j], c[j]) < lvl < max(o[j], c[j]):
                fresh = True
            elif l[j] <= lvl <= h[j]:
                fresh = False
        if fresh:
            out.append(float(lvl))
    return out


def structure_direction(h, l, c, n: int) -> np.ndarray:
    """Market direction from swing breaks, known at each candle's close:
    +1 after a close above the latest confirmed swing high, -1 after a close
    below the latest confirmed swing low, 0 before the first break."""
    out = np.zeros(len(c), dtype=int)
    cur, sh, sl = 0, None, None
    for j in range(len(c)):
        t = j - n                      # swing at t is confirmed when candle j = t + n closes
        if t >= n:
            if is_swing_high(h, t, n):
                sh = h[t]
            if is_swing_low(l, t, n):
                sl = l[t]
        if sh is not None and c[j] > sh:
            cur, sh = 1, None
        elif sl is not None and c[j] < sl:
            cur, sl = -1, None
        out[j] = cur
    return out
