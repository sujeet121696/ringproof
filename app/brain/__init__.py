"""The brain: the pluggable model seam, ported from Resolve's brain.ts.

Every model call goes through this interface, so the provider is swappable via PROVIDER:
  PROVIDER=mock    -> deterministic keyword rules, zero cost (dashboard development)
  PROVIDER=nebius  -> Nemotron 3 Ultra on Token Factory, Nemotron 3 Super as fallback
                      (both Nebius + NVIDIA, so the demo stays within the hackathon rules)
"""

import logging
from typing import Protocol

from app.config import settings
from app.models import AssessRequest, RiskResult

log = logging.getLogger("ringproof.brain")


class Brain(Protocol):
    name: str

    async def assess(self, req: AssessRequest) -> RiskResult: ...


class WithFallback:
    """Tries the primary; any error (timeout, rate limit, bad JSON) retries once on the backup."""

    def __init__(self, primary: Brain, backup: Brain) -> None:
        self.primary = primary
        self.backup = backup
        self.name = primary.name

    async def assess(self, req: AssessRequest) -> RiskResult:
        try:
            return await self.primary.assess(req)
        except Exception as err:  # noqa: BLE001 - any failure should fall back
            log.warning("%s failed -> %s: %s", self.primary.name, self.backup.name, str(err)[:120])
            return await self.backup.assess(req)


def get_brain() -> Brain:
    from app.brain.mock import MockBrain
    from app.brain.nemotron import NemotronBrain

    choice = settings.provider.lower()
    if choice == "nebius":
        return WithFallback(
            NemotronBrain(settings.reasoning_model), NemotronBrain(settings.fallback_model)
        )
    if choice != "mock":
        log.warning('Unknown PROVIDER="%s", using mock', choice)
    return MockBrain()
