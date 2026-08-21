import pytest

from jobpilot.schemas.common import (
    ApplicationStatus,
    assert_transition,
    require_submission_evidence,
)


def test_legal_path_to_submitted():
    assert_transition(ApplicationStatus.DISCOVERED, ApplicationStatus.ANALYZED)
    assert_transition(ApplicationStatus.ANALYZED, ApplicationStatus.MATCHED)
    assert_transition(ApplicationStatus.MATCHED, ApplicationStatus.CV_GENERATED)
    assert_transition(ApplicationStatus.CV_GENERATED, ApplicationStatus.READY_TO_APPLY)
    assert_transition(ApplicationStatus.READY_TO_APPLY, ApplicationStatus.APPLICATION_IN_PROGRESS)
    assert_transition(ApplicationStatus.APPLICATION_IN_PROGRESS, ApplicationStatus.SUBMITTED)
    assert_transition(ApplicationStatus.APPLICATION_IN_PROGRESS, ApplicationStatus.HUMAN_ACTION_REQUIRED)


def test_illegal_jump_to_submitted():
    with pytest.raises(ValueError):
        assert_transition(ApplicationStatus.DISCOVERED, ApplicationStatus.SUBMITTED)


def test_submitted_requires_evidence():
    with pytest.raises(ValueError):
        require_submission_evidence(None)
    with pytest.raises(ValueError):
        require_submission_evidence({"note": "maybe"})
    with pytest.raises(ValueError):
        require_submission_evidence({"http_status": 500})
    require_submission_evidence({"confirmation_id": "GH-123", "http_status": 200})
