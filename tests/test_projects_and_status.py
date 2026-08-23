from pathlib import Path

from jobpilot.agents.builder import scaffold_project
from jobpilot.agents.planner import STREAMING_SPEC, plan_from_gap
from jobpilot.agents.qa import qa_project
from jobpilot.agents.status import format_status
from jobpilot.analyst import analyze_job
from jobpilot.matching import analyze_gaps
from jobpilot.resume.tailor import slug, tailor_master
from jobpilot.schemas.common import ResumeType
from jobpilot.schemas.job import JobPosting


def test_planner_streaming_spec():
    posting = JobPosting(
        source="manual",
        company="X",
        title="Data Platform Engineer",
        location="Stockholm",
        job_url="https://example.com/k",
        description="Required: Kafka Python Spark AWS Kubernetes streaming",
    )
    spec = plan_from_gap(analyze_gaps(analyze_job(posting)))
    assert spec is not None
    assert "Kafka" in spec.architecture
    assert spec.repository_name == "eventpulse"


def test_builder_and_qa(tmp_path):
    written = scaffold_project(tmp_path / "eventpulse", STREAMING_SPEC)
    assert any(p.endswith("README.md") for p in written)
    result = qa_project(tmp_path / "eventpulse")
    assert result["ok"] is True


def test_tailor_does_not_invent_employer():
    tex = "% master\nDerrick Adjei\n"
    out = tailor_master(tex, analyze_job(JobPosting(
        source="m", company="Klarna", title="Data Engineer", job_url="https://x", description="Python SQL"
    )), ResumeType.DATA_ENGINEER)
    assert "Klarna" in out
    assert "Google" not in out
    assert out.endswith(tex) or tex in out


def test_slug_safe():
    assert " " not in slug("Klarna AB", "Senior Data Engineer")


def test_status_format():
    text = format_status({
        "jobs_discovered": 342,
        "jobs_analyzed": 287,
        "strong_matches": 31,
        "applications_submitted": 14,
        "human_actions_required": 3,
        "projects_created": 2,
        "projects_upgraded": 4,
        "failed_applications": 1,
    })
    assert "342" in text
    assert "Jobs discovered" in text


def test_masters_use_official_leslie_cheng_template():
    root = Path(__file__).resolve().parents[1]
    for rel in (
        "cv/data-engineer/master.tex",
        "cv/backend-engineer/master.tex",
        "cv/frontend-engineer/master.tex",
    ):
        text = (root / rel).read_text(encoding="utf-8")
        assert "FiraSans" in text
        assert "0D47A1" in text
        assert "Derrick Adjei" in text
        assert "resumeEntryTSDL" in text
