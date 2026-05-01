# Project Scope

[<- Back to doc index](../README.md)

> **Status:** MUST HAVE
> **Last Updated:** 2026-04-22

---

## Scope Control Rule

This document is the boundary reference for the current system release.

- **Risk:** scope creep caused by undefined or loosely enforced feature boundaries. No clear scope means the team keeps adding features.
- **Result of scope creep:** delivery delays, incomplete implementation, and inconsistent testing.
- **Team rule:** "If it is not in scope, it is not built."
- Any feature not explicitly listed below must be treated as out of scope until formally approved.

---

## In Scope

The following features and functionalities are within the defined scope of AURA v3.2:

### Core Platform

- Multi-tenant architecture with per-school data isolation
- User account management with role-based access (Admin, Campus Admin, Student, SSG, SG, ORG)
- User login, authentication, and session management
- JWT authentication for protected routes
- Session tracking, revocation, and login history

### Event and Attendance

- Event lifecycle management (upcoming -> ongoing -> completed)
- Flexible attendance windows (early check-in, late threshold, sign-out grace, override)
- Manual attendance recording
- Face-recognition attendance via biometric verification
- Face-recognition attendance check-in flow
- Near-start attendance override windows per event

### Governance

- Hierarchical student governance (SSG -> SG -> ORG)
- Scoped event creation and attendance per governance unit
- Announcements and student notes per unit

### Admin and Operations

- Student bulk import via Excel with validation previews
- Audit log tracking per school
- Email notifications for attendance, security, and operational flows
- Subscription plan management per school
- Data governance, retention policies, consent tracking, and user data requests

### AI Assistant (Agentic)

- Role-aware chat assistant backed by an OpenAI-compatible LLM
- MCP policy layer for scoped database access
- Student import proxy through existing backend routes
- Conversation storage and daily usage tracking

### Deployment

- GitHub repository as version control and CI/CD source
- Railway (backend + database) and Vercel (frontend)
- Docker Compose for local development and production
- Production Nginx reverse proxy

---

## Out of Scope

The following are explicitly **not** in scope for the current version:

- Alternate attendance flow outside face recognition
- SMS notification delivery beyond placeholder support
- Native mobile application (iOS or Android)
- Payment gateway integration
- Payment system or billing workflow beyond school subscription configuration
- HR management, payroll, or employee administration modules
- Third-party LMS integration (e.g. Moodle or Canvas)
- Real-time WebSocket push notifications
- Full AI/ML predictive product features beyond experimental tables

---

## Scope Decision Reference

### In Scope

- Attendance tracking
- User login and session management
- Event management
- Role-based access
- Face recognition attendance
- Agentic AI assistant (role-scoped)
- Docker + Railway + Vercel deployment

### Out of Scope

- Alternate attendance flow outside face recognition
- Payment system
- HR management
- LMS integration
- Native mobile app
- WebSocket real-time push
