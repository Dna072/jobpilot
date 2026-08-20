# Agent Specifications

All payloads are Pydantic models in `src/jobpilot/schemas`. This document is the contract.

## Shared types

- `RequirementLevel`: `REQUIRED` | `PREFERRED` | `NICE_TO_HAVE`
- `ResumeType`: `DATA_ENGINEER` | `BACKEND_ENGINEER` | `FRONTEND_ENGINEER`
- `MatchRecommendation`: `APPLY_NOW` | `APPLY_AFTER_PROJECT` | `HUMAN_REVIEW` | `LOW_PRIORITY` | `DO_NOT_APPLY`
- `ApplicationStatus`: see `application-workflow.md`
- `ProjectStatus`: `PROPOSED` | `WAITING_FOR_REPOSITORY` | `REPOSITORY_FOUND` | `PROJECT_BUILDING` | `QA` | `PROJECT_COMPLETE` | `REJECTED_IDEA`

## Job Scout

**In:** `ScoutRequest(sources, countries, query_roles, since, limit)`  
**Out:** `list[JobPosting]`

`JobPosting` fields: company, role, location, work_mode (remote/hybrid/onsite/unknown), salary_raw, salary_min/max/currency, job_url, source, source_job_id, posted_at, closing_at, description, requirements_raw, preferred_raw, seniority, language_requirements, work_authorization, raw_payload.

Dedup is the scout’s responsibility before insert.

## Job Analyst

**In:** `JobPosting`  
**Out:** `JobAnalysis`

Extracts technical, experience, and other requirements, each with `level`. Distinguishes languages, frameworks, databases, cloud, infra, data, ML, DevOps, architecture, distributed systems.

## Match Agent

**In:** `JobAnalysis` + `CandidateProfile` + `PortfolioInventory`  
**Out:** `MatchReport`

Default weights (config):

| Component | Weight |
|---|---|
| Technical skills | 30% |
| Relevant experience | 25% |
| Portfolio evidence | 15% |
| Seniority | 10% |
| Education | 5% |
| Location | 5% |
| Industry | 5% |
| Other | 5% |

Output sections: match_score, strong_matches, missing_requirements, transferable_experience, portfolio_evidence, risks, recommendation.

Thresholds: `minimum_match_score` default 75, `ideal_match_score` default 85.

## Portfolio Inventory Agent

**In:** GitHub username + local workspace roots  
**Out:** `portfolio_inventory.json` (and DB rows)

Per project: name, repository, technologies, architecture, system_design, deployment, tests, documentation_quality, evidence_strength, skills_demonstrated, target_roles, kind (`professional` | `product` | `portfolio` | `academic` | `archival`).

## Portfolio Gap Agent

**In:** `JobAnalysis` + experience + inventory  
**Out:** `GapReport`

Verdict: `EXISTING_SUFFICIENT` | `UPGRADE_EXISTING` | `NEW_PROJECT` | `NO_PROJECT_NEEDED`.

A new project is allowed only if (config): multiple target jobs need the skill, **or** it is strategically important, **or** it materially changes candidacy. Duplicate ideas are rejected via `rejected_project_ideas` memory.

## Project Planner

**In:** `GapReport`  
**Out:** `ProjectSpec` (title, problem, objective, target_jobs, skills, architecture, system design, data flow, APIs, database, infra, security, scalability, observability, testing, CI/CD, deployment, repo structure, acceptance criteria, definition of done).

## Project Builder / QA / Documentation

Builder implements against `ProjectSpec` inside a **found** repository.  
QA: tests, lint, build, Docker, README, links, config, secrets, architecture vs code.  
Docs: first-person README sections listed in the build request. Personal vs professional experience must be labelled.

## CV Selector / Tailor

Selector scores the three masters against the job; stores `ResumeSelection`.  
Tailor copies the selected master, reorders skills, swaps portfolio bullets, ATS-normalizes wording, **never** invents employment. Compile + PDF validation. Artifacts:

```text
cv/generated/<company-role-date>/
  selected_resume_type.txt
  tailored_resume.tex
  tailored_resume.pdf
  tailoring_report.json
```

## Application Agent

**In:** `ApplicationPackage` (resume PDF, cover letter, answers, links)  
**Out:** `ApplicationAttempt`

Mechanism order: official company API → official ATS API → Greenhouse → Lever → other ATS with a legitimate interface → career page.

Forbidden: CAPTCHA bypass, bot-detection defeat, auth circumvention, stolen cookies, rate-limit evasion, IP/identity rotation, private API reverse engineering, unauthorized LinkedIn automation, ToS-violating submits.

## Notification / Weekly Reporter

Email templates and subjects are fixed in `application-workflow.md`. Weekly report includes discovery funnel, geo/role breakdowns, skill demand histogram, gaps, recommended projects, quality commentary.
