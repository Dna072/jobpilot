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


def cover_letter(analysis: JobAnalysis, match: MatchReport, resume_type: ResumeType) -> str:
    profile = load_candidate_profile()
    name = profile["full_name"]
    evidence = match.portfolio_evidence[:3] or match.transferable_experience[:3]
    return (
        f"Dear Hiring Team,\n\n"
        f"I am {name}, a Stockholm-based engineer applying for {analysis.title} at {analysis.company}. "
        f"My professional work includes production data systems at the National Teaching Council "
        f"(PostgreSQL, AWS Glue, Redshift) and process-automation platforms at KPMG Sweden. "
        f"I am not treating portfolio repositories as employment.\n\n"
        f"This role looks like a {match.score:.0f}% match on JobPilot's transparent rubric. "
        f"Relevant evidence: {'; '.join(evidence) or 'see attached CV'}. "
        f"I am presenting my {resume_type.value.replace('_', ' ').title()} resume because it best "
        f"reflects the responsibilities and technology mix in the posting.\n\n"
        f"I would welcome the chance to discuss how I can contribute.\n\n"
        f"Sincerely,\n{name}\n{profile['email']}\n{profile['phone']}\n"
    )


def screening_answers(analysis: JobAnalysis) -> list[dict]:
    """Never fabricate. Unknown questions stay explicitly unanswered."""
    answers = [
        {
            "question": "Are you located in / willing to work in Europe?",
            "answer": "I live in Stockholm, Sweden, and I am targeting European (especially Swedish) roles, including remote/hybrid Europe.",
            "invented": False,
        },
        {
            "question": "Years of professional experience?",
            "answer": (
                "I do not invent a single year count. Documented professional roles: "
                "KPMG Sweden (2023–Present) and National Teaching Council (documented as "
                "Software Engineer 2018–2023 on LinkedIn and Data Engineer contract 2022–2025 on my data CV)."
            ),
            "invented": False,
        },
    ]
    if analysis.work_authorization:
        answers.append(
            {
                "question": "Work authorization",
                "answer": "I am based in Sweden. I will not invent visa details; I can confirm status directly if asked.",
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
