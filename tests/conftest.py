"""Shared test fixtures and helpers (pytest loads this file automatically)."""
import re

import pandas as pd
import pytest

from engine import config as K
from engine.candles import clean, load_m1_csv
from engine.feeds.replay import ReplayFeed
from web.app import create_app
from web.store import MemoryStore


@pytest.fixture(scope="module")
def replay():
    m1 = {p: clean(load_m1_csv(K.LIVE_PAIRS[p]["file"]))[0] for p in K.LIVE_PAIRS}
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
