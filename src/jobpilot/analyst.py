from __future__ import annotations

import re

from jobpilot.schemas.common import RequirementLevel, WorkMode
from jobpilot.schemas.job import ExtractedRequirement, JobAnalysis, JobPosting
from jobpilot.skills import canonical_skill, extract_skills_from_text, load_taxonomy

YEARS_RE = re.compile(r"(\d+)\+?\s*\+?\s*(?:years|yrs)", re.I)
SENIORITY_RE = re.compile(
    r"\b(intern|junior|graduate|mid[- ]level|senior|staff|principal|lead|director)\b", re.I
)

REQUIRED_HINTS = ("required", "must have", "you have", "minimum qualifications", "we need")
PREFERRED_HINTS = ("preferred", "nice to have", "bonus", "plus", "good to have")


def _split_sections(text: str) -> tuple[str, str]:
    lower = text.lower()
    pref_idx = -1
    for hint in PREFERRED_HINTS:
        i = lower.find(hint)
        if i != -1:
            pref_idx = i if pref_idx == -1 else min(pref_idx, i)
    if pref_idx == -1:
        return text, ""
    return text[:pref_idx], text[pref_idx:]


def _category_for(skill: str) -> str:
    tax = load_taxonomy()
    skill = canonical_skill(skill)
    for cat, names in tax.get("categories", {}).items():
        if skill in names or skill in [n.lower() for n in names]:
            return cat
    return "other"


def infer_work_mode(location: str, description: str) -> WorkMode:
    blob = f"{location} {description}".lower()
    if "hybrid" in blob:
        return WorkMode.HYBRID
    if "remote" in blob:
        return WorkMode.REMOTE
    if "on-site" in blob or "onsite" in blob or "on site" in blob:
        return WorkMode.ONSITE
    return WorkMode.UNKNOWN


def infer_country(location: str) -> str | None:
    mapping = {
        "sweden": "Sweden",
        "stockholm": "Sweden",
        "gothenburg": "Sweden",
        "göteborg": "Sweden",
        "malmö": "Sweden",
        "malmo": "Sweden",
        "uppsala": "Sweden",
        "denmark": "Denmark",
        "copenhagen": "Denmark",
        "norway": "Norway",
        "oslo": "Norway",
        "finland": "Finland",
        "helsinki": "Finland",
        "germany": "Germany",
        "berlin": "Germany",
        "munich": "Germany",
        "netherlands": "Netherlands",
        "amsterdam": "Netherlands",
        "switzerland": "Switzerland",
        "zurich": "Switzerland",
        "ireland": "Ireland",
        "dublin": "Ireland",
        "belgium": "Belgium",
        "remote europe": "Europe",
        "eu remote": "Europe",
    }
    blob = location.lower()
    for key, country in mapping.items():
        if key in blob:
            return country
    return None


def infer_city(location: str) -> str | None:
    cities = [
        "Stockholm",
        "Gothenburg",
        "Göteborg",
        "Goteborg",
        "Malmö",
        "Malmo",
        "Uppsala",
        "Copenhagen",
        "Oslo",
        "Helsinki",
        "Berlin",
        "Amsterdam",
        "Zurich",
        "Dublin",
    ]
    blob = location.lower()
    for city in cities:
        if city.lower() in blob:
            return city
    return None


def analyze_job(posting: JobPosting) -> JobAnalysis:
    text = "\n".join(
        [
            posting.title,
            posting.description,
            posting.requirements_raw,
            posting.preferred_raw,
        ]
    )
    req_section, pref_section = _split_sections(text)
    required_skills = extract_skills_from_text(req_section or text)
    preferred_skills = extract_skills_from_text(pref_section) if pref_section else []
    preferred_skills = [s for s in preferred_skills if s not in required_skills]

    requirements: list[ExtractedRequirement] = []
    dist: dict[str, int] = {}
    for skill in required_skills:
        cat = _category_for(skill)
        dist[cat] = dist.get(cat, 0) + 1
        requirements.append(
            ExtractedRequirement(
                name=skill,
                normalized=canonical_skill(skill),
                category=cat,
                level=RequirementLevel.REQUIRED,
            )
        )
    for skill in preferred_skills:
        cat = _category_for(skill)
        dist[cat] = dist.get(cat, 0) + 1
        requirements.append(
            ExtractedRequirement(
                name=skill,
                normalized=canonical_skill(skill),
                category=cat,
                level=RequirementLevel.PREFERRED,
            )
        )

    years = None
    m = YEARS_RE.search(text)
    if m:
        years = float(m.group(1))
    sen = posting.seniority
    sm = SENIORITY_RE.search(posting.title + " " + text[:400])
    if sm and not sen:
        sen = sm.group(1).lower()

    languages = []
    for lang in ("english", "swedish", "german", "dutch", "french", "finnish", "norwegian", "danish"):
        if re.search(rf"\b{lang}\b", text.lower()):
            languages.append(lang)
    education = []
    if re.search(r"\b(phd|doctorate)\b", text.lower()):
        education.append("PhD")
    if re.search(r"\b(master|msc|m\.sc)\b", text.lower()):
        education.append("Master")
    if re.search(r"\b(bachelor|bsc|b\.sc)\b", text.lower()):
        education.append("Bachelor")

    work_mode = posting.work_mode if posting.work_mode != WorkMode.UNKNOWN else infer_work_mode(
        posting.location, posting.description
    )
    country = posting.country or infer_country(posting.location + " " + posting.description[:500])
    city = posting.city or infer_city(posting.location)

    leadership = bool(re.search(r"\b(lead|mentor|manage|people manager)\b", text.lower()))
    auth = posting.work_authorization
    if not auth and re.search(r"work (permit|authorization|visa)|must be eligible", text.lower()):
        auth = "mentioned"

    return JobAnalysis(
        job_url=posting.job_url,
        title=posting.title,
        company=posting.company,
        seniority=sen,
        years_required=years,
        education=education,
        languages=languages,
        location=posting.location,
        country=country,
        city=city,
        work_mode=work_mode,
        work_authorization=auth,
        requirements=requirements,
        leadership_required=leadership,
        tech_distribution=dist,
        responsibilities=[line.strip("-• ") for line in posting.description.splitlines() if len(line.strip()) > 40][:8],
    )
