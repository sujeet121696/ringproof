# Tasks

> Step-by-step build plan. Deadline: **Oct 30, 2026**. Target submit: **Oct 29** (1-day buffer).

## Milestones

| # | Milestone | Target |
|---|---|---|
| M1 | Both models answer a test call on real infra | Oct 4 |
| M2 | Sample audio → transcript → memory-aware risk score, end-to-end in code | Oct 11 |
| M3 | Full demo flow in the dashboard: memory, intervention, data control | Oct 18 |
| M4 | Polished, resilient, demo-ready | Oct 25 |
| M5 | Submitted | Oct 29 |

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
11. [ ] Transcriber module with speaker turns; save each sample's transcript to `samples/`
    (English; plus Hindi/Hinglish route if the go/no-go passed)
12. [ ] Family memory in the browser (IndexedDB): profiles + household rules, CRUD + delete-all
    - [x] Oct 7: IndexedDB store, seeded once from `/api/seed/family` (`web/src/memory.ts`)
    - [ ] Edit, delete, delete-all (with step 22)
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
15. [ ] Run all samples through and tune the prompt until scam and real separate cleanly,
    with and without a matching profile (`python -m scripts.eval_samples`)
    - [x] Oct 7: Nemotron 3 Ultra 4/4 on the first prompt, 2–6 s per call (mock: right scores)
    - [x] Oct 7: harder cases added (samples 05–09: small usual ask, Suvaani, Sahni, fake-bank OTP,
      fake Shivam cut off before any ask). 9/9 on two full runs after two prompt/brain fixes
      (JSON mode + 4000 tokens; `claimed_org` only when the caller speaks for an organisation)
    - [ ] Turn-by-turn: score rises at the right moment as the call replays

## Week 3 · Oct 12 – 18 · Agent + dashboard → M3
16. [ ] Lookup module: Tavily search with the official-domain allowlist + built-in verified numbers
    (verify 1930 and every built-in number against an official source)
17. [ ] Action layer: challenge by caller type (ARCHITECTURE §9): code word checked in the
    browser, "Is this you?" one-tap email check to the real contact, "hang up + helpline" for
    organisations
    - [x] Oct 7: code word checked in the browser (`web/src/useCall.ts`): passes if the caller says
      it; fails after 2 caller replies once the user has asked
    - [ ] "Is this you?" email to the real contact (with step 18)
18. [ ] Action layer: trusted-contact alert by email, ported from Resolve's `mailer.ts`
19. [x] Dashboard: input panel + live transcript (Oct 7)
20. [x] Dashboard: risk meter + signals panel with triggering quotes (Oct 7)
21. [x] Dashboard: caller card + actions panel + official-check panel (Oct 7; official check
    shows the built-in 1930 for now, Tavily details come with step 16)
22. [ ] Dashboard: memory view with contact cards, delete, and delete-all
23. [x] Wire the favicon + logo into the dashboard (mark + text wordmark, so it follows the theme)

## Week 4 · Oct 19 – 25 · Polish + resilience → M4
24. [x] Replay cached transcripts at call speed so risk updates live (done early in 14a, Oct 7)
    (live audio streaming only if time allows)
25. [ ] Fallback providers for reasoning and transcription, tested by forcing a failure
26. [ ] UI polish: legible at a glance, intervention is the climax, memory is visible
27. [x] Lock the logo font (convert text to fixed shapes) and add PNG/ICO favicon fallbacks
    (Oct 7: redesigned in the kharidwise style; full icon set + manifest; `assets/build/`)
28. [ ] Deploy to a public **demo URL** (required)
29. [ ] If Hindi/Hinglish is in: record one Hinglish digital-arrest sample and add it to the demo
30. [ ] Full dry run with every sample on the deployed URL, and fix what breaks
30a. [ ] **Stretch, only if M3 is done by Oct 18:** a live call through a Vobiz number
    (Vobiz call source → Parakeet on GPU → same agent), recorded for the demo video only.
    Listen-only; the agent talking back stays post-hackathon (VISION §3a)

## Week 5 · Oct 26 – 29 · Submission → M5
31. [ ] README: differentiation story (family memory + personal challenge + Tavily lookup),
    screenshots, setup steps
32. [ ] Write the required feedback on Nebius + NVIDIA tools 
    (specific and honest; $100 feedback prizes)
33. [ ] Record the demo video (**≤3 min**, with voiceover on Nebius + NVIDIA usage) following the PRD
    demo story: digital-arrest call caught, fake Sujeet fails the code word, real Sujeet's call stays quiet
34. [ ] Devpost submission: track, repo link, demo URL, video, description, feedback;
    mention Tavily usage (select Best Use of Tavily if the form asks)
35. [ ] Final check against the hackathon rules, then submit before **Oct 30, 10:00 AM PDT
    (10:30 PM IST)**
