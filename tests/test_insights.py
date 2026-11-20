import random

import pytest

from web import insights, service
from tests.conftest import login


def seed(store, name, rule, n=150, seed=1):
    store.community_add_user(name, name.title(), "h")
    facts = insights.item_facts()
    items = [i for i, f in facts.items() if f["best_R"] is not None]
    rng = random.Random(seed)
    rng.shuffle(items)
    for i in items[:n]:
        take = rule(facts[i]["best_R"], rng)
        store.community_add_review({"username_key": name, "item_id": i, "decision": "take" if take else "skip",
                                    "option_id": None, "reasons": ["gut"], "notes": "", "confidence": 5 if take else 2})


def test_dashboard_tells_good_random_and_bad_pickers_apart(env):
    app, store, clock = env
    if not service.practice_items():
        pytest.skip("practice set not built")
    seed(store, "oracle", lambda r, g: r > 0)                 # knows the future: must look helpful
    seed(store, "coin", lambda r, g: g.random() < 0.5, seed=2)  # random: no edge expected
    seed(store, "anti", lambda r, g: r <= 0, seed=3)           # picks losers: must look harmful
    seed(store, "newbie", lambda r, g: True, n=10, seed=4)     # too few to judge
    d = insights.build(store)
    by = {t["name"]: t for t in d["traders"]}
    assert by["Oracle"]["verdict"] == "good" and by["Oracle"]["selection"] > 0 and by["Oracle"]["sel_z"] > 2
    assert by["Anti"]["verdict"] == "bad" and by["Anti"]["selection"] < 0
    assert by["Coin"]["verdict"] in ("none", "good", "bad") and abs(by["Coin"]["sel_z"] or 0) < 3
    assert by["Newbie"]["verdict"] == "early"
    assert d["traders"][0]["name"] == "Oracle"                 # ranked first
    assert d["crowd"]["items_3plus"] >= 0 and d["baseline"]["n"] > 100
    c = app.test_client()
    login(c)
    page = c.get("/insights").get_data(as_text=True)
    assert "is the community helping" in page and "Oracle" in page and "Helping" in page and "<svg" in page


def test_dashboard_empty_state(env):
    app, store, clock = env
    c = app.test_client()
    login(c)
    page = c.get("/insights").get_data(as_text=True)
    assert "No answers yet" in page
    assert c.get("/insights").status_code == 200
    assert app.test_client().get("/insights").status_code == 302      # private
