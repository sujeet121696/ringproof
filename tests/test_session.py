"""CallSession (app/session.py): event flow, profile hand-off and one-time actions."""

import asyncio

from app.models import AssessRequest, Contact, Profile, RiskResult, Turn
from app.session import CallSession

SUJEET = Profile(id="sujeet", name="Sujeet", relation="son", addresses_user_as="Maa", has_code_word=True)
CONTACTS = [Contact(id="sujeet", name="Sujeet", relation="son")]


class SlowBrain:
    """Says 'high, claims Sujeet' after a delay; records whether each check had the profile."""

    name = "slow"

    def __init__(self, delay: float) -> None:
        self.delay = delay
        self.saw_profile: list[bool] = []

    async def assess(self, req: AssessRequest) -> RiskResult:
        await asyncio.sleep(self.delay)
        self.saw_profile.append(req.profile is not None)
        return RiskResult(score="high", rationale="", claimed_contact="sujeet")


async def run_call(brain: SlowBrain, turns: list[Turn]) -> list[dict]:
    events: list[dict] = []
    session: CallSession

    async def send(ev: dict) -> None:
        events.append(ev)
        if ev["type"] == "need_profile":  # play the browser: answer a moment later
            async def reply() -> None:
                await asyncio.sleep(0.01)
                await session.set_profile(SUJEET)
            asyncio.create_task(reply())

    session = CallSession(brain, send, CONTACTS, [], alert_contact="sujeet")
    for t in turns:
        await session.add_turn(t)
    await session.finish()
    return events


def caller(text: str, t: float = 0) -> Turn:
    return Turn(t=t, speaker="caller", text=text)


def test_short_call_still_uses_the_profile_before_ending():
    # The whole call arrives before the first check returns, as at 4x replay speed.
    brain = SlowBrain(delay=0.05)
    events = asyncio.run(run_call(brain, [caller("Mummy, it's Sujeet"), caller("Send money")]))
    assert brain.saw_profile[-1] is True
    risks = [e for e in events if e["type"] == "risk"]
    assert risks[-1]["with_profile"] is True
    assert events[-1]["type"] == "end"


def test_each_action_is_sent_once():
    brain = SlowBrain(delay=0.01)
    events = asyncio.run(run_call(brain, [caller(f"line {i}") for i in range(4)]))
    kinds = [e["action"]["kind"] for e in events if e["type"] == "action"]
    assert len(kinds) == len(set(kinds))
    assert "code_word_challenge" in kinds and "alert_guardian" in kinds


def test_turns_are_never_held_back_by_slow_checks():
    brain = SlowBrain(delay=0.05)
    events = asyncio.run(run_call(brain, [caller(f"line {i}") for i in range(5)]))
    turn_positions = [i for i, e in enumerate(events) if e["type"] == "turn"]
    first_risk = next(i for i, e in enumerate(events) if e["type"] == "risk")
    assert turn_positions == list(range(5)) and first_risk > 4


def test_closing_mid_call_stops_checks_and_closes_links():
    # The browser leaves (Stop, tab closed): finish() never runs, so close() must clean up.
    from app import checks

    async def go() -> tuple[CallSession, list[str]]:
        async def send(ev: dict) -> None:
            pass

        session = CallSession(SlowBrain(delay=10), send, CONTACTS, [])
        await session.add_turn(caller("Mummy, it's Sujeet"))
        token = checks.open_check(lambda yes: session.send({}))
        session._check_tokens.append(token)
        session.close()
        await asyncio.sleep(0)  # let the cancellation land
        return session, [token]

    session, tokens = asyncio.run(go())
    assert session._task.cancelled()
    assert not checks.is_open(tokens[0])
