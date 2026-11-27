"""Prop mode (Ore's request, 27 Nov 2026): run the site for a prop-firm challenge.

Plan from spec v29 (docs/spec-v29-prop-eval.md): Equity Edge 1-Step "Swift" 5K, trade only Ore's model + IRL/ERL at
1.5% risk. This module holds the account rules, lot sizes under the firm's leverage, the challenge tracker (target,
daily limit, trailing floor, the most the next trade may risk) and high-impact news windows.
"""
from __future__ import annotations

import json
import math
import urllib.request

import pandas as pd

DEFAULTS = {
    "on": False,
    "firm": "Equity Edge · 1-Step Swift",
    "size": 5000.0,
    "target_pct": 8.0,
    "daily_pct": 3.0,
    "trailing_pct": 5.0,
    "risk_pct": 1.5,
    "leverage": {"GBPUSD": 30, "XAUUSD": 10},
    "strategies": ["ore_poi", "irl_erl"],
    "news_min": 2,                       # no opening or closing within this many minutes of high-impact news
    "reset": "22:00 London",
    # tracker (Ore types these in on the Prop page)
    "balance": 5000.0, "peak": 5000.0, "day_start": 5000.0, "days_traded": 0, "started": "",
}
NEWS_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"   # ForexFactory weekly calendar (public)
NEWS_KEY = "news_week"
NEWS_EVERY = pd.Timedelta("6h")
CURRENCIES = {"GBPUSD": {"USD", "GBP"}, "XAUUSD": {"USD"}}             # USD news affects every pair (firm rule)


def plan(settings: dict) -> dict:
    p = {**DEFAULTS, **(settings.get("prop") or {})}
    p["leverage"] = {k: int(v) for k, v in {**DEFAULTS["leverage"], **(p.get("leverage") or {})}.items()}
    return p


def in_plan(settings: dict, strategy: str) -> bool:
    return strategy in plan(settings)["strategies"]


def lot(settings: dict, pair: str, entry: float, stop: float) -> dict:
    """Lots for the prop account at the plan's risk, capped by the firm's leverage on the current balance."""
    p = plan(settings)
    contract = float(settings["contract"][pair])
    bal = float(p["balance"]) or float(p["size"])
    risk_amt = float(p["size"]) * float(p["risk_pct"]) / 100.0
    per_lot = abs(entry - stop) * contract
    if per_lot <= 0 or entry <= 0:
        return {"lots": 0.0, "risk_amount": 0.0, "capped": False, "margin": 0.0, "too_small": True}
    want = risk_amt / per_lot
    max_lots = bal * float(p["leverage"].get(pair, 30)) / (entry * contract)
    lots = math.floor(min(want, max_lots) * 100) / 100
    return {"lots": lots, "risk_amount": round(lots * per_lot, 2), "target_risk": round(risk_amt, 2),
            "capped": want > max_lots, "max_lots": round(max_lots, 2),
            "margin": round(lots * entry * contract / float(p["leverage"].get(pair, 30)), 2), "too_small": lots < 0.01}


def status(settings: dict) -> dict:
    """The challenge in numbers, from what Ore entered: room to the target, the daily limit and the trailing floor."""
    p = plan(settings)
    size, bal, peak, day0 = float(p["size"]), float(p["balance"]), float(p["peak"]), float(p["day_start"])
    target = size * (1 + p["target_pct"] / 100)
    daily_floor = day0 - size * p["daily_pct"] / 100
    trail_floor = max(peak, bal) - size * p["trailing_pct"] / 100
    floor = max(daily_floor, trail_floor)
    risk_amt = size * p["risk_pct"] / 100
    room = bal - floor
    out = {"target": round(target, 2), "to_target": round(target - bal, 2), "daily_floor": round(daily_floor, 2),
           "daily_room": round(bal - daily_floor, 2), "trail_floor": round(trail_floor, 2),
           "trail_room": round(bal - trail_floor, 2), "binding": "daily" if daily_floor >= trail_floor else "trailing",
           "room": round(room, 2), "risk_amt": round(risk_amt, 2),
           "next_risk": round(max(0.0, min(risk_amt, room * 0.9)), 2),           # keep 10% of the room as a buffer
           "losses_left": int(room // risk_amt) if risk_amt > 0 else 0,
           "progress": max(0.0, min(1.0, (bal - size) / (target - size))) if target > size else 0.0,
           "days_traded": int(p["days_traded"]), "passed": bal >= target and int(p["days_traded"]) >= 2}
    out["warn"] = (out["next_risk"] < risk_amt * 0.999)
    return out


# ------------------------------------------------------------------ news windows

def parse_news(payload) -> list[dict]:
    """ForexFactory weekly JSON -> high-impact events [{time (UTC ISO), currency, title}]."""
    out = []
    for e in payload or []:
        if str(e.get("impact", "")).lower() != "high":
            continue
        try:
            t = pd.Timestamp(e["date"]).tz_convert("UTC")
        except Exception:
            continue
        out.append({"time": t.isoformat(), "currency": str(e.get("country", "")).upper(), "title": str(e.get("title", ""))})
    return sorted(out, key=lambda x: x["time"])


def fetch_news(opener=urllib.request.urlopen, timeout: float = 10.0) -> list[dict]:
    req = urllib.request.Request(NEWS_URL, headers={"User-Agent": "setup-scanner/1.0"})
    with opener(req, timeout=timeout) as r:
        return parse_news(json.loads(r.read().decode("utf-8")))


def refresh_news(store, now: pd.Timestamp, opener=urllib.request.urlopen) -> str | None:
    """At most every 6 hours; never raises (news is a helper, not part of the scan)."""
    try:
        c = store.get_cache(NEWS_KEY)
        if c and now - pd.Timestamp(c["fetched"]) < NEWS_EVERY:
            return None
        events = fetch_news(opener)
        store.set_cache(NEWS_KEY, {"fetched": now.isoformat(), "events": events})
        return f"news calendar: {len(events)} high-impact events"
    except Exception as e:
        return f"news calendar not refreshed ({type(e).__name__})"


def upcoming(store, now: pd.Timestamp, hours: float = 36, pair: str | None = None) -> list[dict]:
    try:
        c = store.get_cache(NEWS_KEY) or {}
    except Exception:
        return []
    cur = CURRENCIES.get(pair) if pair else {"USD", "GBP"}
    out = []
    for e in c.get("events", []):
        t = pd.Timestamp(e["time"])
        if now - pd.Timedelta("5min") <= t <= now + pd.Timedelta(hours=hours) and e["currency"] in cur:
            out.append({**e, "in_min": int((t - now).total_seconds() // 60)})
    return out


def news_fetched(store) -> str | None:
    try:
        return (store.get_cache(NEWS_KEY) or {}).get("fetched")
    except Exception:
        return None
