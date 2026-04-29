# Aura Navigation Map (Non-Developer)

<!--nav-->
[Previous](../../README.md) | [Next](overview.md) | [Home](/README.md)

---
<!--/nav-->

Note: Menu labels may differ slightly, but the sections below reflect the appâ€™s primary route groups.

## Login and Account

- Login screen: `/`
- Change password (when required): `/change-password`
- Security settings: `/profile/security`
  - Password change: `/profile/security/password`
  - Face update: `/profile/security/face`
- Face registration (first-time enrollment): `/face-registration`

## Student Dashboard (`/dashboard`)

Common sections:

- Home: `/dashboard`
- Schedule: `/dashboard/schedule`
- Event details: `/dashboard/schedule/:id`
- Attendance for an event: `/dashboard/schedule/:id/attendance`
- Analytics: `/dashboard/analytics`
- Sanctions (student view): `/dashboard/sanctions`
- Aura chat: `/dashboard/chat`
- Gather mode:
  - Welcome: `/dashboard/gather`
  - Attendance capture: `/dashboard/gather/attendance`

## School IT Workspace (`/workspace`)

This is typically where school-side operations happen:

- Home: `/workspace`
- Users:
  - Users list: `/workspace/users`
  - Department/program setup: `/workspace/users/departments`
  - Program students: `/workspace/users/programs/:programId`
  - Unassigned students: `/workspace/users/unassigned`
- Student import: `/workspace/import`
- Student council: `/workspace/student-council`
- Schedule:
  - Schedule list: `/workspace/schedule`
  - Monitor: `/workspace/schedule/monitor`
  - Reports: `/workspace/schedule/reports`
  - Event details: `/workspace/schedule/:id`
- Settings: `/workspace/settings`
- Aura chat: `/workspace/chat`

## Admin Workspace (`/admin`)

Admin sections are permissioned, but typically include:

- Overview: `/admin`
- Schools: `/admin/schools`
- Accounts: `/admin/accounts`
- Oversight: `/admin/oversight`
- Reports: `/admin/reports`
- Profile: `/admin/profile`
- Aura chat: `/admin/chat`

## Governance Workspace (`/governance`)

Governance routes support governance/unit management and event operations:

- Overview: `/governance`
- Students: `/governance/students`
- Governance admin/members: `/governance/admin` (and `/governance/members` redirects here)
- Events: `/governance/events`
- Reports: `/governance/reports`
- Create unit: `/governance/create-unit`
- Event details: `/governance/events/:id`
- Sanctions (event-focused):
  - Dashboard: `/governance/events/sanctions`
  - Students: `/governance/events/:eventId/sanctions/students`
  - Student detail: `/governance/events/:eventId/sanctions/students/:userId`
- Aura chat: `/governance/chat`
- Gather mode:
  - Welcome: `/governance/gather`
  - Attendance capture: `/governance/gather/attendance`


