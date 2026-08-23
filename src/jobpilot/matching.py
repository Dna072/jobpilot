from __future__ import annotations

from jobpilot.config import load_app_config
from jobpilot.geo import location_match_score
from jobpilot.knowledge import load_candidate_profile, load_inventory
from jobpilot.schemas.common import (
    GapVerdict,
    MatchRecommendation,
    RequirementLevel,
    ResumeType,
)
from jobpilot.schemas.job import ExtractedRequirement, JobAnalysis
from jobpilot.schemas.match import GapItem, GapReport, MatchBreakdown, MatchReport
from jobpilot.schemas.portfolio import PortfolioInventory
from jobpilot.skills import candidate_skill_set, canonical_skill, expand_aliases

def _has_skill(owned: set[str], skill: str) -> bool:
    skill = canonical_skill(skill)
    if skill in owned:
        return True
    aliases = expand_aliases(skill)
    return any(canonical_skill(a) in owned or a in owned for a in aliases)


def _required(analysis: JobAnalysis) -> list[ExtractedRequirement]:
    return [r for r in analysis.requirements if r.level == RequirementLevel.REQUIRED]


def _preferred(analysis: JobAnalysis) -> list[ExtractedRequirement]:
    return [r for r in analysis.requirements if r.level != RequirementLevel.REQUIRED]


def score_technical(analysis: JobAnalysis, owned: set[str]) -> tuple[float, list[str], list[str]]:
    required = _required(analysis)
    preferred = _preferred(analysis)
    strong: list[str] = []
    missing: list[str] = []
    if not required:
        req_score = 1.0
    else:
        hits = 0
        for req in required:
            if _has_skill(owned, req.normalized or req.name):
                hits += 1
                strong.append(req.name)
            else:
                missing.append(req.name)
        req_score = hits / len(required)
    pref_score = 1.0
    if preferred:
        ph = sum(1 for p in preferred if _has_skill(owned, p.normalized or p.name))
        pref_score = ph / len(preferred)
        for p in preferred:
            if _has_skill(owned, p.normalized or p.name):
                strong.append(p.name)
    return 0.75 * req_score + 0.25 * pref_score, strong, missing


def score_experience(analysis: JobAnalysis, profile: dict) -> tuple[float, list[str]]:
    title = (analysis.title or "").lower()
    transferable: list[str] = []
    score = 0.35
    for exp in profile.get("experience", []):
        skills = " ".join(exp.get("skills", [])).lower()
        employer = exp.get("employer", "")
        if any(k in title for k in ("data", "analytics", "warehouse", "etl")) and any(
            k in skills for k in ("redshift", "glue", "etl", "airflow", "spark", "warehouse")
        ):
            score = max(score, 0.92)
            transferable.append(f"{exp.get('title')} at {employer}")
        if any(k in title for k in ("backend", "platform", "api", "software")) and any(
            k in skills for k in ("api", "postgresql", "docker", "node", "python", "kubernetes")
        ):
            score = max(score, 0.82)
            transferable.append(f"{exp.get('title')} at {employer}")
        if any(k in title for k in ("frontend", "react", "full stack", "fullstack")) and any(
            k in skills for k in ("javascript", "react", "node")
        ):
            score = max(score, 0.7)
            transferable.append(f"{exp.get('title')} at {employer}")
        if "kpmg" in employer.lower() and any(k in title for k in ("consult", "risk", "analytics")):
            score = max(score, 0.75)
    years = analysis.years_required or 0
    if years >= 8:
        score *= 0.85
        transferable.append("Role asks for senior tenure; candidate years are not fabricated.")
    return min(score, 1.0), list(dict.fromkeys(transferable))


def score_portfolio(analysis: JobAnalysis, inventory: PortfolioInventory) -> tuple[float, list[str]]:
    reqs = [canonical_skill(r.normalized or r.name) for r in analysis.requirements]
    if not reqs:
        return 0.6, []
    evidence: list[str] = []
    covered = 0
    unique_reqs = list(dict.fromkeys(reqs))
    for skill in unique_reqs:
        for project in inventory.projects:
            skills = {canonical_skill(s) for s in project.skills_demonstrated + project.technologies}
            if _has_skill(skills, skill):
                covered += 1
                evidence.append(f"{skill} ← {project.name} ({project.kind})")
                break
    return min(1.0, 0.2 + 0.8 * (covered / max(len(unique_reqs), 1))), evidence


def score_seniority(analysis: JobAnalysis) -> float:
    title = f"{analysis.title} {analysis.seniority or ''}".lower()
    if any(w in title for w in ("intern", "graduate", "junior", "jr ")):
        return 0.7
    if any(w in title for w in ("staff", "principal", "distinguished", "director", "head of")):
        return 0.45
    if any(w in title for w in ("senior", "sr ", "lead")):
        return 0.85
    return 0.9


def score_education(analysis: JobAnalysis) -> float:
    blob = " ".join(analysis.education).lower() + (analysis.title or "").lower()
    if "phd" in blob or "doctorate" in blob:
        return 0.7
    return 0.95


def score_location(analysis: JobAnalysis, config: dict | None = None) -> float:
    config = config or load_app_config()
    return location_match_score(
        analysis.location,
        analysis.country,
        analysis.city,
        analysis.work_mode,
        config,
    )


def score_industry(analysis: JobAnalysis) -> float:
    industry = (analysis.industry or "").lower()
    if not industry:
        return 0.7
    if any(k in industry for k in ("education", "public", "gov", "consult", "fintech", "saas", "media")):
        return 0.85
    return 0.65


def score_other(analysis: JobAnalysis) -> float:
    langs = [lang.lower() for lang in analysis.languages]
    if langs and not any(lang in ("english", "en") for lang in langs):
        if any(lang in ("swedish", "svenska") for lang in langs):
            return 0.55
        return 0.4
    return 0.8


def recommend(score: float, missing: list[str], config: dict) -> MatchRecommendation:
    minimum = float(config.get("match", {}).get("minimum_match_score", 75))
    ideal = float(config.get("match", {}).get("ideal_match_score", 85))
    strategic_gaps = {"kafka", "dbt", "snowflake", "databricks"}
    missing_canon = {canonical_skill(m) for m in missing}
    if score * 100 < minimum - 15:
        return MatchRecommendation.DO_NOT_APPLY
    if score * 100 < minimum:
        return MatchRecommendation.LOW_PRIORITY
    if missing_canon & strategic_gaps and score * 100 < ideal:
        return MatchRecommendation.APPLY_AFTER_PROJECT
    if score * 100 >= ideal and not (missing_canon & {"security clearance"}):
        return MatchRecommendation.APPLY_NOW
    if missing:
        return MatchRecommendation.HUMAN_REVIEW
    return MatchRecommendation.APPLY_NOW


def match_job(
    analysis: JobAnalysis,
    profile: dict | None = None,
    inventory: PortfolioInventory | None = None,
    config: dict | None = None,
) -> MatchReport:
    profile = profile or load_candidate_profile()
    inventory = inventory or load_inventory()
    config = config or load_app_config()
    owned = candidate_skill_set(profile)
    weights = config.get("match", {}).get("weights", {})
    tech, strong, missing = score_technical(analysis, owned)
    exp, transferable = score_experience(analysis, profile)
    port, evidence = score_portfolio(analysis, inventory)
    breakdown = MatchBreakdown(
        technical_skills=round(tech, 4),
        relevant_experience=round(exp, 4),
        portfolio_evidence=round(port, 4),
        seniority=round(score_seniority(analysis), 4),
        education=round(score_education(analysis), 4),
        location=round(score_location(analysis, config), 4),
        industry=round(score_industry(analysis), 4),
        other=round(score_other(analysis), 4),
    )
    score = (
        breakdown.technical_skills * float(weights.get("technical_skills", 0.30))
        + breakdown.relevant_experience * float(weights.get("relevant_experience", 0.25))
        + breakdown.portfolio_evidence * float(weights.get("portfolio_evidence", 0.15))
        + breakdown.seniority * float(weights.get("seniority", 0.10))
        + breakdown.education * float(weights.get("education", 0.05))
        + breakdown.location * float(weights.get("location", 0.05))
        + breakdown.industry * float(weights.get("industry", 0.05))
        + breakdown.other * float(weights.get("other", 0.05))
    )
    rec = recommend(score, missing, config)
    risks = []
    if missing:
        risks.append("Missing required skills: " + ", ".join(missing))
    if breakdown.seniority < 0.5:
        risks.append("Seniority may be above current evidenced level")
    if breakdown.location < 0.5:
        risks.append("Location is outside the preferred European set")
    return MatchReport(
        score=round(score * 100, 2),
        breakdown=breakdown,
        strong_matches=list(dict.fromkeys(strong)),
        missing_requirements=missing,
        transferable_experience=transferable,
        portfolio_evidence=evidence,
        risks=risks,
        recommendation=rec,
        rationale=(
            f"Score {round(score * 100, 2)} with recommendation {rec.value}. "
            f"Technical {breakdown.technical_skills:.2f}, experience {breakdown.relevant_experience:.2f}, "
            f"portfolio {breakdown.portfolio_evidence:.2f}, location {breakdown.location:.2f}."
        ),
    )


ROLE_HINTS = {
    ResumeType.DATA_ENGINEER: [
        "data engineer",
        "analytics engineer",
        "etl",
        "warehouse",
        "spark",
        "airflow",
        "redshift",
        "dbt",
        "glue",
        "pipeline",
        "lakehouse",
    ],
    ResumeType.BACKEND_ENGINEER: [
        "backend",
        "api",
        "platform",
        "distributed",
        "microservice",
        "kubernetes",
        "fastapi",
        "node",
        "django",
        "iam",
        "postgres",
    ],
    ResumeType.FRONTEND_ENGINEER: [
        "frontend",
        "front-end",
        "react",
        "next.js",
        "typescript",
        "ui",
        "css",
        "tailwind",
        "accessibility",
        "vite",
    ],
}


def select_resume(analysis: JobAnalysis, profile: dict | None = None) -> dict:
    profile = profile or load_candidate_profile()
    blob = " ".join(
        [
            analysis.title,
            " ".join(analysis.responsibilities),
            " ".join(f"{r.name} {r.category}" for r in analysis.requirements),
            json_dump_tech(analysis.tech_distribution),
        ]
    ).lower()
    scores: dict[str, float] = {}
    for rtype, hints in ROLE_HINTS.items():
        hint_hits = sum(1 for h in hints if h in blob)
        skill_set = [canonical_skill(s) for s in profile.get("resume_skill_sets", {}).get(rtype.value, [])]
        reqs = [canonical_skill(r.normalized or r.name) for r in analysis.requirements]
        overlap = len(set(skill_set) & set(reqs)) / max(len(set(reqs)), 1) if reqs else 0.3
        dist = analysis.tech_distribution
        dist_boost = 0.0
        if rtype == ResumeType.DATA_ENGINEER:
            dist_boost = (dist.get("data", 0) + dist.get("cloud", 0)) / max(sum(dist.values()), 1)
        elif rtype == ResumeType.BACKEND_ENGINEER:
            dist_boost = (dist.get("language", 0) + dist.get("infra", 0) + dist.get("database", 0)) / max(
                sum(dist.values()), 1
            )
        elif rtype == ResumeType.FRONTEND_ENGINEER:
            dist_boost = (dist.get("frontend", 0) + dist.get("framework", 0)) / max(sum(dist.values()), 1)
        scores[rtype.value] = round(100 * min(1.0, 0.25 * min(hint_hits / 4, 1) + 0.55 * overlap + 0.2 * dist_boost), 2)
    selected = max(scores, key=scores.get)  # type: ignore[arg-type]
    reasoning = (
        f"Data Engineer Resume {scores['DATA_ENGINEER']}% / "
        f"Backend Engineer Resume {scores['BACKEND_ENGINEER']}% / "
        f"Frontend Engineer Resume {scores['FRONTEND_ENGINEER']}% — "
        f"SELECT {selected} based on title, responsibilities, and tech distribution."
    )
    return {**scores, "selected": selected, "reasoning": reasoning}


def json_dump_tech(dist: dict[str, int]) -> str:
    return " ".join(f"{k} " * v for k, v in dist.items())


def analyze_gaps(
    analysis: JobAnalysis,
    profile: dict | None = None,
    inventory: PortfolioInventory | None = None,
    config: dict | None = None,
) -> GapReport:
    profile = profile or load_candidate_profile()
    inventory = inventory or load_inventory()
    config = config or load_app_config()
    owned = candidate_skill_set(profile)
    items: list[GapItem] = []
    missing_required: list[str] = []
    for req in _required(analysis):
        skill = canonical_skill(req.normalized or req.name)
        in_exp = _has_skill(owned, skill)
        in_port = False
        evidence = None
        for project in inventory.projects:
            skills = {canonical_skill(s) for s in project.skills_demonstrated + project.technologies}
            if _has_skill(skills, skill):
                in_port = True
                evidence = project.name
                break
        items.append(GapItem(skill=skill, in_experience=in_exp, in_portfolio=in_port, evidence=evidence))
        if not in_exp and not in_port:
            missing_required.append(skill)

    rejected = {n.lower() for n in config.get("project_strategy", {}).get("rejected_ideas", [])}
    strategic = {"kafka", "dbt", "snowflake"}
    gap_set = set(missing_required)

    if not missing_required:
        return GapReport(
            verdict=GapVerdict.EXISTING_SUFFICIENT
            if any(i.in_portfolio or i.in_experience for i in items)
            else GapVerdict.NO_PROJECT_NEEDED,
            items=items,
            rationale="Required skills are covered by professional experience and/or portfolio.",
        )

    if gap_set & strategic and config.get("project_strategy", {}).get("prefer_upgrade", True):
        if "kafka" in gap_set:
            idea = "Real-Time Event Processing and Analytics Platform"
            if idea.lower() in rejected:
                return GapReport(
                    verdict=GapVerdict.NO_PROJECT_NEEDED,
                    items=items,
                    rationale="This streaming project idea was previously rejected.",
                )
            # Prefer new streaming platform — no existing kafka project to upgrade.
            return GapReport(
                verdict=GapVerdict.NEW_PROJECT,
                items=items,
                proposed_project=idea,
                rationale="Existing portfolio is strong but lacks convincing real-time streaming evidence.",
            )
        if "dbt" in gap_set:
            return GapReport(
                verdict=GapVerdict.UPGRADE_EXISTING,
                items=items,
                upgrade_target="Sparkify Redshift Warehouse",
                rationale="Prefer adding a dbt analytics layer to the existing warehouse rather than a new repo.",
            )

    if len(missing_required) <= 2:
        return GapReport(
            verdict=GapVerdict.NO_PROJECT_NEEDED,
            items=items,
            rationale="Gaps are narrow; a new project would not be justified by a single posting.",
        )
    return GapReport(
        verdict=GapVerdict.NO_PROJECT_NEEDED,
        items=items,
        rationale="Missing skills are not strategically concentrated enough for a new project.",
    )
