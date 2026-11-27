"""Higher-timeframe POIs for Ore's model (specs v25/v26): fresh H4/D1 order blocks, breakers and FVGs, and the
first time price reached each one. Shared by the backtest (backtest/ore_v25.py) and the live scanner."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .smc_structure import external_structure, ore_order_block


def _ohlc(F):
    return tuple(F[k].to_numpy(float) for k in ("open", "high", "low", "close"))


def htf_zones(F: pd.DataFrame, htf: str) -> pd.DataFrame:
    """Zones on one HTF: created (ns, known at that candle's close), lo, hi, dir (+1 buy zone / -1 sell zone), type
    (OB = Ore's 2/3-candle block at a structure origin, BB = an OB a later candle closed through, FVG)."""
    o, h, l, c = _ohlc(F)
    cl = pd.DatetimeIndex(F["close_time_utc"]).as_unit("ns").asi8
    n = len(c)
    rows = []
    for x in range(n - 2):
        if h[x + 2] < l[x]:
            rows.append((int(cl[x + 2]), h[x + 2], l[x], -1, "FVG"))
        if l[x + 2] > h[x]:
            rows.append((int(cl[x + 2]), h[x], l[x + 2], 1, "FVG"))
    for e in external_structure(o, h, l, c, "close"):
        p, d = e["protected"], e["dir"]
        ob = ore_order_block(o, h, l, c, p, d, ahead=max(0, min(2, e["j"] - p)))
        if not ob:
            continue
        lo, hi = min(ob["near"], ob["far"]), max(ob["near"], ob["far"])
        rows.append((int(cl[e["j"]]), lo, hi, d, "OB"))
        for k in range(e["j"] + 1, n):                 # failed: a later candle closes through the far side
            if (d == -1 and c[k] > hi) or (d == 1 and c[k] < lo):
                rows.append((int(cl[k]), lo, hi, -d, "BB"))
                break
    z = pd.DataFrame(rows, columns=["created", "lo", "hi", "dir", "type"])
    z["htf"] = htf
    return z


def first_touch(z: pd.DataFrame, H1: pd.DataFrame) -> np.ndarray:
    """Open time (ns) of the first H1 candle that reaches each zone after it was created (int64 max if never)."""
    ho = H1.index.as_unit("ns").asi8
    hh, hl = H1["high"].to_numpy(float), H1["low"].to_numpy(float)
    out = np.full(len(z), np.iinfo(np.int64).max, dtype=np.int64)
    for i, (cr, lo, hi, d) in enumerate(zip(z["created"].to_numpy(), z["lo"].to_numpy(), z["hi"].to_numpy(),
                                             z["dir"].to_numpy())):
        a = int(np.searchsorted(ho, cr, side="left"))
        seg = hh[a:] >= lo if d == -1 else hl[a:] <= hi
        if len(seg):
            k = int(np.argmax(seg))
            if seg[k]:
                out[i] = ho[a + k]
    return out


def tapped_zone(Z: pd.DataFrame, d: int, t_top: int, px: float, window_ns: int, types=("OB", "FVG")):
    """The fresh zone (pointing direction d, of the given types) whose FIRST tap made this top/bottom: known before
    the top candle, top price inside it, first touch within window_ns before the top. Row or None."""
    if Z is None or not len(Z):
        return None
    m = ((Z["dir"] == d) & Z["type"].isin(types) & (Z["created"] <= t_top) & (Z["lo"] <= px) & (px <= Z["hi"])
         & (Z["touch"] >= t_top - window_ns) & (Z["touch"] <= t_top))
    hit = Z[m]
    return None if hit.empty else hit.iloc[-1]
