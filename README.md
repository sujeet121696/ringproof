<p align="center"><img src="assets/logo.svg" alt="Ringproof" width="320"></p>

# Ringproof

**A personal AI that knows your family and stops "digital arrest" and impersonation scams mid-call.**

Ringproof listens to a call, transcribes it live, and checks what's being said against a private memory of your family: how each trusted contact talks, what they usually ask for, and a shared code word. A call that's unusual *for that person* (urgency + secrecy + a money ask) triggers a personal verification challenge ("ask for the family code word") and alerts a trusted contact before money moves. Your memory stays yours: view it, edit it, delete it; calls are never stored.

> Built for the **Nebius × NVIDIA Global AI Hackathon** — Track: **Personal AI**.
> Status: **pre-build.** Idea locked; nothing implemented yet. Deadline: Oct 30.

## The Problem

In India, "digital arrest" scams target elderly people. A caller posing as a CBI, police or customs officer says the victim is linked to a crime, orders them to stay on the call and tell no one, and makes them transfer money to "clear their name." A second pattern uses a fake family member in trouble, sometimes with a cloned voice. Spam blockers and caller ID catch *unknown* numbers. They don't catch a convincing official or a familiar voice mid-call, and they know nothing about *your* family.

## The Solution

```
Call audio ──▶ Parakeet/Canary ──▶ transcript
                                      │
        Family memory (private) ──▶ Nemotron 3 Ultra on Nebius
                                      │  "is this unusual for this person?"
                                 ┌────┴────┐
                                 ▼         ▼
                              low/med     high
                              → log       → family code-word challenge
                                          + official helpline (Tavily lookup)
                                          + alert to a trusted contact
```

- **Transcription:** NVIDIA Parakeet/Canary turns the call into text. English is primary; Hindi/Hinglish is a stretch goal.
- **Memory:** a private profile for each trusted contact (how they talk, what they usually ask for, a family code word). You can view, edit and delete it; calls are never stored.
- **Reasoning:** Nemotron 3 Ultra on Nebius scores the call against that memory, and against digital-arrest patterns (impersonated authority, isolation, secrecy, urgency, transfer ask).
- **Action:** high-risk calls trigger a personal challenge, show the real official helpline (looked up with Tavily from official sites only), and alert a trusted contact.

Demo scope: sample calls through a dashboard, not live telephony interception (a post-hackathon concern).

## Docs

| File | Contents |
|---|---|
| [`docs/PRD.md`](docs/PRD.md) | Problem, goals, scope, constraints, risks |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Pipeline, stack, modules, fallbacks |
| [`docs/RULES.md`](docs/RULES.md) | Coding and workflow rules |
| [`docs/DESIGN.md`](docs/DESIGN.md) | Dashboard UI/UX direction |
| [`docs/TASKS.md`](docs/TASKS.md) | Build checklist and progress |
