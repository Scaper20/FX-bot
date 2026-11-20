"""Replay feed: serve candles from the Dukascopy 1-minute history as if it were live at `now`.
Used for tests, local development and building practice setups."""
from __future__ import annotations

import pandas as pd

from ..candles import resample

LOOKBACK = {"H1": pd.Timedelta("120D"), "M15": pd.Timedelta("25D"), "M5": pd.Timedelta("10D")}


class ReplayFeed:
    def __init__(self, m1_by_pair: dict[str, pd.DataFrame], day_close: str = "utc0"):
        self.m1 = m1_by_pair
        self.day_close = day_close

    def frames(self, pair: str, now: pd.Timestamp) -> dict[str, pd.DataFrame]:
        m1 = self.m1[pair]
        out = {}
        for tf, back in LOOKBACK.items():
            part = m1[(m1.index >= now - back) & (m1.index < now)]
            out[tf] = resample(part, tf, self.day_close)[["open", "high", "low", "close"]]
        return out
