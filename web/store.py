"""Storage for the website. Two backends with the same methods:

  SupabaseStore - production: Supabase Postgres through its REST API (PostgREST),
                  server-side only, with the secret/service key from the environment.
  MemoryStore   - local development and tests: in memory, optionally saved to a JSON file.

Rules: a setup's `card` is written once, when first shown, and never changed (the forward
log). Later scans only update `status` (tracked outcome), `final` and `added` (options that
appeared later, with the time they were first seen).
"""
from __future__ import annotations

import copy
import datetime as dt
import json
import os
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_SETTINGS = {
    "spreads": {"GBPUSD": 0.00010, "XAUUSD": 0.35},
    "balance": 1000.0,
    "risk_pct": 1.0,
    "contract": {"GBPUSD": 100000, "XAUUSD": 100},
    "tz": "Africa/Lagos",
    "daily_credit_limit": 780,
}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def utc_today() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def merged_settings(saved: dict | None) -> dict:
    out = copy.deepcopy(DEFAULT_SETTINGS)
    for k, v in (saved or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k].update(v)
        else:
            out[k] = v
    return out


class StoreError(Exception):
    pass


# ---------------------------------------------------------------- memory


class MemoryStore:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self.lock = threading.Lock()
        self.db = {"settings": {}, "setups": {}, "reviews": [], "scans": [], "usage": {}, "secrets": {}}
        if self.path and self.path.exists():
            self.db.update(json.loads(self.path.read_text()))

    def _save(self):
        if self.path:
            self.path.write_text(json.dumps(self.db, default=str))

    # settings
    def get_settings(self) -> dict:
        return merged_settings(self.db["settings"])

    def save_settings(self, data: dict) -> None:
        with self.lock:
            self.db["settings"] = data
            self._save()

    # setups
    def get_setup(self, sid: str) -> dict | None:
        s = self.db["setups"].get(sid)
        return copy.deepcopy(s) if s else None

    def insert_setup_if_new(self, row: dict) -> bool:
        with self.lock:
            if row["id"] in self.db["setups"]:
                return False
            r = copy.deepcopy(row)
            r.setdefault("first_seen", now_iso())
            r.setdefault("added", [])
            r.setdefault("status", {})
            r.setdefault("final", False)
            self.db["setups"][r["id"]] = r
            self._save()
            return True

    def update_setup(self, sid: str, **fields) -> None:
        with self.lock:
            if sid not in self.db["setups"]:
                raise StoreError(f"no setup {sid}")
            fields.pop("card", None)          # the snapshot never changes
            self.db["setups"][sid].update(copy.deepcopy(fields))
            self.db["setups"][sid]["updated_at"] = now_iso()
            self._save()

    def list_setups(self, source: str | None = None, final: bool | None = None, pair: str | None = None,
                    limit: int = 500) -> list[dict]:
        rows = list(self.db["setups"].values())
        if source:
            rows = [r for r in rows if r.get("source") == source]
        if final is not None:
            rows = [r for r in rows if bool(r.get("final")) == final]
        if pair:
            rows = [r for r in rows if r.get("pair") == pair]
        rows.sort(key=lambda r: r.get("first_seen", ""), reverse=True)
        return copy.deepcopy(rows[:limit])

    # reviews
    def add_review(self, review: dict) -> int:
        with self.lock:
            rid = (max((r["id"] for r in self.db["reviews"]), default=0) + 1)
            r = {"option_id": None, "reasons": [], "notes": "", "confidence": None, "actual_entry": None,
                 "actual_exit": None, "actual_r": None, "actual_closed_at": None}
            r.update(copy.deepcopy(review))
            r.update(id=rid, created_at=now_iso(), updated_at=now_iso())
            self.db["reviews"].append(r)
            self._save()
            return rid

    def update_review(self, rid: int, **fields) -> None:
        with self.lock:
            for r in self.db["reviews"]:
                if r["id"] == rid:
                    r.update(copy.deepcopy(fields))
                    r["updated_at"] = now_iso()
                    self._save()
                    return
            raise StoreError(f"no review {rid}")

    def list_reviews(self, setup_id: str | None = None) -> list[dict]:
        rows = [r for r in self.db["reviews"] if setup_id is None or r["setup_id"] == setup_id]
        return copy.deepcopy(sorted(rows, key=lambda r: r["created_at"]))

    # scans
    def add_scan(self, row: dict) -> None:
        with self.lock:
            r = copy.deepcopy(row)
            r["id"] = len(self.db["scans"]) + 1
            self.db["scans"].append(r)
            self.db["scans"] = self.db["scans"][-200:]
            self._save()

    def last_scan(self, ok_only: bool = True) -> dict | None:
        for r in reversed(self.db["scans"]):
            if r.get("ok") or not ok_only:
                return copy.deepcopy(r)
        return None

    def recent_scans(self, limit: int = 20) -> list[dict]:
        return copy.deepcopy(list(reversed(self.db["scans"]))[:limit])

    def prune_scans(self, keep_days: int = 14) -> None:
        pass

    # usage
    def credits_today(self) -> int:
        return int(self.db["usage"].get(utc_today(), 0))

    def add_credits(self, n: int) -> None:
        with self.lock:
            d = utc_today()
            self.db["usage"][d] = int(self.db["usage"].get(d, 0)) + n
            self._save()

    # secrets (cron token)
    def get_secret(self, name: str) -> str | None:
        return self.db["secrets"].get(name)


# ---------------------------------------------------------------- supabase


class SupabaseStore:
    """PostgREST over HTTPS. Table definitions: db/migrations/001_init.sql."""

    def __init__(self, url: str, key: str, opener=urllib.request.urlopen, timeout: float = 15.0):
        self.base = url.rstrip("/") + "/rest/v1/"
        self.key = key
        self.opener = opener
        self.timeout = timeout

    def _headers(self, extra: dict | None = None) -> dict:
        h = {"apikey": self.key, "Content-Type": "application/json", "Accept": "application/json"}
        if self.key.startswith("eyJ"):          # legacy JWT keys also go in Authorization
            h["Authorization"] = f"Bearer {self.key}"
        if extra:
            h.update(extra)
        return h

    def _req(self, method: str, path: str, params: dict | None = None, body=None, prefer: str | None = None):
        url = self.base + path + ("?" + urllib.parse.urlencode(params, safe=",.()*:") if params else "")
        data = None if body is None else json.dumps(body, default=str).encode()
        req = urllib.request.Request(url, data=data, method=method,
                                     headers=self._headers({"Prefer": prefer} if prefer else None))
        try:
            with self.opener(req, timeout=self.timeout) as r:
                raw = r.read().decode() if hasattr(r, "read") else ""
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read().decode()).get("message", "")
            except Exception:
                msg = ""
            raise StoreError(f"database error {e.code} on {path}: {msg}") from None
        except urllib.error.URLError as e:
            raise StoreError(f"cannot reach the database: {e.reason}") from None

    # settings
    def get_settings(self) -> dict:
        rows = self._req("GET", "settings", {"id": "eq.1", "select": "data"})
        return merged_settings(rows[0]["data"] if rows else {})

    def save_settings(self, data: dict) -> None:
        self._req("POST", "settings", body={"id": 1, "data": data, "updated_at": now_iso()},
                  prefer="resolution=merge-duplicates,return=minimal")

    # setups
    def get_setup(self, sid: str) -> dict | None:
        rows = self._req("GET", "setups", {"id": f"eq.{sid}", "select": "*"})
        return rows[0] if rows else None

    def insert_setup_if_new(self, row: dict) -> bool:
        r = dict(row)
        r.setdefault("first_seen", now_iso())
        r.setdefault("added", [])
        r.setdefault("status", {})
        r.setdefault("final", False)
        out = self._req("POST", "setups", {"on_conflict": "id"}, body=r,
                        prefer="resolution=ignore-duplicates,return=representation")
        return bool(out)

    def update_setup(self, sid: str, **fields) -> None:
        fields.pop("card", None)
        fields["updated_at"] = now_iso()
        self._req("PATCH", "setups", {"id": f"eq.{sid}"}, body=fields, prefer="return=minimal")

    def list_setups(self, source: str | None = None, final: bool | None = None, pair: str | None = None,
                    limit: int = 500) -> list[dict]:
        p = {"select": "*", "order": "first_seen.desc", "limit": str(limit)}
        if source:
            p["source"] = f"eq.{source}"
        if final is not None:
            p["final"] = f"eq.{str(final).lower()}"
        if pair:
            p["pair"] = f"eq.{pair}"
        return self._req("GET", "setups", p) or []

    # reviews
    def add_review(self, review: dict) -> int:
        out = self._req("POST", "reviews", body=review, prefer="return=representation")
        return int(out[0]["id"])

    def update_review(self, rid: int, **fields) -> None:
        fields["updated_at"] = now_iso()
        self._req("PATCH", "reviews", {"id": f"eq.{rid}"}, body=fields, prefer="return=minimal")

    def list_reviews(self, setup_id: str | None = None) -> list[dict]:
        p = {"select": "*", "order": "created_at.asc", "limit": "5000"}
        if setup_id:
            p["setup_id"] = f"eq.{setup_id}"
        return self._req("GET", "reviews", p) or []

    # scans
    def add_scan(self, row: dict) -> None:
        self._req("POST", "scans", body=row, prefer="return=minimal")

    def last_scan(self, ok_only: bool = True) -> dict | None:
        p = {"select": "*", "order": "started_at.desc", "limit": "1"}
        if ok_only:
            p["ok"] = "eq.true"
        rows = self._req("GET", "scans", p)
        return rows[0] if rows else None

    def recent_scans(self, limit: int = 20) -> list[dict]:
        return self._req("GET", "scans", {"select": "id,started_at,finished_at,trigger,ok,message,credits,ready,armed",
                                          "order": "started_at.desc", "limit": str(limit)}) or []

    def prune_scans(self, keep_days: int = 14) -> None:
        cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=keep_days)).isoformat()
        self._req("DELETE", "scans", {"started_at": f"lt.{cutoff}"}, prefer="return=minimal")

    # usage
    def credits_today(self) -> int:
        rows = self._req("GET", "usage", {"day": f"eq.{utc_today()}", "select": "credits"})
        return int(rows[0]["credits"]) if rows else 0

    def add_credits(self, n: int) -> None:
        self._req("POST", "rpc/add_credits", body={"n": n})

    # secrets
    def get_secret(self, name: str) -> str | None:
        rows = self._req("GET", "app_secrets", {"name": f"eq.{name}", "select": "token"})
        return rows[0]["token"] if rows else None


class UnconfiguredStore:
    """Used in production when the database settings are missing: every call fails loudly,
    so reviews are never written to a throw-away in-memory store."""
    configured = False

    def __getattr__(self, name):
        def fail(*a, **kw):
            raise StoreError("Database not configured: set SUPABASE_URL and SUPABASE_SECRET_KEY "
                             "in the Vercel project settings (docs/website-setup.md).")
        return fail


def from_env():
    url, key = os.environ.get("SUPABASE_URL", "").strip(), os.environ.get("SUPABASE_SECRET_KEY", "").strip()
    if url and key:
        return SupabaseStore(url, key)
    if os.environ.get("LOCAL_DEV") == "1" or os.environ.get("LOCAL_STORE_FILE"):
        return MemoryStore(os.environ.get("LOCAL_STORE_FILE") or None)
    return UnconfiguredStore()
