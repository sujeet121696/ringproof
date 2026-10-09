"""Turn-by-turn check: does the risk rise at the right moment as a call plays?

Drives the real CallSession (app/session.py) one turn at a time and answers `need_profile` the way
the browser does (profile without the code word). After every caller turn it waits for the check
to finish, so each turn gets its own score, then compares every risk result (including the one
before the profile arrives) with `expected.timeline` in the sample: the levels allowed after that
caller turn.

Usage (from the repo root):
  .venv/Scripts/python -m scripts.eval_timeline                 # all samples, PROVIDER from .env
  .venv/Scripts/python -m scripts.eval_timeline fake-sujeet --repeat 3
"""

import argparse
import asyncio
import json

from app.brain import get_brain
from app.models import Turn
from app.session import CallSession
from scripts.eval_samples import SAMPLES, load_family


async def idle(session: CallSession) -> None:
    """Wait until no check is running (a profile arriving can start one more)."""
    while session._task and not session._task.done():
        await session._task


async def run_call(brain, call: dict, family) -> tuple[bool, list[str]]:
    contacts, profiles, rules, alert = family
    timeline: dict[str, list[str]] = call["expected"]["timeline"]
    events: list[dict] = []
    session: CallSession

    async def send(ev: dict) -> None:
        events.append(ev)
        if ev["type"] == "need_profile" and ev["contact"] in profiles:
            await session.set_profile(profiles[ev["contact"]])

    session = CallSession(brain, send, contacts, rules, alert)
    for turn in call["turns"]:
        await session.add_turn(Turn(**turn))
        await idle(session)
    await session.finish()

    ok, lines = True, []
    for ev in events:
        if ev["type"] == "risk":
            idx = str(ev["upto"] - 1)
            score = ev["result"]["score"]
            allowed = timeline[idx]
            good = score in allowed
            ok &= good
            prof = "with profile" if ev["with_profile"] else "names only  "
            lines.append(f"  turn {idx:>2} {prof} {score:<6} {'ok ' if good else 'BAD'} (allowed {'/'.join(allowed)})"
                         f"  {ev['ms'] / 1000:.1f}s  {ev['result']['checked_by']}")
        elif ev["type"] == "action":
            lines.append(f"  turn {ev['upto'] - 1:>2} action -> {ev['action']['kind']}")
        elif ev["type"] == "error":
            ok = False
            lines.append(f"  ERROR {ev['message']}")
    return ok, lines


async def main(only: list[str], repeat: int) -> None:
    brain = get_brain()
    family = load_family()
    print(f"Brain: {brain.name}\n")
    calls = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((SAMPLES / "calls").glob("*.json"))]
    calls = [c for c in calls if not only or c["id"] in only] * repeat
    passed = 0
    for call in calls:
        ok, lines = await run_call(brain, call, family)
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {call['id']}")
        print("\n".join(lines) + "\n")
    print(f"{passed}/{len(calls)} calls rose at the right moments")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("only", nargs="*", help="sample ids to run (default: all)")
    ap.add_argument("--repeat", type=int, default=1)
    a = ap.parse_args()
    asyncio.run(main(a.only, a.repeat))
