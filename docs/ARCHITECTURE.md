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
| Dashboard | React 19 + Vite + TypeScript, installable (PWA) | Served with the backend |
| Trusted-contact alert | Email (SMTP) | Same app as the backend |

**Decided 2026-09-27:** Python backend + React dashboard. Python keeps the backend in the same
language as the transcription models (NeMo, Whisper). Resolve's `brain.ts` and `mailer.ts` are
ported to Python rather than copied (`otp.ts` is no longer needed, see §9).

**Repo layout**

```
ringproof/
├── app/        backend: FastAPI, call sources, brain, risk engine, policy, tools (lookup, verify, mailer)
├── web/        dashboard: React + Vite
├── asr/        speech service (Python + NeMo: Parakeet + Sortformer) on a Nebius AI Cloud GPU
├── samples/    sample call scripts, recordings' transcripts (`transcripts/`), recordings (`audio/`, git-ignored)
├── assets/     logo + favicon
└── docs/
```

## 3. Modules

| Module | Input | Output |
|---|---|---|
| Call source (`app/calls/`) | A sample, an uploaded recording's transcript, or the phone line; companion later | Stream of transcript turns (one interface for every channel) |
| Speech service (`asr/server.py`, GPU) | Audio, any format | Parakeet text segments with times; Sortformer speaker segments (uploads only) |
| Transcriber (`app/asr.py`) | Speech service output | Turns: each segment goes to the speaker heard most during it; the first voice is the caller |
| Phone line (`app/vobiz.py`) | Vobiz audio stream (16 kHz, big-endian L16) | Utterances cut at pauses, transcribed one by one, pushed as caller turns to the waiting dashboard |
| Family memory (browser) | User edits | Profiles + household rules (CRUD + delete-all) |
| Risk engine | Transcript window + contact names + claimed caller's profile | `{ score, signals[], rationale, claimed_contact, claimed_org }` |
| Lookup | `claimed_org` | `{ official_helpline, warnings[], sources[] }` |
| Policy | Risk result + caller type | Which action to take (plain code, not the model) |
| Action layer (tools) | Policy decision + profile + lookup | Personal challenge, "Is this you?" check, helpline, trusted-contact alert |
| Dashboard | All of the above | Live transcript, risk meter, signals, actions, memory view |
| App shell (`web/public/sw.js`) | Browser | Makes it installable on phones; caches only the app files, never `/api`, `/ws` or memory |
| Production serving (`app/web.py`) | `web/dist` (built) | One process, one port: the API also serves the dashboard; hashed `assets/` cached a year, everything else re-checked; security headers on every response (CSP: only this site's own scripts, styles and connections; HSTS) |

**Production run** (Oct 9): `cd web && npm run build`, then from the repo root
`PUBLIC_BASE_URL=https://ringproof.kharidwise.com uvicorn app.main:app --port 8200` (no `--reload`). Locally, `npm run local` builds and serves the same way on 8300.
A Cloudflare Tunnel maps `ringproof.kharidwise.com` to `http://localhost:8200`; one tunnel can
serve several hostnames. Not yet added: a Content Security Policy (needs testing on every page).

## 4. Cached transcripts (cost control)

A Nebius GPU costs about $1–3/hour, too much to keep running for weeks of judging on $50 credit.

- Each recorded sample is transcribed **once** (`python -m scripts.transcribe_samples`) into
  `samples/transcripts/`; the dashboard plays it instead of the script. The scripts stay the
  ground truth for the eval scripts, whose expected levels refer to the script's own turns.
- The demo URL **replays** saved transcripts line by line at call speed, so it looks live.
- Nemotron, Tavily, memory and the challenge still run **for real** on every demo.
- The GPU is switched on only to transcribe new uploads, take phone calls and record the demo
  video. It is reached through an SSH tunnel and a token, never opened to the internet
  (`asr/README.md`).

## 5. Provider fallback

Both model calls go through a thin provider-abstraction layer, ported to Python from `brain.ts`
in the author's earlier project, *Resolve*. It includes a `mock` mode (deterministic, zero API
calls) for building the dashboard.

| Call | Primary | Fallback |
|---|---|---|
| Reasoning | Nemotron 3 Ultra on Nebius | Nemotron 3 Super on Nebius (same API, cheaper; stays NVIDIA + Nebius), then keyword rules if both are down |
| Transcription | Parakeet on Nebius | Cached transcripts (demo); self-hosted weights elsewhere (dev only) |

The reasoning fallback swaps to a smaller Nemotron on the same Token Factory account, so the
demo stays on Nebius and NVIDIA models even when Ultra is slow or rate-limited. If Nebius is
unreachable, the zero-cost keyword rules (`app/brain/keywords.py`) still give a rough warning, since
silence during a scam is the worst outcome. Each result carries `checked_by` and `backup`, and
the risk card says when a backup answered. Tested Oct 8 by forcing failures (TASKS 25).

**Rule:** the hackathon requires the project to run on Nebius. The **demo** must use Nebius.
Non-Nebius hosts (self-hosted ASR weights) are for development only, never for the submitted demo.

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
  only. The model returns `claimed_contact` ("Sujeet") or `claimed_org` ("CBI"). The browser then
  attaches that one profile (without the code word) to later requests. Unknown callers are
  scored on generic signals and household rules.
- **Retention:** call audio and transcripts are discarded when the call ends.

## 8. Lookup (Tavily)

- **Code:** `app/lookup.py` (`Lookup` interface: `TavilyLookup`, or `NoLookup` when no key is set).
- **Trigger:** the risk is medium or high and the risk engine returns a new `claimed_org` (CBI,
  police, a bank, a courier). Each organisation is looked up once per call; results are cached
  per organisation for 24 h (in memory; a shared cache when there are several servers).
- **Query:** only the organisation name + "official helpline" / "scam warning". Never the
  transcript, the family memory or the user's details.
- **Trust:** Tavily `include_domains` = `gov.in`, `nic.in`, `rbi.org.in`, `npci.org.in` (subdomains
  match), and every result URL is checked again in code. **Phone numbers are never taken from
  search text**: a wrong number is worse than none. The number shown comes only from the verified
  table (`policy.NATIONAL_HELPLINE`, 1930).
- **Latency:** the challenge never waits for Tavily. It goes out from the built-in table, and
  the lookup adds details and sources when it returns.
- **Output shown to the user:** 1930 with its source, then up to 3 official pages (site + a
  trimmed excerpt) about calls from that organisation. "No official page found" or "Could not
  check" are shown as such. Measured Oct 8: ~4 s per search, never blocks the call.

## 9. Verification challenge

The challenge depends on who the caller claims to be:

| Caller claims to be | Challenge |
|---|---|
| Family member **with** a code word | "Ask the caller our family code word." The browser checks the caller's answer in the transcript against the stored code word, which never leaves the browser. It passes if the caller says the word, and fails after two caller replies once the user has asked for it. |
| Family member **without** a code word | **"Is this you?" check:** the *real* contact gets an email with a one-tap "Yes, it's me" / "No, it's not me" link. A "No" immediately tells the user to hang up. Replaces the earlier OTP idea: simpler for the contact, and it pulls the real family member in. |
| An organisation (CBI, police, bank…) | No challenge, because the caller can't be verified mid-call. Instruction: "Hang up and call the official helpline," with the number from the built-in table or the lookup. The instruction doesn't name the organisation, because the claim can change mid-call (courier → customs → CBI); the caller card shows the current claim. |
| Unknown | Generic signals only; high risk gives the same "hang up" instruction. |

**Messages to family** (`app/notify.py`, `app/checks.py`, built Oct 8):
- One `Notifier` interface; email over SMTP first (Gmail app password, as in Resolve's
  `mailer.ts`). SMS / WhatsApp / push can be added later without touching the session.
- **Alert** to the trusted contact: who the caller claimed to be + the risk rationale, never the
  transcript or the code word. **"Is this you?"** to the claimed contact: a link to
  `/api/check/{token}`; the page asks, and only a button press (POST) answers, so a mail scanner
  opening links can't answer. One answer per token; tokens close when the call ends, and also
  when the browser leaves mid-call (Stop, tab closed): `CallSession.close()` then cancels the
  running checks too, so nothing is sent to a closed socket. A send that fails in any way is
  shown as not sent; it never ends the call.
- The screen says "Email sent" only after the server confirms it (`notified` event); otherwise it
  shows the reason. If the "Is this you?" email can't go out, the instruction becomes "Do not send
  anything. Hang up and call them back on their usual number."
- The browser sends only the alert contact's email (in `start`) and the claimed contact's email
  (in `profile`), never anyone else's.
- Demo: `@example.com` addresses go to `EMAIL_DEMO_REDIRECT_TO` when set.

**On a public server** (Oct 8, before the deploy). Anyone can open the demo URL, so:
- Email goes only to `EMAIL_DEMO_REDIRECT_TO` and `EMAIL_ALLOWED_TO`. Closed by default: addresses
  come from the browser, so without this the server would email strangers from our account.
  Later, contacts who confirm their address replace the list (VISION §6).
- At most `MAX_LIVE_CALLS` calls at once (default 3), and replay speed is bounded (0.1×–4×), so
  visitors can't run unlimited model calls. A refused call shows the reason on screen.
- No open model endpoint: the model is reached only through a call session.

## 10. Built to grow

The hackathon build is the first slice of the guardian agent in [VISION.md](VISION.md). Five
choices keep it from needing a rewrite later:

| Choice | Hackathon | Later |
|---|---|---|
| **Call source interface** | Sample replay, uploaded recordings, and a listen-only Vobiz call-in line | Guardian Line that screens and connects calls, 3-way call, companion listener plug into the same interface |
| **Call session over WebSocket** | Dashboard receives transcript, risk and action events live | Same event stream for phones and guardian apps |
| **Policy is code, the model only assesses** | A small rules table: signals + caller type → action | Same table, tested and auditable at scale |
| **Actions are tools** | Code word, "Is this you?" check, lookup, email alert | Add callback, WhatsApp, scam report without touching the engine |
| **Model choice in the provider layer** | Ultra for scoring (Super as fallback) | Swap or add models without touching the engine. Oct 7 benchmark: Ultra 8/8 at 2.2 s median beat Super (4.1 s), Nano (7/8, 4.8 s) and Lightning (0/8) |

## 11. Live call protocol (`/ws/call`)

One WebSocket per call. JSON messages. Code: `app/main.py`, `app/session.py`, `app/calls/`.
Reference client: `scripts/ws_replay.py`.

| Direction | `type` | Fields | When |
|---|---|---|---|
| browser → server | `start` | One source: `sample_id`, or `turns[]` + `title` (an uploaded recording, ≤300 turns), or `phone: true`; plus `speed`, `contacts[]` (id, name, relation), `household_rules[]`, `alert_contact`, `alert_email`, `user_called` | First message |
| server → browser | `waiting` | `number` | Phone line: waiting for a call (one screen at a time, up to 10 minutes) |
| server → browser | `started` | `sample` (`id`, `title`), `duration` (0 for a phone call) | Call begins |
| server → browser | `turn` | `index`, `turn` (`t`, `speaker`, `text`) | Each transcript line, at call speed |
| server → browser | `risk` | `upto`, `ms`, `with_profile`, `result` (RiskResult) | After caller turns; runs in the background |
| server → browser | `need_profile` | `contact` | The model named a family contact |
| browser → server | `profile` | `profile` with `has_code_word` (true/false; never the word itself; unknown fields are dropped) and `email` | Reply to `need_profile` |
| server → browser | `action` | `upto`, `action` (`kind`, `message`, `target`, `helpline`) | The policy (`app/policy.py`) picks a new action; each kind is sent once per call |
| server → browser | `lookup` | `ok`, `result` (`org`, `sources[]`: title, url, snippet) | Risk is medium/high and the caller claims a new organisation; once per organisation |
| server → browser | `notified` | `kind`, `target`, `channel`, `ok`, `reason` | An alert or "Is this you?" message was sent (`ok`) or not (`reason`) |
| server → browser | `check_answer` | `target`, `answer` (`yes`/`no`) | The real contact answered "Is this you?" during the call |
| server → browser | `error` | `message` | A risk check failed; the call keeps going |
| server → browser | `end` | | After the last risk check; nothing is kept |

If caller turns arrive while a check is running, they are folded into one follow-up check of
the latest transcript, so the risk never falls behind by more than one check.
