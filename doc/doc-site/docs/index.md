---
slug: /
title: Aura Documentation
description: Role-based guides for Aura users, event managers, administrators, school IT, and developers.
---

# Aura Documentation

Aura is a student attendance platform for event check-ins, face verification, geolocation validation, sanctions, reporting, and AI-assisted administration.

Use this page as the starting point. The documentation is grouped by what each role needs to do, and the technical section is protected by the doc-site RBAC guard.

<div className="aura-doc-grid">
  <a className="aura-doc-card" href="/user/getting-started">
    <span className="aura-card-label">Start</span>
    <strong>Getting started</strong>
    <small>First steps for signing in, checking event access, and reading your attendance records.</small>
  </a>
  <a className="aura-doc-card" href="/user/user-manual/attendance">
    <span className="aura-card-label">Guide</span>
    <strong>Attendance</strong>
    <small>How face scan, geolocation, manual entry, statuses, and attendance history work.</small>
  </a>
  <a className="aura-doc-card" href="/user/user-manual/events">
    <span className="aura-card-label">Operations</span>
    <strong>Events</strong>
    <small>Event creation and monitoring for SSG, SG, ORG, campus admins, and admins.</small>
  </a>
  <a className="aura-doc-card" href="/updates/latest-implementation">
    <span className="aura-card-label">Update</span>
    <strong>Latest implementation</strong>
    <small>What changed in the doc-site UI, RBAC behavior, navigation, and docs structure.</small>
  </a>
</div>

## Access by role

| Role | Main documentation access | Notes |
| --- | --- | --- |
| `student` | User guides | Can read attendance, profile, mobile, FAQ, and troubleshooting guides. |
| `ssg`, `sg`, `org` | User guides and event guides | Can read event management workflows but not technical docs. |
| `admin`, `campus_admin`, `school_it` | User guides and technical docs | Can open API, backend, frontend, assistant, and deployment docs. |
| Authorized email | Technical docs | Email listed in `DOCUSAURUS_AUTHORIZED_EMAILS` is treated as technical access. |

## Main workflows

### Students

1. Read [Getting Started](/user/getting-started).
2. Learn [Attendance](/user/user-manual/attendance).
3. Check [Mobile Guide](/user/mobile-guide) if you use a phone.
4. Use [Troubleshooting](/user/troubleshooting) when face scan, location, or login fails.

### Event managers

1. Review [Event Management](/user/user-manual/events).
2. Confirm attendance rules in [Attendance Guide](/user/user-manual/attendance).
3. Use [Notifications](/user/user-manual/notifications) for reminders and event updates.

### Admins and school IT

1. Open [API Overview](/technical/api/overview).
2. Review [Backend Architecture](/technical/backend/architecture).
3. Check [Database](/technical/backend/database) and [Services](/technical/backend/services).
4. Follow [Deployment](/technical/deployment/production) before production release.

## Current system facts

- Face recognition is the primary check-in method.
- Manual entry is the backup method when a student cannot complete a face scan.
- Geolocation validates whether the check-in happened inside the event boundary.
- Technical docs are hidden from the navbar and blocked by page-level RBAC for non-technical users.
- The doc-site now has a focused layout inspired by modern API documentation pages such as Resend docs.

## Need the latest change summary?

Read [Latest Implementation](/updates/latest-implementation) for the before/current comparison and testing steps.
