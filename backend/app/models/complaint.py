import uuid
from datetime import datetime, timezone
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
from sqlalchemy.orm import declarative_base

from app.schemas.common import Category, Priority, Status

Base = declarative_base()


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(Text, nullable=False)
    location = Column(String(200), nullable=False)
    reporter_contact = Column(String(100), nullable=True)

    category = Column(
        Enum(Category, name="category_enum", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    priority = Column(
        Enum(Priority, name="priority_enum", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    status = Column(
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
