"""Official check (app/lookup.py) and how a call session uses it."""

import asyncio

from app.lookup import OrgCheck, Source, clean_snippet, is_official
from app.models import AssessRequest, RiskResult, Turn
from app.session import CallSession


def test_only_official_domains_pass():
    assert is_official("https://cybercrime.gov.in/")
    assert is_official("https://nhrc.nic.in/media/press-release/x")
    assert is_official("https://www.rbi.org.in/scripts/x.aspx")
    assert not is_official("https://gov.in.example.com/")      # suffix trick
    assert not is_official("https://fakegov.in/")              # no dot before the suffix
    assert not is_official("https://cbi-helpline.com/")
    assert not is_official("javascript://cybercrime.gov.in/%0Aalert(1)")  # becomes a link on screen


def test_snippet_is_cleaned_and_cut_at_a_word():
    s = clean_snippet("Scammers   pose\nas officers. " + "word " * 100)
    assert "  " not in s and "\n" not in s
    assert s.endswith("…") and len(s) <= 221
    assert clean_snippet("## PRESS RELEASE - **Advisory** on Fraud Calls") == "PRESS RELEASE - Advisory on Fraud Calls"
    assert clean_snippet("Search Media & Press Home › Media & Press › PRESS RELEASE - Advisory") == "PRESS RELEASE - Advisory"
    mid = "Scammers pose as officers and ask for money on video calls. See Home › Advisories"
    assert clean_snippet(mid) == mid  # only a leading breadcrumb is removed, never real text


class OrgBrain:
    """Claims the CBI at a fixed score."""

    name = "org"

    def __init__(self, score: str) -> None:
        self.score = score

    async def assess(self, req: AssessRequest) -> RiskResult:
        return RiskResult(score=self.score, rationale="", claimed_org="CBI")


class FakeLookup:
    name = "fake"

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.asked: list[str] = []

    async def check(self, org: str) -> OrgCheck:
        self.asked.append(org)
        if self.fail:
            raise RuntimeError("search down")
        return OrgCheck(org=org, sources=[Source(title="Advisory", url="https://cybercrime.gov.in/", snippet="")])


def run(score: str, lookup: FakeLookup) -> list[dict]:
    events: list[dict] = []

    async def send(ev: dict) -> None:
        events.append(ev)

    async def go() -> None:
        session = CallSession(OrgBrain(score), send, [], [], lookup=lookup)
        for text in ["This is the CBI", "You are under arrest", "Transfer the money"]:
            await session.add_turn(Turn(t=0, speaker="caller", text=text))
            await asyncio.sleep(0)
        await session.finish()

    asyncio.run(go())
    return events


def test_org_is_looked_up_once_and_before_the_call_ends():
    lookup = FakeLookup()
    events = run("high", lookup)
    assert lookup.asked == ["CBI"]
    found = [e for e in events if e["type"] == "lookup"]
    assert len(found) == 1 and found[0]["ok"] is True
    assert events.index(found[0]) < len(events) - 1 and events[-1]["type"] == "end"


def test_low_risk_calls_are_not_looked_up():
    lookup = FakeLookup()
    events = run("low", lookup)
    assert lookup.asked == [] and not [e for e in events if e["type"] == "lookup"]


def test_a_failed_lookup_is_reported_and_the_call_goes_on():
    events = run("high", FakeLookup(fail=True))
    found = [e for e in events if e["type"] == "lookup"]
    assert found and found[0]["ok"] is False
    assert events[-1]["type"] == "end"
