import numpy as np

from backtest import patterns as P


def _bars(path):
    """Candles that walk along a price path: each close = path value, high/low 0.2 around open/close."""
    c = np.array(path, float)
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + 0.2
    lo = np.minimum(o, c) - 0.2
    return o, h, lo, c


def _ramp(a, b, n):
    return list(np.linspace(a, b, n + 1)[1:])


def test_double_top_found_only_after_breakout_and_swing_known():
    path = [100.0] * 20 + _ramp(100, 90, 15) + _ramp(90, 110, 12) + _ramp(110, 100, 8) \
        + _ramp(100, 110, 8) + _ramp(110, 95, 10) + [95.0] * 10
    o, h, l, c = _bars(path)
    A = P.atr(h, l, c)
    hi, lo = P.swings(h, l)
    found = list(P.double_tops(h, l, c, A, hi))
    assert len(found) == 1
    p = found[0]
    a, neck_i, b = p["pts"]
    assert abs(h[a] - h[b]) < 0.5 and c[p["d"]] < p["line"] and p["d"] >= b + P.N
    assert p["stop"] == max(h[a], h[b]) and p["height"] > 0


def test_head_and_shoulders_needs_head_above_shoulders():
    def make(head):
        return [100.0] * 20 + _ramp(100, 90, 15) + _ramp(90, 105, 8) + _ramp(105, 100, 6) + _ramp(100, head, 8) \
            + _ramp(head, 100, 8) + _ramp(100, 105, 6) + _ramp(105, 92, 12) + [92.0] * 10
    for head, n in ((115, 1), (104, 0)):
        o, h, l, c = _bars(make(head))
        assert len(list(P.head_shoulders(h, l, c, P.atr(h, l, c), P.swings(h, l)[0]))) == n


def test_flag_breakout_below_lower_line():
    path = [120.0] * 20 + _ramp(120, 100, 6) + [101, 102, 101.5, 102.5, 102, 103, 102.6, 103.2] + _ramp(103, 95, 4) \
        + [95.0] * 10
    o, h, l, c = _bars(path)
    A = P.atr(h, l, c)
    found = list(P.flags(h, l, c, A, P.swings(h, l)[1]))
    assert found and c[found[0]["d"]] < found[0]["line"] and found[0]["height"] >= 3 * A[found[0]["pts"][1]]
