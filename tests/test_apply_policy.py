from jobpilot.apply.policy import ApplyPolicy
from jobpilot.apply.submit import attempt_application
from jobpilot.schemas.application import ApplicationPackage
from jobpilot.schemas.common import ApplicationStatus, ApplyMechanism, ResumeType
from jobpilot.schemas.job import JobPosting


def test_linkedin_is_manual():
    posting = JobPosting(
        source="linkedin",
        company="X",
        title="Data Engineer",
        job_url="https://www.linkedin.com/jobs/view/123",
    )
    assert ApplyPolicy().detect(posting) == ApplyMechanism.MANUAL
    permitted, reason = ApplyPolicy().automation_permitted(ApplyMechanism.MANUAL)
    assert permitted is False
    assert "yourself" in reason.lower() or "linkedin" in reason.lower()


def test_captcha_stops_automation():
    ok, reason = ApplyPolicy().automation_permitted(
        ApplyMechanism.CAREER_PAGE, page_html="<div class='g-recaptcha'></div>"
    )
    assert ok is False
    assert "yourself" in reason.lower() or "security" in reason.lower()


def test_attempt_never_submitted_without_live_flag():
    posting = JobPosting(
        source="greenhouse",
        company="spotify",
        title="Data Engineer",
        job_url="https://boards.greenhouse.io/spotify/jobs/1",
    )
    package = ApplicationPackage(
        company="spotify",
        role="Data Engineer",
        job_url=posting.job_url,
        match_score=90,
        selected_resume=ResumeType.DATA_ENGINEER,
    )
    attempt = attempt_application(posting, package)
    assert attempt.status != ApplicationStatus.SUBMITTED
    assert attempt.status == ApplicationStatus.HUMAN_ACTION_REQUIRED
