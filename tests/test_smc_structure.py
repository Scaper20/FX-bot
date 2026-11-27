import numpy as np

from engine.smc_structure import dealing_range, external_structure, irl_erl_bias, ore_order_block


def _bars(path):
    c = np.array(path, float)
    prev = np.r_[c[0], c[:-1]]
    o = prev + 0.3 * (c - prev)
    return o, np.maximum(o, c) + 0.1, np.minimum(o, c) - 0.1, c


def _ramp(a, b, n):
    return list(np.linspace(a, b, n + 1)[1:])


def test_bos_then_mss_on_the_protected_low():
    # warm-up range, rally (BOS), pullback = higher low, rally (BOS), then a drop below that higher low (MSS)
    path = [100.0, 101.0] * 10 + _ramp(101, 106, 5) + _ramp(106, 103, 3) + _ramp(103, 110, 6) + _ramp(110, 104, 3) \
        + _ramp(104, 112, 6) + _ramp(112, 100, 8)
    o, h, l, c = _bars(path)
    ev = external_structure(o, h, l, c, "close")
    kinds = [(e["kind"], e["dir"]) for e in ev]
    assert ("BOS", 1) in kinds and kinds[-1] == ("MSS", -1)
    last_bull = [e for e in ev if e["dir"] == 1][-1]
    mss = ev[-1]
    assert mss["broken"] == last_bull["protected"]                 # MSS breaks the higher low that launched the BOS
    assert c[mss["j"]] < l[mss["broken"]] and all(c[k] >= l[mss["broken"]] for k in range(mss["broken"], mss["j"]))
    assert h[mss["protected"]] == h[last_bull["j"]:mss["j"] + 1].max()   # origin = top of the move


def test_ore_order_block_two_and_three_candles_and_mirror():
    # 2-candle: up candle then a down candle closing below its open
    o = np.array([10.0, 10.0, 10.2, 11.0]); c = np.array([10.0, 10.2, 11.0, 9.9])
    h = np.maximum(o, c) + 0.05; l = np.minimum(o, c) - 0.05
    ob = ore_order_block(o, h, l, c, origin=2, direction=-1)
    assert ob["kind"] == "2-candle" and ob["first"] == 2 and ob["last"] == 3
    assert ob["near"] == l[2] and ob["far"] == h[2:4].max() and ob["body_edge"] == o[2]
    # 3-candle: candle, pin bar (long upper wick), candle closing below both bodies
    o = np.array([10.0, 10.0, 10.5, 10.6]); c = np.array([10.0, 10.5, 10.6, 9.8])
    h = np.array([10.1, 10.6, 11.5, 10.65]); l = np.array([9.9, 9.95, 10.45, 9.7])
    ob = ore_order_block(o, h, l, c, origin=2, direction=-1)
    assert ob["kind"] == "3-candle" and ob["first"] == 1 and ob["far"] == 11.5
    # mirror: the same 2-candle shape flipped is a buy block with its near edge at the first candle's high
    o2 = np.array([10.0, 10.0, 9.8, 9.0]); c2 = np.array([10.0, 9.8, 9.0, 10.1])
    h2 = np.maximum(o2, c2) + 0.05; l2 = np.minimum(o2, c2) - 0.05
    ob = ore_order_block(o2, h2, l2, c2, origin=2, direction=1)
    assert ob["kind"] == "2-candle" and ob["near"] == h2[2] and ob["far"] == l2[2:4].min() and ob["body_edge"] == o2[2]
    # no takeover -> no order block
    c3 = np.array([10.0, 10.2, 11.0, 10.5]); o3 = np.array([10.0, 10.0, 10.2, 11.0])
    assert ore_order_block(o3, np.maximum(o3, c3) + .05, np.minimum(o3, c3) - .05, c3, origin=2, direction=-1) is None


def test_irl_erl_bias_flips_on_erl_and_irl_events():
    # range, rally that takes the range high (ERL high -> bias down), then a pullback into the rally's bullish FVG
    # (IRL -> bias up)
    path = [100.0, 101.0] * 12 + [101.5, 102.5, 104.5, 106.5, 108.0, 107.0, 106.0, 104.8, 104.0, 103.6, 104.5]
    o, h, l, c = _bars(path)
    hi, lo = dealing_range(o, h, l, c)
    b, last = irl_erl_bias(o, h, l, c)
    k_erl = next(k for k in range(len(c)) if last[k] == "erl_high")
    assert b[k_erl] == -1 and h[k_erl] > hi[k_erl - 1]
    k_irl = next(k for k in range(k_erl, len(c)) if last[k] == "irl_bull")
    assert b[k_irl] == 1 and k_irl > k_erl
    assert all(b[k] == -1 for k in range(k_erl, k_irl))            # bias stays down until the IRL is reached
