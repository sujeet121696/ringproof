"""Call sources: every channel delivers a call as a stream of transcript turns.

ReplaySource plays a saved transcript (a sample, or an uploaded recording after transcription).
LiveSource carries a phone call as it is heard (app/vobiz.py); `line` hands a phone call to the
dashboard that is waiting for one. The companion listener will be another source of the same shape
(ARCHITECTURE §10, VISION §3).
"""

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Protocol

from app.models import Turn

SAMPLES = Path(__file__).resolve().parent.parent.parent / "samples" / "calls"
# Transcripts of the recorded samples (scripts/transcribe_samples.py), one per sample id.
TRANSCRIPTS = SAMPLES.parent / "transcripts"


class CallSource(Protocol):
    def turns(self) -> AsyncIterator[Turn]: ...


def load_sample(sample_id: str) -> dict | None:
    for p in SAMPLES.glob("*.json"):
        call = json.loads(p.read_text(encoding="utf-8"))
        if call["id"] == sample_id:
            return call
    return None


def list_samples() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(SAMPLES.glob("*.json"))]


def sample_turns(call: dict) -> tuple[list[Turn], bool]:
    """The turns to play: the recording's transcript if there is one, else the script.

    Returns (turns, from_recording). The script stays the ground truth for the eval scripts,
    whose expected levels refer to the script's own turns.
    """
    path = TRANSCRIPTS / f"{call['id']}.json"
    if path.is_file():
        return [Turn(**t) for t in json.loads(path.read_text(encoding="utf-8"))["turns"]], True
    return [Turn(**t) for t in call["turns"]], False


class ReplaySource:
    """Plays a saved transcript at call speed (speed=2 plays twice as fast)."""

    def __init__(self, turns: list[Turn], speed: float = 1.0) -> None:
        self._turns = turns
        self._speed = max(speed, 0.01)

    async def turns(self) -> AsyncIterator[Turn]:
        elapsed = 0.0
        for turn in self._turns:
            await asyncio.sleep(max(turn.t - elapsed, 0) / self._speed)
            elapsed = turn.t
            yield turn


class LiveSource:
    """Turns pushed in as they are heard; ends when the call hangs up (`end`)."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[Turn | None] = asyncio.Queue()
        self.connected = asyncio.Event()  # set when a phone call is handed to this source
        self.watching = True  # cleared when the dashboard leaves, so the phone side stops too

    def push(self, turn: Turn) -> None:
        self._queue.put_nowait(turn)

    def end(self) -> None:
        self._queue.put_nowait(None)

    async def turns(self) -> AsyncIterator[Turn]:
        while (turn := await self._queue.get()) is not None:
            yield turn


class Line:
    """The one dashboard waiting for a phone call. The next call goes to it; with nobody
    waiting, the call is turned away (the family memory lives in that dashboard's browser)."""

    def __init__(self) -> None:
        self._waiting: LiveSource | None = None

    def wait(self) -> LiveSource | None:
        """A source for the next call, or None if another dashboard is already waiting."""
        if self._waiting:
            return None
        self._waiting = LiveSource()
        return self._waiting

    def is_waiting(self) -> bool:
        return self._waiting is not None

    def take(self) -> LiveSource | None:
        source, self._waiting = self._waiting, None
        if source:
            source.connected.set()
        return source

    def leave(self, source: LiveSource) -> None:
        if self._waiting is source:
            self._waiting = None


line = Line()
