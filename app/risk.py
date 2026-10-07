"""Risk engine prompt: builds the model input and parses its answer.

The model only assesses (signals, rationale, who the caller claims to be). Which action to take
is decided later by the policy in code, never here.
"""

import json
import re

from app.models import AssessRequest, RiskResult

SYSTEM_PROMPT = """You protect an elderly person in India from phone scams. You read a live call
transcript and judge how risky it is FOR THIS PERSON, using their private family memory.

Reply with one JSON object and nothing else:
{"score": "low" | "medium" | "high",
 "signals": [{"type": <signal>, "quote": <the caller's exact words>}],
 "rationale": <one or two plain sentences>,
 "claimed_contact": <contact id or null>,
 "claimed_org": <organisation name or null>}

Signals (only from the CALLER's words, each with a short exact quote):
- urgency: pressure to act now, deadlines, threats of what happens if they wait.
- secrecy: told not to tell family or anyone.
- transfer_ask: asked to send money, UPI, gift cards, crypto, or share an OTP, PIN or password.
- impersonation: claims to be an authority (police, CBI, customs, RBI, courier, bank) or a family
  member AND makes demands such a person would not make on a call.
- isolation: told to stay on the call, not disconnect, or that they are under "digital arrest".
- out_of_character: ONLY when a profile is given. The caller differs from what memory says about
  that person (how they address the user, what they ask for, what they never do). Never use it
  without a profile.

Fields:
- claimed_contact: the id of a family contact from the list ONLY if the caller says they are that
  person. Officials, companies and strangers are never contacts; use null.
- claimed_org: the organisation the caller says they ARE calling from or acting for (e.g. "This is
  the CBI", "calling from your bank"). Use the most senior one if several callers speak for
  organisations. An organisation the caller only MENTIONS ("the police say I must pay") is not
  claimed_org. If the caller claims to be a family contact, claimed_org is null.

Scoring:
- high: a transfer_ask combined with any of urgency, secrecy, isolation or impersonation; or any
  household rule is broken; or out_of_character together with a money ask.
- medium: some pressure signals but no ask yet, or something unusual worth watching.
- low: an ordinary call. Warnings like "we will never ask for your OTP" are NOT a risk; they are
  what genuine organisations say. Do not list signals for a low call unless they are real.
"""


def build_messages(req: AssessRequest) -> list[dict[str, str]]:
    parts: list[str] = []
    if req.contacts:
        parts.append("Family contacts (id: name, relation):")
        parts += [f"- {c.id}: {c.name}, {c.relation}" for c in req.contacts]
    if req.household_rules:
        parts.append("\nHousehold rules (true for every call):")
        parts += [f"- {r}" for r in req.household_rules]
    if req.profile:
        p = req.profile
        parts.append(f"\nProfile of the claimed caller ({p.id}):")
        parts.append(f"- {p.name}, {p.relation}; calls the user \"{p.addresses_user_as}\"")
        if p.usual_topics:
            parts.append(f"- Usually talks about: {', '.join(p.usual_topics)}")
        if p.never:
            parts.append(f"- Never: {'; '.join(p.never)}")
        if p.past_requests:
            parts.append(f"- Past requests: {'; '.join(p.past_requests)}")
    parts.append("\nTranscript so far:")
    parts += [f"{t.speaker.upper()}: {t.text}" for t in req.turns]
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(parts)},
    ]


def parse_result(text: str) -> RiskResult:
    """Parse the model's JSON, tolerating stray text around it. Raises ValueError if unusable."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"no JSON object in model output: {text[:200]!r}")
    return RiskResult.model_validate(json.loads(match.group(0)))
