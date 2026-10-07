"""A live call session: turns in, transcript + risk events out.

Assessments run in the background so the transcript never waits for the model. If new caller
turns arrive while one is running, they are folded into a single follow-up assessment of the
latest transcript (no queue build-up when the model is slower than the call).

Privacy (ARCHITECTURE §7): the session starts with contact names only. When the model names a
family contact, the session asks the browser for that one profile (`need_profile`); the browser
answers with a `profile` message, never including the code word. Nothing is stored after the call.
"""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable

from app.brain import Brain
from app.models import AssessRequest, Contact, Profile, Turn
from app.policy import decide

log = logging.getLogger("ringproof.session")

Send = Callable[[dict], Awaitable[None]]


class CallSession:
    def __init__(
        self,
        brain: Brain,
        send: Send,
        contacts: list[Contact],
        household_rules: list[str],
        alert_contact: str | None = None,
    ) -> None:
        self.brain = brain
        self.send = send
        self.contacts = contacts
        self.household_rules = household_rules
        self.alert_contact = alert_contact
        self._issued: set[str] = set()  # each action kind is sent once per call
        self.turns: list[Turn] = []
        self.profile: Profile | None = None
        self._asked_for: str | None = None
        self._task: asyncio.Task | None = None
        self._dirty = False

    async def add_turn(self, turn: Turn) -> None:
        self.turns.append(turn)
        await self.send({"type": "turn", "index": len(self.turns) - 1, "turn": turn.model_dump()})
        if turn.speaker == "caller":
            self._request_assessment()

    async def set_profile(self, profile: Profile) -> None:
        self.profile = profile
        self._request_assessment()

    async def finish(self) -> None:
        """Wait for the last assessment so the final risk reflects the whole call."""
        while self._task and not self._task.done():
            await self._task
        await self.send({"type": "end"})

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
                    if action.kind not in self._issued:
                        self._issued.add(action.kind)
                        await self.send({"type": "action", "upto": upto, "action": action.model_dump()})
                contact = result.claimed_contact
                if contact and contact != self._asked_for and (not self.profile or self.profile.id != contact):
                    self._asked_for = contact
                    await self.send({"type": "need_profile", "contact": contact})
            if not self._dirty:
                return
