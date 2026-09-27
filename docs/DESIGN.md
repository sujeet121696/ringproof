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

## 4. Open questions

- Visual style, colors and UI framework.
- How to show the trusted-contact alert: a mock phone notification, or a real SMS or email?
