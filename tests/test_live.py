import io
import json

import numpy as np
import pandas as pd
import pytest

from engine import config as K
from engine.candles import clean, load_m1_csv
from engine.feeds import twelvedata as TD
from engine.feeds.replay import ReplayFeed
from engine.live import scan, track_card_options
from engine.setups import Market


@pytest.fixture(scope="module")
def feed():
    m1 = {p: clean(load_m1_csv(K.PAIRS[p]["file"]))[0] for p in K.PAIRS}
    m1 = {p: d[(d.index >= "2023-01-01") & (d.index < "2023-07-01")] for p, d in m1.items()}
    return ReplayFeed(m1)


SPREADS = {p: K.PAIRS[p]["spread"] for p in K.PAIRS}


def markets(feed, now):
    return {p: Market.from_frames(feed.frames(p, now), now) for p in K.PAIRS}


def test_scan_cards_are_consistent(feed):
    now = pd.Timestamp("2023-06-07 10:15", tz="UTC")
    res = scan(markets(feed, now), SPREADS)
    assert res["ready"], "expected ready setups at this time"
    for c in res["ready"]:
        assert c["options"] and c["state"] == "ready"
        for op in c["options"]:
            assert op["rr"] >= K.MIN_RR
            assert pd.Timestamp(op["decision_time"]) <= now
            risk, reward = abs(op["stop"] - op["entry"]), abs(op["entry"] - op["target"])
            assert op["chance"] == pytest.approx(risk / (risk + reward), abs=1e-3)
            if c["direction"] == "short":
                assert op["stop"] > op["entry"] > op["target"]
            else:
                assert op["stop"] < op["entry"] < op["target"]
            assert op["recommended"] == (op["rules"]["session_ok"] and op["rules"]["direction_ok"])
        assert c["recommended"] == any(op["recommended"] for op in c["options"])
        assert c["chart"]["range"] and c["chart"]["entry"]
        assert pd.Timestamp(c["chart"]["entry"][-1][0]) < now


def test_scan_never_sees_the_future(feed):
    """Cards at `now` are identical whatever happens after `now`."""
    now = pd.Timestamp("2023-06-07 10:15", tz="UTC")
    a = scan(markets(feed, now), SPREADS)
    m1 = {p: d.copy() for p, d in feed.m1.items()}
    for p, d in m1.items():
        fut = d.index >= now
        d.loc[fut, ["open", "high", "low", "close"]] *= 1.05
    b = scan({p: Market.from_frames(ReplayFeed(m1).frames(p, now), now) for p in K.PAIRS}, SPREADS)
    strip = lambda r: json.dumps([[c["id"], [o["id"] for o in c["options"]]] for c in r["ready"]], sort_keys=True)
    assert strip(a) == strip(b)


def test_tracking_resolves_later(feed):
    now = pd.Timestamp("2023-06-07 10:15", tz="UTC")
    card = scan(markets(feed, now), SPREADS)["ready"][0]
    later = pd.Timestamp("2023-06-20 00:00", tz="UTC")
    st = track_card_options(Market.from_frames(feed.frames(card["pair"], later), later), card, SPREADS[card["pair"]])
    assert set(st) == {o["id"] for o in card["options"]}
    for s in st.values():
        assert s["status"] in ("filled", "expired", "cancelled")
        if s["status"] == "filled":
            assert s["state"] in ("stop", "target", "breakeven", "time")


# ------------------------------------------------------------ Twelve Data client (no network)

PAYLOAD = {"meta": {"symbol": "XAU/USD", "interval": "1h"}, "status": "ok",
           "values": [{"datetime": "2026-11-18 10:00:00", "open": "2650.1", "high": "2655.0", "low": "2648.2", "close": "2653.3"},
                      {"datetime": "2026-11-18 11:00:00", "open": "2653.3", "high": "2654.0", "low": "2640.0", "close": "2641.5"}]}


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_twelvedata_parse_and_header(monkeypatch):
    monkeypatch.setenv("TWELVEDATA_API_KEY", "secret-test-key")
    seen = {}

    def opener(req, timeout):
        seen["url"], seen["auth"] = req.full_url, req.headers.get("Authorization")
        return FakeResp(json.dumps(PAYLOAD).encode())
    df = TD.fetch("XAUUSD", "H1", opener=opener)
    assert list(df["close"]) == [2653.3, 2641.5]
    assert df.index[0] == pd.Timestamp("2026-11-18 10:00", tz="UTC")
    assert "secret-test-key" not in seen["url"] and seen["auth"] == "apikey secret-test-key"
    assert "symbol=XAU%2FUSD" in seen["url"] and "timezone=UTC" in seen["url"]


def test_twelvedata_error_message_is_shown(monkeypatch):
    monkeypatch.setenv("TWELVEDATA_API_KEY", "k")
    err = {"code": 404, "message": "symbol not available on your plan", "status": "error"}
    with pytest.raises(TD.FeedError, match="not available on your plan"):
        TD.fetch("XAUUSD", "H1", opener=lambda req, timeout: FakeResp(json.dumps(err).encode()))


def test_twelvedata_missing_key(monkeypatch):
    monkeypatch.delenv("TWELVEDATA_API_KEY", raising=False)
    with pytest.raises(TD.FeedError, match="not set"):
        TD.fetch("GBPUSD", "M5", opener=lambda req, timeout: None)
