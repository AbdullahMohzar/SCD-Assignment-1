import asyncio
import json
import logging
import random
from typing import Optional

import httpx
from pydantic import ValidationError

from app.config import get_settings
from app.providers.triage.base import TriageResult
from app.schemas.common import Category, Priority

logger = logging.getLogger(__name__)
settings = get_settings()

OLLAMA_SYSTEM_PROMPT = """You are CivicPulse AI for offline municipal complaint triage.
Classify the complaint into Category, Priority, Summary (<140 chars), and Confidence (0.0-1.0).
Respond with valid JSON only.

Category must be: water, electricity, sanitation, roads, streetlights, other.
Priority must be: high, normal, low.
"""


class OllamaTriage:
    """Fully offline triage provider calling a local Ollama container."""

    name: str = "llm:ollama"

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: float = 10.0,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout_seconds = timeout_seconds

    async def triage(self, text: str, location: str) -> TriageResult:
        prompt = (
            f"Location: {location}\n"
            f"Complaint: {text}\n\n"
            f"Return JSON matching:\n"
            f'{{"category":"...", "priority":"...", "summary":"...", "confidence":0.9}}'
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": OLLAMA_SYSTEM_PROMPT,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1, "num_predict": 200},
        }

        max_attempts = 2
        last_error: Optional[Exception] = None

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            for attempt in range(1, max_attempts + 1):
                try:
                    resp = await client.post(f"{self.base_url}/api/generate", json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    response_text = data.get("response", "")
                    parsed = json.loads(response_text)

                    return TriageResult(
                        category=Category(parsed["category"].lower()),
                        priority=Priority(parsed["priority"].lower()),
                        summary=str(parsed["summary"])[:140],
                        confidence=float(parsed.get("confidence", 0.80)),
                    )
                except (ValidationError, KeyError, ValueError) as parse_err:
                    logger.warning(f"Ollama response failed validation: {parse_err}")
                    raise
                except Exception as e:
                    last_error = e
                    logger.warning(f"Ollama attempt {attempt} failed: {e}")
                    if attempt < max_attempts:
                        await asyncio.sleep(0.5 + random.uniform(0.1, 0.5))

        if last_error:
            raise last_error
        raise RuntimeError("Ollama triage call failed")
