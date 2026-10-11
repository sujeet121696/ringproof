"""Speech to text: the client for the speech service on the Nebius GPU (asr/server.py), and
turning what it returns into transcript turns.

The service returns Parakeet's text segments (`start`, `end`, `text`) and, for recordings with
two voices, Sortformer's speaker segments as it prints them ("begin end speaker_N"). Merging the
two happens here, in plain code, so it can be tested without a GPU.
"""

import re

import httpx

from app.config import settings
from app.models import Turn

# A recording is a whole call; keep uploads to a few minutes of audio.
MAX_AUDIO_BYTES = 20 * 1024 * 1024


class AsrError(Exception):
    """Transcription failed; the message is safe to show on the dashboard."""


async def transcribe(audio: bytes, diarize: bool) -> dict:
    if not settings.asr_url:
        raise AsrError("Transcription is not switched on (no speech service is set up).")
    try:
        async with httpx.AsyncClient(timeout=settings.asr_timeout_s) as client:
            resp = await client.post(
                f"{settings.asr_url.rstrip('/')}/transcribe",
                params={"diarize": "true" if diarize else "false"},
                headers={"Authorization": f"Bearer {settings.asr_token}"},
                content=audio,
            )
    except httpx.HTTPError as err:
        raise AsrError("The speech service did not answer.") from err
    if resp.status_code == 400:
        raise AsrError("That file could not be read as audio.")
    if resp.status_code != 200:
        raise AsrError(f"The speech service failed (HTTP {resp.status_code}).")
    return resp.json()


def parse_speakers(lines: list[str]) -> list[tuple[float, float, int]]:
    """Sortformer lines ("0.80 3.20 speaker_0", commas allowed) -> (start, end, speaker)."""
    out = []
    for line in lines:
        parts = re.split(r"[,\s]+", line.strip())
        if len(parts) >= 3 and (digits := re.sub(r"\D", "", parts[2])):
            out.append((float(parts[0]), float(parts[1]), int(digits)))
    return out


def to_turns(segments: list[dict], speaker_lines: list[str]) -> list[Turn]:
    """Text segments -> turns. Each segment goes to the speaker heard most during it.

    The first speaker heard is the caller (record calls starting with the caller, as in every
    sample script); everyone else is the user. A segment no speaker covers stays with the current
    speaker; with no speaker data at all, every line is the caller.
    Consecutive segments from the same speaker join into one turn.
    """
    speakers = parse_speakers(speaker_lines)
    caller = min(speakers)[2] if speakers else None
    turns: list[Turn] = []
    for seg in segments:
        text = seg["text"].strip()
        if not text:
            continue
        start, end = float(seg["start"]), float(seg["end"])
        overlap: dict[int, float] = {}
        for s_start, s_end, who in speakers:
            overlap[who] = overlap.get(who, 0) + max(0.0, min(end, s_end) - max(start, s_start))
        who = max(overlap, key=overlap.get) if overlap and max(overlap.values()) > 0 else None
        if who is None:  # no speaker heard in this stretch: keep the current one
            speaker = turns[-1].speaker if turns else "caller"
        else:
            speaker = "caller" if who == caller else "user"
        if turns and turns[-1].speaker == speaker:
            turns[-1] = Turn(t=turns[-1].t, speaker=speaker, text=f"{turns[-1].text} {text}")
        else:
            turns.append(Turn(t=round(start, 1), speaker=speaker, text=text))
    return turns
