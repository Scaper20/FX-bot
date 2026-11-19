"""Load 1-minute candles, check them, and build higher timeframes.

No trading rules live here. Everything is in UTC internally.

Daily and H4 candles depend on when the broker's day ends:
  "ny17" - day ends 17:00 New York (moves with US daylight saving).
           H4 candles then start 17:00, 21:00, 01:00, 05:00, 09:00, 13:00 New York.
  "utc0" - day ends 00:00 UTC. H4 candles start 00:00, 04:00 ... UTC.
M5, M15 and H1 are the same under both.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

NY = "America/New_York"
COLS = ["open", "high", "low", "close"]

TF_MINUTES = {"M1": 1, "M5": 5, "M15": 15, "H1": 60, "H4": 240, "D1": 1440}
DAY_CLOSES = ("ny17", "utc0")


# ---------------------------------------------------------------- loading

def load_m1_csv(path) -> pd.DataFrame:
    """Read a 1-minute CSV.

    Accepts a time column called timestamp/time/date/datetime holding either
    epoch milliseconds (dukascopy-node output) or text dates. Text dates without
    a timezone are read as UTC. Returns columns open/high/low/close (+volume if
    present), indexed by candle OPEN time in UTC, in file order (not cleaned).
    """
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    tcol = next((c for c in ("timestamp", "time", "datetime", "date", "gmt time") if c in df.columns), None)
    if tcol is None:
        raise ValueError(f"No time column in {path}. Columns found: {list(df.columns)}")
    missing = [c for c in COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing price columns {missing} in {path}")

    t = df[tcol]
    if pd.api.types.is_numeric_dtype(t):
        idx = pd.to_datetime(t, unit="ms", utc=True)
    else:
        idx = pd.to_datetime(t, utc=True, format="mixed", dayfirst=False)
    if len(idx) and (idx.min().year < 2000 or idx.max().year > 2100):
        raise ValueError(f"Times in {path} decode to {idx.min()} .. {idx.max()}. "
                         "Expected epoch milliseconds or text dates; check the time unit.")
    out = df[COLS + (["volume"] if "volume" in df.columns else [])].astype(float)
    out.index = pd.DatetimeIndex(idx, name="time_utc")
    return out


# ---------------------------------------------------------------- checking

@dataclass
class CheckReport:
    rows: int
    first: pd.Timestamp | None
    last: pd.Timestamp | None
    duplicates: int = 0
    out_of_order: int = 0
    bad_ohlc: int = 0          # high below open/close, low above open/close, high < low
    non_positive: int = 0
    gaps: pd.DataFrame = field(default_factory=pd.DataFrame)  # weekday gaps only

    def summary(self) -> str:
        lines = [
            f"rows {self.rows:,}  from {self.first}  to {self.last}",
            f"duplicate times {self.duplicates}, out of order {self.out_of_order}, "
            f"bad OHLC {self.bad_ohlc}, zero/negative prices {self.non_positive}",
            f"weekday gaps listed: {len(self.gaps)}",
        ]
        if len(self.gaps):
            top = self.gaps.sort_values("minutes", ascending=False).head(10)
            for _, g in top.iterrows():
                lines.append(f"   {g['from']} -> {g['to']}  ({int(g['minutes'])} min)")
        return "\n".join(lines)


def _is_weekend_gap(a: pd.Timestamp, b: pd.Timestamp) -> bool:
    """True if the gap a->b covers the forex weekend (Fri 17:00 to Sun 17:00 New York)."""
    a_ny, b_ny = a.tz_convert(NY), b.tz_convert(NY)
    return a_ny.weekday() >= 4 and b_ny.weekday() in (6, 0) and (b - a) >= pd.Timedelta(hours=40)


def check(df: pd.DataFrame, min_gap_minutes: int = 30) -> CheckReport:
    """Report problems without changing anything. Gaps shorter than
    min_gap_minutes and the normal weekend close are not listed."""
    rep = CheckReport(rows=len(df), first=df.index.min() if len(df) else None,
                      last=df.index.max() if len(df) else None)
    if not len(df):
        return rep
    rep.duplicates = int(df.index.duplicated().sum())
    rep.out_of_order = int((df.index.to_series().diff() < pd.Timedelta(0)).sum())
    o, h, l, c = (df[k] for k in COLS)
    rep.bad_ohlc = int(((h < o) | (h < c) | (l > o) | (l > c) | (h < l)).sum())
    rep.non_positive = int((df[COLS] <= 0).any(axis=1).sum())

    t = df.index.sort_values().unique()
    step = pd.Series(t[1:] - t[:-1], index=t[1:])
    big = step[step > pd.Timedelta(minutes=min_gap_minutes)]
    rows = []
    for end, d in big.items():
        start = end - d
        if not _is_weekend_gap(start, end):
            rows.append({"from": start, "to": end, "minutes": d.total_seconds() / 60})
    rep.gaps = pd.DataFrame(rows, columns=["from", "to", "minutes"])
    return rep


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Sort, drop exact duplicate times (keep first) and drop rows with bad OHLC
    or non-positive prices. Returns the cleaned frame and counts of what was dropped.
    Nothing is invented or filled in."""
    n0 = len(df)
    df = df.sort_index(kind="stable")
    dup = df.index.duplicated(keep="first")
    df = df[~dup]
    o, h, l, c = (df[k] for k in COLS)
    bad = (h < o) | (h < c) | (l > o) | (l > c) | (h < l) | (df[COLS] <= 0).any(axis=1)
    df = df[~bad]
    return df, {"input_rows": n0, "duplicates_dropped": int(dup.sum()),
                "bad_rows_dropped": int(bad.sum()), "output_rows": len(df)}


# ---------------------------------------------------------------- resampling

def _bucket_open_utc(idx: pd.DatetimeIndex, tf: str, day_close: str) -> pd.DatetimeIndex:
    """Open time (UTC) of the tf candle that each 1-minute candle belongs to."""
    minutes = TF_MINUTES[tf]
    if tf in ("M1", "M5", "M15", "H1") or day_close == "utc0":
        return idx.floor(f"{minutes}min")
    if day_close != "ny17":
        raise ValueError(f"day_close must be one of {DAY_CLOSES}")
    # Shift New York wall clock by +7h so that 17:00 NY becomes midnight,
    # floor there, then shift back. DST is handled by the timezone database.
    shifted = idx.tz_convert(NY).tz_localize(None) + pd.Timedelta(hours=7)
    floored = shifted.floor(f"{minutes}min") - pd.Timedelta(hours=7)
    # Bucket starts are 17,21,01,05,09,13 NY. US clocks change at 02:00 on a
    # Sunday, when forex is shut, so 01:00 on change days has no data. If it ever
    # does, 'raise' makes us find out rather than guess.
    return floored.tz_localize(NY, ambiguous="raise", nonexistent="raise").tz_convert("UTC")


def resample(m1: pd.DataFrame, tf: str, day_close: str = "ny17") -> pd.DataFrame:
    """Build tf candles from cleaned 1-minute candles.

    Index = candle open time (UTC). Extra columns:
      close_time_utc - when the candle is finished. A candle may only be used
                       once this time has passed (no look-ahead).
      m1_count       - number of 1-minute candles inside (thin candles show up here).
    The last candle may be unfinished if data stops early; callers compare
    close_time_utc with "now".
    """
    if tf not in TF_MINUTES:
        raise ValueError(f"Unknown timeframe {tf}")
    if day_close not in DAY_CLOSES:
        raise ValueError(f"day_close must be one of {DAY_CLOSES}")
    if not m1.index.is_monotonic_increasing or m1.index.has_duplicates:
        raise ValueError("Run clean() first: index must be sorted and unique")

    key = _bucket_open_utc(m1.index, tf, day_close)
    g = m1.groupby(key)
    out = pd.DataFrame({
        "open": g["open"].first(),
        "high": g["high"].max(),
        "low": g["low"].min(),
        "close": g["close"].last(),
    })
    if "volume" in m1.columns:
        out["volume"] = g["volume"].sum()
    out["m1_count"] = g["open"].size()
    out.index = pd.DatetimeIndex(out.index, name="time_utc")
    out["close_time_utc"] = _close_times(out.index, tf, day_close)
    return out


def _close_times(opens: pd.DatetimeIndex, tf: str, day_close: str) -> pd.DatetimeIndex:
    if tf in ("H4", "D1") and day_close == "ny17":
        # Add the period on the New York wall clock, so a D1 candle spanning a
        # DST change ends at 17:00 NY (23h or 25h long), not after a fixed 24h.
        local = opens.tz_convert(NY).tz_localize(None) + pd.Timedelta(minutes=TF_MINUTES[tf])
        return local.tz_localize(NY, ambiguous="raise", nonexistent="raise").tz_convert("UTC")
    return opens + pd.Timedelta(minutes=TF_MINUTES[tf])


def closed_only(candles: pd.DataFrame, now_utc: pd.Timestamp) -> pd.DataFrame:
    """Candles that had finished at now_utc. The engine must only ever see these."""
    return candles[candles["close_time_utc"] <= now_utc]
