from __future__ import annotations

from jobpilot.apply.ats import submit_official
from jobpilot.apply.policy import ApplyPolicy
from jobpilot.config import get_settings
from jobpilot.schemas.application import ApplicationAttempt, ApplicationPackage
from jobpilot.schemas.common import ApplicationStatus, ApplyMechanism, require_submission_evidence
from jobpilot.schemas.job import JobPosting


def attempt_application(
    posting: JobPosting,
    package: ApplicationPackage,
    *,
    approved: bool = False,
) -> ApplicationAttempt:
    """Try a legitimate apply path. Never claim SUBMITTED without evidence or approval."""
    policy = ApplyPolicy()
    mechanism = policy.detect(posting)
    settings = get_settings()

    if not approved:
        return ApplicationAttempt(
            mechanism=mechanism,
            status=ApplicationStatus.HUMAN_ACTION_REQUIRED,
            dry_run=True,
            human_action=(
                "Review the application draft, then choose Send this application or "
                "I'll submit it myself."
            ),
            evidence={"policy_reason": "awaiting_approval"},
        )

    if mechanism == ApplyMechanism.MANUAL:
        return ApplicationAttempt(
            mechanism=mechanism,
            status=ApplicationStatus.HUMAN_ACTION_REQUIRED,
            dry_run=True,
            human_action="This one has to be sent on the company's own site. Use the draft below.",
            evidence={"policy_reason": "manual_portal"},
        )

    permitted, reason = policy.automation_permitted(mechanism)
    if not permitted:
        return ApplicationAttempt(
            mechanism=mechanism,
            status=ApplicationStatus.HUMAN_ACTION_REQUIRED,
            dry_run=not settings.jobpilot_allow_live_apply,
            human_action=policy.remaining_human_action(mechanism, reason),
            evidence={"policy_reason": reason},
        )

    result = submit_official(posting.job_url, package)
    if result.get("ok"):
        evidence = result.get("evidence") or {}
        evidence["confirmation_id"] = result.get("confirmation_id")
        require_submission_evidence(evidence)
        return ApplicationAttempt(
            mechanism=mechanism,
            status=ApplicationStatus.SUBMITTED,
            dry_run=False,
            confirmation_id=result.get("confirmation_id"),
            evidence=evidence,
        )
    return ApplicationAttempt(
        mechanism=mechanism,
        status=ApplicationStatus.HUMAN_ACTION_REQUIRED,
        dry_run=True,
        human_action=result.get("error")
        or "Please submit this one yourself using the draft.",
        error=result.get("error"),
        evidence={"policy_reason": result.get("error"), "http_status": result.get("http_status")},
    )


def mark_submitted(attempt: ApplicationAttempt) -> ApplicationAttempt:
    require_submission_evidence(attempt.evidence)
    return attempt.model_copy(update={"status": ApplicationStatus.SUBMITTED})
