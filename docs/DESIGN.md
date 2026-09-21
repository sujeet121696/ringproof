# Ringproof — Design

## Hackathon

- Nebius × NVIDIA Global AI Hackathon — https://nebiusglobalaihackathon.devpost.com/
- Deadline: Oct 30 · $50k · online · India eligible
- Track: **Personal AI** (protects an individual/family during a live call)
  Fallback: **Best Apps and Agents**, if Personal AI's spec doesn't fit cleanly once we're deeper in.
  **Not** Physical AI — that track requires ≥1 minute of real hardware footage, which a phone-call
  software demo can't produce.

## Pipeline

```
Call audio (sample upload/stream)
        │
        ▼
1) NVIDIA speech model (Parakeet/Canary) ──▶ live transcript + speaker turns
        │
        ▼
2) Nemotron 3 Ultra (on Nebius)          ──▶ scam-risk reasoning over transcript
        │
        ▼
3) Risk score/branch
   ┌────┴────┐
   ▼         ▼
 low/med    high
 → log      → out-of-band verification challenge + trusted-contact alert
```

**1. Transcription — NVIDIA NeMo Parakeet/Canary**
Turns raw call audio into a live transcript with speaker segmentation. A real, shipping NVIDIA
open speech model — satisfies the hackathon's requirement of running ≥1 NVIDIA open model, and is
the correct model category for this job (unlike NVIDIA Sonic — see Naming History below).

**2. Reasoning — Nemotron 3 Ultra**
Scores the transcript for scam-behavior patterns: urgency ("act now"), secrecy ("don't tell
anyone"), and a money-transfer ask (wire, gift card, crypto), plus context like impersonation of a
known contact. Runs on Nebius infra (Token Factory or AI Cloud) — satisfies the hackathon's
requirement of running on Nebius, not just calling NVIDIA models from anywhere.

**3. Action layer (product logic, not a model)**
A high risk score triggers a real intervention, not just a label:
- Out-of-band verification challenge (OTP-style — reusing the pattern already proven in
  [Resolve](../../resolve)).
- Alert to a pre-registered trusted contact.

This is what makes it a Personal AI *agent* rather than a passive classifier — it acts on the
user's behalf, which is what the track is judged on.

## Demo scope (hackathon)

Upload/stream sample scam-vs-real call audio through a dashboard with live risk scoring.
**Not** live telephony interception — that requires carrier-level access and is a post-hackathon
product concern, out of scope for a solo build.

## Startup angle

- **B2C:** family/elder-protection subscription.
- **B2B:** fintech/call-center API, usage-priced per minute.
- Real, growing market — but not uncontested. Pindrop and Reality Defender already operate here.

## Naming history

- Originally pitched as **"SonicGuard,"** using **NVIDIA Sonic** for real-time acoustic/synthetic-
  voice-artifact detection. Verified against the hackathon page that this is wrong: Sonic is a
  low-latency **robotics control** model, grouped with GROOT and Cosmos under the **Physical AI**
  track. It has no audio/voice function. Corrected by dropping Sonic entirely and using a real
  NVIDIA speech model (Parakeet/Canary) for transcription instead.
- Renamed **"VocalArmor" → Ringproof"** (Sept 19) — VocalArmor is already a live Hugging Face
  project (`surabhibh05/vocal-armor`).
- Other names checked and rejected for collisions: EchoGuard, VoxShield (8+ near-identical GitHub
  repos doing this exact idea), CallGuard, TrustGuard, KinGuard (a live Google Play app doing
  almost exactly this — elder scam protection with a family-alert loop). **Ringproof** came back
  clean.

## Open risk — idea saturation

"Voice-fraud defense" as a *concept* is heavily built already this hackathon season, independent
of naming: VoxShield (×8 repos), EchoGuard, CallGuard, KinGuard, plus established players Pindrop
and Reality Defender. Differentiation needs real thought during the build — not just a clean name
— likely in the *action* layer (out-of-band challenge + trusted-contact alert as a first-class
agent action) rather than the detection step alone, since detection is where everyone else already
is.

## Budget

Hackathon gives every participant free Nebius Token Factory credit — no spend required:
- **$25** via event activation code `NEBIUS-DEVPOST-GLOBAL26`
- **+$25** via the free Nebius Builders Program
- **$50 total**, per real registered participant

Estimated actual cost for a hackathon-scope build: **cents to a couple dollars** —
Nemotron 3 Ultra runs ~$1.20/1M tokens and a demo-scope build won't approach 1M tokens;
Parakeet/Canary ships as open weights (CC-BY-4.0) and can be self-hosted for **$0**, or used via
a cheap hosted endpoint (~$0.0015/min elsewhere in the market). One account's $50 comfortably
covers this. No reason to spend beyond the free credit.

**Multiple accounts to re-claim the same promo is off the table** — that's a real ToS/disqualification
risk (the hackathon rules allow disqualifying anyone "tampering with the entry process," and Nebius's
own promo terms are one-per-person). The only legitimate way to get more than $50 of credit is more
than one **real, distinct person** each registering under their own identity — not the same person
running several accounts.

## Team

Solo build — Sujeet writes all the code. If additional real people join as teammates, each would
register and claim their own Nebius credit under their own identity (perfectly fine, unrelated to
the multi-accounting risk above) — not yet confirmed whether that's happening. Rules allow teams of
any size; one person is named the "Representative" who submits.

## Resilience — multi-provider fallback (not multi-account)

To avoid a single provider outage/rate-limit blocking the demo, both model calls go through a thin
provider-abstraction layer (same pattern as Resolve's `brain.ts`):
- **Reasoning:** primary = Nemotron 3 Ultra on Nebius Token Factory → fallback = an equivalent
  open model via a different host (e.g. OpenRouter/Groq), each under its own separate free tier.
- **Transcription:** primary = Parakeet/Canary via hosted endpoint → fallback = self-hosted open
  weights on any free GPU tier.

This is provider resilience, not credit-stacking — different companies' own free tiers, not the
same Nebius promo claimed twice.

## Status

Pre-build. Code starts after TGPF Stage 2 wraps (Sept 27). Nothing in this repo is implemented yet.
