# Architecture

> How Ringproof is built: pipeline, stack, modules and fallbacks.

## 1. Pipeline

```
Call audio (sample upload/stream)          [M] Family memory
        │                                   (trusted-contact profiles,
        ▼                                    user-controlled)
[1] Transcriber   Parakeet/Canary                  │
        │                                          │ profile of claimed caller
        ▼                                          ▼
[2] Risk engine   Nemotron 3 Ultra  ◀──────────────┘
        │          ──▶ score + signals + rationale + claimed contact / org
   ┌────┴────┐
   ▼         ▼
 low/med    high
 log only   [3] Action layer ──▶ personal challenge (code word / shared fact)
                    │             + official helpline + trusted-contact alert
                    ▼
              [4] Lookup   Tavily ──▶ official helpline + current scam warnings
                  (claimed org name only; official domains only)
```

## 2. Stack

| Layer | Choice | Hosting |
|---|---|---|
| Transcription (English) | NVIDIA NeMo Parakeet/Canary | Nebius AI Cloud GPU (not offered on Token Factory) |
| Transcription (Hindi/Hinglish, stretch) | Whisper large-v3 or AI4Bharat IndicConformer | Nebius AI Cloud GPU |
| Reasoning | Nemotron 3 Ultra (`nvidia/Nemotron-3-Ultra-550b-a55b`) | Nebius Token Factory (`https://api.tokenfactory.nebius.com/v1`, OpenAI-compatible) |
| Action layer | App logic (not a model) | Same app as the backend |
| Lookup | Tavily Search API | Tavily (external API, no personal data sent) |
| Family memory | Browser IndexedDB | On the user's device only |
| Backend | Python 3.12 + FastAPI | Render (or a small Nebius VM) |
| Dashboard | React 19 + Vite + TypeScript | Served with the backend |
| Trusted-contact alert | Email (SMTP) | Same app as the backend |

**Decided 2026-09-27:** Python backend + React dashboard. Python keeps the backend in the same
language as the transcription models (NeMo, Whisper). Resolve's `brain.ts`, `otp.ts` and
`mailer.ts` are ported to Python rather than copied.

**Repo layout**

```
ringproof/
├── app/        backend: FastAPI, brain, risk engine, lookup, otp, mailer
├── web/        dashboard: React + Vite
├── asr/        transcription service (Python + NeMo), only if Nebius doesn't host Parakeet
├── samples/    sample calls + cached transcripts
├── assets/     logo + favicon
└── docs/
```

## 3. Modules

| Module | Input | Output |
|---|---|---|
| Audio ingest | Uploaded or streamed audio | Audio chunks |
| Transcriber | Audio chunks | Transcript segments with speaker turns |
| Family memory (browser) | User edits | Profiles + household rules (CRUD + delete-all) |
| Risk engine | Transcript window + contact names + claimed caller's profile | `{ score, signals[], rationale, claimed_contact, claimed_org }` |
| Lookup | `claimed_org` | `{ official_helpline, warnings[], sources[] }` |
| Action layer | High-risk result + profile + lookup | Personal challenge + helpline + trusted-contact alert |
| Dashboard | All of the above | Live transcript, risk meter, signals, actions, memory view |

## 4. Cached transcripts (cost control)

A Nebius GPU costs about $1–3/hour, too much to keep running for weeks of judging on $50 credit.

- Each sample call is transcribed **once** and the transcript is saved in `samples/`.
- The demo URL **replays** saved transcripts line by line at call speed, so it looks live.
- Nemotron, Tavily, memory and the challenge still run **for real** on every demo.
- The GPU is switched on only to transcribe new uploads and to record the demo video.

## 5. Provider fallback

Both model calls go through a thin provider-abstraction layer, ported to Python from `brain.ts`
in the author's earlier project, *Resolve*. It includes a `mock` mode (deterministic, zero API
calls) for building the dashboard.

| Call | Primary | Fallback |
|---|---|---|
| Reasoning | Nemotron 3 Ultra on Nebius | Equivalent open model on another host (OpenRouter/Groq) |
| Transcription | Parakeet on Nebius | Cached transcripts (demo); self-hosted weights elsewhere (dev only) |

These fallbacks give resilience across *different* providers' free tiers. They are not
credit-stacking on the Nebius promo.

**Rule:** the hackathon requires the project to run on Nebius. The **demo** must use the Nebius
primaries. Non-Nebius fallbacks are for development outages only, never for the submitted demo.

## 6. Languages

- **English (primary):** Parakeet/Canary.
- **Hindi/Hinglish (stretch):** an open multilingual model, because Parakeet and Canary cover only
  English + 24 European languages. The user or sample picks the language; no auto-detection in v1.
- The risk engine receives the transcript as-is. Nemotron's Hindi/Hinglish reading is unverified;
  the week-1 test checks it.
- The NVIDIA-model rule is met by Nemotron (and Parakeet for English) either way.

## 7. Family memory

- **Profile fields:** name, relation, how they address the user, usual topics and asks, past
  requests, family code word, email. See PRD §4.
- **Household rules:** apply to every call ("police never arrest over a call"), plus which
  contact to alert.
- **Where it lives:** only in the browser (IndexedDB) on the user's device. The user can view,
  edit and delete profiles, and delete everything. The backend never stores memory.
- **Identifying the caller:** the browser sends the transcript plus contact names and relations
  only. The model returns `claimed_contact` ("Rahul") or `claimed_org` ("CBI"). The browser then
  attaches that one profile (without the code word) to later requests. Unknown callers are
  scored on generic signals and household rules.
- **Retention:** call audio and transcripts are discarded when the call ends.

## 8. Lookup (Tavily)

- **Trigger:** the risk engine returns a `claimed_org` (CBI, police, RBI, a bank, a courier).
- **Query:** only the organisation name + "official helpline" / "scam warning". Never the
  transcript, the family memory or the user's details.
- **Trust:** restrict results to an allowlist of official domains (`.gov.in`, `rbi.org.in`,
  `cybercrime.gov.in`, bank domains). A built-in table of verified numbers (e.g. 1930) wins over
  any search result.
- **Latency:** the challenge never waits for Tavily. It goes out from the built-in table, and
  the lookup adds details and sources when it returns.
- **Output shown to the user:** one helpline number, one warning line, and the source link.

## 9. Verification challenge

The challenge depends on who the caller claims to be:

| Caller claims to be | Challenge |
|---|---|
| Family member **with** a code word | "Ask the caller our family code word." The browser checks the caller's answer in the transcript against the stored code word, which never leaves the browser. |
| Family member **without** a code word | OTP fallback, ported from Resolve's `otp.ts` (expiry, attempt limits, lockout): a code is emailed to the *real* contact, and the caller must read it back. |
| An organisation (CBI, police, bank…) | No challenge, because the caller can't be verified mid-call. Instruction: "Hang up and call the official helpline," with the number from the built-in table or the lookup. |
| Unknown | Generic signals only; high risk gives the same "hang up" instruction. |
