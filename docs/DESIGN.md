# Design

> UI/UX direction for the demo dashboard.

## 1. Principles

- **Legible at a glance.** Anyone should grasp the risk level in under two seconds.
- **Show the reasoning.** Explain *why* a call is risky (signals + quoted lines), not just a number.
- **The intervention is the climax.** The challenge and alert are the most visible moment of the
  demo.
- **Memory is visible.** Show which profile was used and how the call differs from it
  ("Rahul calls you Maa; this caller said Madam").
- **Control is obvious.** The user can always see what Ringproof remembers and delete it in one
  click.

## 2. Layout (draft)

**Call view**

| Panel | Shows |
|---|---|
| Input | Sample picker (scam/real) or upload |
| Live transcript | Speaker-labelled lines that auto-scroll; lines that triggered a signal are highlighted |
| Caller | Who the caller claims to be, and the matching profile card (or "unknown") |
| Risk meter | Low, medium or high, updating live |
| Signals | Urgency, secrecy, transfer ask, impersonation, isolation and out-of-character, each lit with its triggering quote |
| Actions | Idle, then personal challenge issued ("Ask for the family code word"), then trusted contact alerted |
| Official check | The claimed organisation, its official helpline, one warning line, and the source link (from Tavily) |

**Memory view**

| Panel | Shows |
|---|---|
| Contacts | One card per trusted contact; add, edit, delete |
| Household rules | Rules for every call, plus which contact gets alerted |
| Data control | What's stored, "Delete all" button, and a note that calls are never stored |

## 3. Decisions

| Decision | Reason |
|---|---|
| Frame risk around *behavior* ("asked for secrecy + a wire transfer"), not "fake voice" | Detection is over content, not acoustics |
| Frame risk around *this person* ("unusual for Rahul") when a profile exists | Memory is the differentiator; make it visible |
| The code word is shown masked (`••••`) in the UI | It's a secret |
| Demo uses sample audio, not live calls | Live telephony is out of scope (see PRD) |
| UI copy in plain English; transcripts shown in the call's language | English is primary; Hindi/Hinglish is a stretch goal (see PRD) |
| High-risk screen gives one clear instruction ("Hang up. Call 1930.") | Elderly users under pressure need one action, not a report |

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

- Visual style beyond the brand colors (React + Vite is decided).
