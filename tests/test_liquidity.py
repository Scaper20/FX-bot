import numpy as np

from backtest import liquidity_ie as L


def candles(rows):
    o, h, l, c = (np.array(x, float) for x in zip(*rows))
    t = np.arange(len(rows), dtype=np.int64) * 3600 * 10**9
    return o, h, l, c, t, t + 3600 * 10**9


def base(n=12):
    # flat-ish market with a swing low at index 3 (target for a SELL) well below the action
    rows = [(10, 10.5, 9.5, 10)] * n
    rows[3] = (10, 10.5, 5.0, 10)
    return rows


def test_sniper_sell_matches_his_diagram(monkeypatch):
    monkeypatch.setattr(L, "LOOK", 12)
    rows = base()
    rows += [(10.0, 11.0, 9.8, 10.8),    # C1 high 11
             (10.8, 11.6, 10.5, 10.7),   # C2 sweeps above C1 high, closes back below it (liquidity block)
             (10.7, 11.2, 10.2, 10.3),   # C3 high below C2 high, bearish
             (10.3, 11.4, 10.1, 10.6)]   # C4 trades above the C3 high -> sell zone
    o, h, l, c, to, tc = candles(rows)
    found = [x for x in L.sniper_orders(o, h, l, c, to, tc, 0.01) if x["idx"]["c3"] == len(rows) - 2]
    edge = next(x for x in found if x["entry_kind"] == "edge")
    assert edge["e"] == 11.2 and abs(edge["stop"] - 11.62) < 1e-9 and edge["target"] == 5.0
    assert edge["window"] == (int(to[-1]), int(tc[-1]))          # only during C4


def test_sniper_rejects_when_c2_closes_above_c1_high_or_c3_bullish(monkeypatch):
    monkeypatch.setattr(L, "LOOK", 12)
    for c2, c3 in (((10.8, 11.6, 10.5, 11.3), (10.7, 11.2, 10.2, 10.3)),     # C2 closed above C1 high: no sweep
                   ((10.8, 11.6, 10.5, 10.7), (10.3, 11.2, 10.2, 10.9))):    # C3 bullish: not the model
        rows = base() + [(10.0, 11.0, 9.8, 10.8), c2, c3, (10.3, 11.4, 10.1, 10.6)]
        o, h, l, c, to, tc = candles(rows)
        assert not [x for x in L.sniper_orders(o, h, l, c, to, tc, 0.01) if x["idx"]["c3"] == len(rows) - 2]


def test_reward_risk_uses_spread():
    assert abs(L.rr(10.0, 7.0, 11.0, 0.0) - 3.0) < 1e-12
    assert L.rr(10.0, 7.0, 11.0, 0.1) < 3.0
