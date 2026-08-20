from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import httpx

from jobpilot.config import get_settings, load_app_config
from jobpilot.db.models import ProjectRepository, get_session
from jobpilot.schemas.common import ProjectStatus


def watch_repositories() -> list[dict]:
    """Detect repos the human created. Never create them."""
    settings = get_settings()
    config = load_app_config()
    roots = [Path(p) for p in config.get("project_strategy", {}).get("project_roots", ["/workspace"])]
    session = get_session()
    updates = []
    try:
        pending = (
            session.query(ProjectRepository)
            .filter(ProjectRepository.status == ProjectStatus.WAITING_FOR_REPOSITORY.value)
            .all()
        )
        remote_names = _list_github_repos(settings.github_username, settings.github_token)
        for row in pending:
            local = _find_local(roots, row.requested_name)
            remote = next((u for name, u in remote_names if name.lower() == row.requested_name.lower()), None)
            if local or remote:
                row.status = ProjectStatus.REPOSITORY_FOUND.value
                row.local_path = str(local) if local else None
                row.github_url = remote
                row.detected_at = datetime.now(UTC)
                updates.append({"name": row.requested_name, "local": row.local_path, "github": remote})
        session.commit()
    finally:
        session.close()
    return updates


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


def _list_github_repos(username: str, token: str) -> list[tuple[str, str]]:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        resp = httpx.get(
            f"https://api.github.com/users/{username}/repos",
            params={"per_page": 100},
            headers=headers,
            timeout=20.0,
        )
        if resp.status_code >= 400:
            return []
        return [(r["name"], r["html_url"]) for r in resp.json()]
    except httpx.HTTPError:
        return []
