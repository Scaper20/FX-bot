"""My test (docs/plan-judgment.md): does Ore's judgment add an edge, and is his risk within the plan?"""
from __future__ import annotations

from engine.strategies import STRATEGIES, strategy_of

from . import service
from .insights import _mean, _r, _z_diff, _z_vs

FIRST_READ = 30
DECISION = 100
RISK_BEFORE = 0.25
RISK_AFTER = 0.5
RISK_MAX = 1.0
PAUSE_DD_R = 10.0
PAUSE_STREAK = 8
GAP_WARN = -0.2


def judgment(store, source: str, strategy: str | None = None) -> dict:
    """Take results vs chance, and Takes vs Skips, for one source (live or practice).
    strategy=None is the pre-registered test (all strategies together); an id gives that strategy alone."""
    latest = {}
    for rv in store.list_reviews():
        latest[rv["setup_id"]] = rv
    take_R, take_ch, sel_take, sel_skip = [], [], [], []
    counts = {"take": 0, "skip": 0, "unsure": 0}
    for row in store.list_setups(source=source, limit=5000):
        rv = latest.get(row["id"])
        if not rv or (strategy and strategy_of(row["card"]) != strategy):
            continue
        counts[rv["decision"]] = counts.get(rv["decision"], 0) + 1
        _, best_st = service._option_outcome(row, None)
        best_R = _r(best_st)
        if rv["decision"] == "take":
            op, st = service._option_outcome(row, rv.get("option_id"))
            r = _r(st)
            if r is not None and op:
                take_R.append(r)
                take_ch.append(op["chance_avg_R"])
            if best_R is not None:
                sel_take.append(best_R)
        elif rv["decision"] == "skip" and best_R is not None:
            sel_skip.append(best_R)
    avg, chance = _mean(take_R), _mean(take_ch)
    n = len(take_R)
    edge = None if avg is None or chance is None else avg - chance
    z = _z_vs(take_R, chance)
    sel = None if not sel_take or not sel_skip else _mean(sel_take) - _mean(sel_skip)
    if n < FIRST_READ:
        stage, verdict, text = "early", "early", f"Too early: {n} of {FIRST_READ} finished Takes for a first read."
    elif n < DECISION:
        stage = "read"
        if z is not None and z <= -2:
            verdict, text = "bad", "First read: clearly worse than chance. Plan says: no real money, demo only."
        else:
            verdict, text = "none", f"First read: no alarm. Decision at {DECISION} finished Takes ({DECISION - n} to go)."
    else:
        stage = "decision"
        if edge is not None and edge > 0 and z is not None and z >= 2 and sel is not None and sel > 0:
            verdict, text = "good", "PASS: your Takes beat chance and beat your Skips."
        else:
            verdict, text = "bad", "FAIL: no clear evidence your judgment adds an edge. Plan says: stay on demo or stop."
    return {"n": n, "avg_R": avg, "chance_R": chance, "edge": edge, "z": z, "total_R": sum(take_R),
            "win_rate": (sum(1 for r in take_R if r > 0) / n) if n else None,
            "selection": sel, "sel_z": _z_diff(sel_take, sel_skip), "sel_n": (len(sel_take), len(sel_skip)),
            "counts": counts, "stage": stage, "verdict": verdict, "verdict_text": text,
            "progress": min(n / DECISION, 1.0)}


def real_trades(store) -> dict:
    """Trades Ore recorded (actual R), oldest first: drawdown, losing streak, execution gap."""
    rows = {r["id"]: r for r in store.list_setups(limit=5000)}
    trades = []
    for rv in store.list_reviews():
        if rv.get("actual_r") is None:
            continue
        row = rows.get(rv["setup_id"])
        sys_R = None
        if row:
            _, st = service._option_outcome(row, rv.get("option_id"))
            sys_R = _r(st)
        trades.append({"when": rv.get("actual_closed_at") or rv.get("created_at") or "", "R": float(rv["actual_r"]),
                       "sys_R": sys_R, "pair": row["pair"] if row else "", "setup_id": rv["setup_id"]})
    trades.sort(key=lambda t: t["when"])
    eq = peak = dd = 0.0
    streak = cur = 0
    for t in trades:
        eq += t["R"]
        peak = max(peak, eq)
        dd = peak - eq
        cur = cur + 1 if t["R"] < 0 else 0
        streak = cur          # current run of losses
    gaps = [t["R"] - t["sys_R"] for t in trades if t["sys_R"] is not None]
    gap = _mean(gaps)
    return {"n": len(trades), "total_R": eq, "avg_R": _mean([t["R"] for t in trades]), "drawdown": dd,
            "loss_streak": streak, "gap": gap, "gap_n": len(gaps), "recent": trades[-10:][::-1],
            "pause": dd >= PAUSE_DD_R or streak >= PAUSE_STREAK,
            "gap_warn": gap is not None and len(gaps) >= 10 and gap < GAP_WARN}


def risk_check(settings: dict, passed: bool) -> dict:
    cap = RISK_AFTER if passed else RISK_BEFORE
    risk = float(settings.get("risk_pct") or 0)
    spreads_set = bool(settings.get("spreads_confirmed"))
    return {"risk": risk, "cap": cap, "ok": risk <= cap, "max": RISK_MAX, "spreads_set": spreads_set}


def build(store, settings: dict) -> dict:
    live = judgment(store, "live")
    practice = judgment(store, "practice")
    passed = live["verdict"] == "good"
    return {"live": live, "practice": practice, "real": real_trades(store),
            "by_strategy": {k: judgment(store, "live", k) for k in STRATEGIES},
            "risk": risk_check(settings, passed), "passed": passed,
            "rules": {"first": FIRST_READ, "decision": DECISION, "before": RISK_BEFORE, "after": RISK_AFTER,
                      "max": RISK_MAX, "dd": PAUSE_DD_R, "streak": PAUSE_STREAK, "gap": GAP_WARN}}


def digest_line(store, settings: dict) -> str:
    d = build(store, settings)
    lv, rl = d["live"], d["real"]
    line = f"My test: {lv['n']} of {DECISION} finished live Takes. {lv['verdict_text']}"
    if rl["pause"]:
        line += f" PAUSE: recorded trades are {rl['drawdown']:.1f}R below their best or {rl['loss_streak']} losses in a row; back to demo."
    if not d["risk"]["ok"]:
        line += f" Risk in Settings is {d['risk']['risk']:g}%, above the plan's {d['risk']['cap']:g}%."
    return line
