"""Policy: risk result + who the caller claims to be -> actions. Plain code, never the model.

The same inputs always give the same actions, so the agent is predictable and testable.

| Risk   | Caller claims to be           | Actions                                      |
|--------|-------------------------------|----------------------------------------------|
| low    | anyone                        | none                                         |
| medium | anyone                        | watch                                        |
| high   | family, with a code word      | code_word_challenge + alert_guardian         |
| high   | family, without a code word   | is_this_you_check + alert_guardian           |
| high   | an organisation, or unknown   | hang_up_helpline + alert_guardian            |

A high-risk claim to be a family contact whose profile hasn't arrived yet (it follows within a
second or two) gets only `watch`, so the user is never told "hang up" and then "ask the code word".
"""

from app.models import Action, Contact, Profile, RiskResult

# Verified Oct 6 on cybercrime.gov.in and i4c.mha.gov.in (Ministry of Home Affairs).
NATIONAL_HELPLINE = {
    "name": "National Cyber Crime Helpline",
    "number": "1930",
    "source": "https://cybercrime.gov.in",
}

WATCH = Action(kind="watch", message="Be careful. Do not send money or share any OTP on this call.")


def decide(
    result: RiskResult,
    profile: Profile | None,
    contacts: list[Contact],
    alert_contact: str | None,
) -> list[Action]:
    if result.score == "low":
        return []
    if result.score == "medium":
        return [WATCH]

    names = {c.id: c.name for c in contacts}
    family = profile if profile and profile.id == result.claimed_contact else None
    if result.claimed_contact in names and not family:
        return [WATCH]

    actions: list[Action] = []

    if family and family.has_code_word:
        actions.append(Action(
            kind="code_word_challenge",
            target=family.id,
            message=f"This caller says they are {family.name}. Ask them for your family code word.",
        ))
    elif family:
        actions.append(Action(
            kind="is_this_you_check",
            target=family.id,
            message=f"We are checking with the real {family.name}. Do not send anything until they confirm.",
        ))
    else:
        who = f"Callers from {result.claimed_org}" if result.claimed_org else "Genuine callers"
        actions.append(Action(
            kind="hang_up_helpline",
            helpline=NATIONAL_HELPLINE,
            message=(
                f"This looks like a scam. {who} never ask for this on a call. "
                f"Hang up now. If you are worried, call {NATIONAL_HELPLINE['number']}."
            ),
        ))

    if alert_contact:
        actions.append(Action(
            kind="alert_guardian",
            target=alert_contact,
            message=f"{names.get(alert_contact, 'Your trusted contact')} has been told about this call.",
        ))
    return actions
