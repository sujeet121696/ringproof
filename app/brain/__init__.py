"""The brain: the pluggable model seam, ported from Resolve's brain.ts.

Every model call goes through this interface, so the provider is swappable via PROVIDER:
  PROVIDER=mock    -> deterministic keyword rules, zero cost (dashboard development)
  PROVIDER=nebius  -> Nemotron 3 Ultra on Token Factory, then Nemotron 3 Super, then the keyword
                      rules as a last resort (both models are Nebius + NVIDIA, so the demo stays
                      within the hackathon rules; the rules only answer when both are down)

Each result says which brain answered (`checked_by`), so the screen can say when a backup is used.
"""

import logging
from typing import Protocol

from app.config import settings
from app.models import AssessRequest, RiskResult

log = logging.getLogger("ringproof.brain")


class Brain(Protocol):
    name: str

    async def assess(self, req: AssessRequest) -> RiskResult: ...


class FallbackChain:
    """Tries each brain in order; any error (timeout, rate limit, bad JSON) moves to the next."""

    def __init__(self, *brains: Brain) -> None:
        self.brains = brains
        self.name = " -> ".join(b.name for b in brains)

    async def assess(self, req: AssessRequest) -> RiskResult:
        for i, brain in enumerate(self.brains):
            try:
                result = await brain.assess(req)
            except Exception as err:  # noqa: BLE001 - any failure should fall back
                if i == len(self.brains) - 1:
                    raise
                log.warning("%s failed -> %s: %s", brain.name, self.brains[i + 1].name, str(err)[:120])
            else:
                return result.model_copy(update={"checked_by": brain.name, "backup": i > 0})
        raise RuntimeError("no brains configured")


def get_brain() -> Brain:
    from app.brain.keywords import KeywordBrain
    from app.brain.nemotron import NemotronBrain

    choice = settings.provider.lower()
    if choice == "nebius":
        return FallbackChain(
            NemotronBrain(settings.reasoning_model), NemotronBrain(settings.fallback_model), KeywordBrain()
        )
    if choice != "mock":
        log.warning('Unknown PROVIDER="%s", using mock', choice)
    return FallbackChain(KeywordBrain())
