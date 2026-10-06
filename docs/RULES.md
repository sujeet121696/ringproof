# Rules

> How we write code and work in this repo.

## 1. Code

- Build the smallest thing that demos well. This is a solo hackathon build.
- Backend: Python 3.12, FastAPI, type hints everywhere. Dashboard: React + TypeScript.
- All model calls go through the provider-abstraction layer. Never call a provider SDK directly.
- The risk engine returns structured output (`score`, `signals`, `rationale`, `claimed_contact`,
  `claimed_org`), never free text.
- Keep modules separate: ingest, transcriber, memory, risk engine, lookup, action layer, dashboard.

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
- Update `TASKS.md` as tasks start and finish.
- Update `ARCHITECTURE.md` when the stack or modules change, and `PRD.md` when scope changes.

## 4. Hackathon compliance

- Run ≥1 NVIDIA open model and run on Nebius.
- One account per real person. No promo re-claiming.
