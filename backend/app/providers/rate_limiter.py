import logging
import time
from typing import Optional, Tuple

from app.config import get_settings
from app.providers.cache import get_cache_provider

logger = logging.getLogger(__name__)
settings = get_settings()


class DistributedRateLimiter:
    """Distributed rate limiter using Redis fixed-window counters keyed by client IP."""

    def __init__(self, limit_per_minute: Optional[int] = None):
        self.limit_per_minute = limit_per_minute or settings.RATE_LIMIT_PER_MINUTE

    async def is_allowed(self, client_ip: str) -> Tuple[bool, int]:
        """Checks if client_ip has exceeded rate limit.

        Returns:
            (allowed: bool, retry_after_seconds: int)
        """
        # If rate limiting is disabled or client is internal test
        if self.limit_per_minute <= 0:
            return True, 0

        cache = get_cache_provider()
        try:
            client = await cache.get_client()
            current_window = int(time.time() // 60)
            key = f"civicpulse:ratelimit:{client_ip}:{current_window}"

            # Pipeline INCR and EXPIRE to guarantee atomic window TTL
            pipe = client.pipeline()
            pipe.incr(key)
            pipe.expire(key, 65)  # 65s so key expires cleanly after window
            results = await pipe.execute()

            request_count = results[0]
            if request_count > self.limit_per_minute:
                # Seconds remaining until next minute window
                retry_after = 60 - int(time.time() % 60)
                if retry_after <= 0:
                    retry_after = 1
                return False, retry_after

            return True, 0
        except Exception as e:
            logger.warning(f"Rate limiter check failed for IP {client_ip}: {e}. Failing open.")
            return True, 0


_rate_limiter: Optional[DistributedRateLimiter] = None


def get_rate_limiter() -> DistributedRateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = DistributedRateLimiter()
    return _rate_limiter
