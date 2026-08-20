from __future__ import annotations

from jobpilot.apply.policy import ApplyPolicy
from jobpilot.config import get_settings
from jobpilot.schemas.application import ApplicationAttempt, ApplicationPackage
from jobpilot.schemas.common import ApplicationStatus, ApplyMechanism, require_submission_evidence
from jobpilot.schemas.job import JobPosting


def attempt_application(posting: JobPosting, package: ApplicationPackage) -> ApplicationAttempt:
    """Try a legitimate apply path. Never claim SUBMITTED without evidence."""
    policy = ApplyPolicy()
    mechanism = policy.detect(posting)
    permitted, reason = policy.automation_permitted(mechanism)
    settings = get_settings()

    if mechanism == ApplyMechanism.MANUAL or not permitted:
        return ApplicationAttempt(
            mechanism=mechanism,
            status=ApplicationStatus.HUMAN_ACTION_REQUIRED,
            dry_run=not settings.jobpilot_allow_live_apply,
            human_action=policy.remaining_human_action(mechanism, reason),
            error=None,
            evidence={"policy_reason": reason},
        )

    # Live HTTP apply adapters would go here (Greenhouse/Lever public forms).
    # They are intentionally not implemented as reverse-engineered private APIs.
    # A future official company/ATS API key can be plugged in without changing callers.
    return ApplicationAttempt(
        mechanism=mechanism,
        status=ApplicationStatus.HUMAN_ACTION_REQUIRED,
        dry_run=True,
        human_action=(
            "No official public apply API is configured for this employer. "
            "Materials are ready; submit on the career page without bot-detection bypass."
        ),
        evidence={"policy_reason": "no_official_apply_api"},
    )


def mark_submitted(attempt: ApplicationAttempt) -> ApplicationAttempt:
    require_submission_evidence(attempt.evidence)
    return attempt.model_copy(update={"status": ApplicationStatus.SUBMITTED})
