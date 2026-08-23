from jobpilot.agents.github_sync import fill_and_push, token_is_usable
from jobpilot.agents.repo_watch import watch_repositories
from jobpilot.config import get_settings
from jobpilot.db.models import Notification, ProjectRepository, get_session
from jobpilot.emailer import render_repo_request
from jobpilot.schemas.common import ProjectStatus


def test_token_placeholder_is_not_usable():
    assert token_is_usable("") is False
    assert token_is_usable("unset") is False
    assert token_is_usable("changeme") is False
    assert token_is_usable("ghp_real_token") is True


def test_fill_and_push_requires_token(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "unset")
    get_settings.cache_clear()
    result = fill_and_push("eventpulse", "https://github.com/Dna072/eventpulse", None)
    assert result["ok"] is False
    assert "token" in result["error"].lower()


def test_watch_scaffolds_local_repo_without_github(tmp_path, monkeypatch):
    dest = tmp_path / "eventpulse"
    dest.mkdir()
    session = get_session()
    session.add(
        ProjectRepository(
            requested_name="eventpulse",
            status=ProjectStatus.WAITING_FOR_REPOSITORY.value,
            spec={},
        )
    )
    session.commit()
    session.close()

    monkeypatch.setattr("jobpilot.agents.repo_watch._list_github_repos", lambda *args, **kwargs: [])
    monkeypatch.setattr("jobpilot.agents.repo_watch._github_repo_url", lambda *args, **kwargs: None)
    monkeypatch.setattr("jobpilot.agents.repo_watch._find_local", lambda *args, **kwargs: dest)

    updates = watch_repositories()
    assert updates
    assert updates[0]["ok"] is True
    assert (dest / "README.md").exists()
    session = get_session()
    row = session.query(ProjectRepository).one()
    assert row.status == ProjectStatus.PROJECT_COMPLETE.value
    session.close()


def test_watch_keeps_found_status_and_emails_when_token_missing(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "unset")
    get_settings.cache_clear()
    session = get_session()
    session.add(
        ProjectRepository(
            requested_name="eventpulse",
            status=ProjectStatus.REPOSITORY_FOUND.value,
            github_url="https://github.com/Dna072/eventpulse",
            spec={},
        )
    )
    session.commit()
    session.close()

    monkeypatch.setattr(
        "jobpilot.agents.repo_watch._list_github_repos",
        lambda *args, **kwargs: [("eventpulse", "https://github.com/Dna072/eventpulse")],
    )
    monkeypatch.setattr(
        "jobpilot.agents.repo_watch._github_repo_url",
        lambda *args, **kwargs: "https://github.com/Dna072/eventpulse",
    )

    updates = watch_repositories()
    assert updates
    assert updates[0]["ok"] is False
    session = get_session()
    row = session.query(ProjectRepository).one()
    assert row.status == ProjectStatus.REPOSITORY_FOUND.value
    note = session.query(Notification).filter_by(kind="github_token_needed").one()
    assert "eventpulse" in note.subject
    session.close()

    watch_repositories()
    session = get_session()
    assert session.query(Notification).filter_by(kind="github_token_needed").count() == 1
    session.close()


def test_repo_request_says_code_will_be_added():
    body = render_repo_request(
        "Real-Time Event Processing and Analytics Platform",
        "eventpulse",
        "Streaming evidence",
        ["Data Engineer"],
        ["Kafka"],
        "Producers → Kafka",
    )
    assert "eventpulse" in body
    assert "github.com/new" in body
    assert "automatically" in body
    assert "Clone it onto this machine" not in body
    assert "JobPilot" not in body
    assert "WAITING_FOR_REPOSITORY" not in body
