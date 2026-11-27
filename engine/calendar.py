"""When is the forex market open? Used to project future candle close times live
(the backtest always has the real candles). Weekend: Friday 17:00 to Sunday 17:00
New York time. Holidays are not modelled."""
from __future__ import annotations

import pandas as pd

NY = "America/New_York"
PERIOD = {"D1": pd.Timedelta("1D"), "H4": pd.Timedelta("4h"), "H1": pd.Timedelta("1h"),
          "M15": pd.Timedelta("15min"), "M5": pd.Timedelta("5min")}


def market_open(t: pd.Timestamp) -> bool:
    ny = t.tz_convert(NY)
    wd, hr = ny.weekday(), ny.hour
    if wd == 5:
        return False
    if wd == 4 and hr >= 17:
        return False
    if wd == 6 and hr < 17:
        return False
    return True


def open_mask(index: pd.DatetimeIndex):
    """True for candles that open while the forex market is open (vectorised market_open). The live feed also
    sends weekend quotes (Friday 17:00 to Sunday 17:00 New York); the backtest data has none, so they are dropped."""
    ny = index.tz_convert(NY)
    wd, hr = ny.dayofweek, ny.hour
    closed = (wd == 5) | ((wd == 4) & (hr >= 17)) | ((wd == 6) & (hr < 17))
    return ~closed


def interval_has_trading(a: pd.Timestamp, b: pd.Timestamp) -> bool:
    t = a
    while t < b:
        if market_open(t):
            return True
        t += pd.Timedelta("30min")
    return False


def next_closes(tf: str, after_close_ns: int, count: int) -> list[int]:
    """Close times (ns) of the next `count` trading candles after the candle closing at
    `after_close_ns`, for UTC-aligned candles (Exness GMT+0 day)."""
    p = PERIOD[tf]
    t = pd.Timestamp(after_close_ns, tz="UTC")
    out = []
    while len(out) < count:
        a, b = t, t + p
        if interval_has_trading(a, b):
            out.append(b.value)
        t = b
    return out
