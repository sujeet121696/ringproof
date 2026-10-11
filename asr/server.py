"""Ringproof speech service: runs on a Nebius AI Cloud GPU (see asr/README.md).

POST /transcribe  (body: audio in any format ffmpeg reads; header: Authorization: Bearer ASR_TOKEN)
  ?diarize=true   also split speakers (an uploaded call); false for one phone utterance
  -> {"segments": [{"start", "end", "text"}], "speakers": ["<begin> <end> speaker_<n>", ...]}

Models (NVIDIA, open weights, loaded once at start):
- nvidia/parakeet-tdt-0.6b-v2: English speech to text with timestamps (CC-BY-4.0)
- nvidia/diar_sortformer_4spk-v1: who spoke when, up to 4 speakers (CC-BY-NC-4.0)

Turning these into transcript turns happens in the Ringproof app (app/asr.py). Audio is written
to a temporary folder only for the models to read, and deleted when the request ends.
"""

import hmac
import os
import subprocess
import tempfile
import threading
from pathlib import Path

import nemo.collections.asr as nemo_asr
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from nemo.collections.asr.models import SortformerEncLabelModel

TOKEN = os.environ["ASR_TOKEN"]
MAX_BYTES = 20 * 1024 * 1024

asr_model = nemo_asr.models.ASRModel.from_pretrained(model_name="nvidia/parakeet-tdt-0.6b-v2")
diar_model = SortformerEncLabelModel.from_pretrained("nvidia/diar_sortformer_4spk-v1")
diar_model.eval()
gpu = threading.Lock()  # one request on the GPU at a time

app = FastAPI(title="Ringproof speech")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def run(audio: bytes, diarize: bool) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        src, wav = Path(tmp) / "input", Path(tmp) / "audio.wav"
        src.write_bytes(audio)
        # Any format in; 16 kHz mono WAV out, which is what both models expect.
        convert = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(src), "-ac", "1", "-ar", "16000", str(wav)],
            capture_output=True,
        )
        if convert.returncode != 0:
            raise HTTPException(400, "could not read the audio")
        with gpu:
            out = asr_model.transcribe([str(wav)], timestamps=True)[0]
            speakers = diar_model.diarize(audio=[str(wav)], batch_size=1)[0] if diarize else []
    segments = [{"start": s["start"], "end": s["end"], "text": s["segment"]} for s in out.timestamp["segment"]]
    return {"segments": segments, "speakers": [str(s) for s in speakers]}


@app.post("/transcribe")
async def transcribe(request: Request, diarize: bool = True, authorization: str = Header("")) -> dict:
    if not hmac.compare_digest(authorization.encode(), f"Bearer {TOKEN}".encode()):
        raise HTTPException(401)
    audio = await request.body()
    if not audio or len(audio) > MAX_BYTES:
        raise HTTPException(413 if audio else 400)
    return await run_in_threadpool(run, audio, diarize)
