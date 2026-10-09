"""Open "Is this you?" checks: a random token in the emailed link -> the live call waiting for it.

In memory, so it works with one server process. Several servers would need a shared store
(e.g. Redis with pub/sub) so the answer reaches whichever server holds the call (VISION §6).
"""

import secrets
from collections.abc import Awaitable, Callable

OnAnswer = Callable[[bool], Awaitable[None]]

_open: dict[str, OnAnswer] = {}


def open_check(on_answer: OnAnswer) -> str:
    token = secrets.token_urlsafe(16)
    _open[token] = on_answer
    return token


def close_check(token: str) -> None:
    _open.pop(token, None)


def is_open(token: str) -> bool:
    return token in _open


async def answer(token: str, yes: bool) -> bool:
    """Deliver the answer once. False if the check is unknown, already answered or the call ended."""
    on_answer = _open.pop(token, None)
    if on_answer is None:
        return False
    await on_answer(yes)
    return True
