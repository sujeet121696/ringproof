# Speech service (Nebius GPU)

Parakeet (speech to text) and Sortformer (who spoke when) behind one small HTTP endpoint, used by
the Ringproof app for uploaded recordings and the Vobiz phone line. See `server.py` for the API.

Nebius Token Factory has no speech models, so this runs on a Nebius AI Cloud GPU VM. **Billed per
hour while the VM runs: delete it when done.** An L40S is plenty (Parakeet is 0.6B parameters).

## Run on the GPU VM

```bash
sudo apt-get update && sudo apt-get install -y ffmpeg python3-venv
python3 -m venv .venv && .venv/bin/pip install -r asr/requirements.txt
export ASR_TOKEN=<a long random string, the same as ASR_TOKEN in Ringproof's .env>
.venv/bin/uvicorn asr.server:app --host 127.0.0.1 --port 9000
```

It listens on `127.0.0.1` only, so it is not open to the internet. Reach it from the machine running
Ringproof through an SSH tunnel:

```bash
ssh -N -L 9000:127.0.0.1:9000 <user>@<gpu-vm-ip>
```

Then in Ringproof's `.env`: `ASR_URL=http://127.0.0.1:9000` and the same `ASR_TOKEN`.

## Check it

```bash
curl -s http://127.0.0.1:9000/health
curl -s -X POST -H "Authorization: Bearer $ASR_TOKEN" --data-binary @call.wav \
  "http://127.0.0.1:9000/transcribe?diarize=true"
```

## Licences

- `nvidia/parakeet-tdt-0.6b-v2`: CC-BY-4.0
- `nvidia/diar_sortformer_4spk-v1`: CC-BY-NC-4.0 (non-commercial; fine for the hackathon demo,
  to be replaced or licensed before any commercial use)
