import numpy as np
import pandas as pd
import pytest

from engine import config as K
from engine import structure as S
from engine.candles import clean, load_m1_csv
from engine.setups import Market, find_orders
from engine.simulate import simulate


def arr(*rows):
    """rows of (o, h, l, c) -> four arrays"""
    a = np.array(rows, float)
    return a[:, 0], a[:, 1], a[:, 2], a[:, 3]


# ------------------------------------------------------------ structure

def test_bear_fvg():
    o, h, l, c = arr((10, 11, 9.5, 10.8), (10.8, 10.9, 8, 8.2), (8.2, 9.0, 7.5, 7.8))
    assert S.bear_fvg_at(h, l, 0) == (9.0, 9.5)
    o, h, l, c = arr((10, 11, 9.5, 10.8), (10.8, 10.9, 8, 8.2), (8.2, 9.6, 7.5, 7.8))
    assert S.bear_fvg_at(h, l, 0) is None


def test_cisd_uses_open_of_first_up_candle_in_run():
    #            down          up(run start)    up             up (top)        down          down (closes below 10.0)
    o, h, l, c = arr((11, 11.2, 9.8, 10.1), (10.0, 10.6, 9.9, 10.5), (10.5, 11, 10.4, 10.9),
                     (10.9, 12, 10.8, 11.8), (11.8, 11.9, 10.6, 10.7), (10.7, 10.8, 9.5, 9.7))
    assert S.cisd_level(o, c, top=3) == (10.0, 3)
    assert S.first_cisd(o, c, top=3, end=6) == 5
    assert S.first_cisd(o, c, top=3, end=5) == -1      # not visible before candle 5 exists


def test_swing_low_needs_confirmation():
    l = np.array([5, 4, 3, 4, 5, 6.0])
    assert S.last_swing_low(l, known_by=4, n=2, lookback=10) == 2
    assert S.last_swing_low(l, known_by=3, n=2, lookback=10) == -1   # candle 4 not closed yet


def test_mss_breaks_swing_low_formed_before_high():
    l = np.array([5, 4, 3, 4, 5, 6, 7, 6, 4, 2.5])
    c = l + 0.5
    c[9] = 2.8
    # swing low 3 at idx 2, high at idx 6, close 2.8 at idx 9 < 3 -> MSS at 9
    assert S.first_mss(l, c, top=6, end=9, n=2) == -1
    assert S.first_mss(l, c, top=6, end=10, n=2) == 9


def test_fresh_a_level_wick_and_body_rules():
    #   up then down -> A-level at 10.0 (close of candle 0)
    o, h, l, c = arr((9, 10.1, 8.9, 10.0), (10.0, 10.0, 9.0, 9.2), (9.2, 9.5, 9.0, 9.3), (9.3, 9.6, 9.1, 9.4))
    assert S.fresh_a_levels(o, h, l, c, i_range=3, lookback=10) == [10.0]
    h2 = h.copy(); h2[3] = 10.05                     # wick touches -> unfresh
    assert S.fresh_a_levels(o, h2, l, c, i_range=3, lookback=10) == []
    o3, c3 = o.copy(), c.copy(); h3 = h2.copy()
    o3 = np.append(o3, 9.4); h3 = np.append(h3, 10.6); l3 = np.append(l, 9.3); c3 = np.append(c3, 10.5)  # body crosses
    assert S.fresh_a_levels(o3, h3, l3, c3, i_range=4, lookback=10) == [10.0]


# ------------------------------------------------------------ simulator

def run_sim(h, l, c, **kw):
    h, l, c = (np.array(x, float) for x in (h, l, c))
    base = dict(entry=10.0, market=False, stop=11.0, targets={"T1": 9.0, "T2": 7.0, "T3": None}, t1=9.0,
                fill_shift=0.0, exit_shift=0.0)
    base.update(kw)
    return simulate(h, l, c, 0, len(h), lambda f: len(h), **base)


def test_stop_counts_when_stop_and_target_in_same_candle():
    r = run_sim([10.1, 11.5], [9.9, 6.0], [10, 8])
    assert r["results"]["M1_T2"]["reason"] == "stop" and r["results"]["M1_T2"]["R"] == -1


def test_fill_candle_only_checks_stop():
    r = run_sim([10.2, 9.5], [6.5, 8.5], [9, 9])      # target 7 touched on fill candle: ignored
    assert r["results"]["M1_T2"]["reason"] == "time"
    r = run_sim([11.2], [9.9], [10])                  # stop on fill candle counts
    assert r["results"]["M1_T2"]["reason"] == "stop"


def test_pending_cancelled_if_t1_reached_first():
    r = run_sim([9.5, 10.5], [8.9, 9.5], [9, 10])
    assert r["status"] == "cancelled"


def test_spread_shifts_stop_for_shorts():
    r = run_sim([10.1, 10.95, 9], [9.9, 9.9, 6.9], [10, 10, 7], exit_shift=0.1)
    assert r["results"]["M1_T2"]["reason"] == "stop"          # ask = 10.95 + 0.1 >= 11
    r = run_sim([10.1, 10.85, 9], [9.9, 9.9, 6.85], [10, 10, 7], exit_shift=0.1)
    assert r["results"]["M1_T2"]["reason"] == "target"


def test_half_off_then_breakeven():
    r = run_sim([10.1, 9.5, 10.2], [9.9, 8.9, 9.5], [10, 9, 10])
    m2 = r["results"]["M2_T2"]
    assert m2["reason"] == "breakeven" and m2["R"] == pytest.approx(0.5)


def test_market_entry_long_pays_spread():
    # short space; long real -> fill_shift = spread. Market entry at close 10 becomes 9.9
    r = run_sim([10, 9.5], [10, 6.9], [10, 7], market=True, fill_shift=0.1, entry=10.0)
    assert r["entry_px"] == pytest.approx(9.9)


# ------------------------------------------------------------ setups on real data

@pytest.fixture(scope="module")
def gbp():
    m1, _ = clean(load_m1_csv(K.PAIRS["GBPUSD"]["file"]))
    return m1[m1.index < "2022-02-15"]


def _sample_orders(mkt, n=25):
    found = []
    R = mkt.view[("H4", False)]
    for i in range(30, len(R.o)):
        for mir in (False, True):
            orders, _ = find_orders(mkt, "H4", "M15", i, 1, mir, 0.0001)
            if orders:
                found.append((i, mir, orders))
        if len(found) >= n:
            break
    return found


def test_no_look_ahead_future_prices_do_not_change_setups(gbp):
    mkt = Market(gbp, data_end=pd.Timestamp("2022-02-15", tz="UTC"))
    rng = np.random.default_rng(0)
    for i, mir, orders in _sample_orders(mkt, 8):
        t_dec = orders[0]["decision_time"]
        mut = gbp.copy()
        after = mut.index >= t_dec
        f = rng.uniform(0.97, 1.03, after.sum())
        for col in ("open", "high", "low", "close"):
            mut.loc[after, col] = mut.loc[after, col] * f
        mut["high"] = mut[["open", "high", "low", "close"]].max(axis=1)
        mut["low"] = mut[["open", "high", "low", "close"]].min(axis=1)
        mkt2 = Market(mut, data_end=pd.Timestamp("2022-02-15", tz="UTC"))
        orders2, _ = find_orders(mkt2, "H4", "M15", i, 1, mir, 0.0001)
        key = lambda o: (o["trigger"], o["entry_type"], o["stop_type"], round(o["entry"], 6), round(o["stop"], 6),
                         o["decision_time"], o["has_fvg"], o["has_ob"], o["htf_fvg"], o["msnr"], o["mtf_mss"],
                         o["trend_struct"], o["trend_ema"], o["session"], round(o["sweep_ratio"], 6))
        first = sorted(key(o) for o in orders if o["decision_time"] == t_dec)
        again = sorted(key(o) for o in orders2 if o["decision_time"] == t_dec)
        assert first == again


def test_mirror_symmetry(gbp):
    """A long setup on real prices = the same short setup on upside-down prices."""
    flip = gbp.copy()
    flip["open"], flip["close"] = -gbp["open"] + 3, -gbp["close"] + 3
    flip["high"], flip["low"] = -gbp["low"] + 3, -gbp["high"] + 3
    end = pd.Timestamp("2022-02-15", tz="UTC")
    a, b = Market(gbp, end), Market(flip, end)
    n = 0
    R = a.view[("H4", False)]
    for i in range(30, len(R.o)):
        oa, _ = find_orders(a, "H4", "M15", i, 1, True, 0.0001)
        ob, _ = find_orders(b, "H4", "M15", i, 1, False, 0.0001)
        assert [(o["entry_type"], o["stop_type"], o["trigger"]) for o in oa] == \
               [(o["entry_type"], o["stop_type"], o["trigger"]) for o in ob]
        n += len(oa)
    assert n > 0


def test_time_stop_counts_trading_candles_not_weekend_hours(gbp):
    """A trade decided at Friday's close must still run into the next week."""
    from engine.setups import simulate_order
    mkt = Market(gbp, data_end=pd.Timestamp("2022-02-15", tz="UTC"))
    M = mkt.view[("M1", False)]
    fri_close = pd.Timestamp("2022-01-14 22:00", tz="UTC").value      # last minute closes 22:00 UTC
    order = dict(t_dec=fri_close, t_end={1: fri_close, 2: fri_close}, entry=float(M.c[np.searchsorted(M.t_close, fri_close) - 1]),
                 market=True, stop=10.0, targets={"T1": 0.1, "T2": 0.05, "T3": None})
    out = simulate_order(mkt, order, "H4", False, 0.0001)
    exit_t = pd.Timestamp(out["results"]["M1_T2"]["exit_time"], tz="UTC")
    assert out["results"]["M1_T2"]["reason"] == "time"
    assert exit_t >= pd.Timestamp("2022-01-17 10:00", tz="UTC")   # ~5 H4 candles after Sunday open


def test_structure_direction_flips_on_swing_breaks():
    # swing high 12 at idx 2 (confirmed idx 4); close 13 at idx 6 -> up.
    # swing low 9 at idx 8 (confirmed idx 10); close 8.5 at idx 12 -> down.
    h = np.array([10, 11, 12, 11, 10.5, 11, 13.5, 12, 11, 12, 12.5, 11, 10.0])
    l = np.array([9.5, 10, 11, 10, 10.2, 10, 12.5, 11, 9.0, 10, 11, 10, 8.0])
    c = np.array([10, 10.5, 11.5, 10.5, 10.4, 10.8, 13.0, 11.5, 9.5, 11, 12, 10.5, 8.5])
    d = S.structure_direction(h, l, c, n=2)
    assert d[5] == 0 and d[6] == 1 and d[11] == 1 and d[12] == -1


def test_session_flags_follow_daylight_saving():
    from engine.sessions import friday_late, session_flags
    ts = lambda s: pd.Timestamp(s, tz="UTC")
    assert session_flags(ts("2024-01-10 07:30")) == "london"      # winter: London 07:00 = 07:00 UTC
    assert session_flags(ts("2024-01-10 14:00")) == "overlap"     # NY 09:00
    assert session_flags(ts("2024-01-10 19:00")) == "newyork"     # NY 14:00, London closed
    assert session_flags(ts("2024-07-10 06:30")) == "london"      # summer: London 07:30 BST
    assert session_flags(ts("2024-07-10 02:00")) == ""
    assert friday_late(ts("2024-01-12 20:30")) and not friday_late(ts("2024-01-11 20:30"))


# ------------------------------------------------------------ live market

def _frames_from_m1(m1, now):
    from engine.candles import resample
    past = m1[m1.index < now]
    return {tf: resample(past, tf, "utc0")[["open", "high", "low", "close"]] for tf in ("H1", "M15", "M5")}


def test_live_market_finds_the_same_setups_as_backtest_market(gbp):
    """Same engine code, live inputs (H1/M15/M5 only) -> same orders as the 1-minute backtest market."""
    now = pd.Timestamp("2022-02-10 14:00", tz="UTC")
    a = Market(gbp, data_end=now)
    b = Market.from_frames(_frames_from_m1(gbp, now), now)
    n = 0
    for range_tf, etf in (("H4", "M15"), ("H4", "M5"), ("D1", "H1")):
        R = a.view[(range_tf, False)]
        assert len(R.o) == len(b.view[(range_tf, False)].o)
        for i in range(len(R.o) - 40, len(R.o) - 3):
            for mir in (False, True):
                oa, ra = find_orders(a, range_tf, etf, i, 1, mir, 0.0001)
                ob, rb = find_orders(b, range_tf, etf, i, 1, mir, 0.0001)
                ka = [(o["trigger"], o["entry_type"], o["stop_type"], round(o["entry"], 6), round(o["stop"], 6),
                       o["decision_time"], o["htf_fvg"], o["trend_struct"]) for o in oa]
                kb = [(o["trigger"], o["entry_type"], o["stop_type"], round(o["entry"], 6), round(o["stop"], 6),
                       o["decision_time"], o["htf_fvg"], o["trend_struct"]) for o in ob]
                assert ka == kb
                n += len(oa)
    assert n > 0


def test_live_reasons_waiting_and_projected_window(gbp):
    from engine.calendar import next_closes
    # Friday H4 candle closing 20:00 UTC -> next H4 closes are Fri 24:00 (market closes 22:00) and Sun 24:00
    fri = pd.Timestamp("2022-01-14 20:00", tz="UTC").value
    nxt = [pd.Timestamp(x, tz="UTC") for x in next_closes("H4", fri, 2)]
    assert nxt == [pd.Timestamp("2022-01-15 00:00", tz="UTC"), pd.Timestamp("2022-01-17 00:00", tz="UTC")]
    d1 = [pd.Timestamp(x, tz="UTC") for x in next_closes("D1", pd.Timestamp("2022-01-15 00:00", tz="UTC").value, 2)]
    assert d1 == [pd.Timestamp("2022-01-17 00:00", tz="UTC"), pd.Timestamp("2022-01-18 00:00", tz="UTC")]


def test_track_order_reports_pending_then_final(gbp):
    from engine.setups import track_order
    full = Market(gbp, data_end=pd.Timestamp("2022-02-15", tz="UTC"))
    R = full.view[("H4", False)]
    for i in range(30, len(R.o) - 10):
        orders, _ = find_orders(full, "H4", "M15", i, 1, False, 0.0001)
        lim = [o for o in orders if not o["market"]]
        if lim:
            o = lim[0]
            break
    early = Market(gbp, data_end=pd.Timestamp(o["t_dec"], tz="UTC") + pd.Timedelta("5min"))
    st = track_order(early, o, "H4", False, 0.0001)
    assert st["status"] in ("pending", "filled")
    final = track_order(full, o, "H4", False, 0.0001)
    assert final["status"] in ("filled", "expired", "cancelled")
    if final["status"] == "filled":
        assert all(r["state"] in ("stop", "target", "breakeven", "time") for r in final["results"].values())


def test_crt_close_must_be_inside_c1_body(monkeypatch):
    from engine import config as K
    o, c = np.array([10.0]), np.array([12.0])           # C1 body 10-12, wick 9-14
    h, l = np.array([14.0]), np.array([9.0])
    assert S.crt_inside(o, h, l, c, 0, 11.0)             # inside the body
    assert not S.crt_inside(o, h, l, c, 0, 13.0)         # inside the wick only: not a CRT (Ore, 23 Nov 2026)
    assert not S.crt_inside(o, h, l, c, 0, 9.5)
    monkeypatch.setattr(K, "CRT_CLOSE", "range")         # old, looser rule still available for comparison
    assert S.crt_inside(o, h, l, c, 0, 13.0)
