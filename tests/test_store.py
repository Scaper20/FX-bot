"""SupabaseStore request formation, checked against a fake server (no network)."""
import io
import json
import urllib.error

import pytest

from web.store import MemoryStore, StoreError, SupabaseStore


class Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeServer:
    def __init__(self, replies=None):
        self.calls, self.replies = [], list(replies or [])

    def __call__(self, req, timeout):
        self.calls.append({"method": req.get_method(), "url": req.full_url, "headers": dict(req.header_items()),
                           "body": json.loads(req.data) if req.data else None})
        reply = self.replies.pop(0) if self.replies else []
        if isinstance(reply, Exception):
            raise reply
        return Resp(b"" if reply is None else json.dumps(reply).encode())


def test_secret_key_goes_in_apikey_header_only():
    fs = FakeServer([[]])
    SupabaseStore("https://x.supabase.co", "sb_secret_abc", opener=fs).list_setups()
    h = {k.lower(): v for k, v in fs.calls[0]["headers"].items()}
    assert h["apikey"] == "sb_secret_abc" and "authorization" not in h
    fs = FakeServer([[]])
    SupabaseStore("https://x.supabase.co", "eyJhbGciOi.test", opener=fs).list_setups()
    h = {k.lower(): v for k, v in fs.calls[0]["headers"].items()}
    assert h["authorization"] == "Bearer eyJhbGciOi.test"


def test_insert_if_new_uses_on_conflict_ignore():
    fs = FakeServer([[{"id": "a"}], []])
    st = SupabaseStore("https://x.supabase.co/", "sb_secret_abc", opener=fs)
    assert st.insert_setup_if_new({"id": "a", "card": {}}) is True
    assert st.insert_setup_if_new({"id": "a", "card": {}}) is False
    c = fs.calls[0]
    assert c["method"] == "POST" and c["url"].startswith("https://x.supabase.co/rest/v1/setups?on_conflict=id")
    assert "resolution=ignore-duplicates" in {k.lower(): v for k, v in c["headers"].items()}["prefer"]
    assert c["body"]["final"] is False and c["body"]["status"] == {}


def test_update_never_sends_the_snapshot():
    fs = FakeServer([None])
    SupabaseStore("https://x.supabase.co", "k", opener=fs).update_setup("a", card={"x": 1}, final=True)
    c = fs.calls[0]
    assert c["method"] == "PATCH" and "id=eq.a" in c["url"]
    assert "card" not in c["body"] and c["body"]["final"] is True


def test_filters_and_rpc():
    fs = FakeServer([[], None, [{"credits": 12}]])
    st = SupabaseStore("https://x.supabase.co", "k", opener=fs)
    st.list_setups(source="live", final=False, pair="XAUUSD", limit=5)
    st.add_credits(6)
    assert st.credits_today() == 12
    url = fs.calls[0]["url"]
    assert "source=eq.live" in url and "final=eq.false" in url and "pair=eq.XAUUSD" in url and "limit=5" in url
    assert fs.calls[1]["url"].endswith("/rest/v1/rpc/add_credits") and fs.calls[1]["body"] == {"n": 6}


def test_http_errors_become_store_errors():
    err = urllib.error.HTTPError("https://x", 401, "Unauthorized", {}, io.BytesIO(b'{"message":"Invalid API key"}'))
    st = SupabaseStore("https://x.supabase.co", "k", opener=FakeServer([err]))
    with pytest.raises(StoreError, match="Invalid API key"):
        st.get_settings()


def test_memory_store_keeps_snapshot_immutable(tmp_path):
    m = MemoryStore(tmp_path / "s.json")
    assert m.insert_setup_if_new({"id": "a", "card": {"v": 1}, "source": "live"})
    m.update_setup("a", card={"v": 2}, final=True)
    again = MemoryStore(tmp_path / "s.json").get_setup("a")
    assert again["card"] == {"v": 1} and again["final"] is True
