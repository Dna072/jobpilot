from __future__ import annotations

from typing import Any

import httpx

from jobpilot.analyst import infer_city, infer_country, infer_work_mode
from jobpilot.config import get_settings, load_app_config
from jobpilot.geo import in_geographic_scope, location_rank
from jobpilot.schemas.job import JobPosting
from jobpilot.sources.util import parse_dt


def _client() -> httpx.Client:
    settings = get_settings()
    return httpx.Client(timeout=20.0, headers={"User-Agent": settings.http_user_agent})


def from_arbeitnow(limit: int = 80) -> list[JobPosting]:
    url = "https://www.arbeitnow.com/api/job-board-api"
    jobs: list[JobPosting] = []
    with _client() as client:
        page = 1
        while len(jobs) < limit:
            resp = client.get(url, params={"page": page})
            resp.raise_for_status()
            data = resp.json()
            rows = data.get("data") or []
            if not rows:
                break
            for row in rows:
                loc = row.get("location") or ""
                desc = row.get("description") or ""
                jobs.append(
                    JobPosting(
                        source="arbeitnow",
                        source_job_id=str(row.get("slug") or row.get("url")),
                        company=row.get("company_name") or "Unknown",
                        title=row.get("title") or "",
                        location=loc,
                        country=infer_country(loc),
                        city=infer_city(loc),
                        work_mode=infer_work_mode(loc, desc),
                        job_url=row.get("url") or "",
                        description=desc,
                        posted_at=parse_dt(row.get("created_at")),
                        raw=row if isinstance(row, dict) else {},
                    )
                )
                if len(jobs) >= limit:
                    break
            page += 1
            if page > 5:
                break
    return jobs


def from_greenhouse(board: str, limit: int = 80) -> list[JobPosting]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
    jobs: list[JobPosting] = []
    with _client() as client:
        resp = client.get(url, params={"content": "true"})
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        for row in (resp.json().get("jobs") or [])[:limit]:
            loc = (row.get("location") or {}).get("name") or ""
            jobs.append(
                JobPosting(
                    source="greenhouse",
                    source_job_id=str(row.get("id")),
                    company=board,
                    title=row.get("title") or "",
                    location=loc,
                    country=infer_country(loc),
                    city=infer_city(loc),
                    work_mode=infer_work_mode(loc, row.get("content") or ""),
                    job_url=row.get("absolute_url") or "",
                    description=row.get("content") or "",
                    posted_at=parse_dt(row.get("updated_at") or row.get("created_at")),
                    raw={"board": board, **{k: row.get(k) for k in ("id", "internal_job_id")}},
                )
            )
    return jobs


def from_lever(company: str, limit: int = 80) -> list[JobPosting]:
    url = f"https://api.lever.co/v0/postings/{company}"
    jobs: list[JobPosting] = []
    with _client() as client:
        resp = client.get(url, params={"mode": "json"})
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        for row in resp.json()[:limit]:
            cats = row.get("categories") or {}
            loc = cats.get("location") or row.get("country") or ""
            jobs.append(
                JobPosting(
                    source="lever",
                    source_job_id=str(row.get("id")),
                    company=company,
                    title=row.get("text") or "",
                    location=str(loc),
                    country=infer_country(str(loc)),
                    city=infer_city(str(loc)),
                    work_mode=infer_work_mode(str(loc), row.get("descriptionPlain") or ""),
                    job_url=row.get("hostedUrl") or row.get("applyUrl") or "",
                    description=row.get("descriptionPlain") or row.get("description") or "",
                    posted_at=parse_dt(row.get("createdAt")),
                    raw={"company": company, "id": row.get("id")},
                )
            )
    return jobs


def from_jobtech(limit: int = 80, queries: list[str] | None = None) -> list[JobPosting]:
    from jobpilot.sources.jobtech import (
        DEFAULT_QUERIES,
        JOBTECH_SEARCH,
        jobtech_params,
        posting_from_jobtech,
        priority_municipality_codes,
    )

    jobs: list[JobPosting] = []
    seen: set[str] = set()
    queries = queries or DEFAULT_QUERIES
    per_query = max(10, min(50, limit // 2))
    with _client() as client:
        for query in queries:
            for municipalities in (priority_municipality_codes(), None):
                if len(jobs) >= limit:
                    return jobs
                try:
                    resp = client.get(JOBTECH_SEARCH, params=jobtech_params(query, municipalities, per_query))
                    resp.raise_for_status()
                except httpx.HTTPError:
                    continue
                for hit in resp.json().get("hits") or []:
                    posting = posting_from_jobtech(hit)
                    key = posting.source_job_id or posting.job_url
                    if not key or key in seen:
                        continue
                    seen.add(key)
                    jobs.append(posting)
                    if len(jobs) >= limit:
                        return jobs
    return jobs


def from_remotive(limit: int = 80) -> list[JobPosting]:
    url = "https://remotive.com/api/remote-jobs"
    jobs: list[JobPosting] = []
    with _client() as client:
        resp = client.get(url, params={"category": "software-dev"})
        resp.raise_for_status()
        for row in (resp.json().get("jobs") or [])[: limit * 3]:
            loc = row.get("candidate_required_location") or ""
            posting = JobPosting(
                source="remotive",
                source_job_id=str(row.get("id") or ""),
                company=row.get("company_name") or "Unknown",
                title=row.get("title") or "",
                location=loc,
                country=infer_country(loc),
                city=infer_city(loc),
                work_mode=infer_work_mode(loc, row.get("description") or "remote"),
                job_url=row.get("url") or "",
                description=row.get("description") or "",
                posted_at=parse_dt(row.get("publication_date")),
                raw={"id": row.get("id")},
            )
            if in_geographic_scope(posting.location, posting.country, posting.city, posting.work_mode):
                jobs.append(posting)
            if len(jobs) >= limit:
                break
    return jobs


def from_adzuna(limit: int = 80, countries: list[str] | None = None) -> list[JobPosting]:
    settings = get_settings()
    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        return []
    countries = countries or ["se", "de", "nl", "at", "be", "ch", "dk", "no", "fi"]
    queries = ["data engineer", "backend engineer", "frontend engineer"]
    jobs: list[JobPosting] = []
    with _client() as client:
        for country in countries:
            if len(jobs) >= limit:
                break
            for query in queries:
                url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
                try:
                    resp = client.get(
                        url,
                        params={
                            "app_id": settings.adzuna_app_id,
                            "app_key": settings.adzuna_app_key,
                            "results_per_page": min(20, limit),
                            "what": query,
                            "content-type": "application/json",
                        },
                    )
                    if resp.status_code >= 400:
                        continue
                except httpx.HTTPError:
                    continue
                for row in resp.json().get("results") or []:
                    loc_obj = row.get("location") or {}
                    loc = loc_obj.get("display_name") or " ".join(loc_obj.get("area") or [])
                    company = (row.get("company") or {}).get("display_name") or "Unknown"
                    jobs.append(
                        JobPosting(
                            source="adzuna",
                            source_job_id=str(row.get("id") or ""),
                            company=company,
                            title=row.get("title") or "",
                            location=loc,
                            country=infer_country(loc) or country.upper(),
                            city=infer_city(loc),
                            work_mode=infer_work_mode(loc, row.get("description") or ""),
                            job_url=row.get("redirect_url") or row.get("adref") or "",
                            description=row.get("description") or "",
                            posted_at=parse_dt(row.get("created")),
                            raw={"id": row.get("id"), "country": country},
                        )
                    )
                    if len(jobs) >= limit:
                        return jobs
    return jobs


def _in_scope(posting: JobPosting) -> bool:
    return in_geographic_scope(posting.location, posting.country, posting.city, posting.work_mode)


def _sort_sweden_first(postings: list[JobPosting]) -> list[JobPosting]:
    return sorted(
        postings,
        key=lambda p: location_rank(p.location, p.country, p.city, p.work_mode),
        reverse=True,
    )


def discover_jobs(limit: int | None = None) -> list[JobPosting]:
    config = load_app_config()
    scout = config.get("scout", {})
    per = limit or int(scout.get("max_jobs_per_source", 80))
    sources = scout.get("sources", {})
    found: list[JobPosting] = []
    if sources.get("jobtech", {}).get("enabled", True):
        try:
            found.extend(from_jobtech(per, sources.get("jobtech", {}).get("queries")))
        except httpx.HTTPError:
            pass
    if sources.get("arbeitnow", {}).get("enabled", True):
        try:
            found.extend(from_arbeitnow(per))
        except httpx.HTTPError:
            pass
    if sources.get("greenhouse", {}).get("enabled", True):
        for board in sources.get("greenhouse", {}).get("boards", []):
            try:
                found.extend(from_greenhouse(board, per))
            except httpx.HTTPError:
                continue
    if sources.get("lever", {}).get("enabled", True):
        for company in sources.get("lever", {}).get("companies", []):
            try:
                found.extend(from_lever(company, per))
            except httpx.HTTPError:
                continue
    if sources.get("remotive", {}).get("enabled", True):
        try:
            found.extend(from_remotive(per))
        except httpx.HTTPError:
            pass
    if sources.get("adzuna", {}).get("enabled", False):
        try:
            found.extend(from_adzuna(per, sources.get("adzuna", {}).get("countries")))
        except httpx.HTTPError:
            pass
    scoped = [p for p in found if _in_scope(p)]
    return _sort_sweden_first(scoped)


def parse_generic_job(payload: dict[str, Any]) -> JobPosting:
    """Fixture / test helper for ingestion tests."""
    loc = payload.get("location") or ""
    return JobPosting(
        source=payload.get("source") or "manual",
        source_job_id=payload.get("id"),
        company=payload["company"],
        title=payload["title"],
        location=loc,
        country=payload.get("country") or infer_country(loc),
        city=payload.get("city") or infer_city(loc),
        work_mode=infer_work_mode(loc, payload.get("description") or ""),
        job_url=payload["job_url"],
        description=payload.get("description") or "",
        seniority=payload.get("seniority"),
        posted_at=parse_dt(payload.get("posted_at")),
        raw=payload,
    )
