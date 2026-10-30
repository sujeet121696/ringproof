<p align="center"><img src="assets/logo.svg" alt="Ringproof" width="320"></p>

# Ringproof

**A personal AI that knows your family and stops "digital arrest" and impersonation scams mid-call.**

Ringproof listens to a call, transcribes it live, and checks what's being said against a private memory of your family: how each trusted contact talks, what they usually ask for, and a shared code word. A call that's unusual *for that person* (urgency + secrecy + a money ask) triggers a personal verification challenge ("ask for the family code word") and alerts a trusted contact before money moves. Your memory stays yours: view it, edit it, delete it; calls are never stored.

> Built for the **Nebius × NVIDIA Global AI Hackathon** — Track: **Personal AI**.
> **Demo:** https://ringproof.kharidwise.com · **Video:** https://www.youtube.com/watch?v=ZgwzwPnLL_w
>
> Status: **working demo on 10 sample calls** (risk engine, family memory, code word, "Is this
> you?" check, official lookup, email alerts), all scored live by Nemotron 3 Ultra on Nebius.
> Speech-to-text (Parakeet + Sortformer) is built and tested with a stand-in service, but has **not
> yet run on a GPU**, so the demo plays the calls' transcripts at call speed.

| A "CBI officer" call is caught | A fake son is asked for the family code word |
|---|---|
| ![Digital-arrest call at high risk: hang up, call 1930, official sources shown](docs/screenshots/digital-arrest.png) | ![Fake son call: the app asks Maa to request the family code word](docs/screenshots/fake-son-code-word.png) |
| **The real son's call stays quiet** | **The family memory, kept in the browser** |
| ![Real son calling about dinner: low risk, nothing needed](docs/screenshots/real-son-quiet.png) | ![Family memory: contacts, how they talk, household rules, who to alert](docs/screenshots/family-memory.png) |

## The Problem

In India, "digital arrest" scams target elderly people. A caller posing as a CBI, police or customs officer says the victim is linked to a crime, orders them to stay on the call and tell no one, and makes them transfer money to "clear their name." A second pattern uses a fake family member in trouble, sometimes with a cloned voice. Spam blockers and caller ID catch *unknown* numbers. They don't catch a convincing official or a familiar voice mid-call, and they know nothing about *your* family.

**The scale.** The Ministry of Home Affairs told Parliament that citizens reported cyber-fraud losses of ₹2,290 crore in 2022, ₹7,465 crore in 2023 and **₹22,846 crore in 2024** [[1]](#sources). The government warns specifically about "digital arrest" calls by criminals impersonating the police, NCB, CBI and RBI, and runs the **1930** cyber-crime helpline [[2]](#sources). It does not keep separate national figures for digital-arrest scams [[2]](#sources); news reports cite MHA figures of about ₹1,935 crore lost to digital-arrest and related scams in 2024 [[3]](#sources).

## How it compares

| Product | What it does | Where Ringproof differs |
|---|---|---|
| Truecaller AI Call Scanner | Detects whether the caller's voice is **AI-generated**; part of Truecaller Premium [[4]](#sources) | Ringproof judges **what is said**, so a real human scammer is caught too |
| Google Scam Detection (Phone app) | On-device Gemini Nano flags scam calls; off by default; in India only on Pixel 9 and later [[5]](#sources) | Ringproof checks the call against **your family's memory**, then verifies the caller (code word, "Is this you?" to the real person) and alerts family |
| Enterprise voice security (e.g. Pindrop, Reality Defender) | Deepfake and synthetic-voice detection for contact centres and enterprises [[6]](#sources) [[7]](#sources) | Ringproof is a **personal** agent for one family, with the data kept by the family |

The others ask *"is this a scam, or a fake voice?"* Ringproof asks *"is this really your son, and is this how he talks?"*, and then checks with him.

## The Solution

```
Call audio ──▶ Parakeet/Canary ──▶ transcript
                                      │
        Family memory (private) ──▶ Nemotron 3 Ultra on Nebius
                                      │  "is this unusual for this person?"
                                 ┌────┴────┐
                                 ▼         ▼
                              low/med     high
                              → log       → family code-word challenge
                                          + official helpline (Tavily lookup)
                                          + alert to a trusted contact
```

- **Transcription:** NVIDIA Parakeet (speech to text) and Sortformer (who spoke when), as a small service for a Nebius GPU (`asr/`). Built, not yet run on a GPU; the demo uses the calls' transcripts. English first; Hindi/Hinglish is post-hackathon.
- **Memory:** a private profile for each trusted contact (how they talk, what they usually ask for, a family code word). You can view, edit and delete it; calls are never stored.
- **Reasoning:** Nemotron 3 Ultra on Nebius scores the call against that memory, and against digital-arrest patterns (impersonated authority, isolation, secrecy, urgency, transfer ask).
- **Action:** high-risk calls trigger a personal challenge, show the real official helpline (looked up with Tavily from official sites only), and alert a trusted contact.

Demo scope: sample calls through a dashboard, not live telephony interception (a post-hackathon concern).

## Built with Nebius, NVIDIA and Tavily

| Part | What we use | Status |
|---|---|---|
| Reasoning | **Nemotron 3 Ultra** (`nvidia/Nemotron-3-Ultra-550b-a55b`) on **Nebius Token Factory**, JSON output, scores every caller turn against the family memory | Live in the demo |
| Backup reasoning | **Nemotron 3 Super** on Token Factory, then keyword rules; the screen says when a backup answered | Live; tested by forcing Ultra to fail |
| Official lookup | **Tavily** search limited to official domains (`.gov.in`, `rbi.org.in`, …); helpline numbers only from a verified table (1930) | Live |
| Speech to text | **Parakeet** + **Sortformer** (NVIDIA NeMo) on a **Nebius AI Cloud** L40S GPU, created and destroyed with Terraform (`infra/gpu/`) | Built; not yet run on a GPU |

**Results on Oct 30, Nemotron 3 Ultra:** all 10 sample calls scored as expected
(`scripts/eval_samples`, 2–13 s per call), and on all 10 the risk rose at the right turn: scams
went high at the money, OTP or "officer" demand, and real calls stayed low throughout
(`scripts/eval_timeline`). The samples are scripted: 5 scams and 5 real calls from the demo
family, with expected results written before running. The model is not fully repeatable: in four
more runs of "real son asks for a small, usual amount" that evening, it went high twice (a code-word
challenge on a real call), medium once and low once.

## Run locally

Needs Python 3.12 and Node 20.11+. Windows commands shown; on macOS/Linux use `.venv/bin/` and `cp`.

**One-time setup**

```bash
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt -c requirements.lock
cd web && npm install && cd ..
copy .env.example .env      # then fill in NEBIUS_API_KEY and TAVILY_API_KEY
```

No keys yet? Set `PROVIDER=mock` in `.env` to run with deterministic rules and no API calls.

**One command: check, clean, build and run** (production-style, http://localhost:8300)

```bash
npm run local              # setup check, clean, lint + build, tests, security audit, then serve
npm run local -- --mock    # same, with PROVIDER=mock (no model credits)
npm run check              # everything except serving: run it before every commit
npm run local:tunnel       # same checks, then serve the public demo (port 8200 behind the
                           # Cloudflare Tunnel; starts cloudflared if it isn't running)
```

**Develop with live reload** (two terminals)

```bash
# 1. Backend: http://localhost:8100 (API docs at /docs)
.venv\Scripts\python -m uvicorn app.main:app --port 8100 --reload

# 2. Dashboard: http://localhost:5180 (proxies /api to the backend)
cd web && npm run dev
```

**Check the risk engine against the sample calls**

```bash
.venv\Scripts\python -m scripts.eval_samples
```

**Run the unit tests**

```bash
.venv\Scripts\python -m pytest tests
```

**Watch a call replay live in the terminal** (backend running)

```bash
.venv\Scripts\python -m scripts.ws_replay digital-arrest --speed 2
```

## Docs

| File | Contents |
|---|---|
| [`docs/PRD.md`](docs/PRD.md) | Problem, goals, scope, constraints, risks |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Pipeline, stack, modules, fallbacks |
| [`docs/RULES.md`](docs/RULES.md) | Coding and workflow rules |
| [`docs/DESIGN.md`](docs/DESIGN.md) | Dashboard UI/UX direction |
| [`docs/TASKS.md`](docs/TASKS.md) | Build checklist and progress |
| [`docs/VISION.md`](docs/VISION.md) | Post-hackathon: guardian agent, channels, privacy, scaling |
| [`docs/FEEDBACK.md`](docs/FEEDBACK.md) | Feedback on Nebius, NVIDIA models and Tavily |

## Sources

Checked on Oct 9, 2026.

1. Ministry of Home Affairs, Lok Sabha Unstarred Question No. 432, "Cases of Cybercrime", answered 2 Dec 2025 (loss table, 1930 helpline): https://www.mha.gov.in/MHA1/Par2017/pdfs/par2025-pdfs/LS02122025/432.pdf
2. Press Information Bureau (MHA), "Incidents of Digital Arrest" (impersonation of Police, NCB, CBI, RBI; 1930 helpline; digital-arrest data not kept separately by NCRB): https://www.pib.gov.in/PressReleasePage.aspx?PRID=2114750
3. Inc42 (news report citing MHA), "Indians Lost INR 1,935 Cr To Digital Arrest Scams In 2024": https://inc42.com/?p=504907
4. MediaNama, Truecaller AI Call Scanner (detects AI-generated voices; Premium), May 2024: https://www.medianama.com/2024/05/223-truecaller-ai-voice-scanner-spam-call/
5. Google, Phone app Help, "Use Scam Detection" (Pixel 9 and later in India; off by default; on-device): https://support.google.com/phoneapp/answer/15654065?hl=en
6. Pindrop, Audio Deepfake Detection: https://www.pindrop.com/solution/deepfake-detection/
7. Reality Defender, Enterprise deepfake detection: https://www.realitydefender.com/solutions/enterprise
8. National Cyber Crime Reporting Portal (the 1930 number used in the app, `app/policy.py`): https://cybercrime.gov.in
