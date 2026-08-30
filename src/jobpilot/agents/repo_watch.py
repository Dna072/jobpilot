from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import httpx

from jobpilot.agents.github_sync import token_is_usable
from jobpilot.config import get_settings, load_app_config
from jobpilot.db.models import Application, Notification, ProjectRepository, get_session
from jobpilot.emailer import email_github_token_needed, email_project_complete
from jobpilot.schemas.common import ApplicationStatus, ProjectStatus
from jobpilot.schemas.portfolio import ProjectSpec


def watch_repositories() -> list[dict]:
    """Detect repos the human created, then write and push the project code."""
    settings = get_settings()
    config = load_app_config()
    roots = [Path(p) for p in config.get("project_strategy", {}).get("project_roots", ["/workspace"])]
    session = get_session()
    updates = []
    completed_names: list[str] = []
    try:
        pending = (
            session.query(ProjectRepository)
            .filter(
                ProjectRepository.status.in_(
                    [
                        ProjectStatus.WAITING_FOR_REPOSITORY.value,
                        ProjectStatus.REPOSITORY_FOUND.value,
                    ]
                )
            )
            .all()
        )
        remote_names = _list_github_repos(settings.github_username, settings.github_token)
        for row in pending:
            local = _find_local(roots, row.requested_name)
            remote = next((u for name, u in remote_names if name.lower() == row.requested_name.lower()), None)
            remote = remote or _github_repo_url(settings.github_username, row.requested_name, settings.github_token)
            if not (local or remote):
                continue
            row.status = ProjectStatus.REPOSITORY_FOUND.value
            row.local_path = str(local) if local else row.local_path
            row.github_url = remote or row.github_url
            row.detected_at = row.detected_at or datetime.now(UTC)
            fill = _fill_repository(row, local)
            updates.append(fill)
            if fill.get("ok"):
                row.status = ProjectStatus.PROJECT_COMPLETE.value
                row.local_path = fill.get("local_path") or row.local_path
                completed_names.append(row.requested_name)
                body = (
                    f"Hi Derrick,\n\n"
                    f"The starter code is now in {row.github_url or row.requested_name}. "
                    f"You can open that repository on GitHub to review it.\n"
                )
                result = email_project_complete(row.requested_name, body)
                session.add(
                    Notification(
                        kind="project_complete",
                        subject=f"The {row.requested_name} repository is ready to use",
                        body=body,
                        sent=bool(result.get("sent")),
                    )
                )
            else:
                row.status = ProjectStatus.REPOSITORY_FOUND.value
                _notify_fill_blocked(session, row, fill.get("error") or "")
        session.commit()
        waiting_ids = [
            a.job_id
            for a in session.query(Application)
            .filter(Application.status == ApplicationStatus.WAITING_FOR_REPOSITORY.value)
            .all()
        ]
    finally:
        session.close()
    if completed_names:
        from jobpilot.agents.orchestrator import process_job

        for job_id in waiting_ids:
            try:
                process_job(job_id)
            except Exception:
                continue
    return updates


def _fill_repository(row: ProjectRepository, local: Path | None) -> dict:
    spec = None
    if row.spec:
        try:
            spec = ProjectSpec.model_validate(row.spec)
        except Exception:
            spec = None
    if row.github_url:
        from jobpilot.agents.github_sync import fill_and_push

        return fill_and_push(row.requested_name, row.github_url, spec)
    if local and local.exists():
        from jobpilot.agents.builder import scaffold_project
        from jobpilot.agents.planner import STREAMING_SPEC
        from jobpilot.agents.qa import qa_project

        used = spec or STREAMING_SPEC
        written = scaffold_project(local, used)
        qa = qa_project(local)
        return {"ok": True, "local_path": str(local), "written": written, "qa": qa}
    return {"ok": False, "error": "Repository was found but there is no local path or GitHub URL."}


def _notify_fill_blocked(session, row: ProjectRepository, error: str) -> None:
    settings = get_settings()
    kind = "github_token_needed" if not token_is_usable(settings.github_token) else "github_push_failed"
    already = (
        session.query(Notification)
        .filter(Notification.kind == kind, Notification.subject.contains(row.requested_name))
        .first()
    )
    if already:
        return
    if kind == "github_token_needed":
        result = email_github_token_needed(row.requested_name, row.github_url or "")
        session.add(
            Notification(
                kind=kind,
                subject=f"A GitHub token is needed to add code to {row.requested_name}",
                body=result.get("body") or error,
                sent=bool(result.get("sent")),
            )
        )
        return
    session.add(
        Notification(
            kind=kind,
            subject=f"Could not add starter code to {row.requested_name}",
            body=error,
            sent=False,
        )
    )


def _find_local(roots: list[Path], name: str) -> Path | None:
    for root in roots:
        candidate = root / name
        if candidate.exists():
            return candidate
        if root.exists():
            for child in root.iterdir():
                if child.is_dir() and child.name.lower() == name.lower():
                    return child
    return None


def _github_headers(token: str) -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    if token_is_usable(token):
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _github_repo_url(username: str, name: str, token: str) -> str | None:
    try:
        resp = httpx.get(
            f"https://api.github.com/repos/{username}/{name}",
            headers=_github_headers(token),
            timeout=20.0,
        )
        if resp.status_code >= 400:
            return None
        return resp.json().get("html_url")
    except httpx.HTTPError:
        return None


def _list_github_repos(username: str, token: str) -> list[tuple[str, str]]:
    headers = _github_headers(token)
    url = "https://api.github.com/user/repos" if token_is_usable(token) else f"https://api.github.com/users/{username}/repos"
    try:
        resp = httpx.get(
            url,
            params={"per_page": 100, "affiliation": "owner"} if token_is_usable(token) else {"per_page": 100},
            headers=headers,
            timeout=20.0,
        )
        if resp.status_code >= 400:
            return []
        return [(r["name"], r["html_url"]) for r in resp.json()]
    except httpx.HTTPError:
        return []
