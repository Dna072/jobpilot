"""Official public ATS apply endpoints only. No private APIs, no CAPTCHA bypass."""

from __future__ import annotations

import re

import httpx

from jobpilot.config import get_settings
from jobpilot.knowledge import load_candidate_profile
from jobpilot.schemas.application import ApplicationPackage

GREENHOUSE_JOB = re.compile(
    r"greenhouse\.io/(?:embed/)?(?P<board>[^/]+)/jobs/(?P<job>\d+)",
    re.I,
)
LEVER_JOB = re.compile(
    r"jobs\.lever\.co/(?P<company>[^/]+)/(?P<job>[0-9a-f-]+)",
    re.I,
)


def parse_greenhouse(url: str) -> tuple[str, str] | None:
    match = GREENHOUSE_JOB.search(url or "")
    if not match:
        return None
    return match.group("board"), match.group("job")


def parse_lever(url: str) -> tuple[str, str] | None:
    match = LEVER_JOB.search(url or "")
    if not match:
        return None
    return match.group("company"), match.group("job")


def submit_official(job_url: str, package: ApplicationPackage) -> dict:
    gh = parse_greenhouse(job_url)
    if gh:
        return submit_greenhouse(gh[0], gh[1], package)
    lever = parse_lever(job_url)
    if lever:
        return submit_lever(lever[0], lever[1], package)
    return {
        "ok": False,
        "human": True,
        "error": "This job is not on a public Greenhouse or Lever board, so it has to be sent by hand.",
    }


def submit_greenhouse(board: str, job_id: str, package: ApplicationPackage) -> dict:
    profile = load_candidate_profile()
    first, _, last = profile["full_name"].partition(" ")
    data = {
        "first_name": first or profile["full_name"],
        "last_name": last or first,
        "email": profile["email"],
        "phone": profile.get("phone") or "",
    }
    files = _resume_files(package)
    settings = get_settings()
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{job_id}"
    questions = _greenhouse_required_unanswered(board, job_id, package)
    if questions:
        return {
            "ok": False,
            "human": True,
            "error": "The form asks extra questions that still need your answers: " + "; ".join(questions),
        }
    with httpx.Client(timeout=30.0, headers={"User-Agent": settings.http_user_agent}) as client:
        resp = client.post(url, data=data, files=files or None)
    if resp.status_code >= 400:
        return {
            "ok": False,
            "human": True,
            "error": "The company site did not accept the automatic form. Please submit it yourself.",
            "http_status": resp.status_code,
        }
    body = {}
    try:
        body = resp.json()
    except ValueError:
        body = {"text": resp.text[:500]}
    return {
        "ok": True,
        "confirmation_id": str(body.get("id") or body.get("application_id") or f"gh-{job_id}"),
        "evidence": {"http_status": resp.status_code, "ats": "greenhouse", **{k: body.get(k) for k in ("id", "success")}},
    }


def submit_lever(company: str, posting_id: str, package: ApplicationPackage) -> dict:
    settings = get_settings()
    key = (settings.lever_api_key or "").strip()
    if not key:
        return {
            "ok": False,
            "human": True,
            "error": "This Lever board needs an API key, so please submit it yourself on the company page.",
        }
    profile = load_candidate_profile()
    data = {
        "name": profile["full_name"],
        "email": profile["email"],
        "phone": profile.get("phone") or "",
        "comments": package.cover_letter or "",
        "urls[LinkedIn]": profile.get("linkedin") or "",
        "urls[GitHub]": profile.get("github") or "",
    }
    files = _resume_files(package)
    url = f"https://api.lever.co/v0/postings/{company}/{posting_id}"
    if "?" not in url:
        url = f"{url}?key={key}"
    with httpx.Client(timeout=30.0, headers={"User-Agent": settings.http_user_agent}) as client:
        resp = client.post(url, data=data, files=files or None)
    if resp.status_code >= 400:
        return {
            "ok": False,
            "human": True,
            "error": "The company site did not accept the automatic form. Please submit it yourself.",
            "http_status": resp.status_code,
        }
    body = {}
    try:
        body = resp.json()
    except ValueError:
        body = {"text": resp.text[:500]}
    return {
        "ok": True,
        "confirmation_id": str(body.get("applicationId") or body.get("id") or f"lever-{posting_id}"),
        "evidence": {"http_status": resp.status_code, "ats": "lever"},
    }


def _greenhouse_required_unanswered(board: str, job_id: str, package: ApplicationPackage) -> list[str]:
    settings = get_settings()
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{job_id}"
    try:
        with httpx.Client(timeout=20.0, headers={"User-Agent": settings.http_user_agent}) as client:
            resp = client.get(url, params={"questions": "true"})
            if resp.status_code >= 400:
                return []
            questions = resp.json().get("questions") or []
    except httpx.HTTPError:
        return []
    known = {a.question.lower() for a in package.screening_answers}
    missing = []
    for q in questions:
        if not q.get("required"):
            continue
        label = (q.get("label") or q.get("description") or "").strip()
        field = (q.get("fields") or [{}])[0].get("name") or ""
        if field in {"first_name", "last_name", "email", "phone", "resume", "cover_letter"}:
            continue
        if label and label.lower() in known:
            continue
        if label:
            missing.append(label)
    return missing[:8]


def _resume_files(package: ApplicationPackage) -> dict[str, tuple[str, bytes, str]] | None:
    from jobpilot.storage import read_bytes

    data = read_bytes(package.resume_pdf_path)
    if data is None:
        return None
    files: dict[str, tuple[str, bytes, str]] = {
        "resume": ("resume.pdf", data, "application/pdf"),
    }
    if package.cover_letter:
        files["cover_letter"] = (
            "cover_letter.txt",
            package.cover_letter.encode("utf-8"),
            "text/plain",
        )
    return files
