import asyncio
import hashlib
from typing import Optional
from app.providers.triage.base import TriageResult
from app.providers.triage.rules import RuleBasedTriage
from app.schemas.common import Category, Priority


class SimulatedTriage:
    """Deterministic fake triage provider for CI and testing.

    Configurable failure injection without network dependencies.
    """

    name: str = "simulated"

    def __init__(self, failure_mode: Optional[str] = None, delay_seconds: float = 0.0):
        self.failure_mode = failure_mode  # None | "raise" | "timeout" | "rate_limit" | "malformed_json"
        self.delay_seconds = delay_seconds
        self._fallback_rules = RuleBasedTriage()

    async def triage(self, text: str, location: str) -> TriageResult:
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.failure_mode == "raise":
            raise RuntimeError("Simulated upstream provider connection crash")
        elif self.failure_mode == "timeout":
            raise asyncio.TimeoutError("Simulated LLM call timed out after 10.0s")
        elif self.failure_mode == "rate_limit":
            # Simulate HTTP 429
            raise RuntimeError("HTTP 429: Rate limit exceeded on simulated upstream")
        elif self.failure_mode == "malformed_json":
            raise ValueError("Malformed JSON returned by simulated model")

        # Deterministic result derived from rules and stable hash
        result = await self._fallback_rules.triage(text, location)

        # Stable confidence derived from sha256 hash of text
        h_val = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:4], 16)
        stable_confidence = 0.75 + (h_val % 25) / 100.0

        return TriageResult(
            category=result.category,
            priority=result.priority,
            summary=result.summary,
            confidence=round(min(stable_confidence, 0.99), 2),
        )
