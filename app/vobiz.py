"""Vobiz phone line: a call to the Ringproof number, transcribed live onto the waiting dashboard.

How a call flows (Vobiz audio-stream docs, VISION §3a):
1. Vobiz POSTs to our answer URL; we return VobizXML that speaks a short notice, then opens a
   one-way audio stream (`<Stream>`) to our WebSocket.
2. Vobiz sends one `start` event, then `media` events: base64 16-bit PCM, 16 kHz, mono,
   big-endian on the wire. The WebSocket closes when the call ends (there is no stop event).
3. We cut the audio into utterances at pauses, send each to the speech service (Parakeet, no
   speaker split: the stream carries only the caller's side) and push the text as caller turns
   into the dashboard's call session, which checks them exactly like a replayed call.

Audio is held only until its utterance is transcribed; nothing is saved.

The answer URL and stream URL carry VOBIZ_SECRET in the path, so only Vobiz (configured with
those URLs) can open a call; with no secret set, the line is off.
"""

import asyncio
import base64
import binascii
import contextlib
import hmac
import io
import json
import logging
import math
import wave
from array import array
from xml.sax.saxutils import escape

from fastapi import WebSocket, WebSocketDisconnect

from app import asr
from app.calls import LiveSource
from app.config import settings
from app.models import Turn

log = logging.getLogger("ringproof.vobiz")

RATE = 16000  # what Parakeet expects, so no resampling
FRAME = RATE // 50  # 20 ms, in samples

# Pause detection. Tuned by ear for a phone line; adjust after the first real calls.
SPEECH_RMS = 500  # a 20 ms frame louder than this (16-bit RMS) counts as speech
END_PAUSE_S = 0.8  # this much quiet ends an utterance
MIN_SPEECH_S = 0.3  # shorter bursts (clicks, breaths) are dropped
MAX_UTTERANCE_S = 20.0  # a long monologue is cut here so the dashboard keeps up
PRE_ROLL_S = 0.2  # quiet kept before speech, so the first word isn't clipped

NOTICE = "This call is screened by Ringproof. Please go ahead."
NOBODY = "Ringproof is not watching this line right now. Goodbye."


def secret_ok(secret: str) -> bool:
    return bool(settings.vobiz_secret) and hmac.compare_digest(secret.encode(), settings.vobiz_secret.encode())


def answer_xml(watching: bool) -> str:
    if not watching:
        return f'<?xml version="1.0" encoding="UTF-8"?><Response><Speak>{escape(NOBODY)}</Speak><Hangup/></Response>'
    base = settings.public_base_url.rstrip("/").replace("https://", "wss://", 1).replace("http://", "ws://", 1)
    stream_url = f"{base}/vobiz/stream/{settings.vobiz_secret}"
    # keepCallAlive needs bidirectional="true", and that needs audioTrack="inbound" (Vobiz docs).
    return (
        '<?xml version="1.0" encoding="UTF-8"?><Response>'
        f"<Speak>{escape(NOTICE)}</Speak>"
        '<Stream bidirectional="true" audioTrack="inbound" keepCallAlive="true" '
        f'contentType="audio/x-l16;rate={RATE}">{escape(stream_url)}</Stream>'
        "</Response>"
    )


def to_little_endian(payload: bytes) -> array:
    samples = array("h")
    samples.frombytes(payload[: len(payload) - len(payload) % 2])
    samples.byteswap()  # the wire is big-endian; array uses the machine's order (little-endian)
    return samples


def wav_bytes(samples: array) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(samples.tobytes())
    return buf.getvalue()


class Utterances:
    """Cuts a stream of samples into utterances at pauses. feed() returns finished ones as
    (start_seconds, samples)."""

    def __init__(self) -> None:
        self._pending = array("h")  # samples not yet a whole frame
        self._heard = 0  # frames seen so far (for timestamps)
        self._pre: list[array] = []  # recent quiet frames, for the pre-roll
        self._speech: list[array] = []  # the utterance being collected
        self._start = 0
        self._quiet = 0  # quiet frames since the last speech frame
        self._loud = 0  # speech frames in this utterance

    def feed(self, samples: array) -> list[tuple[float, array]]:
        self._pending.extend(samples)
        done = []
        while len(self._pending) >= FRAME:
            frame, self._pending = self._pending[:FRAME], self._pending[FRAME:]
            if (cut := self._frame(frame)) is not None:
                done.append(cut)
        return done

    def flush(self) -> list[tuple[float, array]]:
        cut = self._cut()
        return [cut] if cut else []

    def _frame(self, frame: array) -> tuple[float, array] | None:
        self._heard += 1
        loud = math.sqrt(sum(s * s for s in frame) / FRAME) > SPEECH_RMS
        if not self._speech:
            if not loud:
                self._pre = (self._pre + [frame])[-round(PRE_ROLL_S * 50):]
                return None
            self._start = self._heard - 1 - len(self._pre)
            self._speech, self._pre = self._pre, []
        self._speech.append(frame)
        self._loud += loud
        self._quiet = 0 if loud else self._quiet + 1
        if self._quiet >= END_PAUSE_S * 50 or len(self._speech) >= MAX_UTTERANCE_S * 50:
            return self._cut()
        return None

    def _cut(self) -> tuple[float, array] | None:
        speech, loud, start = self._speech, self._loud, self._start
        self._speech, self._loud, self._quiet = [], 0, 0
        if loud < MIN_SPEECH_S * 50:
            return None
        out = array("h")
        for frame in speech:
            out.extend(frame)
        return start / 50, out


async def stream_call(ws: WebSocket, source: LiveSource) -> None:
    """Read one Vobiz audio stream into `source` until the call ends."""
    queue: asyncio.Queue[tuple[float, array] | None] = asyncio.Queue()

    async def transcribe_in_order() -> None:
        # One at a time, so turns reach the dashboard in the order they were spoken.
        while (item := await queue.get()) is not None:
            start, samples = item
            try:
                result = await asr.transcribe(wav_bytes(samples), diarize=False)
            except asr.AsrError as err:
                log.warning("utterance not transcribed: %s", err)
                continue
            text = " ".join(s["text"].strip() for s in result.get("segments", [])).strip()
            if text:
                source.push(Turn(t=round(start, 1), speaker="caller", text=text))

    worker = asyncio.create_task(transcribe_in_order())
    cutter = Utterances()
    stream_id = ""
    try:
        while source.watching:
            try:
                msg = json.loads(await ws.receive_text())
                if msg.get("event") == "start":
                    stream_id = msg.get("start", {}).get("streamId", "")
                elif msg.get("event") == "media":
                    payload = base64.b64decode(msg.get("media", {}).get("payload", ""))
                    for item in cutter.feed(to_little_endian(payload)):
                        queue.put_nowait(item)
            except (ValueError, AttributeError, binascii.Error):
                continue  # skip a malformed frame; the call goes on
        # The dashboard left: end the stream, and with nothing after it Vobiz hangs up.
        with contextlib.suppress(Exception):
            await ws.send_json({"event": "stop", "streamId": stream_id})
    except WebSocketDisconnect:
        pass  # the call has ended: Vobiz closes the socket (there is no stop event)
    finally:
        for item in cutter.flush():
            queue.put_nowait(item)
        queue.put_nowait(None)
        with contextlib.suppress(Exception):
            await worker
        source.end()
