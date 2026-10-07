"""Call sources: every channel delivers a call as a stream of transcript turns.

Replay is the only source for the hackathon. Upload, the Vobiz Guardian Line and the companion
listener will be further sources with the same shape (ARCHITECTURE §10, VISION §3).
"""

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Protocol

from app.models import Turn

SAMPLES = Path(__file__).resolve().parent.parent.parent / "samples" / "calls"


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
