# Architecture

> How Ringproof is built: pipeline, stack, modules and fallbacks.

## 1. Pipeline

```
Call audio (sample upload/stream)
        │
        ▼
[1] Transcriber   Parakeet/Canary   ──▶ transcript + speaker turns
        │
        ▼
[2] Risk engine   Nemotron 3 Ultra  ──▶ score + signals + rationale
        │
   ┌────┴────┐
   ▼         ▼
 low/med    high
 log only   [3] Action layer ──▶ verification challenge + trusted-contact alert
```

## 2. Stack

| Layer | Choice | Hosting |
|---|---|---|
| Transcription | NVIDIA NeMo Parakeet/Canary | Hosted endpoint or self-hosted open weights |
| Reasoning | Nemotron 3 Ultra | Nebius Token Factory / AI Cloud |
| Action layer | App logic (not a model) | Same app as the backend |
| Backend | _TBD_ | _TBD_ |
| Dashboard | _TBD_ | _TBD_ |

## 3. Modules

| Module | Input | Output |
|---|---|---|
| Audio ingest | Uploaded or streamed audio | Audio chunks |
| Transcriber | Audio chunks | Transcript segments with speaker turns |
| Risk engine | Transcript window | `{ score, signals[], rationale }` |
| Action layer | High-risk result | Verification challenge + trusted-contact alert |
| Dashboard | All of the above | Live transcript, risk meter, signals, actions |

## 4. Provider fallback

Both model calls go through a thin provider-abstraction layer. It follows the same pattern as
`brain.ts` in the author's earlier project, *Resolve*.

| Call | Primary | Fallback |
|---|---|---|
| Reasoning | Nemotron 3 Ultra on Nebius | Equivalent open model on another host (OpenRouter/Groq) |
| Transcription | Parakeet/Canary hosted endpoint | Self-hosted open weights on a free GPU tier |

These fallbacks give resilience across *different* providers' free tiers. They are not
credit-stacking on the Nebius promo.

## 5. Verification challenge

The challenge is OTP-style, reusing the pattern proven in Resolve.
