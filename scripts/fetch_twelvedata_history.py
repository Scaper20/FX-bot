"""Download 5-minute history from Twelve Data (used when Dukascopy refuses downloads, 28 Nov 2026).

    TWELVEDATA_API_KEY=... python scripts/fetch_twelvedata_history.py USD/JPY 2021-11-01 data/td/usdjpy-m5.csv.gz

Pages backwards 5,000 candles at a time (1 credit each, ~3 weeks of M5), pausing to stay under 8 calls a minute.
Weekend quotes (market closed) are dropped, like the live feed. Columns match the Dukascopy CSVs:
timestamp (ms, UTC), open, high, low, close. Prices are Twelve Data mid prices, not Dukascopy bid.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine.calendar import open_mask  # noqa: E402
from engine.feeds.twelvedata import BASE, _key  # noqa: E402


def page(symbol: str, end: pd.Timestamp) -> pd.DataFrame:
    q = {"symbol": symbol, "interval": "5min", "outputsize": 5000, "end_date": end.strftime("%Y-%m-%d %H:%M:%S"),
         "timezone": "UTC", "order": "ASC", "format": "JSON"}
    req = urllib.request.Request(BASE + "?" + urllib.parse.urlencode(q),
                                 headers={"Authorization": f"apikey {_key()}", "User-Agent": "crt-scanner/history"})
    for attempt in range(6):                             # out of credits for the minute: wait and retry
        try:
            payload = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 5:
                raise
            time.sleep(65)
            continue
        if int(payload.get("code") or 0) == 429 and attempt < 5:
            time.sleep(65)
            continue
        break
    if payload.get("status") == "error":
        raise RuntimeError(f"Twelve Data error {payload.get('code')}: {payload.get('message')}")
    df = pd.DataFrame(payload.get("values") or [])
    if df.empty:
        return df
    df.index = pd.to_datetime(df["datetime"], utc=True)
    return df[["open", "high", "low", "close"]].astype(float)


def main() -> int:
    symbol, start, out = sys.argv[1], pd.Timestamp(sys.argv[2], tz="UTC"), Path(sys.argv[3])
    end = pd.Timestamp.now(tz="UTC").floor("5min")
    parts, calls = [], 0
    while end > start:
        df = page(symbol, end)
        calls += 1
        if df.empty:
            break
        parts.append(df)
        print(f"{symbol}: {df.index[0]} -> {df.index[-1]} ({len(df)})", flush=True)
        if df.index[0] >= end:
            break
        end = df.index[0]
        time.sleep(8)                                    # free plan: 8 credits a minute
    d = pd.concat(parts).sort_index()
    d = d[~d.index.duplicated(keep="last")]
    d = d[(d.index >= start) & open_mask(d.index)]
    out.parent.mkdir(parents=True, exist_ok=True)
    d.insert(0, "timestamp", d.index.as_unit("ms").asi8)
    d.to_csv(out, index=False)
    print(f"{len(d)} candles {d.index[0]} -> {d.index[-1]}, {calls} credits -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
