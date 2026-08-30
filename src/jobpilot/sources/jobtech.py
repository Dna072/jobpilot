"""Arbetsförmedlingen JobSearch (JobTech) — official Swedish job ads."""

from __future__ import annotations

from typing import Any

from jobpilot.analyst import infer_city, infer_country, infer_work_mode
from jobpilot.geo import JOBTECH_PRIORITY_MUNICIPALITIES
from jobpilot.schemas.job import JobPosting
from jobpilot.sources.util import parse_dt

JOBTECH_SEARCH = "https://jobsearch.api.jobtechdev.se/search"

DEFAULT_QUERIES = [
    "data engineer",
    "analytics engineer",
    "backend engineer",
    "backend developer",
    "frontend engineer",
    "frontend developer",
    "platform engineer",
    "software engineer",
    "python developer",
]


def posting_from_jobtech(hit: dict[str, Any]) -> JobPosting:
    addr = hit.get("workplace_address") or {}
    city = addr.get("city") or addr.get("municipality") or ""
    country_raw = addr.get("country") or "Sweden"
    country = "Sweden" if str(country_raw).lower() in {"sverige", "sweden"} else country_raw
    location = ", ".join(p for p in (city, country) if p)
    desc = ""
    description = hit.get("description") or {}
    if isinstance(description, dict):
        desc = description.get("text") or ""
    elif isinstance(description, str):
        desc = description
    apply = (hit.get("application_details") or {}).get("url") or hit.get("webpage_url") or ""
    employer = hit.get("employer") or {}
    return JobPosting(
        source="jobtech",
        source_job_id=str(hit.get("id") or ""),
        company=employer.get("name") or employer.get("workplace") or "Unknown",
        title=hit.get("headline") or "",
        location=location,
        country=country or infer_country(location),
        city=city or infer_city(location),
        work_mode=infer_work_mode(location, desc),
        job_url=apply,
        description=desc,
        posted_at=parse_dt(hit.get("publication_date")),
        closing_at=parse_dt(hit.get("application_deadline") or hit.get("last_publication_date")),
        raw={"id": hit.get("id"), "webpage_url": hit.get("webpage_url")},
    )


def jobtech_params(query: str, municipalities: list[str] | None, limit: int) -> list[tuple[str, str]]:
    params: list[tuple[str, str]] = [
        ("q", query),
        ("limit", str(limit)),
        ("sort", "pubdate-desc"),
    ]
    if municipalities:
        for code in municipalities:
            params.append(("municipality", code))
    else:
        params.append(("country", "199"))
    return params


def priority_municipality_codes() -> list[str]:
    return list(JOBTECH_PRIORITY_MUNICIPALITIES.keys())
