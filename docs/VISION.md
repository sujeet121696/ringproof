# Vision

> Where Ringproof goes after the hackathon: a family guardian agent, and how it scales.
> The hackathon build (PRD) is the first slice of this, not a throwaway.

## 1. The idea

**Ringproof is an AI agent that stands between your parents and scammers.** It knows the family,
listens on their behalf, verifies callers, and pulls in the family when something is wrong.

Detecting a scam is only half the job. The other half is **acting**: verifying the caller,
breaking the scammer's isolation, and getting a real family member involved within seconds.

**The family is the unit**, not the individual: one protected person (Maa), one or more
guardians (Sujeet, Suvaani, Shivam), one shared memory.

## 2. Key insights

| Insight | What it means for the product |
|---|---|
| Scams work by **isolating** the victim ("don't hang up, don't tell anyone") | The agent's main weapon is breaking isolation: bring in the real family, now |
| A cloned voice can't fake **what only the family knows** | Verify with shared secrets and with the *real* person, never with voice analysis |
| Many elderly users have **feature phones** or struggle with apps | The main channel must work with **no app on Maa's phone** |
| The harm is the **money transfer**, not the call | Long term, sit next to the payment step too (banks, UPI apps) |
| Every scam call teaches something | Opt-in, anonymised scam patterns make every family safer |

## 3. Channels (how the agent hears calls)

Phone operating systems block normal apps from hearing call audio (iOS completely; Android for
third-party apps). So the agent reaches calls in other ways:

| # | Channel | How it works | Covers | When |
|---|---|---|---|---|
| 0 | **Replay / upload** | Recorded or sample calls in the dashboard | Demo, testing | Hackathon |
| 1 | **Guardian Line** | Calls Maa doesn't answer, or that come from unknown numbers, are forwarded by the carrier (standard call forwarding) to a Ringproof number on **Vobiz** (see §3a). The agent answers, asks who is calling and why, and only rings Maa with a summary if it's safe. | Any phone, including feature phones and iPhone | First post-hackathon channel |
| 2 | **Add Ringproof to the call** | One button merges the agent into an ongoing call as a 3-way call; it listens and whispers advice to Maa | Calls Maa already answered | After 1 |
| 3 | **Companion listener** | A second device (old phone, tablet) near Maa listens through its microphone, on-device where possible | WhatsApp and video "digital arrest" calls, which no carrier hook sees | After 2 |
| 4 | **Payment guard (B2B)** | Banks and UPI apps call the Ringproof API before a large transfer: "is this customer on a risky call right now?" | The money step | Partnerships |

### 3a. Telephony provider: Vobiz

**Decided 2026-10-07:** Vobiz (Bengaluru), an API-first telephony provider built for voice AI
agents, with Indian numbers and carrier connections.

How it plugs in (from the Vobiz integration guide in Sarvam's docs):

```
Caller ─▶ Vobiz number ─▶ fetches our Answer URL ─▶ we return XML with <Stream bidirectional="true">
                                                    │
         FastAPI WebSocket ◀── JSON events: start (metadata), media (base64 audio) ──┘
                │  ──▶ playAudio (base64 Linear16, no WAV header), clearAudio, checkpoint
                ▼
         Vobiz call source ─▶ streaming ASR ─▶ agent (same pipeline as replay)
```

- **Inbound audio:** request `audio/x-l16;rate=16000`. 16 kHz is what Parakeet expects, so no
  resampling (the default is 8 kHz mu-law).
- **Outbound audio:** Linear16 at 8, 16 or 24 kHz, so the agent can speak (needs text-to-speech;
  NVIDIA's open TTS models are the first option to test).
- **Two-way with barge-in:** the caller can interrupt the agent, which a screening conversation
  needs.
- It is just another **call source**: the risk engine, policy and tools don't change.

## 4. The agent loop

```
perceive ─▶ recall ─▶ assess ─▶ decide ─▶ act ─▶ learn
transcript   family    Nemotron   policy     tools    memory updates
stream       memory    (signals)  (code)              (guardian approves)
```

- **Assess** is the model's job: signals, rationale, who the caller claims to be.
- **Decide** is plain code (a policy), not the model. The same signals always lead to the same
  action, which makes the agent predictable, testable and auditable.
- **Learn** never changes memory on its own. It proposes ("Sujeet mentioned a new job, add it?")
  and a guardian approves.

**Tools the agent can use**

| Tool | Example |
|---|---|
| Code-word challenge | "Ask him our family code word." |
| **"Is this you?" check** | Sends the *real* Sujeet a one-tap message: "Someone claiming to be you is on a call with Maa. Is it you?" A "No" instantly tells Maa to hang up. |
| Callback to the known number | The agent calls Sujeet's saved number to confirm he is safe |
| Official lookup | Tavily search on official domains only, plus a verified-numbers table (1930) |
| Alert guardians | Email now; WhatsApp, SMS or a phone call later |
| Scam report | Drafts a report for the national cyber-crime portal (1930 / cybercrime.gov.in) for Maa to send |

**Verification ladder** (the agent climbs until it's sure):
code word → "Is this you?" check → callback to the known number → "Hang up and call the official
number."

## 5. Privacy model

- **Family memory is local-first and end-to-end encrypted.** It lives on family devices and syncs
  between guardians as ciphertext. The server can't read it.
- **Per call, the server gets a minimal, temporary slice** (the claimed caller's profile, without
  the code word) and deletes it when the call ends.
- **The code word is stored only as a salted hash.** The agent checks a spoken answer against
  the hash and never sees the word itself.
- **Audio and transcripts are deleted at the end of the call** unless a guardian saves one as
  evidence.
- **Shared scam intelligence is opt-in and anonymised:** a hash of the caller's number plus the
  scam category. Never content, never names.

## 6. How it scales

```
Channels ──▶ Ingest gateway ──▶ Streaming ASR pool ──▶ Agent service ──▶ Tools
(Guardian Line,  (WebSocket /     (Parakeet / Riva,     (stateless;         (notify, lookup,
 companion, API)  telephony       GPU, autoscaled)      session in Redis)    verify, report)
                  media streams)                              │
                                                        Nemotron Ultra
                                                 (cheaper cascade later, if a small
                                                  model is tuned to match it)
```

| Concern | Decision |
|---|---|
| Many calls at once | Stateless agent workers + a shared session store; scale out by adding workers |
| Model cost | Ultra on every check for now: on Oct 7 it was both the fastest and most accurate (8/8, median 2.2 s) while Super, Nano and Lightning were slower and Nano/Lightning less accurate. A cheap-model cascade (Nano is ~1/12–1/16 of Ultra's price) only pays off once a small model is tuned to match; re-test at scale |
| Speech-to-text | Streaming ASR on a GPU pool that grows and shrinks with live calls; cost is per live minute |
| Latency | Warnings come from the cheap model and the built-in table first; slower steps (Ultra, lookup) add detail after |
| Reliability | Every model call goes through the provider layer with a fallback; the policy works even when the model is down (fail safe: "verify before you pay") |
| Quality | The sample-call library is a regression test suite; every missed scam becomes a new test case |
| Multi-tenant | Family = tenant; roles: protected person, guardians |
| Languages | English first, then Hindi/Hinglish and regional languages via Indic ASR models |

## 7. Business

- **Families (B2C):** a monthly subscription, usually paid by the adult child.
- **Banks, fintechs, telcos (B2B):** a per-call or per-check API (channel 4), plus white-label
  Guardian Line.

## 8. Roadmap

| Phase | What ships |
|---|---|
| **Hackathon (Oct 2026)** | Replay channel, family memory, risk engine, code word + "Is this you?" check, lookup, alerts, data control |
| **Pilot** | Guardian Line on Vobiz, WhatsApp alerts, encrypted family sync, Hindi |
| **Product** | 3-way "add Ringproof", companion listener, learning memory, scam reports |
| **Scale** | Payment-guard API, community threat feed, regional languages |

## 9. To verify before the pilot

- Vobiz: number pricing, per-minute cost, KYC/business documents needed for an Indian number,
  and whether forwarded calls keep the original caller's number (the agent needs it).
- Carrier support and costs for conditional call forwarding on Indian networks.
- Consent and recording rules for an agent answering or joining calls in India.
- Whether the national cyber-crime portal or DoT reporting tools accept third-party reports.
