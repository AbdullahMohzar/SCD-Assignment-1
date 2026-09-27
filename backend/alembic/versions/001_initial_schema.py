"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-27 21:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create enum types
    category_enum = postgresql.ENUM(
        "water", "electricity", "sanitation", "roads", "streetlights", "other",
        name="category_enum",
        create_type=False,
    )
    priority_enum = postgresql.ENUM(
        "high", "normal", "low",
        name="priority_enum",
        create_type=False,
    )
    status_enum = postgresql.ENUM(
        "open", "in_progress", "resolved", "rejected",
        name="status_enum",
        create_type=False,
    )

    bind = op.get_bind()
    category_enum.create(bind, checkfirst=True)
    priority_enum.create(bind, checkfirst=True)
    status_enum.create(bind, checkfirst=True)

    # 2. Create complaints table
    op.create_table(
        "complaints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=False),
        sa.Column("reporter_contact", sa.String(length=100), nullable=True),
        sa.Column("category", category_enum, nullable=False),
        sa.Column("priority", priority_enum, nullable=False),
        sa.Column("status", status_enum, nullable=False, server_default="open"),
        sa.Column("ai_summary", sa.String(length=140), nullable=True),
        sa.Column("triaged_by", sa.String(length=50), nullable=False),
        sa.Column("triage_latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "length(text) >= 10 AND length(text) <= 2000",
            name="check_complaint_text_length",
        ),
        sa.CheckConstraint(
            "length(location) >= 3 AND length(location) <= 200",
            name="check_complaint_location_length",
        ),
    )

    # 3. Create required performance indexes (§2.3)
    op.create_index(
        "idx_complaints_status_priority",
        "complaints",
        ["status", "priority"],
        unique=False,
    )
    op.create_index(
        "idx_complaints_created_at",
        "complaints",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_complaints_created_at", table_name="complaints")
    op.drop_index("idx_complaints_status_priority", table_name="complaints")
    op.drop_table("complaints")

    bind = op.get_bind()
    sa.Enum(name="status_enum").drop(bind, checkfirst=True)
    sa.Enum(name="priority_enum").drop(bind, checkfirst=True)
    sa.Enum(name="category_enum").drop(bind, checkfirst=True)
