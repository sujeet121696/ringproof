# Ringproof

Personal voice-fraud defense agent. It transcribes a call, scores it against a private,
user-controlled memory of the family ("is this unusual for this person?"), and on high risk
triggers a personal verification challenge (family code word) and a trusted-contact alert.

## Snapshot

| | |
|---|---|
| Hackathon | Nebius × NVIDIA Global AI Hackathon |
| Track | Personal AI (family memory + data control are core) |
| Deadline | Oct 30, 2026 |
| Stack | Python + FastAPI backend, React + Vite dashboard |
| Team | Solo |
| Status | Week 1 done: credits, keys, scaffold, Nemotron + Tavily smoke tests |

## Docs

| File | Contents |
|---|---|
| [docs/PRD.md](docs/PRD.md) | Problem, goals, scope, constraints, risks |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Pipeline, stack, modules, fallbacks |
| [docs/RULES.md](docs/RULES.md) | Coding and workflow rules |
| [docs/DESIGN.md](docs/DESIGN.md) | Dashboard UI/UX direction |
| [docs/TASKS.md](docs/TASKS.md) | Build checklist and progress |
| [docs/VISION.md](docs/VISION.md) | Post-hackathon: guardian agent, channels, privacy, scaling |

## Working agreements

- Never commit or push. The user commits manually.
- Keep docs lean, and update the relevant doc whenever scope, stack or tasks change.
