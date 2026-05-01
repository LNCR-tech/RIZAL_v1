# Functional Requirements

[<- Back to doc index](../README.md)

> **Status:** MUST HAVE — IN PROGRESS
> **Last Updated:** 2026-04-22

---

## FR-01: Authentication and Session Management

| ID | Requirement | Status |
|---|---|---|
| FR-01.1 | Users must log in with email and password | Done |
| FR-01.2 | JWT access token is issued on successful login | Done |
| FR-01.3 | Users with `must_change_password = true` are redirected to change password before accessing the system | Done |
| FR-01.4 | Active sessions can be listed and individually revoked | Done |
| FR-01.5 | Login history is logged per user | Done |
| FR-01.6 | Inactive school sessions are auto-rejected at protected routes | Done |

## FR-02: User Management

| ID | Requirement | Status |
|---|---|---|
| FR-02.1 | Campus Admin can create, update, and delete users within their school | Done |
| FR-02.2 | Campus Admin can assign roles to users | Done |
| FR-02.3 | Campus Admin can initiate student bulk import via Excel | Done |
| FR-02.4 | Campus Admin can reset user passwords | Done |
| FR-02.5 | Students can view their own profile | Done |

## FR-03: Event Management

| ID | Requirement | Status |
|---|---|---|
| FR-03.1 | Authorized roles can create events with name, location, start/end datetime, and status | Done |
| FR-03.2 | Events can be scoped to specific departments, programs, or SSG members | Done |
| FR-03.3 | Events support custom attendance windows (early check-in, late threshold, sign-out grace) | Done |
| FR-03.4 | Organizers can extend near-start attendance override windows per event | Done |
| FR-03.5 | Event status syncs automatically via background scheduler | Done |

## FR-04: Attendance

| ID | Requirement | Status |
|---|---|---|
| FR-04.1 | SSG officers can record manual attendance (time-in/out) | Done |
| FR-04.2 | Face-recognition attendance is supported using biometric encoding | Done |
| FR-04.3 | Students can access their own attendance records | Done |
| FR-04.4 | Face-recognition attendance check-in flow is available for supported event check-in | Done |
| FR-04.5 | Bulk attendance marking is supported | Done |
| FR-04.6 | Students can be marked as excused | Done |

## FR-05: Governance Hierarchy

| ID | Requirement | Status |
|---|---|---|
| FR-05.1 | Governance units can be created: SSG (campus), SG (department), ORG (program) | Done |
| FR-05.2 | Officers are assigned to units with specific permissions | Done |
| FR-05.3 | Events and attendance are scoped to the governance unit level | Done |
| FR-05.4 | Announcements and student notes are scoped per governance unit | Done |

## FR-06: Notifications

| ID | Requirement | Status |
|---|---|---|
| FR-06.1 | Email notifications for missed events, low attendance, and security alerts | Done |
| FR-06.2 | Users can manage notification preferences | Done |
| FR-06.3 | SMS notifications | Placeholder only |

## FR-07: Reporting and Audit

| ID | Requirement | Status |
|---|---|---|
| FR-07.1 | Per-student and per-event attendance reports | Done |
| FR-07.2 | School audit log trail (non-editable) | Done |
| FR-07.3 | Subscription usage metrics and renewal tracking | Done |
| FR-07.4 | Data governance: retention policies, consent tracking, user data requests | Done |

## FR-08: AI Assistant (Agentic)

| ID | Requirement | Status |
|---|---|---|
| FR-08.1 | Authenticated users can send natural language queries to the assistant | Done (backend) |
| FR-08.2 | Assistant enforces role-based access using JWT claims | Done (backend) |
| FR-08.3 | Assistant can query tenant database through role-scoped MCP services | Done (backend) |
| FR-08.4 | Assistant supports student bulk import via proxy to existing backend routes | Done (backend) |
| FR-08.5 | Conversation history is stored per user | Done (backend) |
| FR-08.6 | Frontend chat interface for the assistant | Not yet integrated |
