# Rules

> How we write code and work in this repo.

## 1. Code

- Build the smallest thing that demos well. This is a solo hackathon build.
- Backend: Python 3.12, FastAPI, type hints everywhere. Dashboard: React + TypeScript.
- All model calls go through the provider-abstraction layer. Never call a provider SDK directly.
- The risk engine returns structured output (`score`, `signals`, `rationale`, `claimed_contact`,
  `claimed_org`), never free text.
- Keep modules separate: call source, transcriber, memory, risk engine, policy, tools, dashboard.
- The model assesses; code decides. Which action to take comes from the policy table, never from
  the model's free text.
- Every channel (replay, upload, later telephony) goes through the call source interface.

## 2. Secrets and data

- Keys live in `.env`. Commit only `.env.example`.
- Never commit real people's call recordings. Use synthetic or consented samples only.
- Keep sample audio files small.
- External APIs (Tavily) get only the claimed organisation's name, never transcripts, memory or
  user details.
- Never show a phone number from search unless it comes from an allowlisted official domain.
- Family memory stays in the browser. The code word never leaves it, and the backend never stores
  memory.

## 3. Workflow

- **Never commit or push.** The user commits manually.
- Run `npm run check` before every commit (lint, type check, build, tests, dependency audit).
  `npm run local` does the same, then serves the app on http://localhost:8300.
- Update `TASKS.md` as tasks start and finish.
- Update `ARCHITECTURE.md` when the stack or modules change, and `PRD.md` when scope changes.

## 4. Hackathon compliance

- Run ≥1 NVIDIA open model and run on Nebius.
- One account per real person. No promo re-claiming.

## 5. Privacy, claims and accessibility (checked Oct 13)

- **Privacy page stays true.** `web/src/components/PrivacyView.tsx` lists what stays on the device
  and what each service gets. Any change to what is sent or kept (`useCall.ts`, `app/session.py`,
  `app/notify.py`, a new service) updates that page and the note in `MemoryView.tsx` in the same
  change.
- **No tracking.** No cookies, analytics, ads or third-party fonts/scripts. Fonts are self-hosted
  with their licence files. `localStorage` holds only the theme. A new third party is listed on
  the privacy page first.
- **Collect the minimum.** Send a contact's full profile only when the caller claims to be them;
  never send the code word; the server keeps nothing after a call. Uploads are not stored.
- **Every email says why it came and how to stop it** (`why_footer` in `app/notify.py`), and goes
  only to approved addresses (`EMAIL_ALLOWED_TO`). No transcript in emails.
- **No unsupported claims.** Every fact, number or helpline in the app, README or video is checked
  against an official source first (1930 → cybercrime.gov.in). Never say Ringproof "stops" or
  "guarantees" anything; it is a demo that can be wrong.
- **Consent.** Real names only with consent, all other sample details made up; recordings are
  synthetic or consented. The app is not for children.
- **Accessibility.** Every control reachable by keyboard with a visible focus ring (never remove
  outlines); icon-only buttons get `aria-label` + `title`; decorative images `alt=""`; check
  contrast in light and dark. Run Lighthouse/axe before submitting.
- **Before going public:** remove the Cloudflare Access app so judges need no login, and recheck
  the privacy page against the code.

## 6. Security

- **Our pages only.** `/ws/call` refuses other websites (`origin_ok` in `app/main.py`); a new
  public domain goes in `PUBLIC_BASE_URL`.
- **Cap anything that costs money.** Live calls (`MAX_LIVE_CALLS`), uploads per visitor
  (`UPLOADS_PER_HOUR`), emails (allow-list). A new paid endpoint gets a limit before it ships.
- **CSP stays strict** (`app/web.py`): no inline scripts, no outside hosts. If Cloudflare features
  that inject scripts (Rocket Loader, Web Analytics, email obfuscation) are turned on, they break.
- **Pinned dependencies.** Install with `-c requirements.lock`; after an upgrade, rerun the tests and
  refresh the lock with `pip freeze`. `npm run check` audits both Python and npm packages.
- **Caller words are untrusted input.** The model only scores; code picks the action. Keep it so
  when the prompt changes, and never put the model's text into HTML without escaping.
- **Secrets.** Only in `.env`; never in chat, screenshots, logs or commits. If one leaks, rotate it
  at once. Keep spending alerts on Nebius and Tavily.
- Before merging: `/security-review` and `/code-review`.
