import hashlib
import json
import logging
from typing import Any, Optional
import redis.asyncio as redis

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CacheProvider:
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis: Optional[redis.Redis] = None

    async def get_client(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=2.0,
                socket_connect_timeout=2.0,
            )
        return self._redis

    async def get(self, key: str) -> Optional[str]:
        try:
            client = await self.get_client()
            return await client.get(key)
        except Exception as e:
            logger.warning(f"Redis GET failed for key {key}: {e}")
            return None

    async def set(self, key: str, value: str, ttl_seconds: int) -> bool:
        try:
            client = await self.get_client()
            await client.set(key, value, ex=ttl_seconds)
            return True
        except Exception as e:
            logger.warning(f"Redis SET failed for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        try:
            client = await self.get_client()
            await client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis DELETE failed for key {key}: {e}")
            return False

    # Stats caching helper
    STATS_CACHE_KEY = "civicpulse:stats"

    async def get_stats_cache(self) -> Optional[dict]:
        raw = await self.get(self.STATS_CACHE_KEY)
        if raw:
            try:
                return json.loads(raw)
            except Exception:
                return None
        return None

    async def set_stats_cache(self, stats: dict, ttl: int = 30) -> None:
        await self.set(self.STATS_CACHE_KEY, json.dumps(stats), ttl_seconds=ttl)

    async def invalidate_stats_cache(self) -> None:
        await self.delete(self.STATS_CACHE_KEY)

    # Triage content-hash caching helper
    def compute_triage_hash(self, text: str, location: str) -> str:
        payload = f"{text.strip().lower()}|{location.strip().lower()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    async def get_triage_cache(self, text: str, location: str) -> Optional[dict]:
        h = self.compute_triage_hash(text, location)
        raw = await self.get(f"civicpulse:triage:{h}")
        if raw:
            try:
                return json.loads(raw)
            except Exception:
                return None
        return None

    async def set_triage_cache(self, text: str, location: str, result: dict, ttl: int = 86400) -> None:
        h = self.compute_triage_hash(text, location)
        await self.set(f"civicpulse:triage:{h}", json.dumps(result), ttl_seconds=ttl)

    async def ping(self) -> bool:
        try:
            client = await self.get_client()
            return await client.ping()
        except Exception:
            return False

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()
            self._redis = None


_cache_provider: Optional[CacheProvider] = None


def get_cache_provider() -> CacheProvider:
    global _cache_provider
    if _cache_provider is None:
        _cache_provider = CacheProvider()
    return _cache_provider
