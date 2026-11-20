import random

import pytest

from web import plan, service
from tests.test_web import env, login, replay  # noqa: F401  (fixtures)


def seed_practice(store, rule, n, seed=1):
    items = [it for it in service.practice_items()
             if (it["outcome"].get(it["card"].get("best")) or {}).get("state") in plan.service.FINAL_STATES
             and (it["outcome"].get(it["card"]["best"]) or {}).get("status") == "filled"]
    rng = random.Random(seed)
    rng.shuffle(items)
    for it in items[:n]:
        r = float(it["outcome"][it["card"]["best"]]["R"])
        take = rule(r, rng)
        service.save_practice_review(store, it, {"decision": "take" if take else "skip", "option_id": None,
                                                 "reasons": [], "notes": "", "confidence": 3})


def test_practice_verdicts_separate_good_and_bad_judgment(env, monkeypatch):
    app, store, clock = env
    monkeypatch.setattr(plan, "DECISION", 40)              # the practice set has fewer winners than 100
    if not service.practice_items():
        pytest.skip("practice set not built")
    seed_practice(store, lambda r, g: r > 0, 1000)          # knows the future
    j = plan.judgment(store, "practice")
    assert j["n"] >= plan.DECISION and j["verdict"] == "good" and j["selection"] > 0


def test_practice_bad_picker_fails(env):
    app, store, clock = env
    if not service.practice_items():
        pytest.skip("practice set not built")
    seed_practice(store, lambda r, g: r <= 0, 220, seed=3)
    j = plan.judgment(store, "practice")
    assert j["verdict"] == "bad"


def test_empty_state_and_page(env):
    app, store, clock = env
    d = plan.build(store, store.get_settings())
    assert d["live"]["verdict"] == "early" and d["real"]["n"] == 0
    assert d["risk"]["ok"] and not d["risk"]["spreads_set"]          # default 0.25%, spreads not confirmed
    c = app.test_client()
    assert c.get("/plan").status_code == 302                          # private
    login(c)
    page = c.get("/plan").get_data(as_text=True)
    assert "My test" in page and "still the defaults" in page and "Too early" in page


def test_risk_above_plan_and_pause_rules():
    assert not plan.risk_check({"risk_pct": 1.0}, passed=False)["ok"]
    assert plan.risk_check({"risk_pct": 0.5}, passed=True)["ok"]

    class S:
        def __init__(self, rs):
            self.rs = rs
        def list_setups(self, **kw):
            return []
        def list_reviews(self, setup_id=None):
            return [{"setup_id": f"x{i}", "actual_r": r, "actual_closed_at": f"2026-11-{10 + i:02d}"}
                    for i, r in enumerate(self.rs)]
    real = plan.real_trades(S([3, -1, -1, -1, -1, -1, -1, -1, -1]))
    assert real["loss_streak"] == 8 and real["pause"] and real["drawdown"] == 8
    real = plan.real_trades(S([2, -1, 3, -1]))
    assert not real["pause"] and real["drawdown"] == 1 and real["total_R"] == 3
