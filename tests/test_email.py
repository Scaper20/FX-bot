import io
import json
import re
import urllib.error

import pytest

from web import community, mailer
from tests.conftest import csrf, login


class Outbox:
    def __init__(self):
        self.sent = []

    def __call__(self, to, subject, html, text, tags=None, idempotency_key=None, **kw):
        self.sent.append({"to": to, "subject": subject, "html": html, "text": text, "key": idempotency_key})
        return {"id": "x", "status": "queued"}

    def code_for(self, email):
        m = [re.search(r"code is (\d{6})", e["text"]).group(1) for e in self.sent if e["to"] == email and "code is" in e["text"]]
        return m[-1]


@pytest.fixture()
def mail(monkeypatch):
    box = Outbox()
    monkeypatch.setattr(mailer, "send", box)
    monkeypatch.setattr(community, "email_signin_enabled", lambda: True)
    return box


def signup(c, name, email, notify=True):
    tok = csrf(c, "/p")
    data = {"csrf": tok, "username": name, "email": email}
    if notify:
        data["notify"] = "1"
    return c.post("/p", data=data)


def verify(c, code):
    tok = csrf(c, "/p/verify")
    return c.post("/p/verify", data={"csrf": tok, "code": code})


def test_signup_with_code(env, mail):
    app, store, clock = env
    c = app.test_client()
    r = signup(c, "Bola", "Bola@Example.com")
    assert r.headers["Location"].endswith("/p/verify")
    assert mail.sent[-1]["to"] == "bola@example.com"
    code = mail.code_for("bola@example.com")
    assert code not in json.dumps(store.db["community_codes"])          # only the hash is stored
    assert "Check the email and try again" in verify(c, "000000" if code != "000000" else "111111").get_data(as_text=True)
    r = verify(c, code)
    assert r.headers["Location"].endswith("/p/practice")
    u = store.community_user("bola")
    assert u["email"] == "bola@example.com" and u["email_verified_at"] and u["notify"] is True
    assert c.get("/p/verify").status_code == 302                     # signed in: the code page is done


def test_existing_email_signs_into_same_account_and_names_are_protected(env, mail):
    app, store, clock = env
    a = app.test_client()
    signup(a, "Bola", "bola@example.com")
    verify(a, mail.code_for("bola@example.com"))
    b = app.test_client()
    signup(b, "SomethingElse", "BOLA@example.com")                     # same email, other device
    verify(b, mail.code_for("bola@example.com"))
    with b.session_transaction() as s:
        assert s["pu"] == "bola"
    c = app.test_client()
    r = signup(c, "bola", "intruder@example.com")                       # name owned by another email
    assert "belongs to another email" in r.get_data(as_text=True)


def test_code_expiry_lock_and_rate_limit(env, mail, monkeypatch):
    app, store, clock = env
    pepper = "p"
    assert community.start_signin(store, "Kunle", "k@example.com", False, pepper, "u")[0] == "sent"
    code = mail.code_for("k@example.com")
    for _ in range(community.MAX_ATTEMPTS):
        assert community.verify_code(store, "k@example.com", "999999" if code != "999999" else "888888", pepper)[0] == "wrong"
    assert community.verify_code(store, "k@example.com", code, pepper)[0] == "locked"
    row = store.code_latest("k@example.com")
    store.code_update(row["id"], attempts=0, expires_at="2000-01-01T00:00:00+00:00")
    assert community.verify_code(store, "k@example.com", code, pepper)[0] == "expired"
    for _ in range(community.MAX_CODES_PER_EMAIL_HOUR - 1):
        community.start_signin(store, "Kunle", "k@example.com", False, pepper, "u")
    assert community.start_signin(store, "Kunle", "k@example.com", False, pepper, "u")[0] == "too_many"


def test_unsubscribe_delete_and_updates(env, mail):
    app, store, clock = env
    c = app.test_client()
    signup(c, "Ngozi", "n@example.com", notify=True)
    verify(c, mail.code_for("n@example.com"))
    d = app.test_client()
    signup(d, "Tunde", "t@example.com", notify=False)
    verify(d, mail.code_for("t@example.com"))
    assert [u["username_key"] for u in community.recipients(store)] == ["ngozi"]
    # Ore sends an update: one email per opted-in trader, with an unsubscribe link
    o = app.test_client()
    login(o)
    tok = csrf(o, "/community")
    mail.sent.clear()
    r = o.post("/community", data={"csrf": tok, "subject": "New sets", "message": "Hello <b>all</b>\n\nPara 2",
                                   "action": "all"})
    assert "Sent to 1 of 1" in r.get_data(as_text=True)
    em = mail.sent[-1]
    assert em["to"] == "n@example.com" and "&lt;b&gt;all&lt;/b&gt;" in em["html"] and "/p/unsubscribe/" in em["html"]
    assert em["key"].startswith("upd-")
    token = store.community_user("ngozi")["unsub_token"]
    page = c.get(f"/p/unsubscribe/{token}").get_data(as_text=True)
    assert "Stop update emails" in page
    tok = re.search(r'name="csrf" value="([0-9a-f]+)"', page).group(1)
    c.post(f"/p/unsubscribe/{token}", data={"csrf": tok})
    assert store.community_user("ngozi")["notify"] is False
    assert c.get("/p/unsubscribe/not-a-real-token-123").status_code == 404
    # delete account removes everything
    tok = csrf(d, "/p/me")
    d.post("/p/me/delete", data={"csrf": tok, "confirm": "1"})
    assert store.community_user("tunde") is None


def test_username_only_flow_when_email_not_live(env, monkeypatch):
    app, store, clock = env
    monkeypatch.setattr(community, "email_signin_enabled", lambda: False)
    page = app.test_client().get("/p").get_data(as_text=True)
    assert 'name="email"' not in page and 'name="username"' in page


class Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_sendbyte_request_and_errors(monkeypatch):
    monkeypatch.setenv("SENDBYTE_API_KEY", "sk_test_abc")
    monkeypatch.setenv("SENDBYTE_FROM", "CRT Practice <p@mail.example.com>")
    seen = {}

    def opener(req, timeout):
        seen.update(url=req.full_url, auth=req.headers.get("Authorization"), body=json.loads(req.data))
        return Resp(json.dumps({"id": "e1", "status": "queued", "sandbox": True}).encode())
    out = mailer.send("a@b.ng", "Hi", "<p>x</p>", "x", tags=["t"], idempotency_key="k1", opener=opener)
    assert out["sandbox"] is True and mailer.configured() and not mailer.live()
    assert seen["url"] == "https://api.sendbyte.africa/v1/emails" and seen["auth"] == "Bearer sk_test_abc"
    assert seen["body"] == {"from": "CRT Practice <p@mail.example.com>", "to": "a@b.ng", "subject": "Hi",
                            "html": "<p>x</p>", "text": "x", "tags": ["t"], "idempotency_key": "k1"}
    err = urllib.error.HTTPError(mailer.API, 403, "x", {}, io.BytesIO(json.dumps(
        {"error": {"code": "domain_not_verified", "message": "Verify your domain"}}).encode()))

    def bad(req, timeout):
        raise err
    with pytest.raises(mailer.MailError, match="domain_not_verified"):
        mailer.send("a@b.ng", "Hi", "x", "x", opener=bad)
    monkeypatch.setenv("SENDBYTE_API_KEY", "sk_live_abc")
    assert mailer.live()
