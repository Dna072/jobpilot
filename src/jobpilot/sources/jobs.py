from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

from jobpilot.analyst import infer_city, infer_country, infer_work_mode
from jobpilot.config import get_settings, load_app_config
from jobpilot.schemas.job import JobPosting


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
                        posted_at=_parse_dt(row.get("created_at")),
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
                    posted_at=_parse_dt(row.get("updated_at") or row.get("created_at")),
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
                    posted_at=_parse_dt(row.get("createdAt")),
                    raw={"company": company, "id": row.get("id")},
                )
            )
    return jobs


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        ts = value / 1000 if value > 10_000_000_000 else value
        return datetime.fromtimestamp(ts, tz=UTC)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def discover_jobs(limit: int | None = None) -> list[JobPosting]:
    config = load_app_config()
    scout = config.get("scout", {})
    per = limit or int(scout.get("max_jobs_per_source", 80))
    sources = scout.get("sources", {})
    found: list[JobPosting] = []
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
    return found


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
        posted_at=_parse_dt(payload.get("posted_at")),
        raw=payload,
    )
