"""A live call session: turns in, transcript + risk events out.

Assessments run in the background so the transcript never waits for the model. If new caller
turns arrive while one is running, they are folded into a single follow-up assessment of the
latest transcript (no queue build-up when the model is slower than the call).

Privacy (ARCHITECTURE §7): the session starts with contact names only. When the model names a
family contact, the session asks the browser for that one profile (`need_profile`); the browser
answers with a `profile` message, never including the code word. Nothing is stored after the call.

When the caller claims an organisation, an official check (app/lookup.py) runs beside the risk
checks and sends a `lookup` event; only the organisation's name is sent to the lookup.

Alerts and "Is this you?" checks go out through a Notifier (app/notify.py); a `notified` event
says whether each one was really sent, so the screen never claims a message it didn't send.
"""

import asyncio
import contextlib
import logging
import time
from collections.abc import Awaitable, Callable

from app import checks
from app.brain import Brain
from app.config import settings
from app.lookup import Lookup
from app.models import Action, AssessRequest, Contact, Profile, RiskResult, Turn
from app.notify import Notifier, NotSent, alert_message, is_this_you_message
from app.policy import decide

log = logging.getLogger("ringproof.session")

Send = Callable[[dict], Awaitable[None]]

# How long the end of a call waits for a profile it has asked the browser for.
PROFILE_WAIT_S = 3.0


class CallSession:
    def __init__(
        self,
        brain: Brain,
        send: Send,
        contacts: list[Contact],
        household_rules: list[str],
        alert_contact: str | None = None,
        lookup: Lookup | None = None,
        notifier: Notifier | None = None,
        user_called: str = "",
        alert_email: str = "",
    ) -> None:
        self.brain = brain
        self.send = send
        self.contacts = contacts
        self.household_rules = household_rules
        self.alert_contact = alert_contact
        self.lookup = lookup
        self.notifier = notifier
        self.user_called = user_called or "your family member"
        self.alert_email = alert_email
        self._check_tokens: list[str] = []
        self._looked_up: set[str] = set()  # each organisation is looked up once per call
        self._side_tasks: set[asyncio.Task] = set()
        self._issued: set[str] = set()  # each action kind is sent once per call
        self.turns: list[Turn] = []
        self.profile: Profile | None = None
        self._asked_for: str | None = None
        self._profile_arrived = asyncio.Event()
        self._task: asyncio.Task | None = None
        self._dirty = False

    async def add_turn(self, turn: Turn) -> None:
        self.turns.append(turn)
        await self.send({"type": "turn", "index": len(self.turns) - 1, "turn": turn.model_dump()})
        if turn.speaker == "caller":
            self._request_assessment()

    async def set_profile(self, profile: Profile) -> None:
        self.profile = profile
        self._profile_arrived.set()
        self._request_assessment()

    async def finish(self) -> None:
        """Wait for the last assessment so the final risk reflects the whole call.

        If a profile was requested but hasn't arrived (a short call can end before the first
        check returns), wait briefly for it so the final check uses the family memory.
        """
        while True:
            while self._task and not self._task.done():
                await self._task
            if self._asked_for and not self.profile:
                with contextlib.suppress(TimeoutError):
                    await asyncio.wait_for(self._profile_arrived.wait(), PROFILE_WAIT_S)
            if not (self._task and not self._task.done()):
                break
        if self._side_tasks:
            await asyncio.gather(*self._side_tasks)
        self._close_checks()
        await self.send({"type": "end"})

    def close(self) -> None:
        """Stop everything when the browser leaves mid-call (then finish() never runs).

        Cancels the running checks so nothing is sent to a closed socket and no model calls are
        wasted. An email already handed to the mail server still goes out (it runs in a thread).
        Safe to call after finish().
        """
        for task in [self._task, *self._side_tasks]:
            if task and not task.done():
                task.cancel()
        self._close_checks()

    def _close_checks(self) -> None:
        for token in self._check_tokens:  # answers after the call has ended go nowhere
            checks.close_check(token)
        self._check_tokens.clear()

    def _request_assessment(self) -> None:
        if self._task and not self._task.done():
            self._dirty = True
        else:
            self._task = asyncio.create_task(self._assess_loop())

    async def _assess_loop(self) -> None:
        while True:
            self._dirty = False
            upto = len(self.turns)
            req = AssessRequest(
                turns=self.turns[:upto],
                contacts=self.contacts,
                profile=self.profile,
                household_rules=self.household_rules,
            )
            start = time.perf_counter()
            try:
                result = await self.brain.assess(req)
            except Exception as err:  # noqa: BLE001 - report and keep the call running
                log.warning("assessment failed: %s", err)
                await self.send({"type": "error", "message": "Risk check failed; retrying on the next turn."})
            else:
                await self.send({
                    "type": "risk",
                    "upto": upto,
                    "ms": round((time.perf_counter() - start) * 1000),
                    "with_profile": self.profile is not None,
                    "result": result.model_dump(),
                })
                for action in decide(result, self.profile, self.contacts, self.alert_contact):
                    # The screen shows the latest instruction, so a later "be careful" must never
                    # replace a stronger one already given (e.g. a medium turn after "hang up").
                    stronger = self._issued - {"watch", "alert_guardian"}
                    if action.kind == "watch" and stronger:
                        continue
                    if action.kind not in self._issued:
                        self._issued.add(action.kind)
                        await self.send({"type": "action", "upto": upto, "action": action.model_dump()})
                        self._notify(action, result)
                if result.score != "low":
                    self._start_lookup(result.claimed_org)
                contact = result.claimed_contact
                if contact and contact != self._asked_for and (not self.profile or self.profile.id != contact):
                    self._asked_for = contact
                    await self.send({"type": "need_profile", "contact": contact})
            if not self._dirty:
                return

    def _start_lookup(self, org: str | None) -> None:
        if not (self.lookup and org) or org.lower() in self._looked_up:
            return
        self._looked_up.add(org.lower())
        self._side(self._run_lookup(org))

    async def _run_lookup(self, org: str) -> None:
        try:
            check = await self.lookup.check(org)
        except Exception as err:  # noqa: BLE001 - the call goes on without it
            log.warning("lookup failed for %r: %s", org, err)
            await self.send({"type": "lookup", "ok": False, "result": {"org": org, "sources": []}})
        else:
            await self.send({"type": "lookup", "ok": True, "result": check.model_dump()})

    # --- Notifications (alert + "Is this you?") --------------------------------------------------

    def _side(self, coro) -> None:
        task = asyncio.create_task(coro)
        self._side_tasks.add(task)
        task.add_done_callback(self._side_tasks.discard)

    def _notify(self, action: Action, result: RiskResult) -> None:
        if not self.notifier:
            return
        if action.kind == "alert_guardian":
            claim = (self.profile.name if self.profile and result.claimed_contact == self.profile.id
                     else result.claimed_org or "someone unknown")
            subject, body = alert_message(self.user_called, claim, result.rationale)
            self._side(self._deliver(action, self.alert_email, subject, body))
        elif action.kind == "is_this_you_check" and self.profile:
            profile = self.profile
            token = checks.open_check(lambda yes: self._on_check_answer(profile.id, yes))
            self._check_tokens.append(token)
            link = f"{settings.public_base_url.rstrip('/')}/api/check/{token}"
            subject, body = is_this_you_message(profile.addresses_user_as or self.user_called, profile.name, link)
            self._side(self._deliver(action, profile.email, subject, body))

    async def _deliver(self, action: Action, to: str, subject: str, body: str) -> None:
        event = {"type": "notified", "kind": action.kind, "target": action.target, "channel": self.notifier.name}
        try:
            await self.notifier.send(to, subject, body)
        except NotSent as err:
            await self.send({**event, "ok": False, "reason": str(err)})
        except Exception:  # noqa: BLE001 - an unexpected failure must not end the call
            log.exception("%s via %s failed", action.kind, self.notifier.name)
            await self.send({**event, "ok": False, "reason": "sending failed"})
        else:
            await self.send({**event, "ok": True, "reason": None})

    async def _on_check_answer(self, contact: str, yes: bool) -> None:
        # Runs in the answer page's request: if the call has just closed, the person who tapped
        # still gets the thank-you page instead of an error.
        try:
            await self.send({"type": "check_answer", "target": contact, "answer": "yes" if yes else "no"})
        except Exception:  # noqa: BLE001
            log.warning("check answer arrived as the call closed")
