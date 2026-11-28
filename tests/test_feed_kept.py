"""Feed rework (28 Nov 2026): scans fetch only M5 and rebuild M15/H1 on top of candles kept from earlier scans."""
import pandas as pd
import pytest

from engine import config as K
from engine.candles import clean, load_m1_csv
from engine.feeds import twelvedata as TD
from engine.feeds.replay import ReplayFeed
from engine.setups import Market
from web import service
from web.store import MemoryStore


@pytest.fixture(scope="module")
def replay3():
    m1 = {p: clean(load_m1_csv(K.LIVE_PAIRS[p]["file"]))[0] for p in K.LIVE_PAIRS}
    return ReplayFeed({p: d[(d.index >= "2023-01-01") & (d.index < "2023-08-01")] for p, d in m1.items()})


class KeptFeed:
    """Twelve-Data-like feed over replay candles: 1 call (M5) when kept candles allow it, else 3."""
    uses_kept = True

    def __init__(self, replay):
        self.r, self.calls, self.modes = replay, 0, {}

    def history_h1(self, pair, end):
        self.calls += 1
        return self.r.history_h1(pair, end)

    def frames(self, pair, now, kept=None):
        fr = self.r.frames(pair, now)
        self.last_mode = "full"
        if TD.plan_fetch(kept, now) == "light":
            self.calls += 1
            out = TD.extend_from_m5(kept, fr["M5"])
            if out is not None:
                self.last_mode = self.modes[pair] = "light"
                return out
        self.calls += 3
        self.modes[pair] = "full"
        return fr


def _kept(replay, pair, t):
    m = Market.from_frames(replay.frames(pair, t), t)
    return {tf: m.frames[tf][["open", "high", "low", "close"]].tail(n) for tf, n in TD.KEEP.items()}


def test_m5_rebuild_matches_a_full_fetch(replay3):
    t1 = pd.Timestamp("2023-06-05 10:15", tz="UTC")
    t2 = t1 + pd.Timedelta("2D")
    kept = _kept(replay3, "EURUSD", t1)
    full = replay3.frames("EURUSD", t2)
    out = TD.extend_from_m5(kept, full["M5"])
    for tf in ("M15", "H1"):
        a = Market.from_frames({**out, "M5": full["M5"]}, t2).frames[tf]
        b = Market.from_frames(full, t2).frames[tf]
        common = a.index.intersection(b.index[1:])              # the replay window's first candle is cut short
        assert len(common) > 0.9 * len(b)
        assert (a.loc[common, ["open", "high", "low", "close"]] - b.loc[common, ["open", "high", "low", "close"]]).abs().max().max() < 1e-9
        assert a.index[-1] == b.index[-1] and not a.index.has_duplicates


def test_gap_or_stale_kept_candles_mean_a_full_fetch(replay3):
    t1 = pd.Timestamp("2023-05-01 10:00", tz="UTC")
    kept = _kept(replay3, "GBPUSD", t1)
    assert TD.plan_fetch(kept, t1 + pd.Timedelta("1h")) == "light"
    assert TD.plan_fetch(kept, t1 + pd.Timedelta("6D")) == "full"
    assert TD.plan_fetch(None, t1) == "full"
    assert TD.plan_fetch({"M15": kept["M15"].tail(100), "H1": kept["H1"]}, t1) == "full"
    later = replay3.frames("GBPUSD", t1 + pd.Timedelta("30D"))["M5"]
    assert TD.extend_from_m5(kept, later) is None


def test_scans_stay_under_8_calls_and_switch_to_m5_only(replay3):
    store = MemoryStore()
    feed = KeptFeed(replay3)
    t = pd.Timestamp("2023-06-07 10:15", tz="UTC")
    service.run_scan(store, feed, t, trigger="test", counts_credits=True)
    first = feed.calls
    assert first <= TD.MAX_CALLS_PER_MINUTE
    msg = store.recent_scans(1)[0]["message"]
    assert "EURUSD: waiting for a full candle download" in msg           # 3 + 3 calls, no room for a third 3
    for p in ("GBPUSD", "XAUUSD"):
        assert len(store.get_candles(p)["H1_feed"]) >= 1500 and len(store.get_candles(p)["M15_feed"]) == 1500
    feed.calls = 0
    service.run_scan(store, feed, t + pd.Timedelta("15min"), trigger="test", counts_credits=True)
    assert feed.calls <= TD.MAX_CALLS_PER_MINUTE
    assert {p: feed.modes[p] for p in ("GBPUSD", "XAUUSD", "EURUSD")} == {"GBPUSD": "light", "XAUUSD": "light", "EURUSD": "full"}
    for k in range(2, 5):                                                   # later pairs get their full download in turn
        feed.calls = 0
        service.run_scan(store, feed, t + pd.Timedelta(f"{15 * k}min"), trigger="test", counts_credits=True)
        assert feed.calls <= TD.MAX_CALLS_PER_MINUTE
    assert set(feed.modes) == set(K.LIVE_PAIRS) and set(feed.modes.values()) == {"light"}


def test_eurusd_settings_and_prop_news():
    from web import prop
    assert {"EUR", "USD", "GBP"} <= set().union(*(prop.CURRENCIES[p] for p in K.LIVE_PAIRS))
    assert prop.plan({})["leverage"]["EURUSD"] == 30
    assert K.fmt_distance("EURUSD", 0.00123) == "12.3 pips" and K.fmt_distance("XAUUSD", 4.2) == "$4.20"
    assert K.fmt_price("EURUSD", 1.0812345) == "1.08123" and K.fmt_price("XAUUSD", 2650.456) == "2,650.46"


def test_settings_form_saves_eurusd(env):
    from tests.conftest import csrf, login
    app, store, clock = env
    c = app.test_client()
    login(c)
    page = c.get("/settings").get_data(as_text=True)
    assert 'name="spread_EURUSD_pips"' in page and 'name="contract_EURUSD"' in page
    tok = csrf(c, "/settings")
    c.post("/settings", data={"csrf": tok, "spread_GBPUSD_pips": "1.0", "spread_XAUUSD": "0.24", "spread_EURUSD_pips": "0.8",
                              "balance": "5000", "risk_pct": "0.5", "contract_GBPUSD": "100000", "contract_XAUUSD": "100",
                              "contract_EURUSD": "100000", "tz": "Africa/Lagos", "daily_credit_limit": "780"})
    st = store.get_settings()
    assert st["spreads"]["EURUSD"] == pytest.approx(0.00008) and st["spreads"]["XAGUSD"] == pytest.approx(0.025)
    assert 'name="lev_EURUSD"' in c.get("/prop").get_data(as_text=True)


def test_usdchf_lots_are_priced_in_usd():
    """USD/CHF moves are in CHF: risk per lot = distance x 100,000 / price; one lot is worth $100,000."""
    from web import prop
    from web.store import merged_settings
    st = merged_settings({})
    assert "USDCHF" in K.LIVE_PAIRS and st["spreads"]["USDCHF"] == pytest.approx(0.00015)
    r = service.lot_size({**st, "balance": 5000, "risk_pct": 1.0}, "USDCHF", 0.8000, 0.7980)   # 20 pips
    assert r["per_lot"] == pytest.approx(250.0)                       # 0.0020 x 100,000 CHF = 200 CHF = $250
    assert r["lots"] == 0.2
    pl = prop.lot({**st, "prop": {**st.get("prop", {}), "on": True}}, "USDCHF", 0.8000, 0.7980)
    assert pl["max_lots"] == pytest.approx(5000 * 30 / 100000, abs=0.01)
    assert K.fmt_distance("USDCHF", 0.0020) == "20.0 pips" and K.fmt_price("USDCHF", 0.81234567) == "0.81235"
    assert "CHF" in set().union(*(prop.CURRENCIES[p] for p in K.LIVE_PAIRS))
