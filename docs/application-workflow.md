# Application Workflow

## State machine

```text
DISCOVERED
    → ANALYZED
        → MATCHED
            → REJECTED
            → PROJECT_REQUIRED
                  → WAITING_FOR_REPOSITORY
                        → PROJECT_BUILDING
                              → PROJECT_COMPLETE
            → CV_GENERATED
                  → READY_TO_APPLY
                        → APPLICATION_IN_PROGRESS
                              → SUBMITTED          # evidence required
                              → HUMAN_ACTION_REQUIRED
                              → FAILED
                        → WITHDRAWN
```

Illegal transition: any path into `SUBMITTED` without a verification record (`confirmation_id`, confirmation URL/body, or ATS status). Tests cover this.

## Duplicate prevention

Before `READY_TO_APPLY`, the application agent checks permanent history on:

1. `source + source_job_id`
2. canonical job URL
3. `(company_normalized, title_normalized, location_normalized)`

If any hit is `SUBMITTED`, `APPLICATION_IN_PROGRESS`, or `HUMAN_ACTION_REQUIRED`, do not apply again.

## Human-action fallback

When CAPTCHA, identity verification, prohibited automation, missing credentials, or an inaccessible private API is detected:

1. Persist the full `ApplicationPackage`
2. Ensure tailored CV + cover letter + screening answers exist
3. Set `APPLICATION_STATUS = HUMAN_ACTION_REQUIRED`
4. Email:

```text
Subject: Please apply to [ROLE] at [COMPANY]
```

The email to Derrick is plain English: company, role, location, apply link, and what to do. It includes the **company-facing cover letter**, which must never mention JobPilot, match scores, resume type, or any other internal process.

The orchestrator does **not** poll LinkedIn. The operator marks completion in the dashboard (`POST /api/v1/applications/{id}/human-complete`) or the system records a confirmation email if IMAP is configured (optional, off by default).

## Repository wait loop

```text
PROJECT_STATUS = WAITING_FOR_REPOSITORY
    periodic check:
      - local workspace paths in config.project_roots
      - GitHub user repo list (public, authenticated if token present)
    on match:
      REPOSITORY_FOUND → PROJECT_BUILDING → QA → PROJECT_COMPLETE
```

JobPilot never calls `github.com/repos` POST to create repositories.

## Email subjects

| Event | Subject |
|---|---|
| New repo needed | `Please create a GitHub repository for [PROJECT]` |
| Project completed | `The [PROJECT] repository is ready to use` |
| Human action | `Please apply to [ROLE] at [COMPANY]` |
| Submitted | `Application sent: [ROLE] at [COMPANY]` |
| Failed | `Could not finish applying to [ROLE] at [COMPANY]` |
| Weekly | `Your weekly job search update` |

SMTP settings from env: `EMAIL_PROVIDER`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `EMAIL_FROM`, `EMAIL_TO`.

## Quality over volume

A job is only auto-applied if:

- recommendation is `APPLY_NOW` (or `APPLY_AFTER_PROJECT` once the project is complete)
- match_score ≥ `minimum_match_score`
- country/city/remote policy matches
- daily cap not exceeded
- not a duplicate
- application mechanism is allowed

`HUMAN_REVIEW` queues for the dashboard instead of auto-submit.

## Tests never submit

Pytest uses mock transports. `JOBPILOT_ALLOW_LIVE_APPLY` must be `true` in production config to enable real HTTP apply; default is `false`.
