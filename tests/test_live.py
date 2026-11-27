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


def test_smc_live_cards_follow_spec_v22(feed):
    """Order block, Toni and Lingard cards: built by engine/smc_models (same code as backtest/smc_v22),
    bias agrees, zone and structure finished by the decision, stop beyond the entry, targets per strategy."""
    from engine.smc_live import MODELS, bias_value, scan_smc_pair
    found = []
    for t in pd.date_range("2023-03-01", "2023-06-28", freq="5h", tz="UTC"):
        if t.weekday() >= 5:
            continue
        for pair, mkt in markets(feed, t).items():
            for c in scan_smc_pair(mkt, pair, SPREADS[pair]):
                m = MODELS[c["strategy"]]
                dec = pd.Timestamp(c["decision_time"])
                for tf in m["bias"]:
                    assert bias_value(mkt, tf, dec.value) == (1 if c["direction"] == "long" else -1)
                found.append(c)
    kinds = {c["strategy"] for c in found}
    assert {"smc_ob", "toni"} <= kinds, f"expected order-block and Toni setups in the replay, got {kinds}"
    for c in found:
        op = c["options"][0]
        z, ln = c["smc"]["zone"], c["smc"]["line"]
        assert c["recommended"] and op["recommended"] and c["model"] == c["strategy"]
        sgn = 1 if c["direction"] == "long" else -1
        assert sgn * (op["entry"] - op["stop"]) > 0 and sgn * (op["target"] - op["entry"]) > 0
        assert z["low"] <= op["entry"] <= z["high"] or c["strategy"] == "toni"
        assert pd.Timestamp(z["start"]) <= pd.Timestamp(op["decision_time"])
        assert pd.Timestamp(ln["end"]) < pd.Timestamp(op["decision_time"])
        risk = abs(op["entry"] - op["stop"])
        if c["strategy"] in ("smc_ob", "irl_erl", "ore_poi"):
            assert abs(op["target"] - op["entry"]) == pytest.approx(3 * risk, rel=1e-9)
        if c["strategy"] == "ore_poi":
            hp, og = c["smc"]["htf_poi"], c["smc"]["origin"]
            assert hp["type"] in ("OB", "FVG") and hp["low"] <= og["price"] <= hp["high"]
            assert pd.Timestamp(hp["start"]) <= pd.Timestamp(og["time"]) and pd.Timestamp(hp["touch"]) <= pd.Timestamp(og["time"])
        if c["strategy"] == "lingard":
            assert abs(op["target"] - op["entry"]) == pytest.approx(5 * risk, rel=1e-9)
            assert op["session"] != ""
        o = op["order"]
        assert o["hold_tf"] == "D1" and o["hold_n"] == MODELS[c["strategy"]]["hold"] and not o["market"]
        ie = c["smc"]["irl_erl"]
        assert set(ie) == {"H4", "D1"} and all(v["bias"] in (-1, 0, 1) and isinstance(v["agrees"], bool) for v in ie.values())


def test_smc_watch_level_is_the_one_the_strategy_breaks(feed):
    """Order-block heads-up: when it says 'waiting for the H1 MSS' at a level, and the next H1 candle closes past
    that level, the structure engine reports an MSS on that candle breaking that same level."""
    from engine.smc_live import watch_smc_pair
    from engine.smc_structure import external_structure
    titles, checked = set(), 0
    for t in pd.date_range("2023-03-06 08:00", "2023-06-26 16:00", freq="3h", tz="UTC"):
        if t.weekday() >= 5:
            continue
        for pair, mkt in markets(feed, t).items():
            ws = watch_smc_pair(mkt, pair)
            assert {w["strategy"] for w in ws} == {"smc_ob", "irl_erl", "toni", "lingard", "ore_poi"}
            for w in ws:
                titles.add(w["title"])
                assert (w["direction"] is None) == (w["step"] == 1)
            w = next(x for x in ws if x["strategy"] == "smc_ob")
            if not w["title"].startswith("Waiting for the H1 MSS"):
                continue
            t2 = t + pd.Timedelta("1h")
            nxt = Market.from_frames(feed.frames(pair, t2), t2)
            F, F0 = nxt.frames["H1"], mkt.frames["H1"]
            if F.index[-1] <= F0.index[-1]:
                continue                                   # no new H1 candle (weekend / gap)
            c_last = float(F["close"].iloc[-1])
            up = w["direction"] == "long"
            closed_past = c_last > w["level"] if up else c_last < w["level"]
            ev = external_structure(*(F[k].to_numpy(float) for k in ("open", "high", "low", "close")), "close")
            fired = [e for e in ev if e["j"] == len(F) - 1 and e["kind"] == "MSS" and e["dir"] == (1 if up else -1)]
            assert bool(fired) == closed_past, (pair, t, w["level"], c_last)
            if fired:
                assert fired[0]["level"] == pytest.approx(w["level"])
                checked += 1
    assert "Bias" in titles and "Waiting for the H1 MSS" in titles
    assert checked >= 1, "expected at least one MSS right after a heads-up in the replay"


def test_ore_poi_setups_follow_spec_v26(feed):
    """Ore's model: every setup's top/bottom sits in a fresh H4 OB/FVG on its first tap (never a breaker), the
    pattern finishes within 30 M15 candles of it, one setup per decision, the breaker entry preferred."""
    from engine.smc_live import htf_poi
    from engine.smc_models import ore_poi_setups, ore_reversal_setups
    from engine.smc_structure import external_structure
    n_all = 0
    for t, pair, mkt in [(t, p, m) for t in pd.date_range("2023-03-10", "2023-06-28", freq="14D", tz="UTC")
                         for p, m in markets(feed, t + pd.Timedelta("12h")).items()]:
        F = mkt.frames["M15"]
        o, h, l, c = (F[k].to_numpy(float) for k in ("open", "high", "low", "close"))
        to = F.index.as_unit("ns").asi8
        ev = external_structure(o, h, l, c, "wick")
        Z = htf_poi(mkt)
        ss = ore_poi_setups(o, h, l, c, ev, Z, to, 900)
        keys = [(s["decision"], s["dir"]) for s in ss]
        assert len(keys) == len(set(keys))
        bb = {(s["decision"], s["dir"]) for s in ore_reversal_setups(o, h, l, c, ev) if s["variant"] == "BB"}
        for s in ss:
            z, top, d = s["htf_poi"], s["top"], s["dir"]
            px = h[top] if d == -1 else l[top]
            assert z["type"] in ("OB", "FVG") and z["lo"] <= px <= z["hi"]
            assert z["created"] <= to[top] and to[top] - 20 * 900 * 10**9 <= z["touch"] <= to[top]
            assert 0 < s["decision"] - top <= 30
            assert (s["variant"] == "BB") == ((s["decision"], d) in bb)
        n_all += len(ss)
    assert n_all > 0, "expected some Ore's-model setups in the replay"


def test_watch_lines_carry_chat_steps_and_chart_drawings(feed):
    """Each tracking line has chat steps (done before the current step, one 'now', the rest 'next', ending with the
    setup card) and chart drawings whose levels and marks exist by the scan time."""
    from engine.smc_live import PLAN, watch_smc_pair
    t = pd.Timestamp("2023-04-19 11:00", tz="UTC")
    for pair, mkt in markets(feed, t).items():
        for w in watch_smc_pair(mkt, pair):
            st = [m["state"] for m in w["story"]]
            assert len(st) == len(PLAN[w["strategy"]]) == w["steps"]
            assert st == ["done"] * (w["step"] - 1) + ["now"] + ["next"] * (w["steps"] - w["step"])
            for lv in w["draw"]["levels"]:
                assert pd.Timestamp(lv["from"]) <= t and lv["price"] > 0
            for m in w["draw"]["marks"]:
                assert pd.Timestamp(m["time"]) <= t
            if w["level"] is not None and w["step"] > 1 and w["strategy"] != "toni":
                assert any(abs(lv["price"] - w["level"]) < 1e-9 for lv in w["draw"]["levels"]) or \
                    w["strategy"] == "ore_poi"
