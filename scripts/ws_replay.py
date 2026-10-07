"""Terminal client for /ws/call: plays the browser's role and prints events as they arrive.

It holds the family memory (samples/family.json), sends contact names only, and answers
`need_profile` with that one profile, without the code word, as the dashboard will.

Usage (backend running on :8100):
  .venv/Scripts/python -m scripts.ws_replay digital-arrest --speed 2
"""

import argparse
import asyncio
import json
import time

import websockets

from scripts.eval_samples import load_family


async def main(sample_id: str, speed: float, url: str) -> None:
    contacts, profiles, rules, alert = load_family()
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({
            "type": "start",
            "sample_id": sample_id,
            "speed": speed,
            "contacts": [c.model_dump() for c in contacts],
            "household_rules": rules,
            "alert_contact": alert,
        }))
        t0 = time.perf_counter()
        async for raw in ws:
            ev = json.loads(raw)
            at = f"[{time.perf_counter() - t0:5.1f}s]"
            kind = ev["type"]
            if kind == "started":
                print(f"{at} call started: {ev['sample']['title']} ({ev['duration']}s at {speed}x)")
            elif kind == "turn":
                print(f"{at} {ev['turn']['speaker'].upper():>6}: {ev['turn']['text']}")
            elif kind == "risk":
                r = ev["result"]
                sig = ", ".join(s["type"] for s in r["signals"]) or "none"
                who = r["claimed_contact"] or r["claimed_org"] or "unknown"
                mem = " +memory" if ev["with_profile"] else ""
                print(f"{at}   >> RISK {r['score'].upper()} after turn {ev['upto']}"
                      f" ({ev['ms']} ms{mem}) | caller: {who} | signals: {sig}")
            elif kind == "need_profile":
                profile = profiles.get(ev["contact"])
                print(f"{at}   >> engine asks for {ev['contact']}'s profile -> "
                      f"{'sent (no code word)' if profile else 'unknown contact'}")
                if profile:
                    await ws.send(json.dumps({"type": "profile", "profile": profile.model_dump()}))
            elif kind == "action":
                a = ev["action"]
                print(f"{at}   ** ACTION {a['kind']}: {a['message']}")
            elif kind == "error":
                print(f"{at}   !! {ev['message']}")
            elif kind == "end":
                print(f"{at} call ended; nothing stored")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("sample_id")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--url", default="ws://localhost:8100/ws/call")
    a = ap.parse_args()
    asyncio.run(main(a.sample_id, a.speed, a.url))
