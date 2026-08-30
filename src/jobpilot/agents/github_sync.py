"""Clone a human-created GitHub repo, write the project skeleton, and push."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

from jobpilot.agents.builder import scaffold_project
from jobpilot.agents.qa import qa_project
from jobpilot.config import get_settings
from jobpilot.schemas.portfolio import ProjectSpec

WORKDIR = Path("/tmp/jobpilot-projects")


def token_is_usable(token: str | None) -> bool:
    value = (token or "").strip()
    return bool(value) and value.lower() not in {"unset", "changeme", "placeholder"}


def fill_and_push(name: str, github_url: str, spec: ProjectSpec | None) -> dict:
    settings = get_settings()
    token = (settings.github_token or "").strip()
    if not token_is_usable(token):
        return {
            "ok": False,
            "error": "A GitHub token with access to this repository is needed before code can be pushed.",
        }
    root = WORKDIR / name
    WORKDIR.mkdir(parents=True, exist_ok=True)
    clone_url = _authenticated_clone_url(github_url, token)
    if not (root / ".git").exists():
        if root.exists():
            shutil.rmtree(root)
        result = _run(["git", "clone", clone_url, str(root)])
        if result.returncode != 0:
            return {"ok": False, "error": result.stderr or result.stdout or "Could not clone the repository."}
    spec = spec or _default_spec(name)
    written = scaffold_project(root, spec)
    qa = qa_project(root)
    _run(["git", "-C", str(root), "config", "user.email", "derrick.adjei.eng@gmail.com"])
    _run(["git", "-C", str(root), "config", "user.name", "Derrick Adjei"])
    _run(["git", "-C", str(root), "checkout", "-B", "main"])
    _run(["git", "-C", str(root), "add", "-A"])
    commit = _run(
        ["git", "-C", str(root), "commit", "-m", f"Add {spec.title} project skeleton"],
    )
    if commit.returncode != 0 and "nothing to commit" not in (commit.stdout + commit.stderr):
        return {"ok": False, "error": commit.stderr or commit.stdout or "Could not commit files."}
    push = _run(["git", "-C", str(root), "push", "-u", "origin", "HEAD:main"])
    if push.returncode != 0:
        push = _run(["git", "-C", str(root), "push", "-u", "origin", "HEAD"])
    if push.returncode != 0:
        return {"ok": False, "error": push.stderr or push.stdout or "Could not push to GitHub."}
    return {
        "ok": True,
        "local_path": str(root),
        "written": written,
        "qa": qa,
        "github_url": github_url,
    }


def _default_spec(name: str) -> ProjectSpec:
    from jobpilot.agents.planner import STREAMING_SPEC

    if name.lower() == STREAMING_SPEC.repository_name.lower():
        return STREAMING_SPEC
    return STREAMING_SPEC.model_copy(update={"repository_name": name, "title": name})


def _authenticated_clone_url(html_url: str, token: str) -> str:
    slug = html_url.rstrip("/").split("github.com/", 1)[-1]
    if slug.endswith(".git"):
        slug = slug[:-4]
    return f"https://x-access-token:{token}@github.com/{slug}.git"


def _redact(text: str) -> str:
    return re.sub(r"x-access-token:[^@\s]+@", "x-access-token:***@", text or "")


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "echo"}
    result = subprocess.run(cmd, check=False, capture_output=True, text=True, env=env)
    return subprocess.CompletedProcess(
        result.args,
        result.returncode,
        _redact(result.stdout),
        _redact(result.stderr),
    )
