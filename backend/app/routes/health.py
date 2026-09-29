from fastapi import APIRouter, Depends, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.providers.cache import get_cache_provider
from app.repositories.complaint_repository import ComplaintRepository

router = APIRouter(tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def liveness() -> dict:
    """Liveness probe.

    Verifies process is running. MUST NOT touch the database or cache.
    """
    return {"status": "alive"}


@router.get("/ready")
async def readiness(
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Readiness probe.

    Verifies both PostgreSQL and Redis connectivity.
    Returns 200 if healthy, or 503 naming the failed dependency.
    """
    failed_dependencies = []

    # 1. Check PostgreSQL connectivity via repository layer
    try:
        repo = ComplaintRepository(session)
        is_pg_ok = await repo.ping()
        if not is_pg_ok:
            failed_dependencies.append("postgres (ping returned false)")
    except Exception as e:
        failed_dependencies.append(f"postgres ({e.__class__.__name__})")

    # 2. Check Redis connectivity via provider layer
    try:
        cache = get_cache_provider()
        is_redis_ok = await cache.ping()
        if not is_redis_ok:
            failed_dependencies.append("redis (ping returned false)")
    except Exception as e:
        failed_dependencies.append(f"redis ({e.__class__.__name__})")

    if failed_dependencies:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unready",
            "failed_dependencies": failed_dependencies,
            "detail": f"Service dependencies unreachable: {', '.join(failed_dependencies)}",
        }

    return {
        "status": "ready",
        "dependencies": {
            "postgres": "reachable",
            "redis": "reachable",
        },
    }


@router.get("/metrics")
async def metrics() -> Response:
    """Prometheus exposition endpoint for scraping application metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
