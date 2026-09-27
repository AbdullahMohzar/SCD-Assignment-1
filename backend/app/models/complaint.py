import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase

from app.schemas.common import Category, Priority, Status


class Base(DeclarativeBase):
    pass


class Complaint(Base):
    __tablename__ = "complaints"

    id: Any = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text: Any = Column(Text, nullable=False)
    location: Any = Column(String(200), nullable=False)
    reporter_contact: Any = Column(String(100), nullable=True)

    category: Any = Column(
        Enum(Category, name="category_enum", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    priority: Any = Column(
        Enum(Priority, name="priority_enum", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    status: Any = Column(
        Enum(Status, name="status_enum", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=Status.OPEN,
    )

    ai_summary = Column(String(140), nullable=True)
    triaged_by = Column(String(50), nullable=False)
    triage_latency_ms = Column(Integer, nullable=False, default=0)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        CheckConstraint(
            "length(text) >= 10 AND length(text) <= 2000",
            name="check_complaint_text_length",
        ),
        CheckConstraint(
            "length(location) >= 3 AND length(location) <= 200",
            name="check_complaint_location_length",
        ),
        Index("idx_complaints_status_priority", "status", "priority"),
        Index("idx_complaints_created_at", "created_at"),
    )
