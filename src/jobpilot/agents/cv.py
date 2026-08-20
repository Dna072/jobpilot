from __future__ import annotations

import json
from pathlib import Path

from jobpilot.config import load_app_config, repo_path
from jobpilot.knowledge import load_inventory
from jobpilot.matching import select_resume
from jobpilot.resume.pdf import compile_latex, validate_pdf
from jobpilot.resume.tailor import (
    cover_letter,
    generated_dir,
    screening_answers,
    select_projects_for_resume,
    tailor_master,
)
from jobpilot.schemas.application import ApplicationPackage, ScreeningAnswer
from jobpilot.schemas.common import ResumeType
from jobpilot.schemas.job import JobAnalysis
from jobpilot.schemas.match import MatchReport


def generate_package(analysis: JobAnalysis, match: MatchReport) -> ApplicationPackage:
    selection = select_resume(analysis)
    resume_type = ResumeType(selection["selected"])
    dest = generated_dir(analysis.company, analysis.title)
    (dest / "selected_resume_type.txt").write_text(resume_type.value + "\n", encoding="utf-8")
    (dest / "tailoring_report.json").write_text(json.dumps(selection, indent=2), encoding="utf-8")

    cfg = load_app_config()
    master_rel = cfg["resume"]["masters"][resume_type.value]
    master_path = repo_path(*Path(master_rel).parts)
    master_tex = master_path.read_text(encoding="utf-8") if master_path.exists() else "% missing master\n"
    tailored = tailor_master(master_tex, analysis, resume_type)
    tex_path = dest / "tailored_resume.tex"
    tex_path.write_text(tailored, encoding="utf-8")
    pdf_path = None
    try:
        pdf_path = compile_latex(tex_path, dest)
        validate_pdf(pdf_path, max_pages=int(cfg.get("resume", {}).get("max_pages", 2)))
        pdf_path = dest / "tailored_resume.pdf"
        if pdf_path.name != "tailored_resume.pdf":
            compiled = dest / (tex_path.stem + ".pdf")
            if compiled.exists():
                compiled.replace(dest / "tailored_resume.pdf")
                pdf_path = dest / "tailored_resume.pdf"
    except Exception:
        pdf_path = dest / "tailored_resume.pdf"
        if not pdf_path.exists():
            pdf_path = None

    inventory = load_inventory()
    chosen = select_projects_for_resume(resume_type, analysis)
    links = []
    github = []
    for project in inventory.projects:
        if project.name in chosen:
            if project.url:
                links.append(project.url)
            if project.repository:
                github.append(project.repository)

    answers = [ScreeningAnswer(**row) for row in screening_answers(analysis)]
    return ApplicationPackage(
        company=analysis.company,
        role=analysis.title,
        job_url=analysis.job_url,
        country=analysis.country,
        location=analysis.location,
        match_score=match.score,
        selected_resume=resume_type,
        resume_tex_path=str(tex_path),
        resume_pdf_path=str(pdf_path) if pdf_path else None,
        cover_letter=cover_letter(analysis, match, resume_type),
        screening_answers=answers,
        portfolio_links=links,
        github_links=github,
    )
