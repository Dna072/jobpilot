# Candidate Profile — Derrick Adjei

**Generated:** 2026-08-20  
**Sources inspected:** this workspace (`Dna072/jobpilot`), public GitHub (`Dna072`), portfolio site (`dna072.github.io` / `Dna072/Portfolio`), existing PDF resume, product URLs, and the candidate brief in the build request.  
**Honesty rule:** every claim below is tagged with a source. Nothing is invented. Where sources disagree, both versions are recorded.

## Identity

| Field | Value | Source |
|---|---|---|
| Name | Derrick Adjei | PDF resume, portfolio, GitHub |
| Location | Stockholm, Sweden | PDF resume, portfolio `site.ts` |
| Phone | +46-76-251-7998 | PDF resume |
| Professional email | derrick.adjei.eng@gmail.com | PDF resume, portfolio |
| GitHub account email | adjeiderrick12@gmail.com | `jobpilot` initial commit author |
| GitHub | https://github.com/Dna072 | GitHub, resume |
| Portfolio | https://dna072.github.io | GitHub Pages |
| LinkedIn | https://www.linkedin.com/in/derrick-adjei-5421289a/ | portfolio `site.ts` |
| Headline on current PDFs | Data Engineer / Backend Engineer | `cv/source/Derrick_Adjei_Data_Engineer.pdf`, `cv/source/Derrick_Adjei_Backend_Engineer.pdf` |

## Target roles (configurable; defaults from candidate brief)

**Tier 1 (highest):** Data Engineer, Senior Data Engineer, Analytics Engineer, Data Platform Engineer, Data Infrastructure Engineer, Data Warehouse Engineer.

**Tier 2:** Backend Engineer, Software Engineer — Backend, ML Engineer, MLOps Engineer, Platform Engineer.

**Tier 3:** Frontend Engineer, Full Stack Engineer, Software Engineer.

Geographic priority: Sweden first, then Denmark, Norway, Finland, Germany, Netherlands, Switzerland, Ireland, Belgium, then other Europe. Remote/hybrid Europe and relocation are in scope.

## Professional experience (do not convert portfolio into employment)

### 1. KPMG Sweden — System Specialist, Data & Process Automation

- **Dates:** 2023 – Present
- **Location:** Stockholm, Sweden
- **Sources:** PDF resume, portfolio `experience.ts`, resume page copy
- **Documented work:**
  - Enterprise Microsoft Power Platform solutions (Power Apps, Power Automate, Power BI)
  - Operational and risk-management dashboards
  - Process automation that reduced manual work
  - Stakeholder collaboration to digitize workflows and reporting

The candidate brief also lists AWS, PostgreSQL, Aurora RDS, APIs, IAM, Docker, Kubernetes, CI/CD, and high availability as experience. Those technologies are **not named on the KPMG bullets of the current PDF**. They appear in NTC bullets, product work, and/or the candidate brief. JobPilot must not attribute undocumented KPMG technologies to KPMG.

### 2. National Teaching Council (Ghana)

Sources disagree on title and dates. JobPilot stores all documented variants and never silently merges them into a new title.

| Variant | Title | Dates | Source |
|---|---|---|---|
| A | Data Engineer (Contract) | 2022 – 2025 | PDF resume, portfolio |
| B | Software Engineer | Sep 2018 – Feb 2023 | LinkedIn public profile snippet |
| C | Software Engineer / Lead IT Officer | not dated in brief | candidate brief |

**Location:** Greater Accra, Ghana.

**Documented NTC work (resume/portfolio):**

- Production ETL/ELT with AWS Glue from PostgreSQL into Amazon Redshift
- Staging and transformation layers into a star-schema warehouse
- Redshift distribution/sort-key tuning; query performance improvement “up to 50%”
- Batch pipelines supporting analytics across 500,000+ users
- Data quality checks, validation, and monitoring
- Production web platform TPG (`https://tpg.ntc.gov.gh`)

**Documented NTC work (candidate brief, not on current PDF bullets):**

- Large-scale production / nationwide systems
- Teacher licensing systems and digital certificates (`cert_generator` repo exists)
- APIs, authentication/IAM, dashboards, Docker, Kubernetes, high availability
- Aurora RDS / PostgreSQL optimization

Overlapping dates with KPMG (2023–2025) are recorded as documented, not “cleaned up.”

### 3. NexDev Technologies — product engineering affiliation

- **Sources:** candidate brief; live products on `nexdev.tech`; NexDev public description of SIMSGH and prior NTC Teacher Portal Ghana work
- **Title:** **not documented** on the PDF resume. Do not invent “Founder”, “CTO”, or similar.
- **Products:**
  - SIMSGH (`https://simsgh.com`) — school management (attendance, grades, fees); candidate brief
  - MedLink (`https://medlink.nexdev.tech`) — full-stack TypeScript/React/Next/Node; portfolio
  - Arctiq (`https://arctiq.nexdev.tech`) — full-stack web app; portfolio
  - TPG collaboration history is described by NexDev publicly; TPG is already attributed as NTC production work on the portfolio

NexDev/SIMSGH/MedLink/Arctiq belong in **projects / product work**, not as a fabricated employer row, until a title and dates are supplied.

## Education

| Degree | Institution | Dates | Source |
|---|---|---|---|
| MSc Data Science | Uppsala University, Uppsala, Sweden | 2022 – 2024 | PDF, portfolio |
| Thesis | Deep RL for Job Shop Scheduling (`Dna072/drl-jss`) | MSc period | portfolio, GitHub |
| BSc Computer Engineering | University of Ghana, Accra | 2013 – 2017 | PDF, portfolio |

## Skills (claimed vs evidenced)

The candidate brief lists a broad skill set. The table below is the inventory JobPilot uses. **Evidenced** means a public repo, live product, or resume bullet supports it. **Brief-only** means it must not be written as production employment without more evidence.

### Programming

| Skill | Evidence |
|---|---|
| Python | Resume, almost all data/ML/backend repos |
| SQL | Resume, Redshift/Airflow/STEDI/StreamPulse |
| JavaScript | TPG, BookingApp-Api, cert_generator, older React demos |
| TypeScript | Portfolio site, MedLink/Arctiq stacks, media SaaS frontends |
| Java | Traffic-Simulator, Clustering, NaiveBayes repos (academic/older) |
| C++ / C# | Brief-only; HashCode repo is C, not a C++/C# product |
| React / Next.js / Node / Express | Portfolio, MedLink, Arctiq, StreamPulse/MediaVault/ClipForge UIs |

### Data

| Skill | Evidence |
|---|---|
| PostgreSQL | NTC resume, MediaVault, StreamPulse, TPG stack |
| MySQL | Brief-only |
| MongoDB | Listed on PDF “Experience with”; no dedicated public repo |
| Redis | PDF; ClipForge/RenderFlow queues |
| Elasticsearch / OpenSearch | PDF “Experience with”; no dedicated public repo |
| Spark / PySpark | STEDI lakehouse, resume |
| Airflow | `airflow-pipelines`, resume |
| Kafka | Brief + portfolio radar “Assess”; **no project evidence yet** |
| AWS Redshift / Glue / S3 | NTC, Sparkify, STEDI |
| ETL/ELT, warehousing, lakes, modelling, pipelines | NTC + Sparkify + STEDI + Airflow |

### Cloud / infra

| Skill | Evidence |
|---|---|
| AWS EC2, RDS, Aurora, VPC, Route53, ELB | Brief; NTC uses PostgreSQL/Glue/Redshift — Aurora/VPC/ELB not named on PDF |
| Docker / Compose | ClipForge, MediaVault, StreamPulse, RenderFlow, Airflow |
| Kubernetes | RenderFlow manifests (portfolio, not employment) |
| Jenkins | Brief-only |
| GitHub Actions / CI/CD | Media SaaS repos, portfolio |

### ML

| Skill | Evidence |
|---|---|
| PyTorch, RL, SB3, Gymnasium, DQN/PPO/A2C | `drl-jss`, `rl-cartpole`, thesis |
| Scikit-learn | older ML repos |

### Frontend

React, Next.js, TypeScript, JavaScript, Tailwind, Vite, REST — evidenced by portfolio site and product stacks. Accessibility/performance claims should stay modest unless a repo demonstrates them.

## What this workspace did **not** contain

At discovery time `Dna072/jobpilot` contained only `README.md` (`# jobpilot / Job agent`). Missing from the workspace:

1. The three LaTeX master resumes (`/cv/data-engineer`, `/cv/backend-engineer`, `/cv/frontend-engineer`)
2. Local clones of portfolio repositories
3. Existing JobPilot configuration, database, or agents

Official backend and data PDFs plus matching Leslie Cheng `.tex` sources were added on 2026-08-23. The frontend master uses that same template; no official frontend PDF was provided.

## Profile rules for every agent

1. Never convert ClipForge / MediaVault / StreamPulse / RenderFlow / Sparkify / STEDI / Airflow / DRL-JSS into “I ran this in production at KPMG/NTC.”
2. Never upgrade “portfolio project” to “professional experience.”
3. Never invent certifications, years, or performance numbers beyond the documented “up to 50%” Redshift claim.
4. When sources conflict (NTC title/dates), prefer source-tagged variants over a blended fake title.
5. Kafka, Snowflake, Databricks, dbt, Iceberg are **gap skills**, not claimed skills.
