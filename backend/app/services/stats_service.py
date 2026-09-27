from typing import Dict, Tuple
from app.providers.cache import get_cache_provider
from app.repositories.complaint_repository import ComplaintRepository


class StatsService:
    """Read-through cached stats aggregator with 30s TTL and X-Cache header awareness."""

    def __init__(self, repository: ComplaintRepository):
        self.repository = repository
        self.cache = get_cache_provider()

    async def get_stats(self) -> Tuple[Dict, bool]:
        """Returns (stats_data, is_cache_hit)."""
        cached_data = await self.cache.get_stats_cache()
        if cached_data is not None:
            return cached_data, True

        # Cache miss - query DB repository
        data = await self.repository.get_stats_aggregates()

        # Cache with 30s TTL
        await self.cache.set_stats_cache(data, ttl=30)
        return data, False
