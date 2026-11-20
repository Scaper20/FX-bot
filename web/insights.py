"""Is the community helping? Numbers for the Insights dashboard (private).

All measured on the practice setups, whose outcomes are known (simulated on 1-minute data).
Two questions per trader:
  1. Edge: do their Takes (the option they chose) beat chance? Chance = minus the spread,
     because on a random market every trade's expected result is minus its cost.
  2. Selection: did the setups they Took do better than the ones they Skipped? Both sides are
     scored with the same top-ranked option, so it is a fair comparison of picking skill.
Small samples lie, so every number comes with its count and a z-score, and a verdict needs
at least MIN_TAKES finished Takes.
"""
from __future__ import annotations

import datetime as dt
import math
from collections import defaultdict

from . import service

MIN_TAKES = 30          # before this, the verdict is "too early"
SHRINK = 50             # ranking: edge x n / (n + SHRINK), so small samples can't top the table
FINAL = {"target", "stop", "breakeven", "time"}


def _r(st: dict | None):
    if st and st.get("status") == "filled" and st.get("state") in FINAL and st.get("R") is not None:
        return float(st["R"])
    return None


def _mean(xs):
    return sum(xs) / len(xs) if xs else None


def _sd(xs):
    if len(xs) < 2:
        return None
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def _z_vs(xs, ref):
    """z of mean(xs) against a fixed reference value."""
    sd = _sd(xs)
    if not xs or sd in (None, 0) or ref is None:
        return None
    return (_mean(xs) - ref) / (sd / math.sqrt(len(xs)))


def _z_diff(a, b):
    """Welch z for mean(a) - mean(b)."""
    sa, sb = _sd(a), _sd(b)
    if sa is None or sb is None:
        return None
    se = math.sqrt(sa ** 2 / len(a) + sb ** 2 / len(b))
    return None if se == 0 else (_mean(a) - _mean(b)) / se


def item_facts() -> dict:
    """Per practice setup: best option, its outcome R, and the chance benchmark."""
    out = {}
    for it in service.practice_items():
        card = it["card"]
        best = service.option_by_id(card, card.get("best"))
        if not best:
            continue
        out[it["id"]] = {"item": it, "best": best, "best_R": _r(it["outcome"].get(best["id"])),
                         "chance_R": best["chance_avg_R"], "pair": card["pair"], "recommended": card["recommended"]}
    return out


def _taken_R(fact: dict, review: dict):
    card = fact["item"]["card"]
    op = service.option_by_id(card, review.get("option_id")) or fact["best"]
    return _r(fact["item"]["outcome"].get(op["id"])), op["chance_avg_R"]


def verdict(n: int, z) -> tuple[str, str]:
    if n < MIN_TAKES:
        return "early", f"Too early: {n} of {MIN_TAKES} finished Takes"
    if z is None:
        return "none", "No clear edge"
    if z >= 2:
        return "good", "Helping: Takes beat chance"
    if z <= -2:
        return "bad", "Hurting: Takes worse than chance"
    return "none", "No clear edge yet"


def trader_stats(name: str, reviews: list[dict], facts: dict) -> dict:
    take_R, take_chance, sel_take, sel_skip = [], [], [], []
    counts = defaultdict(int)
    for rv in reviews:
        f = facts.get(rv["item_id"])
        if not f:
            continue
        counts[rv["decision"]] += 1
        if rv["decision"] == "take":
            r, ch = _taken_R(f, rv)
            if r is not None:
                take_R.append(r)
                take_chance.append(ch)
            if f["best_R"] is not None:
                sel_take.append(f["best_R"])
        elif rv["decision"] == "skip" and f["best_R"] is not None:
            sel_skip.append(f["best_R"])
    chance = _mean(take_chance)
    avg = _mean(take_R)
    edge = None if avg is None or chance is None else avg - chance
    z = _z_vs(take_R, chance)
    sel = None if not sel_take or not sel_skip else _mean(sel_take) - _mean(sel_skip)
    v, vtext = verdict(len(take_R), z)
    answers = sum(counts.values())
    return {"name": name, "answers": answers, "takes": counts["take"], "skips": counts["skip"],
            "unsure": counts["unsure"], "take_rate": counts["take"] / answers if answers else None,
            "take_trades": len(take_R), "take_avg_R": avg, "chance_avg_R": chance, "edge": edge, "z": z,
            "win_rate": (sum(1 for r in take_R if r > 0) / len(take_R)) if take_R else None,
            "total_R": sum(take_R), "selection": sel, "sel_z": _z_diff(sel_take, sel_skip),
            "sel_n": (len(sel_take), len(sel_skip)), "verdict": v, "verdict_text": vtext,
            "rank_score": (edge or 0) * len(take_R) / (len(take_R) + SHRINK)}


def build(store, now: dt.datetime | None = None) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    facts = item_facts()
    users = {u["username_key"]: u["display_name"] for u in store.community_users_all()}
    community = store.community_reviews()
    by_user = defaultdict(list)
    for r in community:
        by_user[r["username_key"]].append(r)
    # Ore's own practice answers, for comparison (kept separate from the community)
    ore = [{"item_id": r["setup_id"], "decision": r["decision"], "option_id": r.get("option_id"),
            "reasons": r.get("reasons") or [], "confidence": r.get("confidence"), "created_at": r.get("created_at")}
           for r in store.list_reviews() if str(r.get("setup_id", "")).startswith("P-")]

    traders = [trader_stats(users.get(k, k), rv, facts) for k, rv in by_user.items()]
    traders.sort(key=lambda t: t["rank_score"], reverse=True)
    everyone = trader_stats("Everyone together", community, facts) if community else None
    you = trader_stats("You (Ore)", ore, facts) if ore else None

    # baseline: take every practice setup with its top option
    all_R = [f["best_R"] for f in facts.values() if f["best_R"] is not None]
    baseline = {"n": len(all_R), "avg_R": _mean(all_R),
                "chance_avg_R": _mean([f["chance_R"] for f in facts.values() if f["best_R"] is not None])}

    # crowd: does a higher share of Takes on a setup mean a better outcome?
    votes = defaultdict(lambda: [0, 0])                 # item -> [takes, answers]
    for r in community:
        if r["decision"] in ("take", "skip"):
            votes[r["item_id"]][1] += 1
            if r["decision"] == "take":
                votes[r["item_id"]][0] += 1
    buckets = [("Mostly skipped (<1/3)", 0, 1 / 3), ("Split (1/3 to 2/3)", 1 / 3, 2 / 3),
               ("Mostly taken (>2/3)", 2 / 3, 1.01)]
    crowd_rows, majority_R = [], []
    for label, lo, hi in buckets:
        rs = [facts[i]["best_R"] for i, (t, n) in votes.items()
              if n >= 3 and i in facts and facts[i]["best_R"] is not None and lo <= t / n < hi]
        crowd_rows.append({"label": label, "n": len(rs), "avg_R": _mean(rs)})
    for i, (t, n) in votes.items():
        if n >= 3 and t / n > 0.5 and i in facts and facts[i]["best_R"] is not None:
            majority_R.append(facts[i]["best_R"])
    crowd = {"rows": crowd_rows, "items_3plus": sum(1 for t, n in votes.values() if n >= 3),
             "majority_n": len(majority_R), "majority_avg_R": _mean(majority_R),
             "majority_z": _z_vs(majority_R, baseline["avg_R"])}

    # reasons: for each tag, how did the setups behind it turn out?
    reasons = defaultdict(list)
    for r in community + ore:
        f = facts.get(r["item_id"])
        if f and f["best_R"] is not None and r["decision"] in ("take", "skip"):
            for tag in r.get("reasons") or []:
                reasons[(r["decision"], tag)].append(f["best_R"])
    reason_rows = sorted(({"decision": d, "reason": service.REASON_LABEL.get(t, t), "n": len(v), "avg_R": _mean(v)}
                          for (d, t), v in reasons.items()), key=lambda x: (-x["n"]))

    # confidence: are confident Takes better?
    conf = defaultdict(list)
    for r in community + ore:
        f = facts.get(r["item_id"])
        if f and r["decision"] == "take" and r.get("confidence"):
            rr, _ = _taken_R(f, r)
            if rr is not None:
                conf[int(r["confidence"])].append(rr)
    conf_rows = [{"level": k, "n": len(conf[k]), "avg_R": _mean(conf[k])} for k in range(1, 6)]

    # agreement with Ore on setups both answered
    ore_dec = {r["item_id"]: r["decision"] for r in ore}
    agree = [r["decision"] == ore_dec[r["item_id"]] for r in community if r["item_id"] in ore_dec]

    # activity, last 30 days (UTC)
    days = [(now.date() - dt.timedelta(days=i)).isoformat() for i in range(29, -1, -1)]
    per_day = defaultdict(int)
    active7 = set()
    week_ago = (now - dt.timedelta(days=7)).isoformat()
    for r in community:
        d = str(r["created_at"])[:10]
        per_day[d] += 1
        if str(r["created_at"]) >= week_ago:
            active7.add(r["username_key"])
    activity = [{"day": d, "n": per_day.get(d, 0)} for d in days]

    helping = sum(1 for t in traders if t["verdict"] == "good")
    return {"traders": traders, "everyone": everyone, "you": you, "baseline": baseline, "crowd": crowd,
            "reasons": reason_rows[:20], "confidence": conf_rows,
            "agreement": {"n": len(agree), "rate": (sum(agree) / len(agree)) if agree else None},
            "activity": activity, "active7": len(active7), "total_answers": len(community),
            "n_traders": len(traders), "helping": helping, "min_takes": MIN_TAKES,
            "eligible": sum(1 for t in traders if t["take_trades"] >= MIN_TAKES)}
