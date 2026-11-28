"""Twelve Data client for live candles. API keys are read from the environment and sent in a header, never in
the URL, and never printed: TWELVEDATA_API_KEY, plus an optional backup TWELVEDATA_API_KEY_BACKUP that is used only
when a key reports that its API credits are used up (per minute or per day)."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd

from .. import config as K
from ..calendar import open_mask
from ..candles import resample_from

BASE = "https://api.twelvedata.com/time_series"
SYMBOLS = {p: f"{p[:3]}/{p[3:]}" for p in (*K.LIVE_PAIRS, *K.PAID_PLAN_PAIRS)}
INTERVAL = {"M5": "5min", "M15": "15min", "H1": "1h"}
OUTPUTSIZE = {"H1": 3500, "M15": 2100, "M5": 3500}   # ~2,500 / 1,500 / 2,500 trading candles once weekends are dropped
KEEP = {"H1": 2500, "M15": 1500}                     # candles kept between scans (the live amounts the backtests used)
# Since 28 Nov 2026 a scan fetches only M5 (1 credit a pair) and rebuilds M15/H1 from it on top of the candles kept
# from earlier scans; checked on GBP/USD and EUR/USD: 921 M15 and 229 H1 built candles identical to Twelve Data's own.
CALLS_PER_SCAN = len(K.LIVE_PAIRS)                   # usual cost; a pair without kept candles costs 3 once
MAX_CALLS_PER_MINUTE = 8                             # free plan
STALE = pd.Timedelta("4D")                           # kept candles older than this -> full fetch (3,500 M5 ~ 12 days raw)


class FeedError(Exception):
    pass


KEY_VARS = ("TWELVEDATA_API_KEY", "TWELVEDATA_API_KEY_BACKUP")
_resting: dict[str, float] = {}        # env var name -> time until which its credits are used up (this process)
backup_calls = 0                       # calls answered with the backup key (this process)


def _keys() -> list[tuple[str, str]]:
    return [(v, os.environ.get(v, "").strip()) for v in KEY_VARS if os.environ.get(v, "").strip()]


def key_count() -> int:
    return len(_keys())


def _key() -> str:
    keys = _keys()
    if not keys:
        raise FeedError("TWELVEDATA_API_KEY is not set on the server.")
    return keys[0][1]


def _out_of_credits(payload: dict) -> str | None:
    """'minute' or 'day' if Twelve Data says this key's API credits are used up, else None."""
    if payload.get("status") != "error" or int(payload.get("code") or 0) != 429:
        return None
    return "day" if "day" in str(payload.get("message", "")).lower() else "minute"


def parse(payload: dict) -> pd.DataFrame:
    if payload.get("status") == "error":
        raise FeedError(f"Twelve Data error {payload.get('code')}: {payload.get('message')}")
    vals = payload.get("values") or []
    if not vals:
        raise FeedError("Twelve Data returned no candles.")
    df = pd.DataFrame(vals)
    idx = pd.to_datetime(df["datetime"], utc=True)
    out = df[["open", "high", "low", "close"]].astype(float)
    out.index = pd.DatetimeIndex(idx, name="time_utc")
    out = out[~out.index.duplicated(keep="last")].sort_index()
    return out[open_mask(out.index)]               # weekend quotes: the backtests never saw them (27 Nov 2026)


def fetch(pair: str, tf: str, outputsize: int | None = None, timeout: float = 20.0,
          opener=urllib.request.urlopen, end_date: pd.Timestamp | None = None) -> pd.DataFrame:
    params = {"symbol": SYMBOLS[pair], "interval": INTERVAL[tf], "outputsize": outputsize or OUTPUTSIZE[tf],
              "timezone": "UTC", "order": "ASC", "format": "JSON"}
    if end_date is not None:                                      # older history (D1 backfill)
        params["end_date"] = pd.Timestamp(end_date).tz_convert("UTC").strftime("%Y-%m-%d %H:%M:%S")
    global backup_calls
    keys = _keys()
    if not keys:
        raise FeedError("TWELVEDATA_API_KEY is not set on the server.")
    url = BASE + "?" + urllib.parse.urlencode(params)
    payload = None
    for i, (name, key) in enumerate(keys):
        if _resting.get(name, 0) > time.time() and i < len(keys) - 1:
            continue                                   # this key is out of credits; try the next one
        req = urllib.request.Request(url, headers={"Authorization": f"apikey {key}", "User-Agent": "crt-scanner/1.3"})
        try:
            with opener(req, timeout=timeout) as r:
                payload = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                payload = json.loads(e.read().decode("utf-8"))
            except Exception:
                raise FeedError(f"Twelve Data HTTP {e.code}") from None
        except urllib.error.URLError as e:
            raise FeedError(f"Could not reach Twelve Data: {e.reason}") from None
        spent = _out_of_credits(payload)
        if spent and i < len(keys) - 1:
            _resting[name] = time.time() + (6 * 3600 if spent == "day" else 65)
            continue
        if i > 0:
            backup_calls += 1
        break
    return parse(payload)


class TwelveDataFeed:
    def __init__(self, opener=urllib.request.urlopen):
        self.opener = opener
        self.calls = 0

    def history_h1(self, pair: str, end: pd.Timestamp) -> pd.DataFrame:
        """Up to 5,000 H1 candles ending before `end` (1 credit): builds the long D1 history."""
        self.calls += 1
        df = fetch(pair, "H1", outputsize=5000, opener=self.opener, end_date=end)
        return df[df.index < end]

    uses_kept = True                                  # the scan may pass candles kept from earlier scans

    def frames(self, pair: str, now: pd.Timestamp | None = None, kept: dict | None = None) -> dict[str, pd.DataFrame]:
        """H1, M15 and M5 candles. With `kept` (closed M15/H1 candles from earlier scans) that are recent enough, only
        M5 is fetched (1 credit); otherwise all three (3 credits)."""
        self.last_mode = "full"
        if plan_fetch(kept, now) == "light":
            m5 = fetch(pair, "M5", opener=self.opener)
            self.calls += 1
            out = extend_from_m5(kept, m5)
            if out is not None:
                self.last_mode = "light"
                return out
        out = {}
        for tf in ("H1", "M15", "M5"):
            out[tf] = fetch(pair, tf, opener=self.opener)
            self.calls += 1
        return out


def plan_fetch(kept: dict | None, now: pd.Timestamp | None) -> str:
    """'light' (M5 only) when kept M15/H1 candles exist, are long enough and recent; else 'full'."""
    if not kept or any(kept.get(tf) is None or len(kept[tf]) < 0.6 * n for tf, n in KEEP.items()):
        return "full"
    now = now or pd.Timestamp.now(tz="UTC")
    if any(now - kept[tf].index[-1] > STALE for tf in KEEP):
        return "full"
    return "light"


def extend_from_m5(kept: dict, m5: pd.DataFrame) -> dict | None:
    """M15/H1 = kept candles before the fetched M5 window + candles rebuilt from that M5 (whole periods only).
    None if the M5 window does not reach back to the kept candles (a gap would be left)."""
    if m5 is None or m5.empty:
        return None
    out = {"M5": m5}
    for tf, step in (("M15", pd.Timedelta("15min")), ("H1", pd.Timedelta("1h"))):
        old = kept[tf][["open", "high", "low", "close"]]
        start = m5.index[0].ceil(step)                    # the first period the M5 window covers fully
        if old.index[-1] + step < start:
            return None
        new = resample_from(m5, tf, K.DAY_CLOSE)[["open", "high", "low", "close"]]
        new = new[new.index >= start]
        out[tf] = pd.concat([old[old.index < start], new]).sort_index().tail(KEEP[tf] + 50)
    return out
