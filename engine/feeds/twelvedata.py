"""Twelve Data client for live candles. The API key is read from the environment
(TWELVEDATA_API_KEY) and sent in a header, never in the URL, and never printed."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd

BASE = "https://api.twelvedata.com/time_series"
SYMBOLS = {"GBPUSD": "GBP/USD", "XAUUSD": "XAU/USD"}
INTERVAL = {"M5": "5min", "M15": "15min", "H1": "1h"}
OUTPUTSIZE = {"H1": 2500, "M15": 1500, "M5": 2500}
CALLS_PER_SCAN = len(SYMBOLS) * len(INTERVAL)


class FeedError(Exception):
    pass


def _key() -> str:
    k = os.environ.get("TWELVEDATA_API_KEY", "").strip()
    if not k:
        raise FeedError("TWELVEDATA_API_KEY is not set on the server.")
    return k


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
    return out


def fetch(pair: str, tf: str, outputsize: int | None = None, timeout: float = 20.0,
          opener=urllib.request.urlopen) -> pd.DataFrame:
    params = {"symbol": SYMBOLS[pair], "interval": INTERVAL[tf], "outputsize": outputsize or OUTPUTSIZE[tf],
              "timezone": "UTC", "order": "ASC", "format": "JSON"}
    req = urllib.request.Request(BASE + "?" + urllib.parse.urlencode(params),
                                 headers={"Authorization": f"apikey {_key()}", "User-Agent": "crt-scanner/1.3"})
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
    return parse(payload)


class TwelveDataFeed:
    def __init__(self, opener=urllib.request.urlopen):
        self.opener = opener
        self.calls = 0

    def frames(self, pair: str, now: pd.Timestamp | None = None) -> dict[str, pd.DataFrame]:
        out = {}
        for tf in ("H1", "M15", "M5"):
            out[tf] = fetch(pair, tf, opener=self.opener)
            self.calls += 1
        return out
