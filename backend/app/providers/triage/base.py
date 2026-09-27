from typing import Protocol, runtime_checkable
from pydantic import BaseModel, Field

from app.schemas.common import Category, Priority


class TriageResult(BaseModel):
    category: Category
    priority: Priority
    summary: str = Field(..., max_length=140)
    confidence: float = Field(..., ge=0.0, le=1.0)


@runtime_checkable
class TriageProvider(Protocol):
    name: str

    async def triage(self, text: str, location: str) -> TriageResult:
        """Analyze complaint text and location to return structured triage result."""
        ...
