import numpy as np

from backtest import toni_lingard as T
from backtest.patterns import atr


def _bars(path):
    c = np.array(path, float)
    prev = np.r_[c[0], c[:-1]]
    o = prev + 0.3 * (c - prev)                     # opens a little inside the move: no tied extremes
    return o, np.maximum(o, c) + 0.1, np.minimum(o, c) - 0.1, c


def _ramp(a, b, n):
    return list(np.linspace(a, b, n + 1)[1:])


def test_toni_multiple_bos_needs_two_lows_and_a_body_close_inducement():
    # down leg breaks two swing lows, pulls back, then closes below the structure candle's close
    path = [110.0] * 6 + _ramp(110, 104, 4) + _ramp(104, 107, 3) + _ramp(107, 105, 3) + _ramp(105, 108, 3) \
        + _ramp(108, 115, 5) + _ramp(115, 100, 6) + _ramp(100, 102.5, 3) + _ramp(102.5, 96, 4) + [96.0] * 6
    o, h, l, c = _bars(path)
    ev = [e for e in T.toni_events(o, h, l, c) if e[0] == "dbos"]
    assert ev, "expected a multiple-BOS event"
    kind, j, top, broken = ev[-1]
    assert len(broken) >= 2 and all(c[j] < l[s] for s in broken[-1:])
    setups = T.toni_setups(o, h, l, c, kind, j, top, broken)
    assert setups
    for rule, ptype, e, stop, v, tgt, pi in setups:
        assert v > j and c[v] < c[j] and stop > e > c[v] and tgt == l[j:v + 1].min()
        assert min(o[pi], c[pi]) > h[j + 1:v + 1].max()          # POI body untouched by the inducement leg


def test_lingard_pattern_a_order_block_sits_beyond_the_first_pullback():
    # top made by two bullish candles then a bearish one (the OB), swing low, first pullback just below the OB,
    # then a break of the swing low (BOS)
    path = [100.0, 102.0] * 10 + [103, 105, 107, 106, 105, 110, 112, 108, 104, 101, 103, 105, 103, 100, 99, 98, 98, 98]
    o, h, l, c = _bars(path)
    out = T.lingard_setups(o, h, l, c, atr(h, l, c))
    assert [x[0] for x in out] == ["A"]
    pat, t, ph, zl, zh, tl, zi, bos = out[0]
    assert c[ph] == 105 and c[zi] == 110 and zh == h[zi + 1] and tl == l[bos]     # OB = the 110/112 run
    for pat, t, ph, zl, zh, tl, zi, bos in out:
        assert zl > h[ph] and zh > zl and t >= bos and ph + 2 <= t
