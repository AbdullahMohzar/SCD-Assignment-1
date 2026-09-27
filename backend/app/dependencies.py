from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.repositories.complaint_repository import ComplaintRepository
from app.services.complaint_service import ComplaintService
from app.services.stats_service import StatsService


def get_complaint_service(session: AsyncSession = Depends(get_db_session)) -> ComplaintService:
    """Dependency injector providing ComplaintService with bound persistence repository."""
    repository = ComplaintRepository(session)
    return ComplaintService(repository)


def get_stats_service(session: AsyncSession = Depends(get_db_session)) -> StatsService:
    """Dependency injector providing StatsService with bound persistence repository."""
    repository = ComplaintRepository(session)
    return StatsService(repository)
