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
    row = scan(app, store, "2023-06-07 10:15")
    assert len(box) <= 1
    if box:
        assert box[0]["to"] == "me@example.com" and "new setup" in box[0]["subject"]
        assert "https://site.example/setup/" in box[0]["text"]
        assert "alert emailed" in row["message"]
    for r in store.list_setups(source="live"):              # Ore takes everything he saw
        store.add_review({"setup_id": r["id"], "decision": "take", "option_id": r["card"]["best"]})
    n0 = len(box)
    for t in ("2023-06-07 14:00", "2023-06-08 10:00", "2023-06-09 12:00", "2023-06-12 10:00"):
        scan(app, store, t)
    updates = [e for e in box[n0:] if "update" in e["subject"]]
    assert updates, "expected trade update emails as logged setups resolved"
    assert all(e["subject"].startswith("CRT Scanner:") for e in box)
    # daily summary: once, after 17:00 New York
    before = len(box)
    scan(app, store, "2023-06-12 21:30")          # 17:30 New York
    scan(app, store, "2023-06-12 21:45")
    digests = [e for e in box[before:] if "daily summary" in e["subject"]]
    assert len(digests) == 1 and "setup(s) logged" in digests[0]["text"]


def test_daily_cap(env, box):
    app, store, clock = env
    owner(store, filtered=True, max_per_day=1)
    for t in ("2023-06-07 10:15", "2023-06-07 14:00", "2023-06-08 10:00", "2023-06-09 12:00", "2023-06-12 10:00"):
        scan(app, store, t)
    assert len([e for e in box if "daily summary" not in e["subject"]]) <= 1
