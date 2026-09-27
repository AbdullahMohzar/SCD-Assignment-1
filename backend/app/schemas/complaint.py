from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.schemas.common import Category, Priority, Status


class ComplaintCreate(BaseModel):
    text: str = Field(..., min_length=10, max_length=2000, description="Detailed complaint description")
    location: str = Field(..., min_length=3, max_length=200, description="Geographic location or address")
    reporter_contact: Optional[str] = Field(None, max_length=100, description="Optional reporter phone or email")


class StatusUpdate(BaseModel):
    status: Status = Field(..., description="Target status transition")


class TriageResult(BaseModel):
    category: Category
    priority: Priority
    summary: str = Field(..., max_length=140)
    confidence: float = Field(..., ge=0.0, le=1.0)


class ComplaintResponse(BaseModel):
    id: UUID
    text: str
    location: str
    reporter_contact: Optional[str] = None
    category: Category
    priority: Priority
    status: Status
    ai_summary: Optional[str] = None
    triaged_by: str
    triage_latency_ms: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ComplaintListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ComplaintResponse]


class StatsResponse(BaseModel):
    total: int
    by_category: Dict[str, int]
    by_priority: Dict[str, int]
    by_status: Dict[str, int]


class TriageOutcomeItem(BaseModel):
    provider: str
    latency_ms: int
    fallback: bool
    timestamp: datetime


class ProviderMetaResponse(BaseModel):
    active_provider: str
    recent_outcomes: List[TriageOutcomeItem]
