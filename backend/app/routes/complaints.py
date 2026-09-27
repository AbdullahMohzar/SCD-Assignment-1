from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.dependencies import get_complaint_service
from app.providers.rate_limiter import get_rate_limiter
from app.schemas.common import Category, ErrorResponse, Priority, Status
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintListResponse,
    ComplaintResponse,
    StatusUpdate,
)
from app.services.complaint_service import ComplaintService

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


@router.post(
    "",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        429: {"description": "Rate limit exceeded (Too Many Requests)"},
    },
)
async def create_complaint(
    complaint_in: ComplaintCreate,
    request: Request,
    response: Response,
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintResponse:
    # 1. Distributed rate limiting check keyed by client IP (§2.4 Job 2)
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter = get_rate_limiter()
    allowed, retry_after = await rate_limiter.is_allowed(client_ip)
    if not allowed:
        response.headers["Retry-After"] = str(retry_after)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    # 2. Business service orchestration
    created = await service.create_complaint(complaint_in)
    return ComplaintResponse.model_validate(created)


@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    responses={404: {"model": ErrorResponse, "description": "Complaint not found"}},
)
async def get_complaint(
    complaint_id: UUID,
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintResponse:
    complaint = await service.get_complaint_by_id(complaint_id)
    return ComplaintResponse.model_validate(complaint)


@router.get(
    "",
    response_model=ComplaintListResponse,
)
async def list_complaints(
    category: Optional[Category] = Query(None, description="Filter by category"),
    priority: Optional[Priority] = Query(None, description="Filter by priority"),
    status: Optional[Status] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintListResponse:
    total, items = await service.list_complaints(
        category=category,
        priority=priority,
        status=status,
        page=page,
        page_size=page_size,
    )
    return ComplaintListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[ComplaintResponse.model_validate(item) for item in items],
    )


@router.patch(
    "/{complaint_id}/status",
    response_model=ComplaintResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Complaint not found"},
        409: {"model": ErrorResponse, "description": "Invalid status transition"},
    },
)
async def update_complaint_status(
    complaint_id: UUID,
    update_data: StatusUpdate,
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintResponse:
    updated = await service.update_status(complaint_id, update_data.status)
    return ComplaintResponse.model_validate(updated)
