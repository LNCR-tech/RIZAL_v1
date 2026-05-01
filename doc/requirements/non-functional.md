# Non-Functional Requirements

[<- Back to doc index](../README.md)

> **Status:** MUST HAVE — IN PROGRESS
> **Last Updated:** 2026-04-22

---

## NFR-01: Performance

| ID | Requirement | Target |
|---|---|---|
| NFR-01.1 | API response time for standard CRUD endpoints | < 300ms under normal load |
| NFR-01.2 | Face-scan recognition latency | < 3 seconds |
| NFR-01.3 | Bulk import of 100 students | < 60 seconds |
| NFR-01.4 | Assistant response latency for standard queries | < 5 seconds |

## NFR-02: Scalability

| ID | Requirement | Notes |
|---|---|---|
| NFR-02.1 | System must support multiple schools simultaneously | Multi-tenant `school_id` scoping |
| NFR-02.2 | Background jobs must not block API requests | Celery worker + Redis broker |
| NFR-02.3 | Student paging on governance dashboards must handle large rosters | Server-side pagination enforced |

## NFR-03: Security

| ID | Requirement | Status |
|---|---|---|
| NFR-03.1 | All endpoints must validate JWT tokens server-side | ✅ Done |
| NFR-03.2 | Role-based access control enforced before handler execution | ✅ Done |
| NFR-03.3 | Cross-tenant data access must be prevented | ✅ Done — `school_id` scoping |
| NFR-03.4 | All communication must be over HTTPS in production | 🔧 Planned |
| NFR-03.5 | Rate limiting on login endpoint | 🔧 Not yet implemented |
| NFR-03.6 | Assistant tool access must be scoped by role and school | ✅ Done — MCP policy layer |

## NFR-04: Reliability and Availability

| ID | Requirement | Notes |
|---|---|---|
| NFR-04.1 | Health check endpoint must report DB reachability | ✅ `GET /health` |
| NFR-04.2 | Failed email deliveries must retry automatically | ✅ Celery retry logic |
| NFR-04.3 | Database migrations must be idempotent and reversible | ✅ Alembic |

## NFR-05: Maintainability

| ID | Requirement | Status |
|---|---|---|
| NFR-05.1 | All backend modules must be documented | ✅ Done |
| NFR-05.2 | Changelog must be maintained per update | ✅ Done |
| NFR-05.3 | Alembic migrations must be version-controlled | ✅ Done |
| NFR-05.4 | `doc/` must stay in sync with active codebase | 🔧 Ongoing — Documentation Specialist responsibility |

## NFR-06: Usability

| ID | Requirement | Status |
|---|---|---|
| NFR-06.1 | Role-appropriate dashboards must load without manual navigation | ✅ Done |
| NFR-06.2 | Import errors must show row-level fix suggestions | ✅ Done |
| NFR-06.3 | Mobile-responsive UI | 🔧 Sprint planned |
