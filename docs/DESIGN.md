# Design

> UI/UX direction for the demo dashboard.

## 1. Principles

- **Legible at a glance.** Anyone should grasp the risk level in under two seconds.
- **Show the reasoning.** Explain *why* a call is risky (signals + quoted lines), not just a number.
- **The intervention is the climax.** The challenge and alert are the most visible moment of the
  demo.

## 2. Layout (draft)

| Panel | Shows |
|---|---|
| Input | Sample picker (scam/real), upload, or stream |
| Live transcript | Speaker-labelled lines that auto-scroll; lines that triggered a signal are highlighted |
| Risk meter | Low, medium or high, updating live |
| Signals | Urgency, secrecy, transfer ask and impersonation, each lit with its triggering quote |
| Actions | Idle, then challenge issued, then trusted contact alerted |

## 3. Decisions

| Decision | Reason |
|---|---|
| Frame risk around *behavior* ("asked for secrecy + a wire transfer"), not "fake voice" | Detection is over content, not acoustics |
| Demo uses sample audio, not live calls | Live telephony is out of scope (see PRD) |

## 4. Brand

| Asset | File | Use |
|---|---|---|
| Logo | `assets/logo.svg` | README, dashboard header, demo video |
| Mark | `assets/logo-mark.svg` | Square spots: avatar, app icon |
| Favicon | `assets/favicon.svg` | Browser tab: `<link rel="icon" href="/favicon.svg" type="image/svg+xml">` |

- **Concept:** a shield (protection) around a phone handset (the call).
- **Colors:** indigo `#4F46E5` → sky `#0EA5E9` gradient; text slate `#0F172A` (dark mode `#F1F5F9`).
- **Wordmark:** "Ring" + "proof" in the accent color, using the system sans-serif bold.
- The handset glyph is Material Icons "call" (Apache-2.0).

## 5. Open questions

- UI framework and the rest of the visual style.
- How to show the trusted-contact alert: a mock phone notification, or a real SMS or email?
