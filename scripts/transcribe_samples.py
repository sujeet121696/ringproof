"""Transcribe the recorded sample calls once, so the demo replays them without a GPU.

Reads samples/audio/<sample id>.<wav|mp3|m4a|ogg|flac>, sends each to the speech service
(ASR_URL in .env, see asr/README.md) and writes samples/transcripts/<sample id>.json. The
dashboard then plays the transcript instead of the script; the script stays the ground truth for
the eval scripts. The audio itself is git-ignored and never committed.

Usage (from the repo root, speech service reachable):
  .venv/Scripts/python -m scripts.transcribe_samples              # every recording
  .venv/Scripts/python -m scripts.transcribe_samples fake-sujeet  # one
"""

import argparse
import asyncio
import json
from pathlib import Path

from app.asr import transcribe, to_turns
from app.calls import SAMPLES, TRANSCRIPTS, list_samples

AUDIO = SAMPLES.parent / "audio"
EXTENSIONS = (".wav", ".mp3", ".m4a", ".ogg", ".flac")


def find_audio(sample_id: str) -> Path | None:
    return next((AUDIO / f"{sample_id}{ext}" for ext in EXTENSIONS if (AUDIO / f"{sample_id}{ext}").is_file()), None)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ids", nargs="*", help="sample ids (default: every sample with a recording)")
    ids = parser.parse_args().ids or [c["id"] for c in list_samples()]
    TRANSCRIPTS.mkdir(exist_ok=True)
    for sample_id in ids:
        audio = find_audio(sample_id)
        if not audio:
            print(f"{sample_id:24} no recording in samples/audio/")
            continue
        result = await transcribe(audio.read_bytes(), diarize=True)
        turns = to_turns(result.get("segments", []), result.get("speakers", []))
        out = {"id": sample_id, "audio": audio.name, "models": "parakeet-tdt-0.6b-v2 + diar_sortformer_4spk-v1",
               "turns": [t.model_dump() for t in turns]}
        (TRANSCRIPTS / f"{sample_id}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{sample_id:24} {len(turns)} turns -> samples/transcripts/{sample_id}.json")
        for t in turns:
            print(f"    {t.t:6.1f}  {t.speaker:6}  {t.text}")


if __name__ == "__main__":
    asyncio.run(main())
