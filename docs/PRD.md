# PRD

> What Ringproof is, who it's for, and what's in and out of scope.

## 1. Problem

Voice-cloning scams (fake CEO wire requests, fake "kidnapped" relatives, cloned-voice bank fraud)
are a fast-growing, multi-billion-dollar problem. Spam blockers and caller ID catch *unknown*
numbers. They don't catch a cloned voice of someone the victim trusts, mid-call.

## 2. Target user

An individual or family on a live call, especially people vulnerable to impersonation scams, such
as elderly relatives.

## 3. Goals

| # | Goal | Notes |
|---|---|---|
| G1 | Transcribe call audio live | NVIDIA open speech model |
| G2 | Score the transcript for scam behavior | Signals listed below |
| G3 | Act on high risk | Verification challenge + trusted-contact alert |

**Risk signals**

- **Urgency**: "act now", deadlines, pressure.
- **Secrecy**: "don't tell anyone".
- **Transfer ask**: wire, gift card, crypto.
- **Impersonation**: claims to be a known contact or institution.

G3 is the differentiator. Acting, not just labeling, is what makes this an agent rather than a
classifier.

## 4. Scope

**In (hackathon demo)**
- Upload or stream sample scam-vs-real call audio.
- Dashboard with live transcript, risk scoring and a visible intervention.

**Out**
- Live telephony interception (needs carrier-level access; a post-hackathon concern).
- Acoustic synthetic-voice detection. Ringproof judges *what is said*, not voice artifacts.
- Production auth, billing and multi-user accounts.

## 5. Constraints

**Hackathon**
- Nebius × NVIDIA Global AI Hackathon: https://nebiusglobalaihackathon.devpost.com/
- Deadline: **Oct 30**. Online, India eligible.
- Must run ≥1 NVIDIA open model (Parakeet/Canary) and run on Nebius (Nemotron).
- Track: Personal AI. Not Physical AI, which needs ≥1 min of real hardware footage.
- Teammates, if any, must be real, distinct people registering under their own identity.

**Budget**
- Free credit: $25 (event code `NEBIUS-DEVPOST-GLOBAL26`) + $25 (Nebius Builders Program) = **$50**.
- Expected spend: cents to a couple of dollars. Nemotron 3 Ultra costs about $1.20 per 1M tokens;
  Parakeet/Canary weights are open (CC-BY-4.0) and can be self-hosted.
- **Never** use multiple accounts to re-claim a promo. It's a ToS and disqualification risk.

## 6. Risks

| Risk | Mitigation |
|---|---|
| Idea saturation (VoxShield ×8, EchoGuard, CallGuard, KinGuard, Pindrop, Reality Defender) | Differentiate in the action layer, not detection |
| Provider outage or rate limit during the demo | Provider fallbacks (see ARCHITECTURE.md) |
| Track fit | Fall back to Best Apps and Agents |

## 7. Background

**Startup angle**
- B2C: family and elder-protection subscription.
- B2B: fintech and call-center API, priced per minute.

**Naming history**
- *SonicGuard* was dropped because NVIDIA Sonic is a robotics control model with no audio
  function.
- *VocalArmor* was dropped because it's taken on Hugging Face (`surabhibh05/vocal-armor`).
- *EchoGuard, VoxShield, CallGuard, TrustGuard, KinGuard* were rejected for collisions.
- **Ringproof** came back clean (Sept 19).
