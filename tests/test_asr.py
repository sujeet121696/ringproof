"""Speech service output -> transcript turns (app/asr.py), and the upload endpoint."""

import pytest
from fastapi.testclient import TestClient

from app import asr, main
from app.asr import parse_speakers, to_turns
from app.config import settings


def seg(start, end, text):
    return {"start": start, "end": end, "text": text}


def test_speaker_lines_are_parsed_with_spaces_or_commas():
    assert parse_speakers(["0.80 3.20 speaker_0", "3.5, 6.0, speaker_1", "junk"]) == [(0.8, 3.2, 0), (3.5, 6.0, 1)]


def test_first_voice_is_the_caller_and_same_speaker_lines_join():
    segments = [seg(0.0, 2.0, "This is the CBI."), seg(2.1, 4.0, "You are under arrest."), seg(4.5, 5.5, "What?")]
    speakers = ["0.0 4.0 speaker_1", "4.4 5.6 speaker_0"]  # speaker_1 talks first: the caller
    turns = to_turns(segments, speakers)
    assert [(t.t, t.speaker, t.text) for t in turns] == [
        (0.0, "caller", "This is the CBI. You are under arrest."),
        (4.5, "user", "What?"),
    ]


def test_a_segment_goes_to_whoever_talks_most_during_it():
    turns = to_turns([seg(0, 1, "Hello"), seg(1.0, 3.0, "Mummy, it's me")], ["0 1.2 speaker_0", "1.2 3.0 speaker_1"])
    assert [t.speaker for t in turns] == ["caller", "user"]


def test_uncovered_segments_keep_the_current_speaker_and_no_speaker_data_means_caller():
    assert [t.speaker for t in to_turns([seg(0, 1, "Hi"), seg(9, 10, "there")], ["0 1 speaker_0"])] == ["caller"]
    assert [t.speaker for t in to_turns([seg(0, 1, "Hi"), seg(1, 2, " ")], [])] == ["caller"]


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "provider", "mock")
    monkeypatch.setattr(main, "_uploads", {})  # each test starts with no uploads counted
    return TestClient(main.app)


def test_upload_returns_turns(client, monkeypatch):
    async def fake(audio, diarize):
        assert audio == b"RIFF..." and diarize
        return {"segments": [seg(0, 1, "Send money now.")], "speakers": ["0 1 speaker_0"]}

    monkeypatch.setattr(asr, "transcribe", fake)
    resp = client.post("/api/transcribe", content=b"RIFF...")
    assert resp.status_code == 200
    assert resp.json() == {"turns": [{"t": 0.0, "speaker": "caller", "text": "Send money now."}]}


def test_upload_says_plainly_when_transcription_is_off(client, monkeypatch):
    monkeypatch.setattr(settings, "asr_url", "")
    resp = client.post("/api/transcribe", content=b"audio")
    assert resp.status_code == 502 and "not switched on" in resp.json()["detail"]


def test_upload_size_is_bounded(client, monkeypatch):
    monkeypatch.setattr(asr, "MAX_AUDIO_BYTES", 4)
    assert client.post("/api/transcribe", content=b"12345").status_code == 413
    assert client.post("/api/transcribe", content=b"").status_code == 400


def test_uploads_per_visitor_are_limited(client, monkeypatch):
    async def fake(audio, diarize):
        return {"segments": [seg(0, 1, "Hello")], "speakers": []}

    monkeypatch.setattr(asr, "transcribe", fake)
    monkeypatch.setattr(settings, "uploads_per_hour", 2)
    me, other = {"cf-connecting-ip": "203.0.113.1"}, {"cf-connecting-ip": "203.0.113.2"}
    assert [client.post("/api/transcribe", content=b"a", headers=me).status_code for _ in range(3)] == [200, 200, 429]
    assert client.post("/api/transcribe", content=b"a", headers=other).status_code == 200
