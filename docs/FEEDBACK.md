# Feedback (draft for the Devpost submission)

> Required by the hackathon: feedback on Nebius Token Factory, Nebius AI Cloud and the NVIDIA
> models used. Only what we saw while building Ringproof, with dates.

## Nebius Token Factory

**What worked**
- OpenAI-compatible `/chat/completions`: our client is a plain `httpx` POST, no SDK needed.
- `response_format: json_object` with `temperature: 0` gave parseable JSON once `max_tokens`
  was raised (see below): 9/9 samples on two full runs (Oct 7) and turn by turn on two runs (Oct 8).
- Cost is small for this use: a scoring call is about 530 tokens (Oct 6), at $1 per 1M input and
  $3 per 1M output for Nemotron 3 Ultra (checked Oct 6).

**What could be better**
- **No speech-to-text models in the catalogue** (checked Oct 6). A voice app has to run its own
  ASR (Parakeet/Canary) on an AI Cloud GPU, a second product, setup and bill. Hosted Parakeet on
  Token Factory would remove that step.
- **Hidden reasoning tokens count against `max_tokens`.** With `max_tokens: 1500` the answer was
  sometimes cut off before the JSON (Oct 7); we raised it to 4000. A note in the model card, or
  `finish_reason` docs that mention reasoning, would save this debugging.

## NVIDIA models

**Nemotron 3 Ultra** (`nvidia/Nemotron-3-Ultra-550b-a55b`), our primary
- Oct 6 smoke test: correct high score and valid JSON on a hard-coded scam call, about 4.8 s.
- Oct 7 benchmark on our sample calls: 8/8 correct, median 2.2 s, the fastest of the four we
  tried.
- Oct 30, final run before submitting: 10/10 sample calls correct (2–13 s each), and on all 10
  the risk rose at the right turn when scored turn by turn.
- It judged calls against a family profile ("he always calls her Maa, never asks for money on the
  phone") without fine-tuning: real calls stayed low on every turn, scams went high at the money,
  OTP or "officer" demand (Oct 8, turn by turn).

**Nemotron 3 Super**, our fallback
- Oct 7: slower than Ultra (median 4.1 s).
- Oct 8: with Ultra forced to fail on all 10 samples, Super answered correctly.

**Nano and Lightning** (tried Oct 7, not used)
- Nano: 7/8 at a 4.8 s median. Lightning: 0/8 on our prompt.
- Surprise for us: the largest model was also the fastest, so a "small model first" cascade did not
  pay off for this task.

**Parakeet + Sortformer (ASR)**: built, not run on a GPU before the deadline.
- The speech service (`asr/server.py`) follows the model cards' code and was tested only against a
  stand-in service. We ran out of time to start the GPU, so we have no accuracy or latency numbers
  and don't claim any.
- Sortformer (`diar_sortformer_4spk-v1`) is CC-BY-NC-4.0, so it would need replacing or licensing
  before any commercial use; Parakeet (`parakeet-tdt-0.6b-v2`) is CC-BY-4.0.

## Nebius AI Cloud

- Credits: the $25 event code and the $25 Builders Program credit both landed on Oct 4.
- GPU (for Parakeet), Oct 23: we wrote the VM as Terraform (`infra/gpu/`) with the `nebius/nebius`
  provider (0.6.73). Good: it covers what we needed (VM with a managed boot disk deleted with it,
  public IP, a security group allowing SSH from one IP), and `terraform validate` checked attribute
  names against the schema before any spend. The docs were clear on GPU platforms and images
  (`gpu-l40s-a`, `ubuntu24.04-cuda13.0`).
- What slowed us down: **the Nebius CLI has no Windows build** (the installer is Linux/macOS only;
  the Windows download path returned 404 on Oct 23), and the provider's user sign-in needs a token
  from that CLI. On Windows without WSL the way in is a service account with a key uploaded in the
  console, several manual steps. A Windows CLI, or a console button that issues a short-lived
  Terraform token, would remove that.
- L40S was offered only in `eu-north1` (Oct 23), so the project has to be in that region.
- We did not apply the Terraform before the deadline, so we have no GPU run to report.
- VM to host the demo: not done; the demo runs on the developer's PC behind a Cloudflare Tunnel.

## Tavily

- The official-domain allowlist (`.gov.in`, `rbi.org.in`, `cybercrime.gov.in`, …) returned only
  official sources in our Oct 6 test, which is what makes it safe to show in a scam warning.
- Some result snippets start with a site breadcrumb (`… › … ›`); we strip it before showing
  the text (`app/lookup.py`).
- We never take a phone number from search text: the 1930 helpline comes from a verified table,
  and Tavily adds the official pages around it.
