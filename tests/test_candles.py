import io

import numpy as np
import pandas as pd
import pytest

from engine import candles as C


def fx_minutes(start_ny: str, end_ny: str, seed: int = 1) -> pd.DataFrame:
    """Random-walk 1-minute candles, only while forex is open
    (Sun 17:00 New York to Fri 17:00 New York)."""
    idx = pd.date_range(pd.Timestamp(start_ny, tz=C.NY), pd.Timestamp(end_ny, tz=C.NY),
                        freq="1min", inclusive="left")
    ny = idx
    wd, hr = ny.weekday, ny.hour
    open_ = ~((wd == 5) | ((wd == 4) & (hr >= 17)) | ((wd == 6) & (hr < 17)))
    idx = idx[open_].tz_convert("UTC")
    rng = np.random.default_rng(seed)
    close = 1.25 + np.cumsum(rng.normal(0, 0.0001, len(idx)))
    open_p = np.r_[close[0], close[:-1]]
    spread = np.abs(rng.normal(0, 0.00005, len(idx)))
    df = pd.DataFrame({"open": open_p, "close": close,
                       "high": np.maximum(open_p, close) + spread,
                       "low": np.minimum(open_p, close) - spread,
                       "volume": 1.0}, index=pd.DatetimeIndex(idx, name="time_utc"))
    return df[["open", "high", "low", "close", "volume"]]


# ------------------------------------------------------------ loading

def test_load_epoch_ms_and_text_dates():
    ms = io.StringIO("timestamp,open,high,low,close,volume\n"
                     "1704326400000,1.27,1.28,1.26,1.275,10\n")
    txt = io.StringIO("Time,Open,High,Low,Close\n2024-01-04 00:00:00,1.27,1.28,1.26,1.275\n")
    a, b = C.load_m1_csv(ms), C.load_m1_csv(txt)
    assert a.index[0] == pd.Timestamp("2024-01-04 00:00", tz="UTC")
    assert b.index[0] == a.index[0]
    assert "volume" in a.columns and "volume" not in b.columns


def test_load_rejects_wrong_time_unit():
    secs = io.StringIO("timestamp,open,high,low,close\n1704326400,1.27,1.28,1.26,1.275\n")
    with pytest.raises(ValueError, match="time unit"):
        C.load_m1_csv(secs)


def test_load_rejects_missing_columns():
    with pytest.raises(ValueError):
        C.load_m1_csv(io.StringIO("timestamp,open,high,low\n1,1,1,1\n"))


# ------------------------------------------------------------ check / clean

def test_check_and_clean_find_problems():
    df = fx_minutes("2024-01-07 17:00", "2024-01-10 17:00")
    df = pd.concat([df, df.iloc[[100]]])                     # duplicate
    df.iloc[5, df.columns.get_loc("high")] = df.iloc[5]["low"] - 0.01  # bad OHLC
    gap_start = df.index[2000]
    df = df.drop(df.index[2000:2090])                         # 90-minute weekday hole
    rep = C.check(df)
    assert rep.duplicates == 1
    assert rep.bad_ohlc == 1
    assert len(rep.gaps) == 1 and rep.gaps.iloc[0]["minutes"] == 91
    cleaned, info = C.clean(df)
    assert info["duplicates_dropped"] == 1 and info["bad_rows_dropped"] == 1
    assert cleaned.index.is_monotonic_increasing and not cleaned.index.has_duplicates
    assert gap_start not in cleaned.index


def test_weekend_is_not_reported_as_gap():
    df = fx_minutes("2024-01-07 17:00", "2024-01-21 17:00")
    assert len(C.check(df).gaps) == 0


# ------------------------------------------------------------ resampling

def test_m5_ohlc_matches_hand_calculation():
    df = fx_minutes("2024-01-07 17:00", "2024-01-08 17:00")
    m5 = C.resample(df, "M5")
    first = df.loc[m5.index[3]: m5.index[3] + pd.Timedelta("4min")]
    row = m5.iloc[3]
    assert row["open"] == first["open"].iloc[0]
    assert row["close"] == first["close"].iloc[-1]
    assert row["high"] == first["high"].max() and row["low"] == first["low"].min()
    assert row["m1_count"] == 5


def test_d1_ny17_follows_us_daylight_saving():
    # US clocks: summer time ends 3 Nov 2024. Before: 17:00 NY = 21:00 UTC. After: 22:00 UTC.
    df = fx_minutes("2024-10-27 17:00", "2024-11-08 17:00")
    d1 = C.resample(df, "D1", "ny17")
    opens = d1.index
    assert pd.Timestamp("2024-10-27 21:00", tz="UTC") in opens   # Monday 28 Oct candle
    assert pd.Timestamp("2024-11-03 22:00", tz="UTC") in opens   # Monday 4 Nov candle
    assert len(d1) == 10                                          # 5 candles per week, no Sunday stub
    assert (d1["m1_count"] == 1440).all()
    assert ((d1["close_time_utc"] - d1.index) == pd.Timedelta("24h")).all()


def test_h4_ny17_boundaries():
    df = fx_minutes("2024-01-07 17:00", "2024-01-09 17:00")
    h4 = C.resample(df, "H4", "ny17")
    hours_ny = sorted(set(h4.index.tz_convert(C.NY).hour))
    assert hours_ny == [1, 5, 9, 13, 17, 21]
    assert (h4["m1_count"] == 240).all()


def test_utc0_makes_a_sunday_stub_candle():
    # Documented behaviour: with a midnight-UTC day, Sunday evening is its own short D1 candle.
    df = fx_minutes("2024-01-07 17:00", "2024-01-12 17:00")
    d1 = C.resample(df, "D1", "utc0")
    assert d1.index[0] == pd.Timestamp("2024-01-07", tz="UTC")
    assert d1["m1_count"].iloc[0] == 120          # 22:00-24:00 UTC only
    assert len(d1) == 6


def test_resample_requires_clean_input():
    df = fx_minutes("2024-01-07 17:00", "2024-01-08 17:00")
    with pytest.raises(ValueError):
        C.resample(pd.concat([df, df.iloc[[0]]]), "H1")


# ------------------------------------------------------------ no look-ahead

@pytest.mark.parametrize("tf", ["M5", "M15", "H1", "H4", "D1"])
def test_closed_candles_do_not_change_when_future_data_is_removed(tf):
    full = fx_minutes("2024-03-03 17:00", "2024-03-15 17:00")   # spans US DST start (10 Mar)
    cut = pd.Timestamp("2024-03-12 14:37", tz="UTC")
    past = full[full.index < cut]
    a = C.closed_only(C.resample(full, tf), cut)
    b = C.closed_only(C.resample(past, tf), cut)
    pd.testing.assert_frame_equal(a, b)
    assert (a["close_time_utc"] <= cut).all()


def test_closed_only_hides_the_running_candle():
    df = fx_minutes("2024-01-07 17:00", "2024-01-08 17:00")
    h1 = C.resample(df, "H1")
    now = h1.index[5] + pd.Timedelta("30min")
    seen = C.closed_only(h1, now)
    assert seen.index[-1] == h1.index[4]
