# Ringproof 🛡️📞

**A real-time voice-fraud defense agent — the "immune system" for voice-cloning scams.**

Ringproof listens to a call, transcribes it live, and reasons over what's actually being said to catch scam behavior (urgency + secrecy + a money-transfer ask) before money moves. High-risk calls trigger an out-of-band verification challenge and alert a trusted contact — instead of just flagging risk after the fact.

> Built for the **Nebius × NVIDIA Global AI Hackathon** — Track: **Personal AI** (fallback: Best Apps and Agents).
> Status: **pre-build.** Idea locked; build starts after TGPF Stage 2 wraps (Sept 27).

## The Problem

Voice-cloning scams — fake CEO wire-transfer requests, fake "kidnapped" family members, cloned-voice bank fraud — are a fast-growing, multi-billion-dollar problem. Most existing defenses (spam-call blockers, caller ID) catch *unknown* numbers, not a cloned voice of someone the victim trusts, mid-conversation, while it's happening.

## The Solution

```
Call audio (sample upload/stream)
        │
        ▼
NVIDIA speech model (Parakeet/Canary) ──▶ live transcript
        │
        ▼
Nemotron 3 Ultra ──▶ scam-behavior risk score
        │
   ┌────┴────┐
   ▼         ▼
 low/med    high risk
 → log      → out-of-band verification challenge + trusted-contact alert
```

- **Transcription:** an NVIDIA speech model (NeMo Parakeet/Canary) turns the call into text.
- **Reasoning:** Nemotron 3 Ultra, served on Nebius, scores the transcript for scam patterns.
- **Action:** high-risk calls don't just get flagged — they trigger a real intervention (verification challenge + alert), which is what makes this an agent, not a classifier.

Demo scope is upload/stream of sample scam-vs-real call audio through a dashboard — not live telephony interception (that's a post-hackathon product concern).

## Docs

- [`docs/DESIGN.md`](docs/DESIGN.md) — full design: architecture, tech stack, track rationale, naming history, open risks.

## Status

Nothing is built yet. This repo currently holds design docs only — code starts after TGPF Stage 2 (Sept 25–26, Bangalore).
