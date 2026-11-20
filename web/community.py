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

from . import service

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
    items = list(service.practice_items())
    seed = int(hashlib.sha256(key.encode()).hexdigest()[:12], 16)
    random.Random(seed).shuffle(items)
    return items


def done_ids(store, key: str) -> set[str]:
    return {r["item_id"] for r in store.community_reviews(key)}


def next_item(store, key: str) -> dict | None:
    done = done_ids(store, key)
    return next((p for p in order_for(key) if p["id"] not in done), None)


def progress(store, key: str) -> dict:
    return {"done": len(done_ids(store, key)), "total": len(service.practice_items())}


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
