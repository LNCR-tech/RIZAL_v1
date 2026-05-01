# Stakeholders

[<- Back to doc index](../README.md)

> **Status:** MUST HAVE
> **Last Updated:** 2026-04-22

---

## Primary Stakeholders

| Role | Description | Interest / Responsibility |
|---|---|---|
| **Platform Admin** | Top-level system administrator | Manages all schools, creates Campus Admin accounts, oversees subscriptions and cross-school data |
| **Campus Admin** | Per-school technical administrator | Manages users, imports students, configures school branding and settings, approves password resets, and assigns event organization to SSG, SG, or ORG officers |
| **SSG Officers** | Supreme Student Government members | Record campus-wide attendance, manage school-wide events, create announcements, manage student notes |
| **SG Officers** | Student Government members at department level | Record department-scoped attendance and events |
| **ORG Officers** | Student organization officers at program level | Record program-scoped attendance and events |
| **Students** | Enrolled students | View their own attendance history and upcoming events |

## Development Team

| Role | Responsibilities |
|---|---|
| **Backend Developer** | FastAPI, SQLAlchemy, Alembic, Celery, auth, security, and backend business rules |
| **Frontend Developer** | React, Vite, role-based dashboards, and API integration |
| **Deployment Specialist** | Railway, Vercel, Docker Compose, and GitHub Actions |
| **Scrum Master** | Facilitates sprint planning, tracks team progress, and protects scope during execution |
| **Documentation Specialist** | Maintains all docs, changelogs, scope references, and knowledge artifacts |
| **Tester** | Writes and runs test plans, logs bugs and edge cases, and validates delivery against approved scope |

## Scope Governance Responsibility

| Role | Scope Responsibility |
|---|---|
| **Scrum Master** | Flags scope creep during sprint execution, protects sprint commitments, and escalates unapproved additions |
| **Documentation Specialist** | Maintains the official scope definition in project docs and enforces the rule that undocumented scope is not implementation scope |
| **Backend Developer** | Builds only approved backend features and raises out-of-scope requests before implementation |
| **Frontend Developer** | Builds only approved UI flows and raises unapproved feature additions before implementation |
| **Tester** | Validates test coverage against approved scope, not against informal requests |

## External Dependencies

| Dependency | Purpose |
|---|---|
| **PostgreSQL** | Persistent relational database |
| **Redis** | Celery message broker and background job queue |
| **Docker / Docker Compose** | Container runtime for local dev and production |
| **Railway** | Cloud hosting for backend and database |
| **Vercel** | Cloud hosting for frontend |
| **OpenAI-compatible API** | LLM provider for the Agentic assistant subsystem |
