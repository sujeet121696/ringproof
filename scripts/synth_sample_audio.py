"""Make synthetic recordings of the sample calls, for testing transcription without real voices.

Speaks each turn of samples/calls/*.json with Windows text-to-speech (System.Speech, offline) and
places it at its time in the script, so the recording follows the same timeline as the replay.
The caller's lines are pitched down with ffmpeg so the two speakers sound different. Writes
samples/audio/<sample id>.wav (git-ignored). Synthetic speech only: no real person's voice.

Windows only. Needs ffmpeg on PATH.
  .venv/Scripts/python -m scripts.synth_sample_audio              # every sample
  .venv/Scripts/python -m scripts.synth_sample_audio fake-sujeet  # one
"""

import argparse
import os
import subprocess
import tempfile
import wave
from pathlib import Path

from app.calls import SAMPLES, list_samples, load_sample

AUDIO = SAMPLES.parent / "audio"
RATE = 16000
GAP_S = 0.4  # a turn starts at its scripted time, or this long after the previous turn ends
CALLER_PITCH = 0.82  # caller voice pitch, relative to the user's


def speak(text: str, out: Path) -> None:
    """Speak one line into a 16 kHz mono WAV with the default Windows voice."""
    script = (
        "Add-Type -AssemblyName System.Speech;"
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
        "$f = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(16000, 'Sixteen', 'Mono');"
        "$s.SetOutputToWaveFile($env:OUT_PATH, $f); $s.Speak($env:TEXT); $s.Dispose()"
    )
    env = {**os.environ, "OUT_PATH": str(out), "TEXT": text}
    subprocess.run(["powershell", "-NoProfile", "-Command", script], env=env, check=True)


def pitch_down(src: Path, out: Path) -> None:
    rate = int(RATE * CALLER_PITCH)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af",
                    f"asetrate={rate},aresample={RATE},atempo={1 / CALLER_PITCH:.4f}", str(out)], check=True)


def read_frames(path: Path) -> bytes:
    with wave.open(str(path), "rb") as w:
        return w.readframes(w.getnframes())


def build(sample_id: str) -> Path:
    turns = load_sample(sample_id)["turns"]
    timeline = bytearray()
    with tempfile.TemporaryDirectory() as tmp:
        for i, turn in enumerate(turns):
            line = Path(tmp) / f"{i}.wav"
            speak(turn["text"], line)
            if turn["speaker"] == "caller":
                low = Path(tmp) / f"{i}-low.wav"
                pitch_down(line, low)
                line = low
            frames = read_frames(line)
            start = max(int(turn["t"] * RATE) * 2, len(timeline) + int(GAP_S * RATE) * 2)
            timeline.extend(b"\0" * (start - len(timeline)))
            timeline.extend(frames)
    AUDIO.mkdir(exist_ok=True)
    out = AUDIO / f"{sample_id}.wav"
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(bytes(timeline))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ids", nargs="*", help="sample ids (default: every sample)")
    ids = parser.parse_args().ids or [c["id"] for c in list_samples()]
    for sample_id in ids:
        out = build(sample_id)
        with wave.open(str(out), "rb") as w:
            print(f"{sample_id:24} {w.getnframes() / RATE:5.1f} s  {out.relative_to(SAMPLES.parent.parent)}")


if __name__ == "__main__":
    main()
