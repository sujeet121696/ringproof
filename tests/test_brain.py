"""Brain fallback chain (app/brain/__init__.py): Ultra -> Super -> keyword rules."""

import asyncio

import pytest

from app.brain import FallbackChain, get_brain
from app.config import settings
from app.models import AssessRequest, Contact, RiskResult, Turn

SCAM = AssessRequest(
    turns=[Turn(t=0, speaker="caller", text="This is the CBI. Transfer the money right now and don't tell anyone.")],
    contacts=[Contact(id="sujeet", name="Sujeet", relation="son")],
)


class Down:
    def __init__(self, name: str) -> None:
        self.name = name
        self.calls = 0

    async def assess(self, req: AssessRequest) -> RiskResult:
        self.calls += 1
        raise RuntimeError("503 Service Unavailable")


class Up:
    def __init__(self, name: str) -> None:
        self.name = name

    async def assess(self, req: AssessRequest) -> RiskResult:
        return RiskResult(score="high", rationale="ok")


def assess(brain) -> RiskResult:
    return asyncio.run(brain.assess(SCAM))


def test_primary_answers_when_up():
    result = assess(FallbackChain(Up("ultra"), Up("super")))
    assert (result.checked_by, result.backup) == ("ultra", False)


def test_next_brain_answers_when_primary_is_down_and_says_so():
    ultra = Down("ultra")
    result = assess(FallbackChain(ultra, Up("super"), Up("rules")))
    assert ultra.calls == 1
    assert (result.checked_by, result.backup) == ("super", True)


def test_error_is_raised_only_when_every_brain_is_down():
    with pytest.raises(RuntimeError, match="503"):
        assess(FallbackChain(Down("ultra"), Down("super")))


def test_with_nebius_unreachable_the_keyword_rules_still_warn(monkeypatch):
    # No API key: both Nemotron calls fail before any network request, as in a full outage.
    monkeypatch.setattr(settings, "provider", "nebius")
    monkeypatch.setattr(settings, "nebius_api_key", "")
    result = assess(get_brain())
    assert (result.checked_by, result.backup) == ("keyword rules", True)
    assert result.score == "high"
