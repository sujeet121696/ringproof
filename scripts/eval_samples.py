"""Run every sample call through the risk engine and compare with its expected result.

Mirrors the real flow (ARCHITECTURE §7): pass 1 sends contact names only; if the model names a
family contact, pass 2 adds that contact's profile (never the code word).

Usage (from the repo root):
  .venv/Scripts/python -m scripts.eval_samples            # uses PROVIDER from .env
  set PROVIDER=mock && .venv/Scripts/python -m scripts.eval_samples
  .venv/Scripts/python -m scripts.eval_samples fake-shivam-early --repeat 3   # one sample, 3 times
"""

import argparse
import asyncio
import json
import time
from pathlib import Path

from app.brain import get_brain
from app.models import AssessRequest, Contact, Profile, Turn
from app.policy import decide

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def load_family() -> tuple[list[Contact], dict[str, Profile], list[str], str | None]:
    family = json.loads((SAMPLES / "family.json").read_text(encoding="utf-8"))
    contacts, profiles = [], {}
    for c in family["contacts"]:
        contacts.append(Contact(id=c["id"], name=c["name"], relation=c["relation"]))
        profiles[c["id"]] = Profile(
            id=c["id"],
            name=c["name"],
            relation=c["relation"],
            addresses_user_as=c["addresses_user_as"],
            usual_topics=c["usual_topics"],
            never=c["never"],
            past_requests=[f'{r["date"]}: {r["what"]}' for r in c["past_requests"]],
            has_code_word=bool(c.get("code_word")),
            email=c.get("email", ""),
        )
    return contacts, profiles, family["household_rules"], family.get("alert_contact")


def primary_action(result, profile, contacts, alert) -> str:
    """The first action the policy takes ("none" for a quiet call), to compare with `expected`."""
    actions = decide(result, profile, contacts, alert)
    return actions[0].kind if actions else "none"


async def main(only: list[str], repeat: int) -> None:
    brain = get_brain()
    contacts, profiles, rules, alert = load_family()
    print(f"Brain: {brain.name}\n")
    passed = 0
    calls = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((SAMPLES / "calls").glob("*.json"))]
    calls = [c for c in calls if not only or c["id"] in only] * repeat
    for call in calls:
        exp = call["expected"]
        req = AssessRequest(
            turns=[Turn(**t) for t in call["turns"]], contacts=contacts, household_rules=rules
        )
        start = time.perf_counter()
        result = await brain.assess(req)
        if result.claimed_contact in profiles:
            req.profile = profiles[result.claimed_contact]
            result = await brain.assess(req)
        secs = time.perf_counter() - start

        got = {s.type for s in result.signals}
        want = set(exp["signals"])
        # `score` may list several acceptable levels, e.g. ["low", "medium"].
        ok_scores = exp["score"] if isinstance(exp["score"], list) else [exp["score"]]
        checks = {
            "score": result.score in ok_scores,
            "contact": result.claimed_contact == exp["claimed_contact"],
            "org": (result.claimed_org or "").lower() == (exp["claimed_org"] or "").lower(),
            "signals": want <= got,
            "action": primary_action(result, req.profile, contacts, alert) == exp["action"],
        }
        ok = all(checks.values())
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {call['id']:<15} {secs:5.1f}s  {result.checked_by}")
        print(f"      score {result.score} (want {exp['score']})"
              f" | contact {result.claimed_contact} (want {exp['claimed_contact']})"
              f" | org {result.claimed_org} (want {exp['claimed_org']})")
        print(f"      action {primary_action(result, req.profile, contacts, alert)} (want {exp['action']})")
        print(f"      signals {sorted(got)}")
        if want - got:
            print(f"      missing {sorted(want - got)}")
        if got - want:
            print(f"      extra   {sorted(got - want)}")
        print(f"      why: {result.rationale}\n")
    print(f"{passed}/{len(calls)} passed")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("only", nargs="*", help="sample ids to run (default: all)")
    ap.add_argument("--repeat", type=int, default=1)
    a = ap.parse_args()
    asyncio.run(main(a.only, a.repeat))
