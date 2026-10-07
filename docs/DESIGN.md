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
- **Logo colors (current):** indigo `#4F46E5` → sky `#0EA5E9` gradient. See open questions.
- **Wordmark:** "Ring" + "proof" in the accent color, using the system sans-serif bold.
- The handset glyph is Material Icons "call" (Apache-2.0).

## 5. Dashboard palette and type

**Decided 2026-10-07:** the dashboard reuses the kharidwise palette, fonts and theming
(`D:\Git\kharidwise\kharidwise\plan\docs\10-design.md`). Tokens live in `web/src/index.css`.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--fg` | Deep Navy `#0A2540` | `#E6E8EB` | Text, primary buttons |
| `--bg` / `--card-bg` | `#F6F4FB` / white | `#14161A` / `#1A1D22` | Page / cards |
| `--muted`, `--line` | `#5C6B80`, `#DDE3EA` | `#9AA2AD`, `#2B2F36` | Secondary text, borders |
| `--accent` | `#0077B6` | `#00B0FF` | Links |
| `--accent-green` | AI Green `#00C853` | same | Fills and badges only, never small text (fails contrast on white) |
| `--accent-cyan` | Cyan `#00B0FF` | same | Highlights, hovers |
| `--accent-lavender`, `--note-bg` | `#D1C4E9`, `#F3EFFA` | same, `#211F2B` | **Family memory** cards and notes |
| `--risk-low` / `--risk-medium` / `--risk-high` | `#00C853` / `#FFB300` / `#D32F2F` | high: `#EF5350` | Risk meter. Always paired with a word ("High risk") and shape, never colour alone |

- **Fonts:** Bricolage Grotesque 700–800 for headings and the risk level, Figtree 400–700 for text.
  Self-hosted in `web/public/fonts/` (SIL Open Font License), copied from kharidwise.
- **Themes:** light, dark and system via `data-theme` on `<html>`; `web/public/theme-init.js` applies
  a saved choice before paint (same as kharidwise).

## 6. Open questions

- The logo still uses the indigo → sky gradient. Recolour it to navy → cyan to match the dashboard?
