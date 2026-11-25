import numpy as np

from backtest.smc_bias import mss_events


def test_mss_is_close_below_latest_swing_low_once():
    # bearish space: swing low at 3 (low 9), pullback up to a top at 6, then candle 8 closes below 9
    h = np.array([12, 11.5, 11, 10.5, 11.2, 11.8, 12.5, 11.6, 10.0, 9.5, 9.4, 9.3])
    l = np.array([11, 10.5, 10, 9.0, 10.0, 10.6, 11.5, 10.4, 8.6, 8.4, 8.3, 8.2])
    c = (h + l) / 2
    c[8] = 8.8                                  # closes below the swing low (9.0): MSS
    o = c.copy()
    ev = list(mss_events(o, h, l, c))
    assert ev and ev[0] == (8, 6)               # MSS at candle 8, top at candle 6
    assert len([e for e in ev if e[0] > 8 and e[1] <= 6]) == 0   # that swing low is used only once


def test_no_mss_without_a_close_below():
    h = np.array([12, 11.5, 11, 10.5, 11.2, 11.8, 12.5, 11.6, 10.5, 10.4, 10.3, 10.2])
    l = np.array([11, 10.5, 10, 9.0, 10.0, 10.6, 11.5, 10.4, 8.6, 9.2, 9.3, 9.4])
    c = np.maximum((h + l) / 2, 9.1)            # wicks below 9.0 but never closes below it
    assert not [e for e in mss_events(c.copy(), h, l, c) if e[1] in (5, 6)]
