from __future__ import annotations

import re
from urllib.parse import urlparse

from jobpilot.config import get_settings, load_app_config
from jobpilot.schemas.common import ApplyMechanism
from jobpilot.schemas.job import JobPosting

LINKEDIN = re.compile(r"linkedin\.com", re.I)
GREENHOUSE = re.compile(r"greenhouse\.io|boards-api\.greenhouse", re.I)
LEVER = re.compile(r"lever\.co", re.I)
ASHBY = re.compile(r"ashbyhq\.com", re.I)
SMARTRECRUITERS = re.compile(r"smartrecruiters\.com", re.I)
WORKABLE = re.compile(r"workable\.com", re.I)
TEAMTAILOR = re.compile(r"teamtailor\.com", re.I)
CAPTCHA_MARKERS = ("g-recaptcha", "h-captcha", "cf-challenge", "data-cf-challenge")


class ApplyPolicy:
    """Hard rules: never bypass CAPTCHA, LinkedIn, stolen cookies, or ToS bans."""

    def detect(self, posting: JobPosting) -> ApplyMechanism:
        url = posting.job_url or ""
        source = posting.source or ""
        if LINKEDIN.search(url) or source == "linkedin":
            return ApplyMechanism.MANUAL
        if GREENHOUSE.search(url) or source == "greenhouse":
            return ApplyMechanism.GREENHOUSE
        if LEVER.search(url) or source == "lever":
            return ApplyMechanism.LEVER
        if ASHBY.search(url) or SMARTRECRUITERS.search(url) or WORKABLE.search(url) or TEAMTAILOR.search(url):
            return ApplyMechanism.OTHER_ATS
        host = urlparse(url).hostname or ""
        if host and "jobs" in host:
            return ApplyMechanism.CAREER_PAGE
        return ApplyMechanism.UNKNOWN

    def automation_permitted(self, mechanism: ApplyMechanism, page_html: str | None = None) -> tuple[bool, str]:
        settings = get_settings()
        config = load_app_config()
        apply_cfg = config.get("applications", {})
        if not settings.jobpilot_allow_live_apply:
            return False, "Live apply is disabled (JOBPILOT_ALLOW_LIVE_APPLY=false)."
        if apply_cfg.get("dry_run", True):
            return False, "Dry-run is enabled; packages are prepared but not submitted."
        if apply_cfg.get("linkedin_automation"):
            return False, "LinkedIn automation is forbidden by policy even if misconfigured."
        if mechanism == ApplyMechanism.MANUAL:
            return False, "This mechanism requires a human (LinkedIn or unidentified portal)."
        if page_html and any(m in page_html.lower() for m in CAPTCHA_MARKERS):
            return False, "CAPTCHA or bot-challenge detected; stopping without bypass."
        if mechanism == ApplyMechanism.GREENHOUSE and not apply_cfg.get("allow_greenhouse_http"):
            return False, "Greenhouse public job board automation is off (ToS-safe default)."
        if mechanism == ApplyMechanism.LEVER and not apply_cfg.get("allow_lever_http"):
            return False, "Lever form automation is off (ToS-safe default)."
        if mechanism in {ApplyMechanism.CAREER_PAGE, ApplyMechanism.OTHER_ATS}:
            if not apply_cfg.get("allow_browser_automation"):
                return False, "Browser form automation is disabled."
        return True, "Permitted"

    def remaining_human_action(self, mechanism: ApplyMechanism, reason: str) -> str:
        if mechanism == ApplyMechanism.GREENHOUSE:
            return (
                "Open the Greenhouse job URL, upload the tailored PDF, paste screening answers, "
                "complete any CAPTCHA/login, and submit. Then mark the application complete in JobPilot."
            )
        if mechanism == ApplyMechanism.LEVER:
            return "Open the Lever posting, attach the tailored CV, complete any human checks, and submit."
        if mechanism == ApplyMechanism.MANUAL:
            return "This posting cannot be automated (LinkedIn or prohibited portal). Apply in the official UI."
        return reason
