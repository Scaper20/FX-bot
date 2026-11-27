"""Website logic: scanning, logging, tracking outcomes, lot sizes, performance, practice."""
from __future__ import annotations

import gzip
import json
import math
from functools import lru_cache
from pathlib import Path

import pandas as pd

from engine import config as K
from engine.feeds.twelvedata import CALLS_PER_SCAN, FeedError
from engine.live import (ENGINE_VERSION, ENTRY_LABEL, MGMT_LABEL, STOP_LABEL, all_tf_candles, compact_candles,
                         scan, track_card_options)
from engine.candles import resample_from
from engine.setups import Market
from engine.strategies import STRATEGIES, strategy_of

from . import alerts

PAIRS = tuple(K.PAIRS)
FINAL_STATES = {"stop", "target", "breakeven", "time"}
TF_STEP = {"H1": pd.Timedelta("1h"), "M15": pd.Timedelta("15min"), "M5": pd.Timedelta("5min")}
PRACTICE_FILE = Path(__file__).resolve().parent / "data" / "practice.json.gz"
REASONS = [
    ("romeo_m1", "Model #1: thick candle swept, then closed back through its body"),
    ("romeo_c3", "Candle 3 trap: price ran above/below C3's open first"),
    ("romeo_keylevel", "Swept a key level / old high-low (PDH/PDL, PWH/PWL, FVG)"),
    ("romeo_htf", "HTF candle bias agrees (close/wick rule)"),
    ("romeo_time", "Right time (Tue/Wed sweep, 1/5/9 AM NY, inside 00:00–16:00 NY)"),
    ("romeo_premium", "Selling at premium / buying at discount of the range"),
    ("romeo_smt", "SMT with the correlated market (EUR/USD, DXY, silver)"),
    ("romeo_kod", "Kiss of death / fake MSS before the real move"),
    ("breaker", "Breaker block entry (grab, shift, retest of the breaker)"),
    ("ote", "OTE / failure swing after a true MSS"),
    ("rtm1", "RTM1: retrade into the Model #1 candle"),
    ("rejection_block", "Rejection block (turtle soup of the bodies)"),
    ("msnr_level", "Fresh MSnR level at the sweep, storyline agrees"),
    ("toni_zone", "Toni Iyke: shift at a daily/4H zone on the trendline (HTF confirmation)"),
    ("toni_poi", "Toni Iyke: multiple BOS, valid inducement, closest unmitigated POI"),
    ("liq_pool", "Inside a liquidity pool / range being cleared (Toni: avoid)"),
    ("lingard_liq", "Lingard: first-pullback liquidity taken, POI nearest it"),
    ("lingard_topdown", "Lingard: agrees with the weekly/monthly bias (external swing)"),
    ("with_trend", "With the market direction"),
    ("against_no_backing", "Against the market, no OB/FVG on the left"),
    ("htf_level", "Strong HTF level / OB / FVG on the left"),
    ("sweep_too_big", "Sweep candle too large"),
    ("sweep_too_small", "Sweep too small / not a real sweep"),
    ("no_structure", "No clear structure / messy chart"),
    ("good_structure", "Clean structure shift"),
    ("news", "News or event risk"),
    ("session", "Wrong time / session"),
    ("rr_target", "Target or reward:risk not convincing"),
    ("already_moved", "Price already moved / entry missed"),
    ("liquidity_left", "Liquidity left unswept"),
    ("gut", "Gut feeling"),
    ("other", "Other (see notes)"),
]
REASON_LABEL = dict(REASONS)


class ScanError(Exception):
    pass


# ------------------------------------------------------------------ helpers


def option_by_id(card: dict, oid: str | None) -> dict | None:
    for op in card.get("options", []):
        if op["id"] == oid:
            return op
    return None


def all_options(row: dict) -> list[dict]:
    """Options from the snapshot plus any added later (each tagged with when it was first seen)."""
    ops = [dict(op, seen_at=row.get("first_seen")) for op in row["card"].get("options", [])]
    for a in row.get("added") or []:
        ops.append(dict(a["option"], seen_at=a["seen_at"]))
    return ops


def is_final(st: dict | None) -> bool:
    if not st:
        return False
    if st.get("status") in ("expired", "cancelled", "unknown"):
        return True
    return st.get("status") == "filled" and st.get("state") in FINAL_STATES


def actionable(op: dict, st: dict, now: pd.Timestamp) -> str | None:
    """Can Ore still act on this option right now? Returns a short instruction or None."""
    if st.get("status") == "pending" and not op["market"]:
        return "Limit order still valid"
    if op["market"] and st.get("status") == "filled" and st.get("state") == "open":
        age = now - pd.Timestamp(op["decision_time"])
        if age <= 2 * TF_STEP[op["entry_tf"]]:
            return "Fresh trigger: market entry still close to the planned price"
    return None


def lot_size(settings: dict, pair: str, entry: float, stop: float) -> dict:
    risk_amt = float(settings["balance"]) * float(settings["risk_pct"]) / 100.0
    per_lot = abs(entry - stop) * float(settings["contract"][pair])
    if per_lot <= 0:
        return {"lots": 0.0, "risk_amount": 0.0, "per_lot": 0.0}
    lots = math.floor(risk_amt / per_lot * 100) / 100
    return {"lots": lots, "risk_amount": round(lots * per_lot, 2), "target_risk": round(risk_amt, 2),
            "per_lot": round(per_lot, 2), "too_small": lots < 0.01}


# ------------------------------------------------------------------ scanning


D1_HIST_DAYS = 1500           # stored daily candles: the D1 trend needs years, the live feed gives ~4 months
D1_HIST_MIN = 650             # below this many days, each scan backfills once (the GBP/USD D1 trend needs ~600 days)


def backfill_d1(feed, pair: str, hist: pd.DataFrame) -> pd.DataFrame:
    """Older D1 candles built from the feed's H1 history (same day boundary as the backtests), before `hist`."""
    end = hist.index[0]
    h1 = feed.history_h1(pair, end)
    if h1 is None or len(h1) < 48:
        return hist
    d1 = resample_from(h1, "D1", K.DAY_CLOSE)[["open", "high", "low", "close"]].iloc[1:]   # first day may be partial
    d1 = d1[d1.index < end]
    return pd.concat([d1, hist[["open", "high", "low", "close"]]]).sort_index()


def d1_history(store, pair: str) -> pd.DataFrame | None:
    """Stored long D1 history ([unix_s, o, h, l, c] rows in latest_candles, tf 'D1_hist'), or None."""
    try:
        rows = store.get_candles(pair).get("D1_hist") or []
    except Exception:                                 # never fail a scan over history
        return None
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["t", "open", "high", "low", "close"])
    df.index = pd.to_datetime(df.pop("t"), unit="s", utc=True)
    return df


def run_scan(store, feed, now: pd.Timestamp | None = None, trigger: str = "manual", counts_credits: bool = True,
             base_url: str = "") -> dict:
    """Scan both pairs, log new ready setups, update tracked outcomes, save the scan."""
    now = now or pd.Timestamp.now(tz="UTC").floor("s")
    settings = store.get_settings()
    started = pd.Timestamp.now(tz="UTC").isoformat()
    row = {"started_at": started, "trigger": trigger, "ok": False, "credits": 0}
    if counts_credits and store.credits_today() + CALLS_PER_SCAN > int(settings["daily_credit_limit"]):
        row.update(message="Daily Twelve Data credit budget reached; scanning resumes after 00:00 UTC.",
                   finished_at=pd.Timestamp.now(tz="UTC").isoformat())
        store.add_scan(row)
        raise ScanError(row["message"])
    markets, errors = {}, []
    calls_before = getattr(feed, "calls", 0)
    had_hist, backfills, hist_notes = {}, 1, []                       # at most one extra feed call per scan (rate limit)
    for pair in PAIRS:
        try:
            hist = d1_history(store, pair)
            had_hist[pair] = hist is not None
            if hist is not None and len(hist) < D1_HIST_MIN and backfills and hasattr(feed, "history_h1"):
                backfills -= 1
                try:
                    n0 = len(hist)
                    hist = backfill_d1(feed, pair, hist)
                    hist_notes.append(f"{pair} D1 history {n0} -> {len(hist)} days")
                except Exception as e:                # history is a nice-to-have: never fail the scan
                    errors.append(f"{pair}: D1 history backfill: {e}")
            markets[pair] = Market.from_frames({**feed.frames(pair, now), "D1_hist": hist}, now)
        except FeedError as e:
            errors.append(f"{pair}: {e}")
        except Exception as e:                        # bad data must not kill the scan for the other pair
            errors.append(f"{pair}: {type(e).__name__}: {e}")
    used = getattr(feed, "calls", 0) - calls_before
    if counts_credits and used:
        store.add_credits(used)
    row["credits"] = used
    if not markets:
        row.update(message="; ".join(errors) or "no data", finished_at=pd.Timestamp.now(tz="UTC").isoformat())
        store.add_scan(row)
        raise ScanError(row["message"])
    spreads = {p: float(settings["spreads"][p]) for p in PAIRS}
    res = scan(markets, spreads)
    try:
        store.save_candles([{"pair": p, "tf": tf, "data": data}
                            for p, m in markets.items() for tf, data in all_tf_candles(m).items()]
                           + [{"pair": p, "tf": "D1_hist",            # without history the first day may be partial
                               "data": compact_candles(m.frames["D1"].iloc[0 if had_hist.get(p) else 1:], D1_HIST_DAYS)}
                              for p, m in markets.items()])
    except Exception as e:                            # charts only; never fail a scan over it
        errors.append(f"saving chart candles: {e}")

    ready_summary, new_ids, new_alert_cards = [], [], []
    for card in res["ready"]:
        mkt = markets[card["pair"]]
        status = track_card_options(mkt, card, spreads[card["pair"]])
        logged = store.get_setup(card["id"])
        if logged is None:
            store.insert_setup_if_new({
                "id": card["id"], "source": "live", "pair": card["pair"], "direction": card["direction"],
                "range_tf": card["range_tf"], "k": card["k"], "range_open": card["range_open"],
                "decision_time": card["decision_time"], "recommended": card["recommended"],
                "engine": ENGINE_VERSION, "card": card, "status": status,
                "final": all(is_final(s) for s in status.values()),
            })
            new_ids.append(card["id"])
        else:
            known = {op["id"] for op in all_options(logged)}
            extra = [{"seen_at": now.isoformat(), "option": op} for op in card["options"] if op["id"] not in known]
            if extra:
                store.update_setup(card["id"], added=(logged.get("added") or []) + extra)
        acts = {op["id"]: actionable(op, status.get(op["id"], {}), now) for op in card["options"]}
        if logged is None and any(acts.values()):
            new_alert_cards.append(card)
        ready_summary.append({"id": card["id"], "recommended": card["recommended"],
                              "actionable": [k for k, v in acts.items() if v],
                              "in_play": [k for k, v in status.items() if v.get("state") == "open"]})

    # track every open logged setup on the pairs we have data for
    tracked, events = 0, []
    taken = {}
    for rv in store.list_reviews():
        if rv["decision"] == "take":
            taken[rv["setup_id"]] = rv.get("option_id")
        else:
            taken.pop(rv["setup_id"], None)
    for r in store.list_setups(source="live", final=False):
        if r["pair"] not in markets:
            continue
        card_like = dict(r["card"], options=all_options(r))
        st = track_card_options(markets[r["pair"]], card_like, spreads[r["pair"]])
        st = _unknown_if_uncovered(st, markets[r["pair"]], card_like)
        # trade updates for the option that matters: Ore's Take, else the top-ranked one
        if r.get("recommended") or r["id"] in taken:
            oid = taken.get(r["id"]) or r["card"].get("best")
            what = alerts.transition((r.get("status") or {}).get(oid), st.get(oid))
            if what:
                events.append({"id": r["id"], "pair": r["pair"], "direction": r["direction"], "range_tf": r["range_tf"],
                               "what": what, "R": (st.get(oid) or {}).get("R"), "taken": r["id"] in taken})
        store.update_setup(r["id"], status=st, final=all(is_final(s) for s in st.values()))
        tracked += 1

    notes = list(hist_notes)
    try:
        for note in (alerts.send_scan_alert(store, settings, new_alert_cards, events, base_url),
                     alerts.maybe_send_digest(store, settings, now, base_url)):
            if note:
                notes.append(note)
    except Exception as e:                            # an email problem must never fail a scan
        notes.append(f"alert error: {type(e).__name__}")

    light = lambda c: {k: v for k, v in c.items() if k not in ("options", "chart", "checks")}
    row.update(ok=True, ready=len(res["ready"]), armed=len(res["armed"]),
               message="; ".join(errors + notes) if errors else "; ".join([f"{len(new_ids)} new setup(s) logged"] + notes),
               finished_at=pd.Timestamp.now(tz="UTC").isoformat(),
               result={"now": now.isoformat(), "ready": ready_summary, "armed": [light(c) for c in res["armed"]],
                       "watch": res["watch"], "smc_watch": res.get("smc_watch", []), "errors": errors, "new": new_ids, "tracked": tracked})
    store.add_scan(row)
    try:
        store.prune_scans(14)
    except Exception:
        pass
    return row


def _unknown_if_uncovered(st: dict, mkt: Market, card: dict) -> dict:
    """If the decision is older than the candles we still have, the outcome can't be tracked."""
    first = mkt.frames["M5"].index.min()
    for op in card["options"]:
        if pd.Timestamp(op["decision_time"]) < first and not is_final(st.get(op["id"])):
            st[op["id"]] = {"status": "unknown", "state": None, "R": None, "fill_time": None, "exit_time": None}
    return st


# ------------------------------------------------------------------ dashboard data


def dashboard(store, now: pd.Timestamp | None = None) -> dict:
    now = now or pd.Timestamp.now(tz="UTC")
    last = store.last_scan()
    out = {"last": last, "cards": [], "other": [], "in_play": [], "armed": [], "watch": [], "smc_watch": [], "now": now}
    if not last or not last.get("result"):
        return out
    res = last["result"]
    for s in res.get("ready", []):
        row = store.get_setup(s["id"])
        if not row:
            continue
        item = {"row": row, "card": row["card"], "actionable": s["actionable"], "in_play": s["in_play"],
                "reviews": store.list_reviews(row["id"]), "strategy": strategy_of(row["card"])}
        if s["actionable"]:
            (out["cards"] if s["recommended"] else out["other"]).append(item)
        elif s["in_play"]:
            out["in_play"].append(item)
    out["armed"] = res.get("armed", [])
    out["watch"] = res.get("watch", [])
    out["smc_watch"] = res.get("smc_watch", [])
    return out


def unreviewed(store, source: str = "live", limit: int = 50) -> list[dict]:
    reviewed = {r["setup_id"] for r in store.list_reviews()}
    return [r for r in store.list_setups(source=source, limit=500) if r["id"] not in reviewed][:limit]


# ------------------------------------------------------------------ performance


def _option_outcome(row: dict, oid: str | None) -> tuple[dict | None, dict | None]:
    op = None
    if oid:
        op = next((o for o in all_options(row) if o["id"] == oid), None)
    if op is None:
        op = option_by_id(row["card"], row["card"].get("best"))
    st = (row.get("status") or {}).get(op["id"]) if op else None
    return op, st


def group_stats(items: list[tuple[dict, dict]]) -> dict:
    """items = (option, status) pairs. Only finished, filled trades count towards R."""
    done = [(o, s) for o, s in items if s and s.get("status") == "filled" and s.get("state") in FINAL_STATES]
    rs = [float(s["R"]) for _, s in done]
    n = len(rs)
    out = {"setups": len(items), "trades": n,
           "pending": sum(1 for _, s in items if not is_final(s)),
           "not_filled": sum(1 for _, s in items if s and s.get("status") in ("expired", "cancelled")),
           "avg_R": None, "total_R": 0.0, "chance_avg_R": None, "edge_R": None, "z_R": None,
           "win_rate": None, "chance_win_rate": None, "wins": 0, "expected_wins": 0.0, "z_wins": None}
    if n == 0:
        return out
    avg = sum(rs) / n
    chance_avg = sum(o["chance_avg_R"] for o, _ in done) / n
    wins = sum(1 for r in rs if r > 0)
    exp_wins = sum(o["chance"] for o, _ in done)
    var_w = sum(o["chance"] * (1 - o["chance"]) for o, _ in done)
    sd = (sum((r - avg) ** 2 for r in rs) / (n - 1)) ** 0.5 if n > 1 else 0.0
    out.update(avg_R=avg, total_R=sum(rs), chance_avg_R=chance_avg, edge_R=avg - chance_avg,
               z_R=((avg - chance_avg) / (sd / n ** 0.5)) if sd > 0 else None,
               win_rate=wins / n, chance_win_rate=exp_wins / n, wins=wins, expected_wins=exp_wins,
               z_wins=((wins - exp_wins) / var_w ** 0.5) if var_w > 0 else None)
    return out


def performance(store, source: str = "live", strategy: str | None = None) -> dict:
    """Takes / Skips / system vs chance. strategy=None mixes all strategies; give an id to split them."""
    rows = [r for r in store.list_setups(source=source, limit=5000)
            if strategy is None or strategy_of(r["card"]) == strategy]
    latest = {}
    for r in store.list_reviews():
        latest[r["setup_id"]] = r                     # reviews come oldest first: keep the latest
    groups = {"system": [], "take": [], "skip": [], "unsure": [], "not_reviewed": []}
    by_reason = {}
    actual = []
    for row in rows:
        best_op, best_st = _option_outcome(row, None)
        if row.get("recommended") and best_op:
            groups["system"].append((best_op, best_st))
        rv = latest.get(row["id"])
        if rv is None:
            if best_op:
                groups["not_reviewed"].append((best_op, best_st))
            continue
        op, st = _option_outcome(row, rv.get("option_id") if rv["decision"] == "take" else None)
        if op:
            groups[rv["decision"]].append((op, st))
            for reason in rv.get("reasons") or []:
                by_reason.setdefault((rv["decision"], reason), []).append((op, st))
        if rv.get("actual_r") is not None:
            actual.append(float(rv["actual_r"]))
    return {"groups": {k: group_stats(v) for k, v in groups.items()},
            "by_reason": {k: group_stats(v) for k, v in sorted(by_reason.items())},
            "actual": {"n": len(actual), "avg_R": (sum(actual) / len(actual)) if actual else None,
                       "total_R": sum(actual)},
            "rows": len(rows)}


# ------------------------------------------------------------------ practice


@lru_cache(maxsize=1)
def practice_items() -> list[dict]:
    if not PRACTICE_FILE.exists():
        return []
    with gzip.open(PRACTICE_FILE, "rt") as f:
        return json.load(f)


def practice_strategy(item: dict) -> str:
    return item.get("strategy") or item["card"].get("strategy") or "crt"


def active_practice_items(strategy: str | None = None) -> list[dict]:
    """Setups still served (optionally one strategy). Retired ones (e.g. C2 closed in C1's wick, not its body: Ore's
    rule of 23 Nov 2026) stay in the file so answers already given still count in everyone's stats."""
    return [p for p in practice_items() if not p.get("retired")
            and (strategy is None or practice_strategy(p) == strategy)]


def practice_item(pid: str) -> dict | None:
    return next((p for p in practice_items() if p["id"] == pid), None)


def next_practice(store, strategy: str | None = None) -> dict | None:
    done = {r["setup_id"] for r in store.list_reviews()}
    return next((p for p in active_practice_items(strategy) if p["id"] not in done), None)


def practice_progress(store, strategy: str | None = None) -> dict:
    done = {r["setup_id"] for r in store.list_reviews()}
    items = active_practice_items(strategy)
    return {"done": sum(1 for p in items if p["id"] in done), "total": len(items)}


def practice_menu(store) -> list[dict]:
    """One entry per strategy that has practice setups: {id, done, total} (Practice tab picker)."""
    done = {r["setup_id"] for r in store.list_reviews()}
    out = []
    for sid in STRATEGIES:
        items = active_practice_items(sid)
        if items:
            out.append({"id": sid, "done": sum(1 for p in items if p["id"] in done), "total": len(items)})
    return out


def save_practice_review(store, item: dict, review: dict) -> int:
    card = item["card"]
    store.insert_setup_if_new({
        "id": item["id"], "source": "practice", "pair": card["pair"], "direction": card["direction"],
        "range_tf": card["range_tf"], "k": card["k"], "range_open": card["range_open"],
        "decision_time": card["decision_time"], "recommended": card["recommended"],
        "engine": item.get("engine", ENGINE_VERSION), "card": card, "status": item["outcome"], "final": True,
    })
    review["setup_id"] = item["id"]
    return store.add_review(review)


# ------------------------------------------------------------------ labels for templates

LABELS = {"entry": ENTRY_LABEL, "stop": STOP_LABEL, "mgmt": MGMT_LABEL, "reasons": REASON_LABEL}
