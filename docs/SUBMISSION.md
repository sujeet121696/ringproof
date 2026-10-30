# Submission kit (Oct 30)

Copy-paste text for Devpost and the script for the demo video. Every claim here matches the README
and `docs/FEEDBACK.md`; keep them in step if anything changes.

## Demo video script (≤ 3 min)

Record https://ringproof.kharidwise.com (or `npm run local`) in light mode, browser at about
1440×900. Play the calls at **2×**. Times are targets; the voiceover is what matters.

| Time | On screen | Voiceover |
|---|---|---|
| 0:00–0:20 | README problem section, or the start screen | "In India, scammers pose as CBI or police officers and keep elderly people on 'digital arrest' until they transfer money, or pretend to be a son in trouble. Citizens reported ₹22,846 crore in cyber-fraud losses in 2024. Caller ID doesn't help: the problem is a convincing voice mid-call." |
| 0:20–0:35 | Start screen | "Ringproof is a personal AI that knows your family. It follows the call turn by turn and asks: is this unusual for *this* person?" |
| 0:35–1:15 | Play **"CBI officer" digital-arrest scam** | "A 'CBI officer' calls Maa. Each caller line is scored by Nemotron 3 Ultra on Nebius. It flags impersonation, isolation, secrecy and a money demand, and the quotes that triggered them. At high risk it says: hang up, and call 1930, the official cyber-crime helpline. Tavily looks up only official government sites about the CBI, and Sujeet gets an email alert." |
| 1:15–1:55 | Play **Fake son in an "accident"** | "Now a caller says he's Sujeet, in an accident, needing ₹50,000, and don't tell Shivam. Ringproof's memory says Sujeet calls her 'Maa', not 'Mummy', and never asks for money in a hurry. So it tells Maa: ask for the family code word. The code word never leaves this device. The caller can't give it: 'This is not Sujeet. Hang up.'" |
| 1:55–2:15 | Play **Real son calling about dinner** | "When the real Sujeet calls about dinner, Ringproof stays quiet. Low risk, nothing needed." |
| 2:15–2:35 | **Family memory** tab | "The family memory lives only in this browser. Maa's family can see it, edit it, or delete everything in one tap. Calls are never stored." |
| 2:35–3:00 | README "Built with" table | "Under the hood: Nemotron 3 Ultra on Nebius Token Factory scores every turn, with Nemotron 3 Super as a backup. A policy table in code, not the model, picks the action. Speech-to-text with NVIDIA Parakeet and Sortformer is built for a Nebius GPU and is the next step. Ringproof: is this really your son, and is this how he talks?" |

## Devpost fields

**Name:** Ringproof

**Tagline:** A personal AI that knows your family and stops "digital arrest" and fake-relative scams mid-call.

**Inspiration**
"Digital arrest" scams target elderly parents in India: a fake CBI or police officer keeps them on
the call, orders secrecy and demands a transfer. Another pattern is a "son" in an accident who
needs money now. Citizens reported ₹22,846 crore in cyber-fraud losses in 2024 (MHA, in
Parliament). Caller ID and spam filters know nothing about your family, so they can't tell that
your son would never call you "Mummy" or ask you to keep secrets.

**What it does**
Ringproof follows a call turn by turn and scores each caller line against a private memory of the
family: who each person is, how they talk, what they usually ask for, and household rules ("real
police never arrest anyone over a phone call"). When a call is unusual for that person, it acts:
- an official caller (CBI, bank) gets "hang up, call 1930", with official pages found by Tavily;
- a family member gets a code-word challenge, checked in the browser (the code word never leaves
  the device), or an "Is this you?" email to the real person, whose Yes/No reaches the live call;
- a trusted contact gets an email alert.
Real calls stay quiet. The memory lives in the browser and can be viewed, edited or deleted;
calls are never stored.

**How we built it**
- Nemotron 3 Ultra on Nebius Token Factory scores every caller turn (JSON: score, signals with the
  triggering quote, claimed contact or organisation). Nemotron 3 Super is the backup, then keyword
  rules; the screen says when a backup answered.
- A policy table in code maps signals and caller type to the action, so the model never picks it.
- Tavily search restricted to official domains; helpline numbers only from a verified table.
- FastAPI backend streaming transcript, risk and action events over a WebSocket; React + Vite
  dashboard, installable as a PWA; family memory in IndexedDB.
- Speech-to-text service with NVIDIA Parakeet + Sortformer, and Terraform for a Nebius L40S GPU.
- 10 scripted sample calls (5 scams, 5 real) with expected results written before running: on
  Oct 30 Nemotron 3 Ultra got 10/10, and on all 10 the risk rose at the right turn.

**Challenges**
Hidden reasoning tokens counted against `max_tokens` and cut off the JSON until we raised it.
Keeping real family calls quiet mattered as much as catching scams, so every sample has an
expected level after each turn. Speech-to-text needs a GPU outside Token Factory, and we did not
get it running before the deadline.

**Accomplishments**
Real calls never told to hang up; scams flagged at the money, OTP or "officer" demand. A family
member can confirm or deny a caller from an email link while the call is live.

**What we learned**
The largest model (Nemotron 3 Ultra) was also the fastest on our task, so a small-model-first
cascade didn't pay off. Family context makes the difference between "sounds like a scam" and
"this isn't how Sujeet talks".

**What's next**
Run Parakeet on a Nebius GPU for live audio, Hindi/Hinglish, and a guardian agent on a real phone
line (`docs/VISION.md`).

**Built with:** nvidia-nemotron, nebius-token-factory, nebius-ai-cloud, tavily, python, fastapi,
react, vite, typescript, indexeddb, terraform, nvidia-nemo

**Links:** repo https://github.com/sujeet121696/ringproof · demo https://ringproof.kharidwise.com ·
feedback in `docs/FEEDBACK.md` (paste into the feedback field)

## Before pressing Submit

- [ ] Repo public (it was private on Oct 30)
- [ ] Cloudflare Access app for `ringproof` removed; demo opens in a private window without login
- [ ] PC and tunnel stay on until judging ends (`npm run local:tunnel`)
- [x] Video uploaded: https://www.youtube.com/watch?v=ZgwzwPnLL_w (2:46, unlisted), link in the README
- [ ] Track: Personal AI; Best Use of Tavily if the form asks
- [ ] Feedback pasted from `docs/FEEDBACK.md`
