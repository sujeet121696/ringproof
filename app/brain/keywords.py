"""Deterministic keyword brain: zero API calls. Used to build the dashboard, and as the last
fallback when both Nemotron models are down (a rough warning beats none during a scam).

Deliberately simple. It is not the product; the real assessment comes from Nemotron.
"""

from app.models import AssessRequest, RiskResult, Signal, SignalType

KEYWORDS: dict[SignalType, list[str]] = {
    "urgency": ["right now", "immediately", "next thirty minutes", "no time", " now"],
    "secrecy": ["don't tell", "do not tell", "confidential"],
    "transfer_ask": ["transfer", "send it", "send the money", "upi", "lakh", "thousand", "otp", " pin"],
    "impersonation": ["cbi", "inspector", "customs", "police"],
    "isolation": ["do not disconnect", "don't disconnect", "stay on the line", "digital arrest"],
}
ORGS = ["CBI", "RBI", "customs", "police"]
# Shown on screen, so plain words (the same as the dashboard's labels in web/src/types.ts).
LABELS: dict[SignalType, str] = {
    "urgency": "urgency", "secrecy": "secrecy", "transfer_ask": "money or OTP ask",
    "impersonation": "impersonation", "isolation": "isolation", "out_of_character": "out of character",
}


class KeywordBrain:
    name = "keyword rules"

    async def assess(self, req: AssessRequest) -> RiskResult:
        caller = [t.text for t in req.turns if t.speaker == "caller"]
        signals: list[Signal] = []
        for kind, words in KEYWORDS.items():
            for line in caller:
                if any(w in line.lower() for w in words):
                    signals.append(Signal(type=kind, quote=line))
                    break

        # The first caller line naming a contact is the claim ("it's Suvaani"); names said later
        # ("don't call Sujeet") are people mentioned, not claimed.
        claimed_contact = next(
            (c.id for line in caller for c in req.contacts if c.name.lower() in line.lower()), None
        )
        claimed_org = next((o for o in ORGS if any(o.lower() in l.lower() for l in caller)), None)

        if req.profile and claimed_contact == req.profile.id:
            greeting = req.profile.addresses_user_as.lower()
            if caller and greeting not in " ".join(caller).lower():
                signals.append(Signal(type="out_of_character", quote=caller[0]))

        kinds = {s.type for s in signals}
        if "transfer_ask" in kinds and len(kinds) >= 2:
            score = "high"
        elif kinds:
            score = "medium"
        else:
            score = "low"
        return RiskResult(
            score=score,
            signals=signals,
            rationale=f"Keyword check found: {', '.join(LABELS[k] for k in sorted(kinds)) or 'nothing'}.",
            claimed_contact=claimed_contact,
            claimed_org=claimed_org,
        )
