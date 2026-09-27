from fastapi import APIRouter, Depends, Response

from app.dependencies import get_stats_service
from app.schemas.complaint import StatsResponse
from app.services.stats_service import StatsService

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get(
    "",
    response_model=StatsResponse,
)
async def get_stats(
    response: Response,
    service: StatsService = Depends(get_stats_service),
) -> StatsResponse:
    stats_data, is_cache_hit = await service.get_stats()

    # Required contract (§2.2): X-Cache: HIT | MISS
    response.headers["X-Cache"] = "HIT" if is_cache_hit else "MISS"

    return StatsResponse(
        total=stats_data.get("total", 0),
        by_category=stats_data.get("by_category", {}),
        by_priority=stats_data.get("by_priority", {}),
        by_status=stats_data.get("by_status", {}),
    )
