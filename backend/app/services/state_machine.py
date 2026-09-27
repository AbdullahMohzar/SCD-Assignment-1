from typing import Dict, Set
from fastapi import HTTPException, status
from app.schemas.common import Status


class InvalidStatusTransitionError(HTTPException):
    def __init__(self, current_status: Status, attempted_status: Status):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid transition from {current_status.value} to {attempted_status.value}",
        )


class ComplaintStateMachine:
    """Explicit state machine transition table for complaint status lifecycle.

    Allowed transitions:
      open -> in_progress
      open -> rejected
      in_progress -> resolved
      in_progress -> rejected
      resolved -> (terminal)
      rejected -> (terminal)
    """

    TRANSITION_TABLE: Dict[Status, Set[Status]] = {
        Status.OPEN: {Status.IN_PROGRESS, Status.REJECTED},
        Status.IN_PROGRESS: {Status.RESOLVED, Status.REJECTED},
        Status.RESOLVED: set(),  # Terminal
        Status.REJECTED: set(),  # Terminal
    }

    @classmethod
    def can_transition(cls, current: Status, target: Status) -> bool:
        allowed = cls.TRANSITION_TABLE.get(current, set())
        return target in allowed

    @classmethod
    def validate_transition(cls, current: Status, target: Status) -> None:
        if not cls.can_transition(current, target):
            raise InvalidStatusTransitionError(current, target)
