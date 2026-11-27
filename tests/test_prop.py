import json

import pandas as pd

from tests.conftest import csrf, login
from web import alerts, mailer, prop
from web.store import MemoryStore, merged_settings


def st(**p):
    s = merged_settings({})
    s["prop"] = {**prop.DEFAULTS, "on": True, **p}
    return s


def test_lot_sizes_respect_leverage():
    s = st()
    # GBP/USD 20-pip stop, 1.5% of $5,000 = $75 -> 0.37 lots; 1:30 allows ~1.13 lots on $5,000
    g = prop.lot(s, "GBPUSD", 1.3200, 1.3180)
    assert g["lots"] == 0.37 and not g["capped"] and g["risk_amount"] <= 75
    # gold $2 stop: $75 wants 0.375 lots, but 1:10 on $5,000 allows ~0.14 lots at $3,550
    x = prop.lot(s, "XAUUSD", 3550.0, 3548.0)
    assert x["capped"] and x["lots"] == 0.14 and x["risk_amount"] < 75
    assert x["margin"] <= 5000


def test_status_rooms_and_next_risk():
    s = st(balance=5150.0, peak=5250.0, day_start=5200.0, days_traded=3)
    r = prop.status(s)
    assert r["target"] == 5400.0 and r["to_target"] == 250.0
    assert r["daily_floor"] == 5050.0 and r["daily_room"] == 100.0           # 5200 - 3% of 5000
    assert r["trail_floor"] == 5000.0 and r["trail_room"] == 150.0           # 5250 - 5% of 5000
    assert r["binding"] == "daily" and r["room"] == 100.0
    assert r["next_risk"] == 75.0 and not r["warn"]                          # 1.5% fits inside 90% of the room
    tight = prop.status(st(balance=5060.0, peak=5250.0, day_start=5100.0))
    assert tight["warn"] and tight["next_risk"] < 75.0


def test_news_parse_refresh_and_upcoming():
    payload = [
        {"title": "Non-Farm Employment Change", "country": "USD", "date": "2026-12-04T08:30:00-05:00", "impact": "High"},
        {"title": "CPI m/m", "country": "GBP", "date": "2026-12-03T02:00:00-05:00", "impact": "High"},
        {"title": "Retail Sales", "country": "EUR", "date": "2026-12-03T05:00:00-05:00", "impact": "High"},
        {"title": "Minor", "country": "USD", "date": "2026-12-03T10:00:00-05:00", "impact": "Low"},
    ]
    ev = prop.parse_news(payload)
    assert [e["currency"] for e in ev] == ["GBP", "EUR", "USD"] and ev[-1]["time"].startswith("2026-12-04T13:30")

    class Resp:
        def __init__(self, b): self.b = b
        def read(self): return self.b
        def __enter__(self): return self
        def __exit__(self, *a): return False
    calls = []

    def opener(req, timeout):
        calls.append(req.full_url)
        return Resp(json.dumps(payload).encode())
    store = MemoryStore()
    now = pd.Timestamp("2026-12-03 06:00", tz="UTC")
    assert "3 high-impact" in prop.refresh_news(store, now, opener)
    assert prop.refresh_news(store, now + pd.Timedelta("1h"), opener) is None and len(calls) == 1   # 6-hour cache
    up = prop.upcoming(store, now, hours=48, pair="XAUUSD")
    assert [e["currency"] for e in up] == ["USD"]                           # gold: USD news only
    assert {e["currency"] for e in prop.upcoming(store, now, hours=48, pair="GBPUSD")} == {"GBP", "USD"}

    def broken(req, timeout):
        raise OSError("down")
    assert "not refreshed" in prop.refresh_news(MemoryStore(), now, broken)  # never raises


def test_prop_page_plan_tracker_and_settings_keep_it(env):
    app, store, clock = env
    c = app.test_client()
    login(c)
    page = c.get("/prop").get_data(as_text=True)
    assert "Prop account" in page and "prop mode off" in page
    tok = csrf(c, "/prop")
    c.post("/prop", data={"csrf": tok, "what": "plan", "on": "1", "firm": "Equity Edge · 1-Step Swift", "size": "5000",
                          "target_pct": "8", "daily_pct": "3", "trailing_pct": "5", "risk_pct": "1.5", "lev_GBPUSD": "30",
                          "lev_XAUUSD": "10", "strategies": ["ore_poi", "irl_erl"], "news_min": "2"})
    c.post("/prop", data={"csrf": tok, "what": "tracker", "balance": "5150", "day_start": "5200", "peak": "5250",
                          "days_traded": "3"})
    p = prop.plan(store.get_settings())
    assert p["on"] and p["strategies"] == ["ore_poi", "irl_erl"] and p["balance"] == 5150 and p["peak"] == 5250
    page = c.get("/prop").get_data(as_text=True)
    assert "prop mode on" in page and "$5050.00" in page                       # daily floor shown
    home = c.get("/").get_data(as_text=True)
    assert "Prop mode" in home and "next trade risk at most" in home
    # saving the ordinary Settings page keeps the prop account
    s = c.get("/settings").get_data(as_text=True)
    assert s
    c.post("/settings", data={"csrf": csrf(c, "/settings"), "spread_GBPUSD_pips": "1.0", "spread_XAUUSD": "0.24",
                              "balance": "1000", "risk_pct": "0.25", "contract_GBPUSD": "100000",
                              "contract_XAUUSD": "100", "daily_credit_limit": "780"})
    assert prop.plan(store.get_settings())["on"]


def test_prop_mode_emails_only_plan_strategies(monkeypatch):
    sent = []
    monkeypatch.setattr(mailer, "send", lambda to, subject, html, text, **kw: sent.append(text) or {"id": "x"})
    monkeypatch.setattr(mailer, "configured", lambda: True)
    store = MemoryStore()
    s = st()
    s["owner_email"] = "me@example.com"
    s["alerts"] = dict(alerts.DEFAULTS)

    def card(strategy, cid):
        op = {"id": "o", "entry": 1.3, "stop": 1.29, "target": 1.33, "rr": 3.0, "chance": 0.25, "entry_tf": "H1",
              "trigger": "SMC", "decision_time": "2026-12-01T10:00:00+00:00"}
        return {"id": cid, "strategy": strategy, "pair": "GBPUSD", "direction": "long", "recommended": True,
                "range_tf": "H1", "options": [op]}
    note = alerts.send_scan_alert(store, s, [card("crt", "a"), card("ore_poi", "b")], [], "https://x")
    assert note and len(sent) == 1 and "Ore's model" in sent[0] and "CRT" not in sent[0]
