# Old Frontend UI Brief

This note summarizes what the old frontend actually does, what each role needs to see, and what should be redesigned instead of copied 1:1.

## Core Finding

The old app's "dashboard" pages are mostly launchpads, not true dashboards.

- Student dashboard: 3 shortcut cards only
- Admin dashboard: 2 shortcut cards only
- School IT dashboard: a list of operational links
- Real work happens in the pages behind those links

For a redesign, the team should keep the information architecture and user jobs, but not copy the old layouts directly.

## Main User Flows

### Student

First login flow:

1. Log in
2. Change password if `must_change_password = true`
3. Register face
4. Reach dashboard

Primary student jobs:

- See ongoing and upcoming events
- Check attendance history
- Sign in or sign out for an ongoing event
- Manage own profile

Key old files:

- `src/dashboard/StudentDashboard.tsx`
- `src/pages/UpcomingEvents.tsx`
- `src/pages/EventsAttended.tsx`
- `src/pages/StudentEventCheckIn.tsx`
- `src/pages/StudentFaceEnrollment.tsx`
- `src/pages/Profile.tsx`

### School IT

Primary School IT jobs:

- View school-scoped events
- Create departments and programs
- Change school branding
- Import students in bulk
- Process password reset requests
- Manage school users
- Perform privileged face verification

Key old files:

- `src/dashboard/SchoolITDashboard.tsx`
- `src/pages/SchoolBrandingSettings.tsx`
- `src/pages/SchoolImportUsers.tsx`
- `src/pages/ManageUsers.tsx`
- `src/pages/AcademicManagement.tsx`
- `src/pages/FacialVerification.tsx`

### Admin

Primary admin jobs:

- Create schools and School IT accounts
- Review platform-level audit, security, and governance areas
- Handle privileged face verification

Key old files:

- `src/dashboard/AdminDashboard.tsx`
- `src/pages/AdminSchoolManagement.tsx`
- `src/pages/SecurityCenter.tsx`
- `src/pages/AuditLogs.tsx`
- `src/pages/SubscriptionCenter.tsx`
- `src/pages/DataGovernance.tsx`

### SSG / Event Organizer

Primary SSG / organizer jobs:

- View and manage events
- Create events
- Track records and attendance
- Run manual attendance workflows

Key old files:

- `src/pages/Events.tsx`
- `src/pages/CreateEvent.tsx`
- `src/pages/ManageEvent.tsx`
- `src/pages/ManualAttendance.tsx`
- `src/pages/Records.tsx`

## What The New Dashboard Should Show

### Student Dashboard

The student home should not be only shortcuts.

Recommended sections:

- Welcome header with school identity
- Next event / current event card
- Attendance status summary
- Quick action: Sign in / Sign out
- Upcoming events preview
- Recent attendance history
- Alerts: password required, face not registered, event access blocked, location needed

The student dashboard should answer:

- "What is happening now?"
- "What do I need to do next?"
- "Can I sign in right now?"

### School IT Dashboard

The School IT home should be an operational control center.

Recommended sections:

- School identity card
- Users needing action
  - password reset requests
  - newly imported users with errors
  - users missing face registration
- Academic setup health
  - department count
  - program count
- Event overview
  - ongoing
  - upcoming
  - draft / misconfigured
- Quick actions
  - Import users
  - Manage users
  - Edit branding
  - Add department / program

The School IT dashboard should answer:

- "What needs my attention today?"
- "Is my school setup complete?"
- "Are students ready to use the system?"

### Admin Dashboard

The admin home should be a platform overview, not just 2 cards.

Recommended sections:

- Total schools
- Active School IT accounts
- Pending onboarding / verification issues
- Recent school creation activity
- Security / audit alerts
- Quick actions
  - Create school
  - Review security
  - Review audit logs

The admin dashboard should answer:

- "Is the platform healthy?"
- "Which schools need help?"
- "Are privileged users fully onboarded?"

### SSG / Event Organizer Dashboard

Recommended sections:

- Events needing action
- Today's attendance activity
- Event creation quick action
- Recently updated events
- Manual attendance shortcut
- Records / reporting snapshot

## What To Keep From The Old Frontend

- Role-based dashboards
- Password-first then face-registration onboarding
- School-branded identity in the shell
- Event attendance as a central student action
- School IT ownership of branding, imports, and user setup

## What To Redesign Instead Of Reusing

- Shortcut-card-only dashboards
- Overloaded navbars with too many equal-priority links
- Mixed visual systems across roles
- Long table-first pages with weak empty/loading/error states
- Utility pages that look disconnected from the main app shell

## Recommended New Information Architecture

### Student

- Home
- Events
- Attendance
- Profile

### School IT

- Overview
- Users
- Imports
- Academic Setup
- Events
- Branding
- Security
- Profile

### Admin

- Overview
- Schools
- Security
- Audit
- Subscription
- Governance
- Profile

## Design Direction

The redesign should treat dashboards as decision surfaces, not link directories.

Good dashboard content:

- status
- next actions
- recent activity
- warnings
- shortcuts only after context

Weak dashboard content:

- only big cards
- no health state
- no recent activity
- no indication of blockers

## Best Practical Rule For The UI Team

For each role, the first screen should show:

1. who they are
2. what matters now
3. what is blocked
4. what they should do next

If a screen only says "Welcome" plus navigation cards, it is not a strong dashboard.
