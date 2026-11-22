import datetime as dt

import pandas as pd

from tests.conftest import csrf, login
from tests.test_email import Outbox
from web import mailer, reminders, service

NOW = dt.datetime(2026, 11, 22, 8, 7, tzinfo=dt.timezone.utc)
BASE = "https://site.test"


def people(store):
    t = "2026-11-01T00:00:00+00:00"
    store.community_add_user("amy", "Amy", "h", email="amy@x.io", email_verified_at=t, notify=True, unsub_token="tok-amy")
    store.community_add_user("bob", "Bob", "h", email="bob@x.io", email_verified_at=t, notify=False, unsub_token="tok-bob")
    store.community_add_user("cat", "Cat", "h", email="cat@x.io", email_verified_at=None, notify=True, unsub_token="tok-cat")
    store.community_add_user("dan", "Dan", "h", email="dan@x.io", email_verified_at=t, notify=True, unsub_token="tok-dan")
    item = service.practice_items()[0]["id"]          # Dan practised just now: not reminded
    store.community_add_review({"username_key": "dan", "item_id": item, "decision": "take", "option_id": None,
                                "reasons": [], "notes": "", "confidence": 3})


def setup(monkeypatch, env):
    app, store, clock = env
    box = Outbox()
    monkeypatch.setattr(mailer, "configured", lambda: True)
    people(store)
    st = store.get_settings()
    st["owner_email"] = "ore@x.io"
    store.save_settings(st)
    return app, store, box


def test_only_opted_in_inactive_traders_get_one_reminder(monkeypatch, env):
    app, store, box = setup(monkeypatch, env)
    res = reminders.run(store, store.get_settings(), NOW, BASE, send=box)
    to = [e["to"] for e in box.sent]
    assert "amy@x.io" in to                                   # opted in, verified, inactive
    assert "bob@x.io" not in to and "cat@x.io" not in to       # not opted in / not verified
    assert "dan@x.io" not in to and res["skipped_recent"] == 1  # practised in the last 24 hours
    assert "ore@x.io" in to and res["owner"] == "sent"
    amy = next(e for e in box.sent if e["to"] == "amy@x.io")
    assert f"{BASE}/p/unsubscribe/tok-amy" in amy["html"] and f"{BASE}/p/practice" in amy["text"]
    assert "first practice setup" in amy["subject"]
    # same day again: nothing. "Send now" within 12 hours: no second email to anyone already reminded
    # (Dan, who practised recently but was never reminded, may get his first one from a manual send)
    n = len(box.sent)
    reminders.run(store, store.get_settings(), NOW + dt.timedelta(hours=2), BASE, send=box)
    assert len(box.sent) == n
    reminders.run(store, store.get_settings(), NOW + dt.timedelta(hours=3), BASE, force=True, send=box)
    assert {e["to"] for e in box.sent[n:]} <= {"dan@x.io"}
    # 3 days later Amy is due again; Ore (every 2 days) too
    reminders.run(store, store.get_settings(), NOW + dt.timedelta(days=3), BASE, send=box)
    assert [e["to"] for e in box.sent[n:]].count("amy@x.io") == 1 and "ore@x.io" in [e["to"] for e in box.sent[n:]]


def test_switches_off(monkeypatch, env):
    app, store, box = setup(monkeypatch, env)
    st = store.get_settings()
    st["reminders"] = {"community": False, "owner": False}
    assert reminders.run(store, st, NOW, BASE, send=box)["sent"] == 0 and not box.sent


def test_cron_route_needs_token_and_admin_button_sends(monkeypatch, env):
    app, store, box = setup(monkeypatch, env)
    monkeypatch.setattr(mailer, "send", box)
    c = app.test_client()
    assert c.post("/api/cron/reminders").status_code == 401
    r = c.post("/api/cron/reminders", headers={"Authorization": "Bearer cron-token-123"}).get_json()
    assert r["ok"] and r["sent"] == 1
    login(c)
    page = c.get("/community").get_data(as_text=True)
    assert "Send a practice reminder now" in page
    store.community_update_user("amy", last_reminded_at=(pd.Timestamp.now(tz="UTC") - pd.Timedelta("1D")).isoformat())
    r = c.post("/community", data={"csrf": csrf(c, "/community"), "action": "remind"}, follow_redirects=True)
    assert "Practice reminder sent to 1 trader" in r.get_data(as_text=True)
