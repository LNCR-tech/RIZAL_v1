# Project Summary

[<- Back to doc index](../README.md)

> **Project Name:** AURA v3.2 — Attendance and University Records Administration
> **Version:** v3.2 / Multi-Tenant Production Branch
> **Status:** Active Development
> **Last Updated:** 2026-04-22

---

## What is AURA v3.2?

AURA v3.2 is a multi-tenant, school-scoped attendance management system. It enables schools to manage students, events, and attendance tracking through a single SaaS platform with support for face-recognition attendance methods.

The system is built with a FastAPI backend, a React + Vite frontend, an AI assistant subsystem, and a Docker-based deployment stack.

## Delivery Boundary

AURA v3.2 is scoped as an attendance, authentication, event, and governance platform for schools.

- **In scope:** attendance tracking, user login, event management, governance workflows, reporting, and school-scoped administration
- **Out of scope:** alternate attendance methods outside face recognition, payment systems, HR management, and unrelated enterprise modules
- **Project rule:** "If it is not in scope, it is not built."

## Key Features

| Feature | Status |
|---|---|
| Multi-tenant school isolation | In Progress |
| Role-Based Access Control (RBAC) | Complete |
| Event creation and management | Complete |
| Manual and face-recognition attendance | Revise |
| Student bulk import (Excel) | Revise |
| Governance hierarchy (SSG -> SG -> ORG) | Complete |
| Face-recognition attendance | Complete |
| Email notifications | Complete |
| Health check and DB pooling | Complete |
| Production Docker deployment | Complete |
| AI assistant subsystem (Agentic) | In Progress |
| Mobile responsive UI | In Progress |
| SMS notifications | Planned |

## Scope Risk Note

The main project-overview risk in this area is scope creep.

- If the boundary is unclear, the team may keep adding features outside the actual product target.
- That creates delays, weak testing focus, and incomplete delivery.
- Scope decisions must always be validated against [scope.md](./scope.md).

## Quick Links

- Project scope: [scope.md](./scope.md)
- Objectives: [objectives.md](./objectives.md)
- Stakeholders: [stakeholders.md](./stakeholders.md)
