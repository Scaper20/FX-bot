import io
import json

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
        if c.get("model"):                     # order-block strategy: checked in test_smc_live
            assert c["strategy"] == "smc_ob"
            continue
        for op in c["options"]:
            assert op["rr"] >= K.MIN_RR
            assert pd.Timestamp(op["decision_time"]) <= now
            risk, reward = abs(op["stop"] - op["entry"]), abs(op["entry"] - op["target"])
            if op["mgmt"].startswith("M1"):
                assert op["chance"] == pytest.approx(risk / (risk + reward), abs=1e-3)
                assert op["breakeven"] > op["chance"]          # spread makes break-even harder
            else:
                r1 = abs(op["entry"] - op["t1"])
                assert op["chance"] == pytest.approx(risk / (risk + r1), abs=1e-3)
                assert op["p_target"] == pytest.approx(risk / (risk + r1) * r1 / reward, abs=1e-3)
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


def test_smc_live_cards_follow_spec_v16(feed):
    """Order-block model: D1+H4 bias, MSS on H1, entry at the OB open, stop above the top, exactly 3R before
    spread, no 50% cancel, 3-day hold; a full strategy (recommended, with its backtest stats)."""
    from engine.smc_live import MODEL, scan_smc_pair
    found = []
    for day in pd.date_range("2023-03-01", "2023-07-20", freq="1D", tz="UTC"):
        if day.weekday() >= 5:
            continue
        now = day + pd.Timedelta("15h")
        for pair, mkt in markets(feed, now).items():
            found += scan_smc_pair(mkt, pair, SPREADS[pair])
        if len(found) >= 3:
            break
    assert found, "expected at least one order-block setup in the replay months"
    for c in found:
        op = c["options"][0]
        assert c["model"] == MODEL and c["strategy"] == "smc_ob" and c["recommended"] and op["recommended"]
        assert op["stats"]["n"] > 100 and op["stats"]["enough"]
        sgn = 1 if c["direction"] == "long" else -1
        assert sgn * (op["target"] - op["entry"]) == pytest.approx(3 * sgn * (op["entry"] - op["stop"]), rel=1e-9)
        assert sgn * (op["entry"] - op["stop"]) > 0 and op["entry"] == c["smc"]["ob_open"]
        assert sgn * (c["smc"]["top_price"] - op["stop"]) > 0          # stop beyond the top of the move
        o = op["order"]
        assert o["hold_tf"] == "D1" and o["hold_n"] == 3 and not o["market"]
        assert pd.Timestamp(c["smc"]["mss_time"]) < pd.Timestamp(op["decision_time"])
        assert pd.Timestamp(c["smc"]["ob_time"]) <= pd.Timestamp(c["smc"]["top_time"])
