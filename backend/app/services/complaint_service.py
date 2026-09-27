from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status

from app.models.complaint import Complaint
from app.providers.cache import get_cache_provider
from app.repositories.complaint_repository import ComplaintRepository
from app.schemas.common import Category, Priority, Status
from app.schemas.complaint import ComplaintCreate
from app.services.state_machine import ComplaintStateMachine
from app.services.triage_service import get_triage_service


class ComplaintService:
    """Business logic service for complaint management."""

    def __init__(self, repository: ComplaintRepository):
        self.repository = repository
        self.triage_service = get_triage_service()
        self.cache_provider = get_cache_provider()

    async def create_complaint(self, data: ComplaintCreate) -> Complaint:
        # 1. AI Triage with fallback & latency measurement
        triage_result, triaged_by, latency_ms = await self.triage_service.triage_complaint(
            text=data.text,
            location=data.location,
        )

        # 2. Build model
        complaint = Complaint(
            text=data.text,
            location=data.location,
            reporter_contact=data.reporter_contact,
            category=triage_result.category,
            priority=triage_result.priority,
            status=Status.OPEN,
            ai_summary=triage_result.summary,
            triaged_by=triaged_by,
            triage_latency_ms=latency_ms,
        )

        # 3. Persist to DB
        created = await self.repository.create(complaint)

        # 4. Invalidate stats cache on write (§2.4: Invalidate on write)
        await self.cache_provider.invalidate_stats_cache()

        return created

    async def get_complaint_by_id(self, complaint_id: UUID) -> Complaint:
        complaint = await self.repository.get_by_id(complaint_id)
        if not complaint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Complaint with id {complaint_id} not found",
            )
        return complaint

    async def list_complaints(
        self,
        category: Optional[Category] = None,
        priority: Optional[Priority] = None,
        status: Optional[Status] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[int, List[Complaint]]:
        # Enforce page_size <= 100 per API contract (§2.2)
        if page_size > 100:
            page_size = 100
        if page < 1:
            page = 1

        return await self.repository.list_complaints(
            category=category,
            priority=priority,
            status=status,
            page=page,
            page_size=page_size,
        )

    async def update_status(self, complaint_id: UUID, target_status: Status) -> Complaint:
        complaint = await self.get_complaint_by_id(complaint_id)

        # Enforce state machine transitions
        ComplaintStateMachine.validate_transition(Status(complaint.status), target_status)

        updated = await self.repository.update_status(complaint, target_status)

        # Invalidate stats cache on write
        await self.cache_provider.invalidate_stats_cache()

        return updated
