"""Personal email alerts for the site owner: new setups, trade updates, daily summary.

Everything found in one scan goes out as ONE email. A daily cap stops floods.
Email failures are recorded but never stop a scan."""
from __future__ import annotations

import datetime as dt
from html import escape

import pandas as pd

from engine import strategies

from . import mailer

SUBJECT = "Setup Scanner: "

NY = "America/New_York"
DEFAULTS = {"new": True, "outcomes": True, "digest": True, "filtered": False, "smc": True, "irl_erl": True, "toni": True,
            "lingard": True, "ore_poi": True, "max_per_day": 30}


def kind(card: dict) -> str:
    """Short name of the setup type, for emails."""
    return strategies.name(card)


def wanted(card: dict, p: dict) -> bool:
    """New-setup alert switch: each strategy has its own (CRT: 'new', order block: 'smc')."""
    if not p.get(strategies.STRATEGIES[strategies.strategy_of(card)]["alert"], True):
        return False
    return bool(card["recommended"] or p["filtered"])


def prefs(settings: dict) -> dict:
    return {**DEFAULTS, **(settings.get("alerts") or {})}


def _price(pair: str, x) -> str:
    return "—" if x is None else (f"{x:.5f}" if pair == "GBPUSD" else f"{x:,.2f}")


def _loc(t, tz: str) -> str:
    return pd.Timestamp(t).tz_convert(tz).strftime("%a %d %b %H:%M")


def new_setup_line(card: dict, base: str, tz: str) -> tuple[str, str]:
    op = card["options"][0]
    sid = strategies.strategy_of(card)
    rule = (f"matches {strategies.STRATEGIES[sid]['rules_word']}" if card["recommended"] else "a rule is NOT met")
    text = (f"{card['pair']} {card['direction'].upper()} · {kind(card)} · {rule}\n"
            f"  Entry {_price(card['pair'], op['entry'])}  Stop {_price(card['pair'], op['stop'])}  "
            f"Target {_price(card['pair'], op['target'])}  (1:{op['rr']:.1f}, chance win rate {op['chance']:.0%})\n"
            f"  {op['entry_tf']} {op['trigger']} trigger at {_loc(op['decision_time'], tz)}\n  {base}/setup/{card['id']}")
    html = (f"<p><b>{escape(card['pair'])} {escape(card['direction'].upper())}</b> · {escape(kind(card))} · {rule}<br>"
            f"Entry <b>{_price(card['pair'], op['entry'])}</b> · Stop <b>{_price(card['pair'], op['stop'])}</b> · "
            f"Target <b>{_price(card['pair'], op['target'])}</b> (1:{op['rr']:.1f}, chance {op['chance']:.0%})<br>"
            f"{escape(op['entry_tf'])} {escape(op['trigger'])} trigger at {_loc(op['decision_time'], tz)}<br>"
            f'<a href="{base}/setup/{escape(card["id"])}">Open the setup and record your call</a></p>')
    return text, html


def outcome_line(ev: dict, base: str) -> tuple[str, str]:
    what = {"filled": "entry filled", "target": "TARGET hit", "stop": "STOP hit", "breakeven": "half at 50%, rest at breakeven",
            "time": "closed on time limit", "expired": "not filled, expired", "cancelled": "cancelled (reached 50% before filling)"
            }.get(ev["what"], ev["what"])
    r = f" ({ev['R']:+.2f}R)" if ev.get("R") is not None and ev["what"] not in ("filled", "expired", "cancelled") else ""
    mine = " · your Take" if ev.get("taken") else ""
    text = f"{ev['pair']} {ev['direction']} {ev['range_tf']}: {what}{r}{mine}\n  {base}/setup/{ev['id']}"
    html = (f'<p><b>{escape(ev["pair"])} {escape(ev["direction"])} {escape(ev["range_tf"])}</b>: {escape(what)}{r}{mine}<br>'
            f'<a href="{base}/setup/{escape(ev["id"])}">Open</a></p>')
    return text, html


def transition(old: dict | None, new: dict | None) -> str | None:
    """What changed for one option between two scans (None = nothing worth telling)."""
    old, new = old or {}, new or {}
    if new.get("status") == "filled":
        st = new.get("state")
        if st in ("target", "stop", "breakeven", "time") and old.get("state") != st:
            return st
        if st == "open" and old.get("status") != "filled":
            return "filled"
    if new.get("status") in ("expired", "cancelled") and old.get("status") not in ("expired", "cancelled"):
        return new["status"]
    return None


def _budget_ok(store, settings: dict, n: int = 1) -> bool:
    p = prefs(settings)
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    c = settings.get("alert_count") or {}
    used = c.get("n", 0) if c.get("day") == today else 0
    if used + n > int(p["max_per_day"]):
        return False
    settings["alert_count"] = {"day": today, "n": used + n}
    store.save_settings({k: v for k, v in settings.items()})
    return True


def send_scan_alert(store, settings: dict, new_cards: list[dict], events: list[dict], base: str) -> str | None:
    """One email for everything found in a scan. Returns a note for the scan log, or None."""
    to = settings.get("owner_email")
    p = prefs(settings)
    if not to or not mailer.configured():
        return None
    cards = [c for c in new_cards if wanted(c, p)]
    evs = events if p["outcomes"] else []
    if not cards and not evs:
        return None
    if not _budget_ok(store, settings):
        return "owner alert skipped: daily email cap reached"
    tz = settings.get("tz", "Africa/Lagos")
    parts_t, parts_h = [], []
    if cards:
        parts_t.append(f"NEW SETUP{'S' if len(cards) > 1 else ''}")
        parts_h.append(f"<h3>New setup{'s' if len(cards) > 1 else ''}</h3>")
        for c in cards:
            t, h = new_setup_line(c, base, tz)
            parts_t.append(t)
            parts_h.append(h)
    if evs:
        parts_t.append("TRADE UPDATES")
        parts_h.append("<h3>Trade updates</h3>")
        for e in evs:
            t, h = outcome_line(e, base)
            parts_t.append(t)
            parts_h.append(h)
    bits = []
    if cards:
        bits.append(f"{len(cards)} new setup{'s' if len(cards) > 1 else ''}")
    if evs:
        bits.append(f"{len(evs)} update{'s' if len(evs) > 1 else ''}")
    subject = SUBJECT + ", ".join(bits)
    footer_t = "\n\nSetups that match your rules, with their historical results. Not advice; check your own chart. Change alerts in Settings."
    footer_h = ('<p style="color:#5B6577;font-size:12px">Setups that match your rules, with their historical results. '
                f'Not advice; check your own chart. <a href="{base}/settings">Change alerts</a>.</p>')
    html = '<div style="font-family:Arial,sans-serif;color:#0F1B2D;max-width:600px">' + "".join(parts_h) + footer_h + "</div>"
    try:
        mailer.send(to, subject, html, "\n\n".join(parts_t) + footer_t, tags=["owner-alert"])
        return f"alert emailed: {subject[len(SUBJECT):]}"
    except mailer.MailError as e:
        return f"alert email failed: {e}"


def maybe_send_digest(store, settings: dict, now: pd.Timestamp, base: str) -> str | None:
    """Once per New York trading day, after 17:00 New York: a summary of the day."""
    p = prefs(settings)
    to = settings.get("owner_email")
    ny = now.tz_convert(NY)
    day = ny.date().isoformat()
    if not (p["digest"] and to and mailer.configured()) or ny.weekday() >= 5 or ny.hour < 17:
        return None
    if settings.get("last_digest") == day:
        return None
    settings["last_digest"] = day
    store.save_settings(settings)
    start = pd.Timestamp(day + " 00:00", tz=NY).tz_convert("UTC")
    rows = [r for r in store.list_setups(source="live", limit=500) if pd.Timestamp(r["first_seen"]) >= start]
    rec = [r for r in rows if r.get("recommended")]
    latest = {}
    for rv in store.list_reviews():
        latest[rv["setup_id"]] = rv
    unrev = [r for r in rows if r["id"] not in latest]
    tz = settings.get("tz", "Africa/Lagos")
    lines = [f"Today ({ny:%a %d %b}): {len(rows)} setup(s) logged, {len(rec)} matching your rules, "
             f"{len(unrev)} still waiting for your review."]
    for r in rows[:15]:
        best = next((o for o in r["card"]["options"] if o["id"] == r["card"].get("best")), None)
        st = (r.get("status") or {}).get(best["id"]) if best else None
        state = (st or {}).get("state") or (st or {}).get("status") or "tracking"
        lines.append(f"- {r['pair']} {r['direction']} {r['range_tf']} at {_loc(r['first_seen'], tz)}: "
                     f"{'matches' if r.get('recommended') else 'filtered'}, best option {state}"
                     f"{' ' + format(st['R'], '+.2f') + 'R' if st and st.get('R') is not None and state not in ('open',) else ''}")
    try:
        from . import plan
        lines.append(plan.digest_line(store, settings))
    except Exception:                       # the summary must not fail because of this line
        pass
    text = "\n".join(lines) + f"\n\nJournal: {base}/journal\nPerformance: {base}/performance"
    html = ('<div style="font-family:Arial,sans-serif;color:#0F1B2D;max-width:600px">'
            + "".join(f"<p>{escape(x)}</p>" for x in lines)
            + f'<p><a href="{base}/plan">My test</a> · <a href="{base}/journal">Journal</a> · <a href="{base}/performance">Performance</a></p></div>')
    try:
        mailer.send(to, f"Setup Scanner daily summary · {ny:%a %d %b}", html, text, tags=["owner-digest"])
        return "daily summary emailed"
    except mailer.MailError as e:
        return f"daily summary failed: {e}"
