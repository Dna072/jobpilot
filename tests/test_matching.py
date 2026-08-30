from jobpilot.analyst import analyze_job
from jobpilot.matching import match_job, score_location, select_resume
from jobpilot.schemas.common import MatchRecommendation, ResumeType, WorkMode
from jobpilot.schemas.job import JobPosting
from jobpilot.sources.jobs import parse_generic_job

DE_JOB = JobPosting(
    source="manual",
    source_job_id="1",
    company="Example AB",
    title="Senior Data Engineer",
    location="Stockholm, Sweden",
    country="Sweden",
    city="Stockholm",
    work_mode=WorkMode.HYBRID,
    job_url="https://example.com/jobs/de",
    description="""
    We need a Senior Data Engineer with 4 years of experience.
    Required: Python, SQL, Apache Spark, Apache Airflow, AWS, Redshift, PostgreSQL.
    Preferred: Kafka, dbt.
    Build ETL pipelines and a data warehouse. English required.
    """,
)


def test_analyst_extracts_required_and_preferred():
    analysis = analyze_job(DE_JOB)
    names = {r.normalized for r in analysis.requirements}
    assert "python" in names
    assert "sql" in names
    assert "spark" in names
    assert "airflow" in names
    levels = {r.normalized: r.level.value for r in analysis.requirements}
    assert levels.get("kafka") in {"PREFERRED", "NICE_TO_HAVE", "REQUIRED"}
    assert analysis.country == "Sweden"
    assert analysis.years_required == 4


def test_match_data_engineer_is_strong():
    analysis = analyze_job(DE_JOB)
    report = match_job(analysis)
    assert report.score >= 70
    assert "python" in [s.lower() for s in report.strong_matches] or "Python" in str(report.strong_matches)
    assert report.recommendation in {
        MatchRecommendation.APPLY_NOW,
        MatchRecommendation.APPLY_AFTER_PROJECT,
        MatchRecommendation.HUMAN_REVIEW,
    }


def test_sweden_priority_cities_beat_other_eu():
    uppsala = analyze_job(DE_JOB.model_copy(update={"location": "Uppsala, Sweden", "city": "Uppsala"}))
    berlin = analyze_job(
        DE_JOB.model_copy(update={"location": "Berlin, Germany", "country": "Germany", "city": "Berlin"})
    )
    assert score_location(uppsala) > score_location(berlin)
    assert score_location(uppsala) == 1.0


def test_low_match_remote_us():
    posting = DE_JOB.model_copy(
        update={
            "title": "Principal Java Architect",
            "location": "New York, USA",
            "country": "United States",
            "work_mode": WorkMode.ONSITE,
            "description": "Required: COBOL, mainframe, 15 years Java EE, security clearance.",
            "job_url": "https://example.com/jobs/nope",
        }
    )
    report = match_job(analyze_job(posting))
    assert report.recommendation in {MatchRecommendation.DO_NOT_APPLY, MatchRecommendation.LOW_PRIORITY}


def test_resume_selection_data_role():
    analysis = analyze_job(DE_JOB)
    result = select_resume(analysis)
    assert result["selected"] == ResumeType.DATA_ENGINEER.value
    assert result["DATA_ENGINEER"] >= result["FRONTEND_ENGINEER"]


def test_resume_selection_frontend_role():
    posting = JobPosting(
        source="manual",
        company="Example",
        title="Frontend Engineer",
        location="Stockholm, Sweden",
        job_url="https://example.com/fe",
        description="Required: React, Next.js, TypeScript, Tailwind, accessibility, Vite. Build UI components.",
    )
    result = select_resume(analyze_job(posting))
    assert result["selected"] == ResumeType.FRONTEND_ENGINEER.value
    assert result["FRONTEND_ENGINEER"] > result["DATA_ENGINEER"]


def test_parse_generic_job():
    posting = parse_generic_job(
        {
            "id": "abc",
            "company": "Spotify",
            "title": "Data Engineer",
            "location": "Stockholm, Sweden",
            "job_url": "https://example.com/x",
            "description": "Python SQL remote Europe",
        }
    )
    assert posting.company == "Spotify"
    assert posting.country == "Sweden"
