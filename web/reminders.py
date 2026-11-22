"""Practice reminders by email.

- Traders on the public practice site: only those who verified their email AND opted in to emails
  (the same people who get update emails), each with an unsubscribe link. At most one reminder every
  `every_days` days; nobody who practised in the last 24 hours, and nobody who has finished every setup.
- Ore: a practice nudge with his My test progress, at most every `owner_every_days` days, skipped if
  he practised in the last 24 hours.

Run once a day by the scheduled job (/api/cron/reminders); "send now" ignores the interval but still
skips anyone reminded in the last 12 hours, so pressing it twice can't spam anyone.
"""
from __future__ import annotations

import datetime as dt
from html import escape

from . import community, mailer, plan, service

DEFAULTS = {"community": True, "every_days": 3, "owner": True, "owner_every_days": 2}
RECENT_PRACTICE = dt.timedelta(hours=24)
FORCE_GAP = dt.timedelta(hours=12)


def prefs(settings: dict) -> dict:
    return {**DEFAULTS, **(settings.get("reminders") or {})}


def _ts(x) -> dt.datetime | None:
    if not x:
        return None
    t = dt.datetime.fromisoformat(str(x).replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def _due(last: dt.datetime | None, now: dt.datetime, every: dt.timedelta, force: bool) -> bool:
    if last is None:
        return True
    return now - last >= (FORCE_GAP if force else every - dt.timedelta(hours=1))   # 1h slack for job timing


def _pct(x) -> str:
    return "—" if x is None else f"{x * 100:.0f}%"


def _r(x) -> str:
    return "—" if x is None else f"{x:+.2f}R"


def _wrap(display: str, paras: list[str], button: tuple[str, str], footer_html: str) -> str:
    body = "".join(f"<p>{p}</p>" for p in paras)
    label, url = button
    return (f'<div style="font-family:Arial,sans-serif;color:#0F1B2D;max-width:560px">'
            f"<p>Hi {escape(display)},</p>{body}"
            f'<p><a href="{url}" style="display:inline-block;background:#0F1B2D;color:#fff;padding:10px 18px;'
            f'border-radius:8px;text-decoration:none">{escape(label)}</a></p>'
            f'<p style="color:#5B6577;font-size:12px;margin-top:24px">{footer_html}</p></div>')


def trader_email(user: dict, prog: dict, take: dict, base: str) -> tuple[str, str, str]:
    """(subject, html, text) for one trader."""
    done, total = prog["done"], prog["total"]
    left = total - done
    unsub = f"{base}/p/unsubscribe/{user['unsub_token']}"
    link = f"{base}/p/practice"
    if done == 0:
        subject = "Your first practice setup is waiting"
        lines = ["You signed up for CRT Practice but haven't answered a setup yet.",
                 "Each one is a real GBP/USD or gold chart from 2021–2024, stopped at the moment of decision. "
                 "You say Take, Skip or Unsure, and see what happened straight after. Ten take about 15 minutes."]
    else:
        subject = f"{done} of {total} practice setups done, {left} to go"
        lines = [f"You've answered {done} of {total} practice setups. {left} are waiting."]
        if take.get("trades", 0) >= 5:
            lines.append(f"Your Takes so far: {take['trades']} finished trades, win rate {_pct(take['win_rate'])} "
                         f"against {_pct(take['chance_win_rate'])} for chance, average {_r(take['avg_R'])} against "
                         f"{_r(take['chance_avg_R'])} for chance. Under about 50 finished trades, differences are mostly luck, "
                         "so a few more sessions tell you much more.")
        else:
            lines.append("After a few more answers you'll see how your Takes compare with chance.")
        lines.append("Ten setups take about 15 minutes.")
    text = (f"Hi {user['display_name']},\n\n" + "\n\n".join(lines) + f"\n\nPractise now: {link}\n\n--\n"
            f"You get this because you opted in to CRT Practice emails. Unsubscribe: {unsub}")
    html = _wrap(user["display_name"], [escape(x) for x in lines], ("Practise now", link),
                 f'You get this because you opted in to CRT Practice emails. <a href="{unsub}">Unsubscribe</a>.')
    return subject, html, text


def owner_email(store, settings: dict, base: str) -> tuple[str, str, str]:
    prog = service.practice_progress(store)
    test = plan.build(store, settings)
    live, prac = test["live"], test["practice"]
    subject = f"Practice nudge: {prog['done']} of {prog['total']} done"
    lines = [f"Practice: {prog['done']} of {prog['total']} setups answered. A few now keeps your read of the charts sharp.",
             f"My test: {live['n']} of {plan.DECISION} finished live Takes. {live['verdict_text']}",
             f"Practice Takes: {prac['n']} finished, average {_r(prac['avg_R'])} against {_r(prac['chance_R'])} for chance."]
    text = "Hi Ore,\n\n" + "\n\n".join(lines) + f"\n\nPractice: {base}/practice\nMy test: {base}/plan"
    html = _wrap("Ore", [escape(x) for x in lines], ("Open practice", f"{base}/practice"),
                 f'<a href="{base}/plan">My test</a> · Turn these off in <a href="{base}/settings">Settings</a>.')
    return subject, html, text


def _owner_last_practice(store) -> dt.datetime | None:
    practice_ids = {p["id"] for p in service.practice_items()}
    times = [_ts(r.get("created_at")) for r in store.list_reviews() if r.get("setup_id") in practice_ids]
    times = [t for t in times if t]
    return max(times) if times else None


def run(store, settings: dict, now: dt.datetime, base: str, force: bool = False, send=None) -> dict:
    """Send every reminder that is due. Returns counts; never raises for a single failed email."""
    send = send or mailer.send
    p = prefs(settings)
    out = {"traders_due": 0, "sent": 0, "failed": 0, "skipped_recent": 0, "skipped_finished": 0,
           "owner": "off", "errors": []}
    if not mailer.configured():
        out["owner"] = "email not set up"
        return out
    day = now.date().isoformat()
    if p["community"]:
        for u in community.recipients(store):
            if not _due(_ts(u.get("last_reminded_at")), now, dt.timedelta(days=p["every_days"]), force):
                continue
            key = u["username_key"]
            reviews = store.community_reviews(key)
            last = max((_ts(r.get("created_at")) for r in reviews if r.get("created_at")), default=None)
            if last and now - last < RECENT_PRACTICE and not force:
                out["skipped_recent"] += 1
                continue
            prog = community.progress(store, key)
            if prog["done"] >= prog["total"]:
                out["skipped_finished"] += 1
                continue
            out["traders_due"] += 1
            subject, html, text = trader_email(u, prog, community.user_stats(store, key)["take"], base)
            try:
                send(u["email"], subject, html, text, tags=["practice-reminder"], idempotency_key=f"rem-{key}-{day}")
                store.community_update_user(key, last_reminded_at=now.isoformat())
                out["sent"] += 1
            except mailer.MailError as e:
                out["failed"] += 1
                out["errors"].append(str(e))
        if out["traders_due"]:
            store.email_log_add({"subject": "Practice reminder" + (" (sent now)" if force else " (automatic)"),
                                 "recipients": out["traders_due"], "sent": out["sent"], "failed": out["failed"],
                                 "note": (out["errors"] or [""])[0]})
    to = settings.get("owner_email")
    if p["owner"] and to:
        last_sent = _ts(settings.get("last_owner_nudge"))
        last_practice = _owner_last_practice(store)
        if not _due(last_sent, now, dt.timedelta(days=p["owner_every_days"]), force):
            out["owner"] = "not due"
        elif last_practice and now - last_practice < RECENT_PRACTICE and not force:
            out["owner"] = "practised recently"
        else:
            subject, html, text = owner_email(store, settings, base)
            try:
                send(to, subject, html, text, tags=["owner-practice"], idempotency_key=f"own-rem-{day}")
                settings["last_owner_nudge"] = now.isoformat()
                store.save_settings(settings)
                out["owner"] = "sent"
            except mailer.MailError as e:
                out["owner"] = f"failed: {e}"
    return out
