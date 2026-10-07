# Samples

Synthetic demo data. All people, numbers and the bank are fictional; no real recordings.

| File | What it is |
|---|---|
| `family.json` | Demo family memory: Maa's contacts (Rahul, Anjali) + household rules. Seeds the browser store. |
| `calls/01-digital-arrest.json` | "CBI officer" digital-arrest scam → expect **high**, hang up + 1930 |
| `calls/02-fake-rahul.json` | Fake son asks for ₹50,000 → expect **high**, code-word challenge fails |
| `calls/03-real-rahul.json` | Real son, dinner plans → expect **low**, stay quiet |
| `calls/04-real-bank.json` | Genuine bank call, no ask → expect **low** |

**Call format.** `turns[]` has `t` (seconds from call start, used for replay at call speed),
`speaker` (`caller` or `user`) and `text`. `expected` is the ground truth used to tune the
risk engine (TASKS step 15). Once audio is recorded and transcribed, the cached transcript
replaces `turns` with the same shape.
