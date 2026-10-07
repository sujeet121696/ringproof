import asyncio
import contextlib

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError

from app.brain import get_brain
from app.calls import ReplaySource, list_samples, load_sample
from app.config import settings
from app.models import AssessRequest, Contact, Profile, RiskResult, Turn
from app.session import CallSession

app = FastAPI(title="Ringproof")


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


@app.post("/api/assess")
async def assess(req: AssessRequest) -> RiskResult:
    return await get_brain().assess(req)


class StartCall(BaseModel):
    type: str = "start"
    sample_id: str
    speed: float = 1.0
    contacts: list[Contact] = []
    household_rules: list[str] = []
    alert_contact: str | None = None


@app.websocket("/ws/call")
async def call(ws: WebSocket) -> None:
    """Replay a sample call live. Protocol: ARCHITECTURE §11."""
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

    session = CallSession(
        get_brain(), ws.send_json, start.contacts, start.household_rules, start.alert_contact
    )
    turns = [Turn(**t) for t in sample_call["turns"]]
    await ws.send_json({
        "type": "started",
        "sample": {"id": sample_call["id"], "title": sample_call["title"]},
        "duration": turns[-1].t if turns else 0,
    })

    async def receive() -> None:
        while True:
            msg = await ws.receive_json()
            if msg.get("type") == "profile":
                # Unknown fields (e.g. a code word sent by mistake) are dropped by the model.
                with contextlib.suppress(ValidationError, KeyError):
                    await session.set_profile(Profile.model_validate(msg["profile"]))

    receiver = asyncio.create_task(receive())
    try:
        async for turn in ReplaySource(turns, start.speed).turns():
            await session.add_turn(turn)
        await session.finish()
    except WebSocketDisconnect:
        return
    finally:
        receiver.cancel()
        with contextlib.suppress(asyncio.CancelledError, WebSocketDisconnect):
            await receiver
    with contextlib.suppress(RuntimeError):
        await ws.close()
