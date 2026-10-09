# Design

> UI/UX direction for the demo dashboard.

## 1. Principles

- **Legible at a glance.** Anyone should grasp the risk level in under two seconds.
- **Show the reasoning.** Explain *why* a call is risky (signals + quoted lines), not just a number.
- **The intervention is the climax.** The challenge and alert are the most visible moment of the
  demo.
- **Memory is visible.** Show which profile was used and how the call differs from it
  ("Sujeet calls you Maa; this caller said Madam").
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
| Frame risk around *this person* ("unusual for Sujeet") when a profile exists | Memory is the differentiator; make it visible |
| The code word is shown masked (`••••`) in the UI | It's a secret |
| Demo uses sample audio, not live calls | Live telephony is out of scope (see PRD) |
| UI copy in plain English; transcripts shown in the call's language | English is primary; Hindi/Hinglish is a stretch goal (see PRD) |
| High-risk screen gives one clear instruction ("Hang up. Call 1930.") | Elderly users under pressure need one action, not a report |

## 4. Brand

**Decided 2026-10-07:** logo, favicon and app icons follow kharidwise's style and palette. All
artwork is original (drawn in `assets/build/make_svgs.py`); nothing is copied from kharidwise or
an icon set.

| Asset | File | Use |
|---|---|---|
| Logo | `assets/logo.svg` | README, demo video |
| Mark | `assets/logo-mark.svg`, `web/public/logo-mark.svg` | Dashboard header, square spots |
| Favicon | `web/public/favicon.ico` (16/32/48), `favicon.svg` | Browser tab |
| App icons | `web/public/apple-touch-icon.png`, `icons/icon-192/512/maskable-512.png`, `manifest.webmanifest` | Home-screen install, same set as kharidwise |

- **Mark:** a shield (protection) with a phone handset (the call), Deep Navy `#0A2540` → `#0077B6`
  gradient, white handset, and a green AI Green `#00C853` check badge with rays: "this call is
  checked", in the spirit of kharidwise's verified tick. The favicon drops the rays (noise at 16 px)
  and uses a smaller badge so the handset stays readable.
- **Wordmark:** "Ring" in navy + "proof" in AI Green, like "kharid" + "wise". In the logo file the
  letters are outlines from Bricolage Grotesque ExtraBold, so it renders the same everywhere. In
  the dashboard header it is live text (`Ring<b>proof</b>`), so it follows light/dark.
- Rebuild: `assets/build/README.md`.

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

## 6. Built call screen (Oct 7)

- Header: logo mark + text wordmark ("Ring" + "proof" in `--accent-green`), so it follows the app's
  light/dark choice; tabs Call / Family memory; Auto / Light / Dark.
- Call view: sample picker, speed, Play. Transcript left (caller lines with a red edge and signal
  tags when flagged). Right column top to bottom: Risk (3-segment meter, level word, rationale,
  "checking…" while a check runs), What to do (the climax), Caller (claimed person + their memory,
  code word masked, the out-of-character quote), Official check (1930 + source), Warning signs
  (all six, lit with quotes). On phones the right column comes first.
- Memory view (Oct 8): privacy note on top (lavender), About you, one card per contact (Edit opens
  an inline form, code word masked with Show; Delete asks inline, no browser pop-ups), household
  rules (add/remove), who to alert, and Your data (Delete all memory with an inline confirm, Load
  demo family). Every edit saves to IndexedDB at once. Delete-all is one overwrite with an empty
  record, so a reload can't bring the demo family back.
- Install (Oct 8): an "Install app" button in the header, shown only when the browser can install
  (Chrome/Edge/Android) or on iPhone (tap shows "Share → Add to Home Screen"); hidden once
  installed. Opens full-screen without browser bars (`display: standalone`).

## 7. Open questions

- None right now.
