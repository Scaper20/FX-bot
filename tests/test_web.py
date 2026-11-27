import re

import pandas as pd
import pytest

from web import service
from tests.conftest import csrf, login


def test_login_required_and_wrong_password(env):
    app, store, clock = env
    c = app.test_client()
    assert c.get("/").status_code == 302
    tok = csrf(c)
    r = c.post("/login", data={"password": "nope", "csrf": tok})
    assert "Wrong password" in r.get_data(as_text=True)
    login(c)
    assert c.get("/").status_code == 200


def test_post_without_csrf_is_refused(env):
    app, store, clock = env
    c = app.test_client()
    login(c)
    assert c.post("/scan", data={}).status_code == 400


def test_scan_review_and_tracking_flow(env):
    app, store, clock = env
    c = app.test_client()
    login(c)
    tok = csrf(c, "/")
    r = c.post("/scan", data={"csrf": tok, "force": "1"}, follow_redirects=True)
    html = r.get_data(as_text=True)
    assert "Scan done" in html
    live = store.list_setups(source="live")
    assert live, "scan should log ready setups"
    sid = live[0]["id"]
    card_before = live[0]["card"]
    # setup page renders charts, options and the review form
    page = c.get(f"/setup/{sid}").get_data(as_text=True)
    assert "<svg" in page and "Entry options, ranked" in page and "Your decision" in page
    opt = card_before["options"][0]["id"]
    r = c.post(f"/setup/{sid}/review", data={"csrf": tok, "decision": "take", "option_id": opt,
                                             "reasons": ["with_trend", "bogus"], "confidence": "4", "notes": "clean"})
    assert r.status_code == 302
    rv = store.list_reviews(sid)
    assert rv[-1]["decision"] == "take" and rv[-1]["reasons"] == ["with_trend"] and rv[-1]["confidence"] == 4
    # later scans: snapshot unchanged, outcomes tracked to the end
    for t in ("2023-06-07 14:00", "2023-06-09 15:00", "2023-06-20 12:00"):
        clock["now"] = pd.Timestamp(t, tz="UTC")
        service.run_scan(store, app.extensions["feed_factory"](), clock["now"], trigger="test", counts_credits=False)
    after = store.get_setup(sid)
    assert after["card"] == card_before
    assert after["final"] is True
    assert all(service.is_final(s) for s in after["status"].values())
    # journal, csv, performance render
    assert sid in c.get("/journal").get_data(as_text=True)
    csv_text = c.get("/journal.csv").get_data(as_text=True)
    assert csv_text.splitlines()[0].startswith("setup_id") and sid in csv_text
    perf = c.get("/performance").get_data(as_text=True)
    assert "Your Takes" in perf
    # actual result on a Take
    rid = rv[-1]["id"]
    c.post(f"/review/{rid}/result", data={"csrf": tok, "actual_entry": "1.2", "actual_exit": "1.19", "actual_r": "2.5", "closed": "1"})
    assert store.list_reviews(sid)[-1]["actual_r"] == 2.5


def test_practice_flow_hides_outcome_until_review(env):
    app, store, clock = env
    if not service.practice_items():
        pytest.skip("practice set not built")
    c = app.test_client()
    login(c)
    page = c.get("/practice").get_data(as_text=True)
    pid = re.search(r'action="/practice/(P-[^"]+)"', page).group(1)
    assert "target +" not in page and "stop -" not in page     # no outcome pills before review
    tok = csrf(c, "/practice")
    r = c.post(f"/practice/{pid}", data={"csrf": tok, "decision": "skip", "reasons": ["news"]})
    assert r.status_code == 302 and r.headers["Location"].endswith(f"/practice/{pid}/result")
    res = c.get(f"/practice/{pid}/result").get_data(as_text=True)
    assert "What happened" in res
    assert store.get_setup(pid)["source"] == "practice"
    assert service.practice_progress(store)["done"] == 1


def test_cron_endpoint_requires_token(env):
    app, store, clock = env
    c = app.test_client()
    assert c.post("/api/cron/scan").status_code == 401
    assert c.post("/api/cron/scan", headers={"Authorization": "Bearer wrong"}).status_code == 401
    r = c.post("/api/cron/scan", headers={"Authorization": "Bearer cron-token-123"})
    assert r.status_code == 200 and r.get_json()["ok"] is True
    clock["now"] = pd.Timestamp("2023-06-10 12:00", tz="UTC")       # Saturday
    r = c.post("/api/cron/scan", headers={"Authorization": "Bearer cron-token-123"})
    assert "skipped" in r.get_json()


def test_credit_budget_blocks_scans(env):
    app, store, clock = env

    class CountingFeed:
        calls = 0

        def frames(self, pair, now):
            raise AssertionError("must not be called")
    st = store.get_settings()
    st["daily_credit_limit"] = 10
    store.save_settings(st)
    store.add_credits(8)
    with pytest.raises(service.ScanError, match="budget"):
        service.run_scan(store, CountingFeed(), clock["now"], trigger="test", counts_credits=True)


def test_settings_and_lot_size(env):
    app, store, clock = env
    c = app.test_client()
    login(c)
    tok = csrf(c, "/settings")
    c.post("/settings", data={"csrf": tok, "spread_GBPUSD_pips": "1.2", "spread_XAUUSD": "0.25", "balance": "5000",
                              "risk_pct": "0.5", "contract_GBPUSD": "100000", "contract_XAUUSD": "100",
                              "tz": "Africa/Lagos", "daily_credit_limit": "780"})
    st = store.get_settings()
    assert st["spreads"]["GBPUSD"] == pytest.approx(0.00012) and st["balance"] == 5000
    lot = service.lot_size(st, "XAUUSD", 2000.0, 2005.0)          # $25 risk, $500 per lot -> 0.05 lots
    assert lot["lots"] == 0.05 and lot["risk_amount"] == 25.0
    lot = service.lot_size(st, "GBPUSD", 1.25, 1.2520)            # 20 pips, $200 per lot -> 0.12 lots
    assert lot["lots"] == 0.12


def test_health_reveals_no_secrets(env, monkeypatch):
    app, store, clock = env
    monkeypatch.setenv("TWELVEDATA_API_KEY", "super-secret")
    body = app.test_client().get("/api/health").get_data(as_text=True)
    assert "super-secret" not in body and '"feed_key_set":true' in body.replace(" ", "")


def test_all_pages_render(env):
    app, store, clock = env
    c = app.test_client()
    login(c)
    service.run_scan(store, app.extensions["feed_factory"](), clock["now"], trigger="test", counts_credits=False)
    for path in ("/", "/journal", "/journal?source=practice", "/performance", "/practice", "/strategy",
                 "/backtest", "/help", "/settings"):
        r = c.get(path)
        assert r.status_code == 200, path
        assert "guaranteed" not in r.get_data(as_text=True).lower()


# ------------------------------------------------------------ public practice (community)

def p_start(client, name, its_me=False):
    tok = csrf(client, "/p")
    data = {"csrf": tok, "username": name}
    if its_me:
        data["its_me"] = "1"
    return client.post("/p", data=data)


def test_public_practice_is_separate_from_ore(env):
    app, store, clock = env
    if not service.practice_items():
        pytest.skip("practice set not built")
    c = app.test_client()
    assert c.get("/p/practice").status_code == 302                       # needs a username
    assert "letters" in p_start(c, "x!").get_data(as_text=True)          # invalid name
    r = p_start(c, "Trader_One")
    assert r.status_code == 302 and r.headers["Location"].endswith("/p/practice")
    page = c.get("/p/practice").get_data(as_text=True)
    assert "Find a setup" not in page and "Settings" not in page          # no private navigation
    pid = re.search(r'action="/p/practice/(P-[^"]+)"', page).group(1)
    other = next(p for p in service.practice_items() if p["id"] != pid)["id"]
    assert c.get(f"/p/practice/{other}/result").status_code == 302      # no peeking before answering
    tok = csrf(c, "/p/practice")
    r = c.post(f"/p/practice/{pid}", data={"csrf": tok, "decision": "take", "reasons": ["gut"]})
    assert r.headers["Location"].endswith(f"/p/practice/{pid}/result")
    assert "What happened" in c.get(f"/p/practice/{pid}/result").get_data(as_text=True)
    # stored only in community tables
    assert len(store.community_reviews("trader_one")) == 1
    assert store.list_reviews() == [] and store.list_setups() == []
    # answering the same setup twice does not add a second answer
    c.post(f"/p/practice/{pid}", data={"csrf": tok, "decision": "skip"})
    assert len(store.community_reviews("trader_one")) == 1
    # a public username never opens the private site
    assert c.get("/").status_code == 302 and c.get("/journal").status_code == 302
    assert "My results" in c.get("/p/me").get_data(as_text=True)


def test_username_from_another_browser_needs_confirmation(env):
    app, store, clock = env
    a, b = app.test_client(), app.test_client()
    p_start(a, "Ade")
    r = p_start(b, "ADE")                                                 # same name, other browser
    assert r.status_code == 200 and "already in use" in r.get_data(as_text=True)
    r = p_start(b, "ade", its_me=True)
    assert r.status_code == 302
    r = p_start(a, "ade")                                                 # original browser: no question
    assert r.status_code == 302


def test_each_trader_gets_own_order_and_daily_limit(env, monkeypatch):
    app, store, clock = env
    from web import community
    if not service.practice_items():
        pytest.skip("practice set not built")
    o1, o2 = community.order_for("a"), community.order_for("b")
    assert [p["id"] for p in o1] != [p["id"] for p in o2]
    assert sorted(p["id"] for p in o1) == sorted(p["id"] for p in o2)
    monkeypatch.setattr(community, "DAILY_LIMIT", 2)
    store.community_add_user("lim", "lim", "h")
    rv = {"decision": "skip", "option_id": None, "reasons": [], "notes": "", "confidence": None}
    res = [community.save(store, "lim", it, rv) for it in o1[:3]]
    assert res == ["saved", "saved", "limit"]


def test_ore_sees_community_stats(env):
    app, store, clock = env
    if not service.practice_items():
        pytest.skip("practice set not built")
    from web import community
    store.community_add_user("kemi", "Kemi", "h")
    for it in community.order_for("kemi")[:5]:
        community.save(store, "kemi", it, {"decision": "take", "option_id": None, "reasons": [], "notes": "",
                                           "confidence": None})
    c = app.test_client()
    login(c)
    page = c.get("/performance").get_data(as_text=True)
    assert "Community practice" in page and "Kemi" in page and "/p" in page


# ------------------------------------------------------------ interactive chart data

TF_SECONDS = {"M5": 300, "M15": 900, "H1": 3600, "H4": 14400, "D1": 86400}


def test_practice_chart_hides_outcome_until_answered(env):
    app, store, clock = env
    if not service.practice_items():
        pytest.skip("practice set not built")
    c = app.test_client()
    p_start(c, "Chartist")
    page = c.get("/p/practice").get_data(as_text=True)
    pid = re.search(r'action="/p/practice/(P-[^"]+)"', page).group(1)
    assert f'data-src="/p/api/chart/{pid}"' in page
    data = c.get(f"/p/api/chart/{pid}").get_json()
    assert set(data["tfs"]) == {"M5", "M15", "H1", "H4", "D1"} and data["after"] == {}
    item = service.practice_item(pid)
    trigger = pd.Timestamp(item["card"]["decision_time"]).value // 10**9
    for tf, rows in data["tfs"].items():
        assert rows[-1][0] + TF_SECONDS[tf] <= trigger + 1, tf        # last candle closed by the trigger
    other = next(p for p in service.practice_items() if p["id"] != pid)["id"]
    assert c.get(f"/p/api/chart/{other}").get_json()["after"] == {}     # unanswered: still hidden
    tok = csrf(c, "/p/practice")
    c.post(f"/p/practice/{pid}", data={"csrf": tok, "decision": "skip"})
    after = c.get(f"/p/api/chart/{pid}").get_json()["after"]
    assert after and after["M5"] and after["M5"][0][0] >= data["tfs"]["M5"][-1][0]


def test_live_setup_chart_has_all_timeframes_and_levels(env):
    app, store, clock = env
    c = app.test_client()
    login(c)
    service.run_scan(store, app.extensions["feed_factory"](), clock["now"], trigger="test", counts_credits=False)
    sid = store.list_setups(source="live")[0]["id"]
    assert f'data-src="/api/chart/setup/{sid}' in c.get(f"/setup/{sid}").get_data(as_text=True)
    data = c.get(f"/api/chart/setup/{sid}").get_json()
    assert set(data["tfs"]) == {"M5", "M15", "H1", "H4", "D1"}
    titles = {lv["title"] for lv in data["levels"]}
    assert {"Range high", "Range low", "Entry", "Stop", "Target"} <= titles
    assert data["tz_offset"] == 0                                      # GMT+0, same candles as Exness MT5
    lv = {x["title"]: x for x in data["levels"]}
    row = store.get_setup(sid)
    r0 = int(pd.Timestamp(row["card"]["range_open"]).value // 10**9)
    assert lv["Range high"]["from"] == r0 and lv["Range low"]["from"] == r0   # range lines start at the range candle
    mk = {m["kind"]: m for m in data["markers"]}
    assert mk["range"]["time"] == r0 and mk["sweep"]["end"] > mk["sweep"]["time"]
    # the trigger marker is the trigger candle (its open), not the candle after it
    trig_candles = [b[0] for b in data["tfs"][data["default_tf"]]]
    assert mk["trigger"]["time"] in trig_candles
    assert mk["trigger"]["time"] < lv["Entry"]["from"] + 1 and data["direction"] in ("long", "short")
    assert c.get("/api/chart/setup/does-not-exist").status_code == 404
    anon = app.test_client()
    assert anon.get(f"/api/chart/setup/{sid}").status_code == 302      # private: login needed


def test_order_block_strategy_logged_and_shown_separately(env):
    app, store, clock = env
    c = app.test_client()
    login(c)
    feed = app.extensions["feed_factory"]()
    sid = None
    for day in pd.date_range("2023-03-01", "2023-07-20", freq="1D", tz="UTC"):
        if day.weekday() >= 5:
            continue
        service.run_scan(store, feed, day + pd.Timedelta("15h"), trigger="test", counts_credits=False)
        sid = next((r["id"] for r in store.list_setups(source="live") if r["card"].get("model")), None)
        if sid:
            break
    assert sid, "expected an order-block setup to be logged"
    page = c.get(f"/setup/{sid}").get_data(as_text=True)
    assert "H1 order block" in page and "matches the order-block rules" in page and "Range high" not in page
    assert "watch-only" not in page and "is not reliable" in page        # honest evidence stays shown
    data = c.get(f"/api/chart/setup/{sid}").get_json()
    titles = {lv["title"] for lv in data["levels"]}
    assert {"Entry (order block open)", "Stop", "Target 3R"} <= titles
    long = store.get_setup(sid)["direction"] == "long"
    assert ("Bottom of the move" if long else "Top of the move") in titles
    assert ("Swing high broken (MSS)" if long else "Swing low broken (MSS)") in titles
    assert "order block" in data["marker_key"]
    perf = c.get("/performance").get_data(as_text=True)
    assert "Live · Order block" in perf and "Live · CRT" in perf and "Live · all strategies together" in perf
    ob = service.performance(store, "live", "smc_ob")
    crt = service.performance(store, "live", "crt")
    both = service.performance(store, "live")
    assert ob["rows"] >= 1 and ob["rows"] + crt["rows"] == both["rows"]       # split adds up, nothing lost
    assert ob["groups"]["system"]["setups"] >= 1                               # now recommended
    home = c.get("/?strategy=smc_ob").get_data(as_text=True)
    assert "Matches the rules, still actionable · Order block" in home and "CRT armed" not in home
    assert "Order block: what it's waiting for" in home and "of 3:" in home
    assert "Order block: what it" not in c.get("/?strategy=crt").get_data(as_text=True)
    jr = c.get("/journal?strategy=crt").get_data(as_text=True)
    assert sid not in jr and sid in c.get("/journal?strategy=smc_ob").get_data(as_text=True)
    plan_page = c.get("/plan").get_data(as_text=True)
    assert "By strategy" in plan_page and "Order block" in plan_page
