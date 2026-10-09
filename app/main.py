import asyncio
import contextlib
import json
from typing import Literal

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, ValidationError

from app import checks
from app.brain import get_brain
from app.calls import SAMPLES as CALLS, ReplaySource, list_samples, load_sample
from app.config import settings
from app.lookup import get_lookup
from app.notify import get_notifier
from app.models import Contact, Profile, Turn
from app.session import CallSession
from app.web import DIST, SECURITY_HEADERS, DashboardFiles

SAMPLES = CALLS.parent

# Calls running now, capped by MAX_LIVE_CALLS (one server process; a shared counter when scaled).
_live_calls = 0

app = FastAPI(title="Ringproof")


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers.update(SECURITY_HEADERS)
    return response


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "provider": settings.provider}


@app.get("/api/samples")
def samples() -> list[dict[str, str]]:
    return [{"id": c["id"], "title": c["title"]} for c in list_samples()]


@app.get("/api/samples/{sample_id}")
def sample(sample_id: str) -> dict:
    call = load_sample(sample_id)
    if not call:
        raise HTTPException(404, f"no sample {sample_id!r}")
    return call


@app.get("/api/seed/family")
def seed_family() -> dict:
    """Demo family, fetched once by the browser to seed its local memory. The server keeps no
    memory of its own; after seeding, the browser's copy is the only one that is used."""
    return json.loads((SAMPLES / "family.json").read_text(encoding="utf-8"))


# --- "Is this you?" answer page (the link in the email) ------------------------------------------
# GET only shows the question; the answer needs a button press (POST), so a mail scanner that
# opens links can't answer by accident.

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Ringproof check</title>
<style>body{{margin:0;font-family:system-ui,sans-serif;background:#f6f4fb;color:#0a2540}}
main{{max-width:420px;margin:12vh auto;padding:24px 16px;text-align:center}}
h1{{font-size:1.4rem}}.row{{display:flex;gap:12px;justify-content:center;margin-top:24px}}form{{margin:0}}
button{{font:inherit;font-weight:700;padding:12px 28px;border-radius:999px;border:0;cursor:pointer}}
.yes{{background:#0a2540;color:#fff}}.no{{background:#d32f2f;color:#fff}}</style></head>
<body><main><h1>{title}</h1><p>{text}</p>{form}</main></body></html>"""


@app.get("/api/check/{token}", response_class=HTMLResponse)
def check_page(token: str) -> str:
    if not checks.is_open(token):
        return PAGE.format(title="This check has closed", text="The call has ended or was already answered.", form="")
    form = (f'<div class="row"><form method="post" action="/api/check/{token}/yes">'
            '<button class="yes">Yes, it&#39;s me</button></form>'
            f'<form method="post" action="/api/check/{token}/no">'
            '<button class="no">No, it&#39;s not me</button></form></div>')
    return PAGE.format(title="Are you on the phone right now?", text="Someone on a call says they are you.", form=form)


@app.post("/api/check/{token}/{answer}", response_class=HTMLResponse)
async def check_answer(token: str, answer: Literal["yes", "no"]) -> str:
    if not await checks.answer(token, answer == "yes"):
        return PAGE.format(title="This check has closed", text="The call has ended or was already answered.", form="")
    return PAGE.format(title="Thank you", text="Ringproof has passed on your answer.", form="")


class StartCall(BaseModel):
    type: str = "start"
    sample_id: str
    # Bounded: a tiny speed would hold one of the MAX_LIVE_CALLS slots for hours.
    speed: float = Field(1.0, ge=0.1, le=4.0)
    contacts: list[Contact] = []
    household_rules: list[str] = []
    alert_contact: str | None = None
    alert_email: str = ""  # only the alert contact's email, to send the alert
    user_called: str = ""  # what the family calls the user ("Maa"), used in the emails


@app.websocket("/ws/call")
async def call(ws: WebSocket) -> None:
    """Replay a sample call live. Protocol: ARCHITECTURE §11."""
    global _live_calls
    await ws.accept()
    try:
        start = StartCall.model_validate(await ws.receive_json())
    except (ValidationError, ValueError):
        await ws.close(code=1003, reason="first message must be a valid 'start'")
        return
    sample_call = load_sample(start.sample_id)
    if not sample_call:
        await ws.close(code=1003, reason=f"no sample {start.sample_id!r}")
        return
    turns = [Turn(**t) for t in sample_call["turns"]]
    session = CallSession(
        get_brain(), ws.send_json, start.contacts, start.household_rules, start.alert_contact,
        lookup=get_lookup(), notifier=get_notifier(),
        user_called=start.user_called, alert_email=start.alert_email,
    )
    # Check and count with no await in between (so calls arriving together can't pass the cap),
    # and nothing that can fail between the count and the try/finally that undoes it.
    if _live_calls >= settings.max_live_calls:
        await ws.close(code=1013, reason="Ringproof is busy. Please try again in a minute.")
        return
    _live_calls += 1

    async def receive() -> None:
        while True:
            msg = await ws.receive_json()
            if msg.get("type") == "profile":
                # Unknown fields (e.g. a code word sent by mistake) are dropped by the model.
                with contextlib.suppress(ValidationError, KeyError):
                    await session.set_profile(Profile.model_validate(msg["profile"]))

    receiver = asyncio.create_task(receive())
    try:
        await ws.send_json({
            "type": "started",
            "sample": {"id": sample_call["id"], "title": sample_call["title"]},
            "duration": turns[-1].t if turns else 0,
        })
        async for turn in ReplaySource(turns, start.speed).turns():
            await session.add_turn(turn)
        await session.finish()
    except WebSocketDisconnect:
        return
    finally:
        _live_calls -= 1  # every path out of the call, including errors and disconnects
        session.close()
        receiver.cancel()
        with contextlib.suppress(asyncio.CancelledError, WebSocketDisconnect):
            await receiver
    with contextlib.suppress(RuntimeError):
        await ws.close()


# Last, so every API and WebSocket route above wins. Only when the dashboard has been built
# (`npm run build`); in development Vite serves it on its own port.
if DIST.is_dir():
    app.mount("/", DashboardFiles(directory=DIST, html=True), name="dashboard")
