"""Public practice: other traders review the same past setups under a username (no password).

Kept apart from Ore's own data: separate tables, separate pages, separate statistics.
A username is "claimed" by the first browser that uses it (a random token in that browser's
session). Another browser typing the same name must confirm it is the same person, so results
are not mixed by accident. This is not security: anyone can type any name.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import random
import re
import secrets

from . import mailer, service

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,20}$")
DAILY_LIMIT = 200


def key_of(name: str) -> str:
    return name.strip().lower()


def valid_name(name: str) -> bool:
    return bool(USERNAME_RE.match(name.strip()))


def new_token() -> str:
    return secrets.token_hex(16)


def token_hash(token: str) -> str:
    return hashlib.sha256(("community|" + token).encode()).hexdigest()


def claim(store, name: str, token: str | None, confirmed: bool) -> tuple[str, str | None]:
    """Returns (result, token): 'new' (name created), 'same' (this browser owns it),
    'confirmed' (other browser, user confirmed it's them), 'taken' (needs confirmation)."""
    k = key_of(name)
    u = store.community_user(k)
    if u is None:
        tok = new_token()
        if store.community_add_user(k, name.strip(), token_hash(tok)):
            return "new", tok
        u = store.community_user(k)              # created by someone else a moment ago
    if token and u and token_hash(token) == u["token_hash"]:
        return "same", token
    if confirmed:
        return "confirmed", token
    return "taken", None


def order_for(key: str) -> list[dict]:
    """Every trader gets the same setups in their own random order."""
    items = list(service.active_practice_items("crt"))     # public practice: CRT setups only
    seed = int(hashlib.sha256(key.encode()).hexdigest()[:12], 16)
    random.Random(seed).shuffle(items)
    return items


def done_ids(store, key: str) -> set[str]:
    return {r["item_id"] for r in store.community_reviews(key)}


def next_item(store, key: str) -> dict | None:
    done = done_ids(store, key)
    return next((p for p in order_for(key) if p["id"] not in done), None)


def progress(store, key: str) -> dict:
    active = {p["id"] for p in service.active_practice_items("crt")}
    return {"done": len(done_ids(store, key) & active), "total": len(active)}


def save(store, key: str, item: dict, review: dict) -> str:
    """Returns 'saved', 'duplicate' or 'limit'."""
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    mine = store.community_reviews(key)
    if sum(1 for r in mine if str(r["created_at"])[:10] == today) >= DAILY_LIMIT:
        return "limit"
    row = {"username_key": key, "item_id": item["id"], **{k: review[k] for k in
           ("decision", "option_id", "reasons", "notes", "confidence")}}
    return "saved" if store.community_add_review(row) else "duplicate"


def _pairs(reviews: list[dict], decision: str | None) -> list[tuple[dict, dict]]:
    out = []
    for r in reviews:
        if decision and r["decision"] != decision:
            continue
        item = service.practice_item(r["item_id"])
        if not item:
            continue
        card = item["card"]
        oid = r.get("option_id") if r["decision"] == "take" else None
        op = service.option_by_id(card, oid) or service.option_by_id(card, card.get("best"))
        if op:
            out.append((op, item["outcome"].get(op["id"])))
    return out


def user_stats(store, key: str) -> dict:
    rv = store.community_reviews(key)
    return {d: service.group_stats(_pairs(rv, d)) for d in ("take", "skip", "unsure")} | {"reviews": len(rv)}


def all_stats(store) -> dict:
    """For Ore's Performance page: every trader, and everyone together."""
    users = {u["username_key"]: u["display_name"] for u in store.community_users_all()}
    rv = store.community_reviews()
    by_user: dict[str, list] = {}
    for r in rv:
        by_user.setdefault(r["username_key"], []).append(r)
    rows = []
    for k, lst in sorted(by_user.items(), key=lambda kv: -len(kv[1])):
        rows.append({"name": users.get(k, k), "reviews": len(lst),
                     "take": service.group_stats(_pairs(lst, "take")),
                     "skip": service.group_stats(_pairs(lst, "skip"))})
    return {"users": rows, "total_reviews": len(rv),
            "everyone_take": service.group_stats(_pairs(rv, "take")),
            "everyone_skip": service.group_stats(_pairs(rv, "skip"))}


# ---------------------------------------------------------------- email sign-in (6-digit codes)

EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[A-Za-z]{2,24}$")
CODE_TTL = dt.timedelta(minutes=10)
MAX_ATTEMPTS = 5
MAX_CODES_PER_EMAIL_HOUR = 5
MAX_CODES_PER_DAY = 300


def email_signin_enabled() -> bool:
    """Email sign-in switches on by itself once SendByte can really deliver (live key + sender)."""
    return mailer.live()


def norm_email(email: str) -> str:
    return (email or "").strip().lower()


def valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(norm_email(email)))


def _code_hash(pepper: str, email: str, code: str) -> str:
    return hashlib.sha256(f"code|{pepper}|{email}|{code}".encode()).hexdigest()


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _ts(x) -> dt.datetime:
    return dt.datetime.fromisoformat(str(x).replace("Z", "+00:00"))


def start_signin(store, name: str, email: str, notify: bool, pepper: str, site_url: str,
                 send=None) -> tuple[str, dict]:
    """Returns (status, info). status: sent | bad_email | bad_name | name_taken | too_many | busy | mail_error."""
    email = norm_email(email)
    if not valid_email(email):
        return "bad_email", {}
    existing = store.community_user_by("email", email)
    if existing:
        key, display = existing["username_key"], existing["display_name"]
    else:
        if not valid_name(name):
            return "bad_name", {}
        key, display = key_of(name), name.strip()
        owner = store.community_user(key)
        if owner and owner.get("email") and owner["email"] != email:
            return "name_taken", {}
    now = _now()
    if store.codes_since((now - dt.timedelta(hours=1)).isoformat(), email) >= MAX_CODES_PER_EMAIL_HOUR:
        return "too_many", {}
    if store.codes_since((now - dt.timedelta(days=1)).isoformat()) >= MAX_CODES_PER_DAY:
        return "busy", {}
    send = send or mailer.send
    code = f"{secrets.randbelow(10 ** 6):06d}"
    store.code_add({"email": email, "username_key": key, "display_name": display, "notify": bool(notify),
                    "code_hash": _code_hash(pepper, email, code), "expires_at": (now + CODE_TTL).isoformat()})
    text = (f"Your CRT Practice sign-in code is {code}\n\nIt works for 10 minutes. If you didn't ask for it, "
            f"ignore this email.\n\n{site_url}")
    html = (f'<div style="font-family:Arial,sans-serif;color:#0F1B2D;max-width:480px">'
            f'<p>Your CRT Practice sign-in code is</p>'
            f'<p style="font-size:28px;letter-spacing:6px;font-family:monospace"><b>{code}</b></p>'
            f'<p>It works for 10 minutes. If you didn\'t ask for it, ignore this email.</p>'
            f'<p style="color:#5B6577;font-size:12px">{site_url}</p></div>')
    try:
        send(email, "Your CRT Practice code", html, text, tags=["signin"])
    except mailer.MailError as e:
        return "mail_error", {"message": str(e)}
    return "sent", {"display": display, "existing": bool(existing)}


def verify_code(store, email: str, code: str, pepper: str) -> tuple[str, str | None]:
    """Returns (status, username_key). status: ok | wrong | expired | locked | none."""
    email, code = norm_email(email), (code or "").strip().replace(" ", "")
    row = store.code_latest(email)
    if not row or row.get("used"):
        return "none", None
    if _ts(row["expires_at"]) < _now():
        return "expired", None
    if int(row.get("attempts", 0)) >= MAX_ATTEMPTS:
        return "locked", None
    if not secrets.compare_digest(_code_hash(pepper, email, code), row["code_hash"]):
        store.code_update(row["id"], attempts=int(row.get("attempts", 0)) + 1)
        return "wrong", None
    store.code_update(row["id"], used=True)
    key = row["username_key"]
    now = _now().isoformat()
    user = store.community_user(key)
    if user is None:
        if not store.community_add_user(key, row["display_name"], token_hash(new_token()), email=email,
                                        email_verified_at=now, notify=bool(row["notify"]),
                                        unsub_token=secrets.token_urlsafe(24)):
            return "none", None
    else:
        fields = {"email": email, "email_verified_at": now}
        if not user.get("unsub_token"):
            fields["unsub_token"] = secrets.token_urlsafe(24)
        if not user.get("email"):                      # first time this name gets an email
            fields["notify"] = bool(row["notify"])
        store.community_update_user(key, **fields)
    return "ok", key


# ---------------------------------------------------------------- update emails

def recipients(store) -> list[dict]:
    return [u for u in store.community_users_all()
            if u.get("email") and u.get("email_verified_at") and u.get("notify") and u.get("unsub_token")]


def update_email(subject: str, message: str, display: str, unsub_url: str) -> tuple[str, str]:
    """Plain-text message -> (html, text) with greeting and unsubscribe link."""
    from html import escape
    paras = [p.strip() for p in message.replace("\r", "").split("\n\n") if p.strip()]
    html_body = "".join(f"<p>{escape(p).replace(chr(10), '<br>')}</p>" for p in paras)
    html = (f'<div style="font-family:Arial,sans-serif;color:#0F1B2D;max-width:560px">'
            f'<p>Hi {escape(display)},</p>{html_body}'
            f'<p style="color:#5B6577;font-size:12px;margin-top:24px">You get this because you opted in to CRT Practice '
            f'updates. <a href="{unsub_url}">Unsubscribe</a>.</p></div>')
    text = f"Hi {display},\n\n{message.strip()}\n\n--\nUnsubscribe: {unsub_url}"
    return html, text


def send_update(store, subject: str, message: str, unsub_base: str, time_budget_s: float = 45.0,
                send=None) -> dict:
    """One email per recipient (nobody sees other addresses). Safe to run again with the same
    subject and message: SendByte's idempotency key skips people already sent to."""
    import time
    send = send or mailer.send
    uid = hashlib.sha256(f"{subject}|{message}".encode()).hexdigest()[:16]
    people = recipients(store)
    t0, sent, failed, errors = time.time(), 0, 0, []
    for i, u in enumerate(people):
        if time.time() - t0 > time_budget_s:
            break
        html, text = update_email(subject, message, u["display_name"], f"{unsub_base}/{u['unsub_token']}")
        try:
            send(u["email"], subject, html, text, tags=["update"], idempotency_key=f"upd-{uid}-{u['username_key']}")
            sent += 1
        except mailer.MailError as e:
            failed += 1
            errors.append(str(e))
    done = sent + failed
    note = f"{len(people) - done} not reached yet: press send again to continue" if done < len(people) else ""
    if errors:
        note = (note + " | " if note else "") + errors[0]
    store.email_log_add({"subject": subject, "recipients": len(people), "sent": sent, "failed": failed, "note": note})
    return {"recipients": len(people), "sent": sent, "failed": failed, "note": note}
