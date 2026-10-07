"""Nemotron on Nebius Token Factory (OpenAI-compatible chat completions)."""

import httpx

from app.config import settings
from app.models import AssessRequest, RiskResult
from app.risk import build_messages, parse_result


class NemotronBrain:
    def __init__(self, model: str) -> None:
        self.model = model
        self.name = model.split("/")[-1]

    async def assess(self, req: AssessRequest) -> RiskResult:
        if not settings.nebius_api_key:
            raise RuntimeError("NEBIUS_API_KEY is not set")
        async with httpx.AsyncClient(timeout=settings.model_timeout_s) as client:
            resp = await client.post(
                f"{settings.nebius_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.nebius_api_key}"},
                json={
                    "model": self.model,
                    "messages": build_messages(req),
                    "temperature": 0,
                    # Hidden reasoning counts against this limit; 1500 sometimes cut the
                    # answer off before the JSON (Oct 7).
                    "max_tokens": 4000,
                    "response_format": {"type": "json_object"},
                },
            )
            resp.raise_for_status()
        choice = resp.json()["choices"][0]
        try:
            return parse_result(choice["message"].get("content") or "")
        except ValueError as err:
            raise ValueError(f"{err} (finish_reason={choice.get('finish_reason')})") from err
