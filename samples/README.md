# Samples

Demo data for building and testing. No real recordings. The family uses real first names (with
their consent); every other detail, including the code word, is made up. The bank is fictional.

| File | What it is | Expect |
|---|---|---|
| `family.json` | Maa's memory: Sujeet (son), Suvaani (daughter-in-law), Shivam (son), Sahni (Suvaani's sister) + household rules. Seeds the browser store. | |
| `calls/01-digital-arrest.json` | "CBI officer" digital-arrest scam | **high**, hang up + 1930 |
| `calls/02-fake-sujeet.json` | Fake son asks for ₹50,000, can't give the code word | **high**, code word fails |
| `calls/03-real-sujeet.json` | Real son, dinner plans | **low**, stay quiet |
| `calls/04-real-bank.json` | Genuine bank call, no ask | **low** |
| `calls/05-real-sujeet-small-ask.json` | Real son asks for ₹2,000 like last time, no pressure | **low/medium**, no alarm |
| `calls/06-real-suvaani.json` | Daughter-in-law asks for a Diwali recipe | **low** |
| `calls/07-fake-bank-otp.json` | Fake bank asks for an OTP (breaks a household rule) | **high** |
| `calls/08-fake-shivam-early.json` | "Shivam" asks for secrecy, cut off before any money ask | **medium** |
| `calls/09-real-sahni.json` | Sahni invites Maa to a family function | **low** |

**Call format.** `turns[]` has `t` (seconds from call start, used for replay at call speed),
`speaker` (`caller` or `user`) and `text`. `expected` is the ground truth for
`python -m scripts.eval_samples`; `score` may list several acceptable levels. `_tests` says what
edge case a call checks. Once audio is recorded and transcribed, the cached transcript replaces
`turns` with the same shape.
