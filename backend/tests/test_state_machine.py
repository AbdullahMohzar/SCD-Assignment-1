import pytest
from app.schemas.common import Status
from app.services.state_machine import ComplaintStateMachine, InvalidStatusTransitionError


def test_allowed_transitions():
    assert ComplaintStateMachine.can_transition(Status.OPEN, Status.IN_PROGRESS) is False
    assert ComplaintStateMachine.can_transition(Status.OPEN, Status.REJECTED) is True
    assert ComplaintStateMachine.can_transition(Status.IN_PROGRESS, Status.RESOLVED) is True
    assert ComplaintStateMachine.can_transition(Status.IN_PROGRESS, Status.REJECTED) is True


def test_disallowed_transitions():
    # Direct jump open -> resolved is not permitted
    assert ComplaintStateMachine.can_transition(Status.OPEN, Status.RESOLVED) is False

    # Backwards transition
    assert ComplaintStateMachine.can_transition(Status.IN_PROGRESS, Status.OPEN) is False

    # Terminal states cannot transition
    assert ComplaintStateMachine.can_transition(Status.RESOLVED, Status.OPEN) is False
    assert ComplaintStateMachine.can_transition(Status.RESOLVED, Status.IN_PROGRESS) is False
    assert ComplaintStateMachine.can_transition(Status.REJECTED, Status.OPEN) is False
    assert ComplaintStateMachine.can_transition(Status.REJECTED, Status.IN_PROGRESS) is False


def test_validate_transition_exception():
    with pytest.raises(InvalidStatusTransitionError) as exc_info:
        ComplaintStateMachine.validate_transition(Status.RESOLVED, Status.OPEN)
    assert exc_info.value.status_code == 409
    assert "Invalid transition from resolved to open" in exc_info.value.detail
