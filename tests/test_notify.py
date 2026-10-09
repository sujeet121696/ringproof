"""Alerts and "Is this you?" checks (app/notify.py, app/checks.py) inside a call session."""

import asyncio
import re

from app import checks
from app.config import settings
from app.models import AssessRequest, Contact, Profile, RiskResult, Turn
from app.notify import NoNotifier, NotSent, delivery_address
from app.session import CallSession

SHIVAM = Profile(id="shivam", name="Shivam", relation="son", addresses_user_as="Mummy",
                 has_code_word=False, email="shivam@example.com")
CONTACTS = [Contact(id="sujeet", name="Sujeet", relation="son"), Contact(id="shivam", name="Shivam", relation="son")]


class FamilyBrain:
    """High risk, caller claims to be Shivam (no code word -> "Is this you?" check)."""

    name = "family"

    async def assess(self, req: AssessRequest) -> RiskResult:
        return RiskResult(score="high", rationale="Asks for money in secret.", claimed_contact="shivam")


class FakeNotifier:
    name = "email"

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append((to, subject, body))


def run(notifier, answer: bool | None = None) -> tuple[list[dict], list[str]]:
    events: list[dict] = []
    links: list[str] = []
    session: CallSession

    async def send(ev: dict) -> None:
        events.append(ev)
        if ev["type"] == "need_profile":
            await session.set_profile(SHIVAM)
        if ev["type"] == "notified" and ev["kind"] == "is_this_you_check" and answer is not None:
            token = links[-1].rsplit("/", 1)[1]
            await checks.answer(token, answer)  # Shivam taps the link during the call

    class Recording:
        name = notifier.name

        async def send(self, to: str, subject: str, body: str) -> None:
            links.extend(re.findall(r"http\S+", body))
            await notifier.send(to, subject, body)

    async def go() -> None:
        nonlocal session
        session = CallSession(FamilyBrain(), send, CONTACTS, [], alert_contact="sujeet",
                              notifier=Recording(), user_called="Maa", alert_email="sujeet@example.com")
        for text in ["Mummy, it's Shivam", "Send money, don't tell anyone"]:
            await session.add_turn(Turn(t=0, speaker="caller", text=text))
        await session.finish()

    asyncio.run(go())
    return events, links


def test_alert_and_check_are_emailed_and_reported_as_sent():
    notifier = FakeNotifier()
    events, links = run(notifier)
    to = {t for t, _, _ in notifier.sent}
    assert to == {"sujeet@example.com", "shivam@example.com"}
    notified = {e["kind"]: e for e in events if e["type"] == "notified"}
    assert notified["alert_guardian"]["ok"] and notified["is_this_you_check"]["ok"]
    assert links and links[0].startswith(settings.public_base_url.rstrip("/") + "/api/check/")
    alert_body = next(b for t, _, b in notifier.sent if t == "sujeet@example.com")
    assert "Maa" in alert_body and "Shivam" in alert_body
    assert events[-1]["type"] == "end"


def test_answer_reaches_the_call_and_the_link_closes_after_it_ends():
    events, links = run(FakeNotifier(), answer=False)
    answers = [e for e in events if e["type"] == "check_answer"]
    assert answers == [{"type": "check_answer", "target": "shivam", "answer": "no"}]
    token = links[-1].rsplit("/", 1)[1]
    assert not checks.is_open(token)


def test_unanswered_check_closes_when_the_call_ends():
    _, links = run(FakeNotifier())
    assert not checks.is_open(links[-1].rsplit("/", 1)[1])


def test_without_email_set_up_the_screen_is_told_it_was_not_sent():
    events, _ = run(NoNotifier())
    notified = [e for e in events if e["type"] == "notified"]
    assert notified and all(not e["ok"] and e["reason"] == "email is not set up" for e in notified)


def test_demo_addresses_are_redirected_only_when_set(monkeypatch):
    monkeypatch.setattr(settings, "email_demo_redirect_to", "")
    assert delivery_address("sujeet@example.com") == "sujeet@example.com"
    monkeypatch.setattr(settings, "email_demo_redirect_to", "me@gmail.com")
    assert delivery_address("sujeet@example.com") == "me@gmail.com"
    assert delivery_address("real@gmail.com") == "real@gmail.com"


def test_no_notifier_raises_not_sent():
    try:
        asyncio.run(NoNotifier().send("a@b.c", "s", "b"))
    except NotSent as err:
        assert str(err) == "email is not set up"
    else:
        raise AssertionError("expected NotSent")


def test_answer_page_shows_buttons_then_closes_after_one_answer():
    from fastapi.testclient import TestClient

    from app.main import app

    got: list[bool] = []

    async def on_answer(yes: bool) -> None:
        got.append(yes)

    token = checks.open_check(on_answer)
    client = TestClient(app)
    page = client.get(f"/api/check/{token}").text
    assert f"/api/check/{token}/yes" in page and f"/api/check/{token}/no" in page
    assert "Thank you" in client.post(f"/api/check/{token}/no").text
    assert got == [False]
    assert "has closed" in client.post(f"/api/check/{token}/yes").text  # only the first answer counts
    assert "has closed" in client.get(f"/api/check/{token}").text
    assert client.post(f"/api/check/{token}/maybe").status_code == 422


class BrokenNotifier:
    name = "email"

    async def send(self, to: str, subject: str, body: str) -> None:
        raise RuntimeError("unexpected")


def test_an_unexpected_send_error_is_reported_and_the_call_still_ends():
    events, _ = run(BrokenNotifier())
    notified = [e for e in events if e["type"] == "notified"]
    assert notified and all(not e["ok"] and e["reason"] == "sending failed" for e in notified)
    assert events[-1]["type"] == "end"


def test_a_line_break_in_the_address_is_not_sent(monkeypatch):
    from app.notify import EmailNotifier

    monkeypatch.setattr(settings, "smtp_user", "me@gmail.com")
    try:
        asyncio.run(EmailNotifier().send("a@b.c\nBcc: x@y.z", "s", "b"))
    except NotSent as err:
        assert str(err) == "the email address is not valid"
    else:
        raise AssertionError("expected NotSent")
