from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

from jobpilot.config import repo_path
from jobpilot.knowledge import load_candidate_profile, load_inventory
from jobpilot.schemas.common import ResumeType
from jobpilot.schemas.job import JobAnalysis
from jobpilot.schemas.match import MatchReport


def slug(company: str, role: str, when: datetime | None = None) -> str:
    when = when or datetime.now(UTC)
    raw = f"{company}-{role}-{when.strftime('%Y%m%d')}"
    return re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")[:80]


def select_projects_for_resume(resume_type: ResumeType, analysis: JobAnalysis) -> list[str]:
    inventory = load_inventory()
    wanted = {r.normalized for r in analysis.requirements}
    scored: list[tuple[int, str]] = []
    for project in inventory.projects:
        if resume_type == ResumeType.DATA_ENGINEER and not any(
            r in project.target_roles for r in ("Data Engineer", "Analytics Engineer", "Data Platform Engineer", "Data Warehouse Engineer")
        ):
            if project.kind == "academic":
                continue
        if resume_type == ResumeType.FRONTEND_ENGINEER and "Frontend Engineer" not in project.target_roles:
            continue
        skills = {s.lower() for s in project.skills_demonstrated + project.technologies}
        overlap = len({w for w in wanted if w in skills})
        kind_bonus = {"professional": 3, "product": 2, "portfolio": 1}.get(project.kind, 0)
        scored.append((overlap + kind_bonus, project.name))
    scored.sort(reverse=True)
    names = [name for _, name in scored[:4]]
    return names


def display_company_name(name: str) -> str:
    raw = (name or "").strip()
    if not raw:
        return "your team"
    if re.fullmatch(r"[a-z0-9]+(?:[-_][a-z0-9]+)+", raw):
        return raw.replace("-", " ").replace("_", " ").title()
    return raw


def _location_clause(analysis: JobAnalysis) -> str:
    place = analysis.city or analysis.location or analysis.country or ""
    place = place.strip()
    if not place:
        return "I live in Stockholm and I am looking for roles in Sweden and across Europe."
    if re.search(r"sweden|stockholm|uppsala|gothenburg|göteborg|malm", place, re.I):
        return f"I live in Stockholm and this {place} role is a natural fit for where I want to work."
    return (
        f"I live in Stockholm and I am open to strong European roles, including this one in {place}."
    )


def _experience_paragraph(resume_type: ResumeType) -> str:
    if resume_type == ResumeType.DATA_ENGINEER:
        return (
            "At the National Teaching Council I designed and ran production data pipelines, "
            "moving data from PostgreSQL into Amazon Redshift with quality checks for a platform "
            "used by hundreds of thousands of people. At KPMG Sweden I build internal automation "
            "and reporting so teams can work from reliable data."
        )
    if resume_type == ResumeType.FRONTEND_ENGINEER:
        return (
            "I have shipped production web interfaces alongside backend services, including "
            "Teacher Portal Ghana and product work such as MedLink and Arctiq using TypeScript, "
            "React, and Next.js. At KPMG Sweden I deliver internal apps and dashboards that "
            "people actually use."
        )
    return (
        "At the National Teaching Council I built and ran backend services with Node.js and "
        "PostgreSQL for a nationwide platform, and I led the backend architecture for Teacher "
        "Portal Ghana. At KPMG Sweden I maintain and automate internal systems, including "
        "SQL-backed reporting and monitoring."
    )


def _fit_paragraph(analysis: JobAnalysis, match: MatchReport, company: str) -> str:
    skills = [s for s in match.strong_matches if s and "←" not in s][:4]
    title = (analysis.title or "this role").lower()
    if skills:
        listed = ", ".join(skills[:-1]) + (f" and {skills[-1]}" if len(skills) > 1 else skills[0])
        return (
            f"The posting asks for {listed}. That matches the work I have already done in "
            f"production, and I would like to bring the same focus on reliability and clear "
            f"design to {company}."
        )
    if any(word in title for word in ("robot", "hardware", "firmware", "embedded")):
        return (
            f"I am a software engineer with a production backend and data-platform background. "
            f"I am interested in this role because it needs careful, reliable software, which is "
            f"the work I have been doing."
        )
    return (
        f"I am interested in this role at {company} because it is close to the systems work I "
        f"already do, and I would welcome the chance to contribute from day one."
    )


def cover_letter(analysis: JobAnalysis, match: MatchReport, resume_type: ResumeType) -> str:
    """Company-facing letter. Never mention JobPilot, scores, or internal process."""
    profile = load_candidate_profile()
    name = profile["full_name"]
    company = display_company_name(analysis.company)
    title = analysis.title or "this role"
    return (
        f"Dear Hiring Team,\n\n"
        f"I am writing to apply for the {title} position at {company}. "
        f"{_location_clause(analysis)}\n\n"
        f"{_experience_paragraph(resume_type)}\n\n"
        f"{_fit_paragraph(analysis, match, company)}\n\n"
        f"I would be glad to discuss how I can help.\n\n"
        f"Sincerely,\n"
        f"{name}\n"
        f"{profile['email']}\n"
        f"{profile['phone']}\n"
    )


def screening_answers(analysis: JobAnalysis) -> list[dict]:
    """Never fabricate. Unknown questions stay explicitly unanswered."""
    answers = [
        {
            "question": "Are you located in / willing to work in Europe?",
            "answer": "I live in Stockholm, Sweden, and I am open to roles in Sweden and elsewhere in Europe, including hybrid and remote.",
            "invented": False,
        },
        {
            "question": "Years of professional experience?",
            "answer": (
                "I have been a System Specialist at KPMG Sweden since 2023. Before that I worked "
                "at the National Teaching Council in Ghana as a software engineer and later as a "
                "data engineer (2018–2025). I am happy to walk through the timeline in an interview."
            ),
            "invented": False,
        },
    ]
    if analysis.work_authorization:
        answers.append(
            {
                "question": "Work authorization",
                "answer": "I am based in Sweden and can confirm work-authorization details if you would like.",
                "invented": False,
            }
        )
    return answers


def tailor_master(master_tex: str, analysis: JobAnalysis, resume_type: ResumeType) -> str:
    """Reorder a skills comment block if present; never invent employers."""
    header = (
        f"% Tailored for {analysis.company} — {analysis.title}\n"
        f"% Resume type: {resume_type.value}\n"
        f"% Do not treat this file as a master.\n"
    )
    skills = ", ".join(r.name for r in analysis.requirements[:12])
    note = f"% Job skills emphasized: {skills}\n"
    return header + note + master_tex


def generated_dir(company: str, role: str) -> Path:
    dest = repo_path("cv", "generated", slug(company, role))
    dest.mkdir(parents=True, exist_ok=True)
    return dest
