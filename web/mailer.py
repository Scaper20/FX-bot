"""SendByte (sendbyte.africa) email client.

Settings (Vercel environment variables):
  SENDBYTE_API_KEY  sk_live_... (real delivery, needs a verified domain) or sk_test_... (sandbox: nothing delivered)
  SENDBYTE_FROM     sender, e.g. "CRT Practice <practice@mail.kiqstat.com>" (domain verified in SendByte)
The key is only ever sent in the Authorization header and never logged.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

API = "https://api.sendbyte.africa/v1/emails"


class MailError(Exception):
    pass


def _key() -> str:
    return os.environ.get("SENDBYTE_API_KEY", "").strip()


def sender() -> str:
    return os.environ.get("SENDBYTE_FROM", "").strip()


def configured() -> bool:
    return bool(_key() and sender())


def live() -> bool:
    """True only when real emails are delivered (live key). Email sign-in needs this."""
    return configured() and _key().startswith("sk_live_")


def send(to: str, subject: str, html: str, text: str, tags: list[str] | None = None,
         idempotency_key: str | None = None, opener=urllib.request.urlopen, timeout: float = 15.0) -> dict:
    """Send one email to one recipient. Returns SendByte's response (id, status, sandbox)."""
    if not configured():
        raise MailError("Email is not set up (SENDBYTE_API_KEY / SENDBYTE_FROM).")
    body = {"from": sender(), "to": to, "subject": subject[:998], "html": html, "text": text}
    if tags:
        body["tags"] = tags[:10]
    if idempotency_key:
        body["idempotency_key"] = idempotency_key
    req = urllib.request.Request(API, data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json",
                                          "User-Agent": "crt-scanner/1.3"})
    try:
        with opener(req, timeout=timeout) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode()).get("error", {})
            msg = f"{err.get('code', e.code)}: {err.get('message', '')}"
        except Exception:
            msg = f"HTTP {e.code}"
        raise MailError(f"SendByte refused the email ({msg})") from None
    except urllib.error.URLError as e:
        raise MailError(f"Could not reach SendByte: {e.reason}") from None
