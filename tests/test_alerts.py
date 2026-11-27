import pandas as pd
import pytest

from web import alerts, mailer, service


class Outbox(list):
    def __call__(self, to, subject, html, text, tags=None, idempotency_key=None, **kw):
        self.append({"to": to, "subject": subject, "text": text, "html": html, "tags": tags})
        return {"id": "x"}


@pytest.fixture()
def box(monkeypatch):
    b = Outbox()
    monkeypatch.setattr(mailer, "send", b)
    monkeypatch.setattr(mailer, "configured", lambda: True)
    return b


def scan(app, store, t):
    return service.run_scan(store, app.extensions["feed_factory"](), pd.Timestamp(t, tz="UTC"), trigger="test",
                            counts_credits=False, base_url="https://site.example")


def owner(store, **al):
    st = store.get_settings()
    st["owner_email"] = "me@example.com"
    st["alerts"] = {**alerts.DEFAULTS, **al}
    store.save_settings(st)


def test_transitions():
    assert alerts.transition({"status": "pending"}, {"status": "filled", "state": "open"}) == "filled"
    assert alerts.transition({"status": "filled", "state": "open"}, {"status": "filled", "state": "target", "R": 3}) == "target"
    assert alerts.transition({"status": "filled", "state": "target"}, {"status": "filled", "state": "target"}) is None
    assert alerts.transition({"status": "pending"}, {"status": "expired"}) == "expired"
    assert alerts.transition(None, {"status": "pending"}) is None


def test_no_owner_email_means_no_alerts(env, box):
    app, store, clock = env
    scan(app, store, "2023-06-07 10:15")
    assert box == []


def test_scan_alerts_updates_and_digest(env, box):
    app, store, clock = env
    owner(store, filtered=True)
    # scan forward through a week until the first setup is logged (independent of which day has one)
    t0 = None
    for t in pd.date_range("2023-06-05 08:15", "2023-06-16 16:15", freq="2h", tz="UTC"):
        if t.weekday() >= 5:
            continue
        row = scan(app, store, str(t.tz_localize(None)))
        if store.list_setups(source="live"):
            t0 = t
            break
    assert t0 is not None, "no setup found in two weeks of replay"
    assert len(box) <= 1
    if box:
        assert box[0]["to"] == "me@example.com" and "new setup" in box[0]["subject"]
        assert "https://site.example/setup/" in box[0]["text"]
        assert "alert emailed" in row["message"]
    for r in store.list_setups(source="live"):              # Ore takes everything he saw
        store.add_review({"setup_id": r["id"], "decision": "take", "option_id": r["card"]["best"]})
    n0 = len(box)
    for d in range(1, 12):
        t = t0 + pd.Timedelta(days=d)
        if t.weekday() < 5:
            scan(app, store, str(t.tz_localize(None)))
    updates = [e for e in box[n0:] if "update" in e["subject"]]
    assert updates, "expected trade update emails as logged setups resolved"
    assert all(e["subject"].startswith("Setup Scanner:") for e in box)
    # daily summary: once, after 17:00 New York
    before = len(box)
    day = (t0 + pd.Timedelta(days=14)).normalize()
    while day.weekday() >= 5:
        day += pd.Timedelta(days=1)
    scan(app, store, str((day + pd.Timedelta("21h30min")).tz_localize(None)))   # 17:30 New York (summer)
    scan(app, store, str((day + pd.Timedelta("21h45min")).tz_localize(None)))
    digests = [e for e in box[before:] if "daily summary" in e["subject"]]
    assert len(digests) == 1 and "setup(s) logged" in digests[0]["text"]


def test_daily_cap(env, box):
    app, store, clock = env
    owner(store, filtered=True, max_per_day=1)
    for t in ("2023-06-07 10:15", "2023-06-07 14:00", "2023-06-08 10:00", "2023-06-09 12:00", "2023-06-12 10:00"):
        scan(app, store, t)
    assert len([e for e in box if "daily summary" not in e["subject"]]) <= 1


def test_each_strategy_has_its_own_new_setup_switch():
    crt = {"recommended": True, "strategy": "crt", "range_tf": "H4"}
    ob = {"recommended": True, "strategy": "smc_ob", "model": "smc_h1_ob"}
    old_ob = {"recommended": False, "model": "smc_h1_ob"}             # logged before it became a strategy
    p = alerts.prefs({})
    assert alerts.wanted(crt, p) and alerts.wanted(ob, p) and not alerts.wanted(old_ob, p)
    p = alerts.prefs({"alerts": {"smc": False}})
    assert alerts.wanted(crt, p) and not alerts.wanted(ob, p)
    p = alerts.prefs({"alerts": {"new": False}})
    assert not alerts.wanted(crt, p) and alerts.wanted(ob, p)
    assert alerts.kind(ob) == "H1 order block · D1+H4 trend" and alerts.kind(crt) == "H4 CRT"
    toni = {"recommended": True, "strategy": "toni", "model": "toni"}
    assert alerts.wanted(toni, alerts.prefs({})) and not alerts.wanted(toni, alerts.prefs({"alerts": {"toni": False}}))
