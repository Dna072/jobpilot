from jobpilot.agents.orchestrator import ingest_postings, process_job, seed_knowledge
from jobpilot.db.models import Application, Job, get_session
from jobpilot.llm import get_provider
from jobpilot.llm.provider import HeuristicProvider
from jobpilot.schemas.job import JobPosting
from jobpilot.sources.jobs import parse_generic_job


def test_ingestion_skips_us_only_roles():
    seed_knowledge()
    us = parse_generic_job(
        {
            "id": "us-1",
            "source": "manual",
            "company": "Example US",
            "title": "Data Engineer",
            "location": "New York, USA",
            "country": "United States",
            "job_url": "https://example.com/us",
            "description": "Onsite New York. Required: Python.",
        }
    )
    se = parse_generic_job(
        {
            "id": "se-1",
            "source": "manual",
            "company": "Example AB",
            "title": "Data Engineer",
            "location": "Uppsala, Sweden",
            "job_url": "https://example.com/se",
            "description": "Hybrid Uppsala. Required: Python SQL.",
        }
    )
    assert ingest_postings([us, se]) == 1


def test_ingestion_dedup():
    seed_knowledge()
    posting = parse_generic_job(
        {
            "id": "gh-1",
            "source": "manual",
            "company": "Spotify",
            "title": "Data Engineer",
            "location": "Stockholm",
            "job_url": "https://example.com/spotify-de",
            "description": "Required: Python SQL Airflow AWS Redshift PostgreSQL. Hybrid Stockholm Sweden.",
        }
    )
    assert ingest_postings([posting, posting]) == 1
    session = get_session()
    try:
        assert session.query(Job).count() == 1
    finally:
        session.close()


def test_process_job_does_not_mark_submitted():
    seed_knowledge()
    posting = JobPosting(
        source="manual",
        source_job_id="job-42",
        company="Example AB",
        title="Data Engineer",
        location="Stockholm, Sweden",
        job_url="https://example.com/apply",
        description="Required: Python, SQL, Airflow, AWS, Redshift, PostgreSQL. Hybrid Stockholm.",
    )
    ingest_postings([posting])
    session = get_session()
    try:
        job = session.query(Job).one()
        job_id = job.id
    finally:
        session.close()
    result = process_job(job_id)
    assert result["status"] != "SUBMITTED"
    session = get_session()
    try:
        app = session.query(Application).filter_by(job_id=job_id).one()
        assert app.status != "SUBMITTED"
        assert app.confirmation_id is None
    finally:
        session.close()


def test_llm_heuristic_structured_output():
    from pydantic import BaseModel

    class Out(BaseModel):
        note: str = "ok"

    provider = get_provider()
    assert isinstance(provider, HeuristicProvider)
    parsed = provider.complete_json("ignored", Out)
    assert parsed.note == "ok"
