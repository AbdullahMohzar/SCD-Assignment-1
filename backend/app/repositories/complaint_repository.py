from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import Complaint
from app.schemas.common import Category, Priority, Status


class ComplaintRepository:
    """Repository handling all SQL persistence and queries for complaints.

    All SQL lives here and nowhere else.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, complaint: Complaint) -> Complaint:
        self.session.add(complaint)
        await self.session.flush()
        await self.session.refresh(complaint)
        return complaint

    async def get_by_id(self, complaint_id: UUID) -> Optional[Complaint]:
        result = await self.session.execute(
            select(Complaint).where(Complaint.id == complaint_id)
        )
        return result.scalar_one_or_none()

    async def list_complaints(
        self,
        category: Optional[Category] = None,
        priority: Optional[Priority] = None,
        status: Optional[Status] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[int, List[Complaint]]:
        query = select(Complaint)

        if category is not None:
            query = query.where(Complaint.category == category)
        if priority is not None:
            query = query.where(Complaint.priority == priority)
        if status is not None:
            query = query.where(Complaint.status == status)

        # Count query
        count_stmt = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one() or 0

        # Pagination & ordering
        offset = (page - 1) * page_size
        query = query.order_by(Complaint.created_at.desc()).offset(offset).limit(page_size)

        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return total, items

    async def update_status(self, complaint: Complaint, new_status: Status) -> Complaint:
        complaint.status = new_status
        await self.session.flush()
        await self.session.refresh(complaint)
        return complaint

    async def get_stats_aggregates(self) -> Dict[str, Any]:
        """Calculates counts aggregated by category, priority, and status."""
        total_stmt = select(func.count(Complaint.id))
        total = (await self.session.execute(total_stmt)).scalar_one() or 0

        # Aggregates by category
        cat_stmt: Any = select(Complaint.category, func.count(Complaint.id)).group_by(Complaint.category)
        cat_res = await self.session.execute(cat_stmt)
        by_category = {cat.value if hasattr(cat, "value") else str(cat): count for cat, count in cat_res.all()}

        # Fill zero counts for missing categories
        for cat in Category:
            if cat.value not in by_category:
                by_category[cat.value] = 0

        # Aggregates by priority
        prio_stmt: Any = select(Complaint.priority, func.count(Complaint.id)).group_by(Complaint.priority)
        prio_res = await self.session.execute(prio_stmt)
        by_priority = {prio.value if hasattr(prio, "value") else str(prio): count for prio, count in prio_res.all()}

        for prio in Priority:
            if prio.value not in by_priority:
                by_priority[prio.value] = 0

        # Aggregates by status
        stat_stmt: Any = select(Complaint.status, func.count(Complaint.id)).group_by(Complaint.status)
        stat_res = await self.session.execute(stat_stmt)
        by_status = {stat.value if hasattr(stat, "value") else str(stat): count for stat, count in stat_res.all()}

        for st in Status:
            if st.value not in by_status:
                by_status[st.value] = 0

        return {
            "total": total,
            "by_category": by_category,
            "by_priority": by_priority,
            "by_status": by_status,
        }

    async def ping(self) -> bool:
        try:
            await self.session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
