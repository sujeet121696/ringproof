"""Public-server protections in app/main.py and app/notify.py: what a stranger on the demo URL can't do."""

import asyncio

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app import main
from app.config import settings
from app.notify import EmailNotifier, NotSent, is_allowed

# One harmless caller line: low risk, so no actions, emails or lookups.
QUIET = {"id": "quiet", "title": "Quiet", "turns": [{"t": 0, "speaker": "caller", "text": "Hello, how are you?"}]}
START = {"type": "start", "sample_id": "quiet", "speed": 4}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "provider", "mock")  # no model credits
    monkeypatch.setattr(main, "load_sample", lambda sid: QUIET if sid == "quiet" else None)
    return TestClient(main.app)


def test_a_full_call_frees_its_slot(client):
    with client.websocket_connect("/ws/call") as ws:
        ws.send_json(START)
        while ws.receive_json()["type"] != "end":
            pass
    assert main._live_calls == 0


def test_calls_over_the_cap_are_refused_with_a_reason(client, monkeypatch):
    monkeypatch.setattr(settings, "max_live_calls", 0)
    with client.websocket_connect("/ws/call") as ws:
        ws.send_json(START)
        with pytest.raises(WebSocketDisconnect) as closed:
            ws.receive_json()
    assert closed.value.code == 1013 and "busy" in closed.value.reason
    assert main._live_calls == 0


def test_replay_speed_is_bounded(client):
    with client.websocket_connect("/ws/call") as ws:
        ws.send_json({**START, "speed": 0.0001})  # would hold a slot for days
        with pytest.raises(WebSocketDisconnect) as closed:
            ws.receive_json()
    assert closed.value.code == 1003


def test_there_is_no_open_model_endpoint(client):
    assert client.post("/api/assess", json={}).status_code in (404, 405)


def test_email_goes_only_to_approved_addresses(monkeypatch):
    monkeypatch.setattr(settings, "email_demo_redirect_to", "me@gmail.com")
    monkeypatch.setattr(settings, "email_allowed_to", "sister@gmail.com, Friend@Mail.com ")
    assert is_allowed("me@gmail.com") and is_allowed("sister@gmail.com") and is_allowed("friend@mail.com")
    assert not is_allowed("stranger@gmail.com")
    monkeypatch.setattr(settings, "email_allowed_to", "")
    monkeypatch.setattr(settings, "email_demo_redirect_to", "")
    assert not is_allowed("me@gmail.com")  # closed by default


def test_a_stranger_address_is_refused_before_any_connection(monkeypatch):
    monkeypatch.setattr(settings, "smtp_user", "me@gmail.com")
    monkeypatch.setattr(settings, "email_demo_redirect_to", "me@gmail.com")
    monkeypatch.setattr(settings, "email_allowed_to", "")
    monkeypatch.setattr(EmailNotifier, "_send", staticmethod(lambda msg: pytest.fail("must not send")))
    with pytest.raises(NotSent, match="approved list"):
        asyncio.run(EmailNotifier().send("stranger@gmail.com", "s", "b"))


def test_dashboard_caching_hashed_assets_long_everything_else_rechecked():
    from app.web import DIST

    if not DIST.is_dir():
        pytest.skip("dashboard not built (npm run build)")
    client = TestClient(main.app)
    asset = next((DIST / "assets").glob("*.js")).name
    assert "immutable" in client.get(f"/assets/{asset}").headers["cache-control"]
    for path in ("/", "/sw.js"):
        assert client.get(path).headers["cache-control"] == "no-cache"
    assert client.get("/api/health").headers["x-frame-options"] == "DENY"
