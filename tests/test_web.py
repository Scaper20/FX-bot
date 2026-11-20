import re

import pandas as pd
import pytest

from engine import config as K
from engine.candles import clean, load_m1_csv
from engine.feeds.replay import ReplayFeed
from web import service
from web.app import create_app
from web.store import MemoryStore


@pytest.fixture(scope="module")
def replay():
    m1 = {p: clean(load_m1_csv(K.PAIRS[p]["file"]))[0] for p in K.PAIRS}
    return ReplayFeed({p: d[(d.index >= "2023-01-01") & (d.index < "2023-08-01")] for p, d in m1.items()})


@pytest.fixture()
def env(monkeypatch, replay):
    monkeypatch.setenv("LOCAL_DEV", "1")
    monkeypatch.setenv("FEED", "replay")
    monkeypatch.delenv("SITE_PASSWORD", raising=False)
    clock = {"now": pd.Timestamp("2023-06-07 10:15", tz="UTC")}
    store = MemoryStore()
    store.db["secrets"]["cron"] = "cron-token-123"
    app = create_app(store=store, feed=replay, now_fn=lambda: clock["now"])
    app.config["TESTING"] = True
    return app, store, clock


def csrf(client, path="/login"):
    html = client.get(path).get_data(as_text=True)
    return re.search(r'name="csrf" value="([0-9a-f]+)"', html).group(1)


def login(client):
    tok = csrf(client)
    r = client.post("/login", data={"password": "local", "csrf": tok})
    assert r.status_code == 302


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
