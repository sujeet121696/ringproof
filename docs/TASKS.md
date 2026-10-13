# Tasks

> Step-by-step build plan. Deadline: **Oct 30, 2026**. Target submit: **Oct 23** (1-week buffer,
> decided Oct 8). Week headings below are the original plan; the dates that count are these.

## Milestones

| # | Milestone | Target |
|---|---|---|
| M1 | Both models answer a test call on real infra | Oct 4 ✓ |
| M2 | Sample audio → transcript → memory-aware risk score, end-to-end in code | Oct 12 |
| M3 | Full demo flow in the dashboard: memory, intervention, data control | Oct 15 |
| M4 | Polished, resilient, deployed, dry-run done | Oct 19 |
| M5 | Submitted (README, feedback, video, Devpost) | Oct 23 |

## Compressed plan (from Oct 8)

| Dates | Build | Needs from Sujeet |
|---|---|---|
| Oct 8–10 | 22 + 12 memory screen, 15 turn-by-turn, 16 Tavily lookup, 18 + 17 emails | Pick an email sender (account + key in `.env`) |
| Oct 10–12 | 6, 10, 11 Parakeet on a Nebius GPU + audio upload; 7 Hinglish go/no-go | Record the 9 sample calls (8); start a GPU |
| Oct 13–15 | 25 fallback test, 26 UI polish | — |
| Oct 16–19 | 28 deploy to `ringproof.kharidwise.com`, 30 dry run; 30a Vobiz only if ahead | Check VM price; Cloudflare DNS |
| Oct 20–23 | 31 README, 32 feedback, 33 video, 34–35 submit | Voiceover for the video |

## Done
- [x] Lock idea, name and track
- [x] Project docs
- [x] Logo + favicon (`assets/`)
- [x] Choose stack: Python + FastAPI backend, React + Vite dashboard (see `ARCHITECTURE.md`)

## Week 1 · Sept 28 – Oct 4 · Foundations → M1
1. [x] Claim Nebius credit ($25 event code + $25 Builders Program): both landed Oct 4,
    $59 balance incl. GST (+ $1 trial credit, expires ~Nov 1)
2. [x] Get a Tavily API key (pay-as-you-go, 1,500 free/month); put it in `.env` and a placeholder
    in `.env.example`. Oct 6 test: gov-domain filter returned only official sources, 1930 confirmed
    (cybercrime.gov.in, i4c.mha.gov.in), ~8.4 s latency
3. [x] Scaffold repo (`app/`, `web/`, `samples/`) + `.env.example` + `LICENSE`
    (Apache-2.0, MIT or MPL-2.0; required)
4. [x] Confirm where Parakeet/Canary runs on Nebius: **not on Token Factory** (no ASR models listed,
    Oct 6), so it needs an AI Cloud GPU
5. [x] Smoke test: call Nemotron 3 Ultra on Nebius with a hard-coded transcript
    (`nvidia/Nemotron-3-Ultra-550b-a55b`, Oct 6: correct high score + JSON, ~4.8 s, ~530 tokens)
6. [ ] Smoke test: transcribe one audio clip with Parakeet/Canary
7. [ ] Language test (stretch go/no-go): one Hinglish clip → Whisper/IndicConformer on Nebius →
    Nemotron. If signals are caught correctly, keep Hindi/Hinglish; otherwise drop to post-hackathon
8. [ ] Write and record English sample calls (synthetic or consented only): digital-arrest scam,
    fake-family-member scam, real family call, real bank call
    - [x] Scripts written as timed transcripts with expected results (`samples/calls/`, Oct 6)
    - [ ] Record audio
9. [x] Write the demo family: Maa + Sujeet, Suvaani, Shivam, Sahni profiles + household rules
    (`samples/family.json`; real first names with consent, all other details made up)

## Week 2 · Oct 5 – 11 · Core pipeline → M2
10. [ ] Audio ingest: upload a file and split it into chunks
    - [x] Oct 10: `POST /api/transcribe` (≤20 MB, not kept) + "Call from: Recording" on the
      dashboard; tested with a stand-in speech service. Real run: needs the GPU
11. [ ] Transcriber module with speaker turns; save each sample's transcript to `samples/`
    (English; plus Hindi/Hinglish route if the go/no-go passed)
    - [x] Oct 10: `asr/server.py` (Parakeet + Sortformer, code as on the model cards),
      `app/asr.py` (segments -> turns, first voice = caller), `scripts/transcribe_samples.py`
    - [ ] First GPU run: check Sortformer's printed format and the speaker split on real audio
12. [x] Family memory in the browser (IndexedDB): profiles + household rules, CRUD + delete-all
    - [x] Oct 7: IndexedDB store, seeded once from `/api/seed/family` (`web/src/memory.ts`)
    - [x] Oct 8: edit, delete, delete-all (with step 22)
13. [x] Port Resolve's `brain.ts` to Python: provider layer with `mock` + Nemotron modes
    (Ultra primary, Super fallback)
14. [x] Risk engine: identify the claimed caller, load their profile, score against it
    (structured output `{ score, signals[], rationale, claimed_contact, claimed_org }`;
    each signal carries the caller's triggering quote). `app/risk.py`, `app/brain/`
14a. [x] Call source interface (replay first) + call session over WebSocket that streams
    transcript, risk and action events (ARCHITECTURE §10, §11). Oct 7: real-speed replay on
    Nemotron, risk 2–5 s behind each turn; fake Sujeet HIGH at 11 s, digital arrest HIGH at 24 s
14b. [x] Policy table in code: signals + caller type → action (the model never picks the action).
    `app/policy.py` + 10 tests (`pytest tests`); 9/9 samples pick the expected action on Nemotron.
    Note: `alert_guardian` is announced but not delivered until step 18 (email)
15. [x] Run all samples through and tune the prompt until scam and real separate cleanly,
    with and without a matching profile (`python -m scripts.eval_samples`)
    - [x] Oct 7: Nemotron 3 Ultra 4/4 on the first prompt, 2–6 s per call (mock: right scores)
    - [x] Oct 7: harder cases added (samples 05–09: small usual ask, Suvaani, Sahni, fake-bank OTP,
      fake Shivam cut off before any ask). 9/9 on two full runs after two prompt/brain fixes
      (JSON mode + 4000 tokens; `claimed_org` only when the caller speaks for an organisation)
    - [x] Oct 8: Turn-by-turn: each sample has `expected.timeline` (levels allowed after each
      caller turn, written before running). `python -m scripts.eval_timeline` drives the real
      CallSession; Nemotron 9/9 on two runs: scams quiet at the greeting, high at the money/OTP/
      "officer" demand; real calls low on every turn, before and after the profile arrives

## Week 3 · Oct 12 – 18 · Agent + dashboard → M3
16. [x] Lookup module: Tavily search with the official-domain allowlist + built-in verified numbers
    (verify 1930 and every built-in number against an official source). Oct 8: `app/lookup.py`,
    5 tests; numbers only from the verified table (1930), Tavily adds official pages. Checked end
    to end: courier → CBI each looked up once, 3 `.gov.in` pages each, ~4 s, shown in Official check
17. [x] Action layer: challenge by caller type (ARCHITECTURE §9): code word checked in the
    browser, "Is this you?" one-tap email check to the real contact, "hang up + helpline" for
    organisations
    - [x] Oct 7: code word checked in the browser (`web/src/useCall.ts`): passes if the caller says
      it; fails after 2 caller replies once the user has asked
    - [x] Oct 8: "Is this you?" email to the real contact: Yes/No page at `/api/check/{token}`,
      answer reaches the live call; new sample 10 (fake Suvaani, no code word) picks it 2/2 on
      Nemotron. Real email send still to test once SMTP is in `.env`
18. [x] Action layer: trusted-contact alert by email, ported from Resolve's `mailer.ts`
    - [x] Oct 8: `app/notify.py` (Notifier interface, SMTP via stdlib, demo redirect), `notified`
      event so the screen says "sent" only when it was; 8 tests. Checked in the browser with email
      off: "Could not email Sujeet: email is not set up"
    - [x] Real Gmail send, Oct 8: alert + "Is this you?" emails arrived; tapping "No" on the emailed
      page reached the live call 30 s after sending (`ws_replay fake-suvaani --speed 0.05`)
19. [x] Dashboard: input panel + live transcript (Oct 7)
20. [x] Dashboard: risk meter + signals panel with triggering quotes (Oct 7)
21. [x] Dashboard: caller card + actions panel + official-check panel (Oct 7; official check
    shows the built-in 1930; Tavily official pages added Oct 8 with step 16)
22. [x] Dashboard: memory view with contact cards, add/edit, delete, and delete-all (Oct 8;
    `web/src/components/MemoryView.tsx`, checked in the browser incl. reload after delete-all)
23. [x] Wire the favicon + logo into the dashboard (mark + text wordmark, so it follows the theme)

## Week 4 · Oct 19 – 25 · Polish + resilience → M4
24. [x] Replay cached transcripts at call speed so risk updates live (done early in 14a, Oct 7)
    (live audio streaming only if time allows)
25. [ ] Fallback providers for reasoning and transcription, tested by forcing a failure
    - [x] Reasoning (Oct 8): Ultra -> Super -> keyword rules (`FallbackChain`); each result says
      who answered and the screen notes a backup. Forced with bad model names on all 10 samples:
      Super answered correctly; with both down the rules still warned on every scam and never
      told a real caller to hang up (5/10 on strict timings; it is a rough last resort)
    - [ ] Transcription: comes with Parakeet (step 4); cached transcripts are the backup
26. [x] UI polish: legible at a glance, intervention is the climax, memory is visible
    - [x] Oct 8, checked in the browser (dark + light, digital-arrest at 4×): risk word and the
      instruction are above the fold; transcript now sticky on wide screens; breadcrumb junk
      removed from official snippets; backup-model note on the risk card
    - [x] Oct 8: real-time fake-Suvaani call; Sujeet tapped "No" in the emailed page and the card
      changed to "The real Suvaani says it is not them. This is a scam. Hang up."
    - [x] Oct 9: on Sujeet's phone via the public URL (reported by Sujeet: working)
26a. [x] Installable on phones (PWA), Oct 8: manifest + `sw.js` (production builds only) + Install
    button (Android/desktop Chrome prompt; iPhone shows "Share → Add to Home Screen"). Checked on
    `localhost` in Chrome: worker active, app files cached, Install button shown. Needs HTTPS, so the
    real phone test comes after the deploy (28). Oct 9: installed on Sujeet's phone from
    https://ringproof.kharidwise.com behind Cloudflare Access (reported by Sujeet: working)
26b. [x] Compliance pass, Oct 13: Privacy and terms page + footer (no cookies, analytics or
    third-party fonts; data flows listed per service), in-app memory note made complete, and every
    email says why it came and how to stop it. Not done: Lighthouse/axe accessibility run
26c. [x] Security pass, Oct 13: `/ws/call` origin check, uploads per visitor per hour, CSP + HSTS,
    pinned Python deps (`requirements.lock`), `pip-audit` + `npm audit` clean; `npm run local` /
    `npm run check` (one command: clean, lint, build, tests, audit, serve). Checked in Chrome:
    page, a full call and the privacy page work under the CSP
27. [x] Lock the logo font (convert text to fixed shapes) and add PNG/ICO favicon fallbacks
    (Oct 7: redesigned in the kharidwise style; full icon set + manifest; `assets/build/`)
28. [ ] Deploy to a public **demo URL** (required)
    - [x] Oct 8: `kharidwise.com` is on Cloudflare (NS aryanna/fattouche); `ringproof` is free
    - [x] Oct 8: public-server protections (email allow-list, call cap, speed bound, removed the
      unused `/api/assess`); 6 tests; real emails still reach the redirect inbox
    - [x] Oct 9: production serving (`app/web.py`, port 8200), checked locally: pages, caching,
      headers, a full call over the WebSocket
    - [x] Oct 9: add `ringproof.kharidwise.com` -> `localhost:8200` to the running Cloudflare Tunnel
      (Sujeet's PC), then the phone install test (26a)
    - [ ] Oct 10: Nebius VM (Sujeet checks the price) so the demo doesn't depend on the PC
    - [x] Oct 9: live at https://ringproof.kharidwise.com via the claimtoglow tunnel; pages, headers
      and a full call over `wss://` checked. Kept behind Cloudflare Access (Team) until submission
    - [x] Oct 9: "Is this you?" over the public URL: emailed link opened
      `https://ringproof.kharidwise.com/api/check/...`, "No" reached the live call ~1 min after sending
    - [ ] **Before submitting (Oct 23): remove the Cloudflare Access app for `ringproof`** so judges
      can open the demo without a login
29. [ ] If Hindi/Hinglish is in: record one Hinglish digital-arrest sample and add it to the demo
30. [ ] Full dry run with every sample on the deployed URL, and fix what breaks
30a. [ ] **Stretch, only if M3 is done by Oct 18:** a live call through a Vobiz number
    (Vobiz call source → Parakeet on GPU → same agent), recorded for the demo video only.
    Listen-only; the agent talking back stays post-hackathon (VISION §3a)
    - [x] Oct 10: `app/vobiz.py` + `/vobiz/answer|stream/{secret}` + "Call from: Phone line";
      tested with a fake Vobiz stream. Real call: needs the GPU, `.env` values, the Answer URL
      in Vobiz, and a Cloudflare Access bypass for `/vobiz/*`; then tune the pause thresholds

## Week 5 · Oct 26 – 29 · Submission → M5
31. [ ] README: differentiation story (family memory + personal challenge + Tavily lookup),
    screenshots, setup steps (Oct 9: problem figures, comparison table and Sources section added,
    each fact checked against its source; screenshots still to do)
32. [ ] Write the required feedback on Nebius + NVIDIA tools (Oct 9: draft in `docs/FEEDBACK.md`;
    Parakeet, GPU and VM parts pending) 
    (specific and honest; $100 feedback prizes)
33. [ ] Record the demo video (**≤3 min**, with voiceover on Nebius + NVIDIA usage) following the PRD
    demo story: digital-arrest call caught, fake Sujeet fails the code word, real Sujeet's call stays quiet
34. [ ] Devpost submission: track, repo link, demo URL, video, description, feedback;
    mention Tavily usage (select Best Use of Tavily if the form asks)
35. [ ] Final check against the hackathon rules, then submit by **Oct 23**
    (hard deadline Oct 30, 10:00 AM PDT = 10:30 PM IST)
