# Objectives

[<- Back to doc index](../README.md)

> **Status:** MUST HAVE
> **Last Updated:** 2026-04-22

---

## Primary Objectives

1. **Digitize School Attendance** — Replace paper-based and manual spreadsheet attendance tracking with a reliable, role-scoped digital system.
2. **Enable Flexible Attendance Methods** — Support manual recording and face-recognition-based attendance flows.
3. **Enforce Governance Hierarchy** — Reflect the real organizational structure of SSG -> SG -> ORG, with scoped access and permissions.
4. **Provide Actionable Reporting** — Give Campus Admins, SSG officers, and event-assigned officers access to per-student, per-event, and aggregate attendance reports.
5. **Ensure Data Isolation** — Maintain strict multi-tenant isolation so no school can access another school's data.
6. **Support Scalable Deployment** — Package the system in Docker Compose for both local development and production with Nginx and PostgreSQL.
7. **Enable Bulk Operations** — Allow Campus Admins to onboard hundreds of students at once via validated Excel import with retry support.
8. **Integrate an AI Assistant** — Provide an authenticated, role-aware Agentic assistant that lets users query attendance data and trigger actions in natural language.

## Secondary Objectives

- Provide audit trails for all significant admin and system actions.
- Implement subscription plan limits to support a SaaS monetization model.
- Support data governance and privacy controls.
- Build a health check system to proactively detect DB connectivity issues.

## Scope Control Objective

- Keep delivery aligned to the approved product boundary defined in [scope.md](./scope.md).
- Prevent scope creep by rejecting unapproved feature additions during active implementation.
- Apply the Documentation Specialist rule: "If it is not in scope, it is not built."
- Use scope boundaries to protect schedule, testing quality, and system completeness.

## Success Metrics

| Metric | Target |
|---|---|
| Event creation to attendance recording time | < 2 minutes |
| Face scan recognition latency | < 3 seconds |
| System uptime | > 99% on Docker production |
| Role isolation accuracy | 100% — no cross-school data leakage |
| Assistant response time | < 5 seconds for standard queries |
