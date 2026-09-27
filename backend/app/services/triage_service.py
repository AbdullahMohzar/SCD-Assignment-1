import logging
import time
from collections import deque
from datetime import datetime, timezone
from typing import Deque, Optional, Tuple

from prometheus_client import Counter, Histogram

from app.config import get_settings
from app.providers.cache import get_cache_provider
from app.providers.triage.base import TriageProvider, TriageResult
from app.providers.triage.factory import get_triage_provider
from app.providers.triage.rules import RuleBasedTriage
from app.schemas.common import Category, Priority

logger = logging.getLogger(__name__)
settings = get_settings()

# Prometheus metrics
TRIAGE_LATENCY_HISTOGRAM = Histogram(
    "civicpulse_triage_latency_seconds",
    "Time spent in complaint triage",
    ["provider", "fallback"],
)
TRIAGE_FALLBACK_COUNTER = Counter(
    "civicpulse_triage_fallback_total",
    "Total number of triage fallback events to RuleBasedTriage",
    ["original_provider", "error_class"],
)
TRIAGE_CACHE_HITS = Counter(
    "civicpulse_triage_cache_hits_total",
    "Total number of content-hash triage cache hits",
)
TRIAGE_CACHE_MISSES = Counter(
    "civicpulse_triage_cache_misses_total",
    "Total number of content-hash triage cache misses",
)


class TriageOutcomeRecord:
    def __init__(self, provider: str, latency_ms: int, fallback: bool, timestamp: datetime):
        self.provider = provider
        self.latency_ms = latency_ms
        self.fallback = fallback
        self.timestamp = timestamp

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "latency_ms": self.latency_ms,
            "fallback": self.fallback,
            "timestamp": self.timestamp.isoformat(),
        }


class TriageService:
    """Orchestrates triage with content-hash caching, fallback, latency tracking, and metrics."""

    def __init__(self, provider: Optional[TriageProvider] = None):
        self.provider = provider or get_triage_provider()
        self.fallback_rules = RuleBasedTriage()
        self.cache = get_cache_provider()
        # Sliding window buffer of last 20 triage outcomes
        self.recent_outcomes: Deque[TriageOutcomeRecord] = deque(maxlen=20)

    async def triage_complaint(
        self,
        text: str,
        location: str,
        correlation_id: Optional[str] = None,
    ) -> Tuple[TriageResult, str, int]:
        """Triages text & location.

        Returns: (triage_result, triaged_by, latency_ms)
        """
        start_time = time.perf_counter()

        # 1. Content-hash cache lookup (duplicate complaints cost 1 inference)
        cached = await self.cache.get_triage_cache(text, location)
        if cached:
            TRIAGE_CACHE_HITS.inc()
            latency_ms = max(int((time.perf_counter() - start_time) * 1000), 1)
            result = TriageResult(
                category=Category(cached["category"]),
                priority=Priority(cached["priority"]),
                summary=cached["summary"],
                confidence=float(cached.get("confidence", 0.9)),
            )
            triaged_by = cached.get("triaged_by", self.provider.name)
            self._record_outcome(triaged_by, latency_ms, fallback=False)
            return result, triaged_by, latency_ms

        TRIAGE_CACHE_MISSES.inc()

        # 2. Call active provider with resilience & fallback
        is_fallback = False
        triaged_by = self.provider.name

        try:
            result = await self.provider.triage(text, location)
        except Exception as e:
            # Fallback to RuleBasedTriage
            is_fallback = True
            triaged_by = "rules:fallback"
            err_cls = e.__class__.__name__

            logger.warning(
                f"Triage fallback triggered: complaint_id={correlation_id or 'unknown'} "
                f"provider={self.provider.name} error_class={err_cls} error='{e}'"
            )
            TRIAGE_FALLBACK_COUNTER.labels(
                original_provider=self.provider.name,
                error_class=err_cls,
            ).inc()

            result = await self.fallback_rules.triage(text, location)

        elapsed_sec = time.perf_counter() - start_time
        latency_ms = max(int(elapsed_sec * 1000), 1)

        TRIAGE_LATENCY_HISTOGRAM.labels(
            provider=triaged_by,
            fallback=str(is_fallback).lower(),
        ).observe(elapsed_sec)

        # 3. Store result in Redis content-hash cache (24h TTL)
        cache_data = {
            "category": result.category.value,
            "priority": result.priority.value,
            "summary": result.summary,
            "confidence": result.confidence,
            "triaged_by": triaged_by,
        }
        await self.cache.set_triage_cache(
            text, location, cache_data, ttl=settings.TRIAGE_CACHE_TTL_SECONDS
        )

        # 4. Record in sliding window
        self._record_outcome(triaged_by, latency_ms, fallback=is_fallback)

        return result, triaged_by, latency_ms

    def _record_outcome(self, provider: str, latency_ms: int, fallback: bool) -> None:
        self.recent_outcomes.append(
            TriageOutcomeRecord(
                provider=provider,
                latency_ms=latency_ms,
                fallback=fallback,
                timestamp=datetime.now(timezone.utc),
            )
        )

    def get_metadata(self) -> dict:
        return {
            "active_provider": self.provider.name,
            "recent_outcomes": [o.to_dict() for o in list(self.recent_outcomes)],
        }


_triage_service: Optional[TriageService] = None


def get_triage_service() -> TriageService:
    global _triage_service
    if _triage_service is None:
        _triage_service = TriageService()
    return _triage_service
