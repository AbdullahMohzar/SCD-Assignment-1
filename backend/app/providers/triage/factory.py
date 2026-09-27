import logging
from typing import Optional

from app.config import get_settings
from app.providers.triage.base import TriageProvider
from app.providers.triage.llm import LLMTriage
from app.providers.triage.ollama import OllamaTriage
from app.providers.triage.rules import RuleBasedTriage
from app.providers.triage.simulated import SimulatedTriage

logger = logging.getLogger(__name__)
settings = get_settings()


def get_triage_provider(provider_name: Optional[str] = None) -> TriageProvider:
    """Factory creating configured TriageProvider based on environment or explicit parameter."""
    choice = (provider_name or settings.TRIAGE_PROVIDER).lower()

    if choice in ("llm:groq", "groq", "llm"):
        return LLMTriage(provider_type="groq", timeout_seconds=settings.TRIAGE_TIMEOUT_SECONDS)
    elif choice in ("llm:gemini", "gemini"):
        return LLMTriage(provider_type="gemini", timeout_seconds=settings.TRIAGE_TIMEOUT_SECONDS)
    elif choice in ("llm:ollama", "ollama"):
        return OllamaTriage(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            timeout_seconds=settings.TRIAGE_TIMEOUT_SECONDS,
        )
    elif choice in ("rules", "rulebased"):
        return RuleBasedTriage()
    elif choice in ("simulated", "sim"):
        return SimulatedTriage()
    else:
        logger.warning(f"Unknown TRIAGE_PROVIDER '{choice}'. Falling back to SimulatedTriage.")
        return SimulatedTriage()
