"""Vobiz phone line (app/vobiz.py, routes in app/main.py), driven by a fake Vobiz stream."""

import base64
import math
import threading
from array import array

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app import asr, main, vobiz
from app.calls import line
from app.config import settings

SECRET = "s3cret"


def tone(seconds: float, loud: bool) -> array:
    n = round(seconds * vobiz.RATE)
    level = 3000 if loud else 0
    return array("h", (round(level * math.sin(i / 5)) for i in range(n)))


def big_endian(samples: array) -> bytes:
    swapped = array("h", samples)
    swapped.byteswap()
    return swapped.tobytes()


def test_wire_audio_is_turned_little_endian():
    assert list(vobiz.to_little_endian(big_endian(array("h", [1, -2, 300])))) == [1, -2, 300]


def test_speech_is_cut_at_pauses_and_short_clicks_are_dropped():
    cutter = vobiz.Utterances()
    audio = tone(1.0, False) + tone(1.0, True) + tone(1.0, False) + tone(0.1, True) + tone(1.0, False)
    cuts = cutter.feed(audio) + cutter.flush()
    assert len(cuts) == 1
    start, samples = cuts[0]
    assert start == pytest.approx(1.0 - vobiz.PRE_ROLL_S)  # the pre-roll keeps the first word whole
    assert len(samples) / vobiz.RATE == pytest.approx(vobiz.PRE_ROLL_S + 1.0 + vobiz.END_PAUSE_S)


def test_a_long_monologue_is_cut_so_the_screen_keeps_up():
    cutter = vobiz.Utterances()
    cuts = cutter.feed(tone(vobiz.MAX_UTTERANCE_S + 1, True)) + cutter.flush()
    assert len(cuts) == 2


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "provider", "mock")
    monkeypatch.setattr(settings, "vobiz_secret", SECRET)
    monkeypatch.setattr(settings, "vobiz_number", "+910000000000")
    monkeypatch.setattr(settings, "public_base_url", "https://ringproof.example")
    with TestClient(main.app) as client:  # one event loop for every socket, as in the real server
        yield client
    line._waiting = None


def test_the_line_is_closed_without_the_secret(client, monkeypatch):
    assert client.post("/vobiz/answer/wrong").status_code == 404
    monkeypatch.setattr(settings, "vobiz_secret", "")
    assert client.post("/vobiz/answer/anything").status_code == 404


def test_with_nobody_watching_the_caller_is_told_and_hung_up(client):
    xml = client.post(f"/vobiz/answer/{SECRET}").text
    assert "<Hangup/>" in xml and "<Stream" not in xml


def test_a_phone_call_reaches_the_waiting_dashboard(client, monkeypatch):
    async def fake(audio, diarize):
        assert not diarize  # the stream carries only the caller's side
        return {"segments": [{"start": 0, "end": 1, "text": "Hello, this is the bank."}]}

    monkeypatch.setattr(asr, "transcribe", fake)
    with client.websocket_connect("/ws/call") as dash:
        dash.send_json({"type": "start", "phone": True})
        assert dash.receive_json() == {"type": "waiting", "number": "+910000000000"}

        xml = client.post(f"/vobiz/answer/{SECRET}").text
        assert f'wss://ringproof.example/vobiz/stream/{SECRET}</Stream>' in xml
        assert 'contentType="audio/x-l16;rate=16000"' in xml

        def phone():
            with client.websocket_connect(f"/vobiz/stream/{SECRET}") as vb:
                vb.send_json({"event": "start", "start": {"streamId": "st1", "callId": "c1"}})
                vb.send_text("not json")  # skipped, the call goes on
                for chunk in (tone(1.0, True), tone(1.0, False)):
                    vb.send_json({"event": "media", "media": {"payload": base64.b64encode(big_endian(chunk)).decode()}})
            # leaving the block closes the socket: the caller hung up

        caller = threading.Thread(target=phone)
        caller.start()
        events = []
        while (ev := dash.receive_json())["type"] != "end":
            events.append(ev)
        caller.join()

    started = events[0]
    assert started["type"] == "started" and started["sample"]["id"] == "phone" and started["duration"] == 0
    assert [e["turn"]["text"] for e in events if e["type"] == "turn"] == ["Hello, this is the bank."]
    assert main._live_calls == 0 and not line.is_waiting()


def test_only_one_dashboard_waits_at_a_time(client):
    with client.websocket_connect("/ws/call") as first:
        first.send_json({"type": "start", "phone": True})
        assert first.receive_json()["type"] == "waiting"
        with client.websocket_connect("/ws/call") as second:
            second.send_json({"type": "start", "phone": True})
            with pytest.raises(WebSocketDisconnect) as closed:
                second.receive_json()
        assert closed.value.code == 1013


def test_phone_start_is_refused_when_the_line_is_off(client, monkeypatch):
    monkeypatch.setattr(settings, "vobiz_secret", "")
    with client.websocket_connect("/ws/call") as ws:
        ws.send_json({"type": "start", "phone": True})
        with pytest.raises(WebSocketDisconnect) as closed:
            ws.receive_json()
    assert closed.value.code == 1003 and "not set up" in closed.value.reason


def test_a_start_must_name_exactly_one_source(client):
    with client.websocket_connect("/ws/call") as ws:
        ws.send_json({"type": "start", "phone": True, "sample_id": "digital-arrest"})
        with pytest.raises(WebSocketDisconnect) as closed:
            ws.receive_json()
    assert closed.value.code == 1003


def test_an_uploaded_transcript_plays_as_a_call(client):
    turns = [{"t": 0, "speaker": "caller", "text": "Hello, how are you?"}]
    with client.websocket_connect("/ws/call") as ws:
        ws.send_json({"type": "start", "turns": turns, "title": "my-call.m4a", "speed": 4})
        events = []
        while (ev := ws.receive_json())["type"] != "end":
            events.append(ev)
    assert events[0]["sample"] == {"id": "upload", "title": "my-call.m4a"}
    assert [e["turn"]["text"] for e in events if e["type"] == "turn"] == ["Hello, how are you?"]
