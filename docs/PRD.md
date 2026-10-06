# PRD

> What Ringproof is, who it's for, and what's in and out of scope.

## 1. Problem

**"Digital arrest" scams in India.** A caller poses as a CBI, police, customs or courier official
and says the victim is linked to a crime (a parcel with drugs, a money-laundering case). The victim
is told they are under "digital arrest": they must stay on the call (often a video call, for
hours), tell no one, and transfer money to "clear their name" or to a "verification account".
It's widely reported, and the Indian government has issued public warnings. Elderly people are
the main targets.

A second pattern uses the same levers: a caller poses as a family member in trouble (sometimes
with a cloned voice) and asks for urgent money.

Spam blockers and caller ID catch *unknown* numbers. They don't catch a convincing official or a
familiar-sounding voice mid-call, and they know nothing about *your* family.

## 2. Target user

**Primary:** an elderly parent in India who gets these calls.
**Secondary:** their adult child, who sets up the family memory and is the trusted contact who
gets alerted.

## 3. Demo story

Maa (68) gets a call: "This is Inspector Sharma, CBI. A parcel in your name had drugs. You are
under digital arrest. Do not disconnect, do not tell your son. Transfer ₹2,00,000 to this RBI
verification account." Ringproof flags an impersonated authority, secrecy, urgency and a transfer
ask, and knows from memory that *"real police never arrest anyone over a call"*. It tells Maa:
"This is a known scam. Hang up. Official cyber-crime helpline: 1930." It alerts Rahul. Later, the
real Rahul calls about dinner and Ringproof stays quiet.

A second call: "Mummy, it's me, I've had an accident, send ₹50,000 now, don't tell Papa." The
voice sounds like Rahul, but he always calls her "Maa" and never asks for money over the phone.
Ringproof prompts: "Ask him our family code word." The caller can't answer, and Ringproof flags
the call.

## 4. Goals

| # | Goal | Notes |
|---|---|---|
| G1 | Transcribe call audio | NVIDIA open speech model; the demo replays saved transcripts at call speed |
| G2 | **Remember the family** | A private profile for each trusted contact (see Memory) |
| G3 | Score each call against that memory | "Is this unusual *for this person*?", not "does this sound like a scam?" |
| G4 | Act on high risk, using memory | Personal verification challenge + trusted-contact alert |
| G5 | Keep the user in control of their data | View, edit and delete memory; no call stored after it ends |
| G6 | **Look up the truth** when a caller claims an organisation | Tavily search for the official helpline + current scam warnings, from official sites only |

**Risk signals**

- **Urgency**: "act now", deadlines, pressure.
- **Secrecy**: "don't tell anyone".
- **Transfer ask**: wire, gift card, crypto, UPI.
- **Impersonation**: claims to be a known contact or an authority (CBI, police, customs, RBI,
  courier, bank).
- **Isolation**: "stay on the call", "don't disconnect", "you are under digital arrest".
- **Out of character**: differs from what memory says about this contact (tone, how they address
  you, what they usually ask for).

**Memory: one profile per trusted contact**

| Field | Example |
|---|---|
| Name + relation | Rahul, son |
| How they address you | "Maa" |
| Usual topics and asks | Dinner plans, rides; never money over the phone |
| Past requests | Asked for ₹2,000 for a train ticket in March |
| Family code word | Shared secret, used in the challenge |
| Email | Where the OTP fallback code goes |

**Memory: household rules** (apply to every call)

- "My bank never asks for an OTP on a call."
- "Police and the CBI never arrest anyone over a call."
- Trusted contact to alert: Rahul.

Example scoring: your son asking for ₹50,000 in gift cards → **high**. Your "bank" asking for an
OTP → **high**. Your son asking about dinner → **low**.

**Why memory matters.** It is what makes Ringproof a *personal* AI (the Personal AI track asks
for "persistent memory" and "data under your control") and what separates it from the many
generic scam classifiers. G2–G6 together are the differentiator.

## 5. Scope

**In (hackathon demo)**
- **Languages:** English is primary and must work. Hindi and Hinglish are a **stretch goal**,
  added only if the week-1 language test passes (TASKS step 7).
- Sample calls, uploaded and replayed at call speed. Demo set: a digital-arrest scam, a
  fake-family-member scam, a real call from a family member, and a real bank call.
- Family memory: create, view, edit and delete trusted-contact profiles.
- Dashboard with live transcript, memory-aware risk scoring and a visible intervention.
- A personal verification challenge ("Ask the caller our family code word").
- A data-control view in the demo: what's stored, and a delete button that works.
- Tavily lookup of the claimed organisation's official helpline and scam warnings, shown in the
  challenge ("The CBI does not arrest over the phone. Call 1930.").

**Out**
- Live telephony interception (needs carrier-level access; a post-hackathon concern).
- Video-call analysis. Ringproof judges the call's audio only.
- Acoustic synthetic-voice detection. Ringproof judges *what is said*, not voice artifacts.
- Production auth, billing and multi-user accounts.

## 6. Constraints

**Hackathon**
- Nebius × NVIDIA Global AI Hackathon: https://nebiusglobalaihackathon.devpost.com/
  (verified 2026-09-27)
- Deadline: **Oct 30, 10:00 AM PDT** (= 10:30 PM IST). Online, India eligible. $50k+ prizes.
- Must run on **Nebius Token Factory or Nebius AI Cloud** and use ≥1 **NVIDIA open model**
  (Nemotron encouraged).
- Track: **Personal AI**: "an always-on, private assistant that works for you while keeping your
  data under your control. Give it persistent memory, reusable skills, access to the tools and
  information you choose…" Family memory (G2) and data control (G5) are what meet this.
- Judging (equal weight): technological implementation, design, potential impact, quality of the
  idea.
- Teammates, if any, must be real, distinct people registering under their own identity.

**Required submission**
- Public repo with an open-source license (Apache-2.0, MIT or MPL-2.0).
- **Working demo URL.**
- Demo video, **≤3 min**, with audio explaining how Nebius and NVIDIA are used.
- Project description + README with setup instructions.
- Feedback on Nebius Token Factory, AI Cloud and the NVIDIA models used (required).

**Bonus prizes we're targeting**
- **Best Use of Tavily: $3,000** (G6).
- **Most Valuable Feedback: $100 × 10** (write real, specific feedback).

**Budget**
- Free credit: $25 (event code `NEBIUS-DEVPOST-GLOBAL26`) + $25 (Nebius Builders Program) = **$50**.
  The repo must be public, so decide before submitting whether this code stays in it.
- Model calls: cents. Nemotron 3 Ultra costs about $1.20 per 1M tokens.
- GPU for transcription (only if Nebius doesn't host Parakeet): about $1–3/hour, kept to a few
  hours in total by transcribing each sample once (see ARCHITECTURE §4).
- Parakeet/Canary weights are open (CC-BY-4.0).
- **Never** use multiple accounts to re-claim a promo. It's a ToS and disqualification risk.

## 7. Risks

| Risk | Mitigation |
|---|---|
| Idea saturation (VoxShield ×8, EchoGuard, CallGuard, KinGuard, Pindrop, Reality Defender) | Differentiate on family memory + memory-based challenge + a concrete India digital-arrest story, not generic detection |
| Real digital-arrest calls are often in Hindi/Hinglish | English primary; Hindi/Hinglish via a second transcription model if the week-1 test passes, otherwise post-hackathon |
| Parakeet/Canary don't support Hindi; code-switched speech is 30–50% less accurate | Route Hindi/Hinglish to an open multilingual model (Whisper large-v3 or IndicConformer) on Nebius; Nemotron still meets the NVIDIA-model rule |
| Provider outage or rate limit during the demo | Provider fallbacks (see ARCHITECTURE.md) |
| Weak Personal AI fit | Memory and data control are core goals (G2, G5), shown clearly in the demo |
| Tavily returns a fake "official" helpline posted by scammers | Search only official domains (`.gov.in`, `rbi.org.in`, `cybercrime.gov.in`, …); a built-in list of verified numbers (e.g. 1930) takes priority |
| Tavily is slow or down mid-call | Challenge goes out immediately from the built-in list; the lookup adds details when it returns |
| Memory is sensitive personal data | Stored only in the user's browser; viewable and deletable; call audio and transcripts discarded after the call |

## 8. Background

**Startup angle**
- B2C: family and elder-protection subscription.
- B2B: fintech and call-center API, priced per minute.

**Naming history**
- *SonicGuard* was dropped because NVIDIA Sonic is a robotics control model with no audio
  function.
- *VocalArmor* was dropped because it's taken on Hugging Face (`surabhibh05/vocal-armor`).
- *EchoGuard, VoxShield, CallGuard, TrustGuard, KinGuard* were rejected for collisions.
- **Ringproof** came back clean (Sept 19).
