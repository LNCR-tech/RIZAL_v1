# Frontend Structure Guide

> **Status:** ACTIVE
> **Last Updated:** 2026-04-17

## Purpose

This page describes the current Aura frontend structure, route layout, and navigation behavior based on the fetched `origin/aurav3` router state.

## Application Flow

```text
index.html
  -> main.js
     -> theme bootstrap
     -> Vue app creation
     -> vue-router install
     -> App.vue
     -> RouterView
```

The frontend uses platform-aware view loading through `createPlatformView(...)`, so the same route can resolve to desktop or mobile implementations when needed.

## Route Groups

All routes are defined in `Frontend/src/router/index.js`.

### Auth and tool routes

| Path | Name | Notes |
|---|---|---|
| `/` | `Login` | guest-only login route |
| `/quick-attendance` | `QuickAttendance` | quick access attendance screen |
| `/api-lab` | `ApiLab` | developer tool for endpoint testing |
| `/face-registration` | `FaceRegistration` | requires auth, allowed before full face enrollment |
| `/change-password` | `ChangePassword` | required-password-change flow |
| `/profile/security/password` | `ProfileSecurityPassword` | password settings flow |
| `/profile/security/face` | `ProfileSecurityFace` | face update flow |
| `/privileged/face` | `PrivilegedFaceVerification` | privileged face MFA gate |
| `/privileged` | `PrivilegedDashboard` | reserved privileged route shell |

### Student dashboard routes

Mounted under `/dashboard` with `AppLayout`.

| Path | Name |
|---|---|
| `/dashboard` | `Home` |
| `/dashboard/profile` | `Profile` |
| `/dashboard/schedule` | `Schedule` |
| `/dashboard/schedule/:id` | `EventDetail` |
| `/dashboard/schedule/:id/attendance` | `Attendance` |
| `/dashboard/analytics` | `Analytics` |
| `/dashboard/sanctions` | `DashboardSanctions` |
| `/dashboard/gather` | `GatherWelcome` |
| `/dashboard/gather/attendance` | `GatherAttendance` |

### Admin workspace routes

Mounted under `/admin` with `AppLayout`.

| Path | Name | Section |
|---|---|---|
| `/admin` | `AdminHome` | overview |
| `/admin/schools` | `AdminSchools` | schools |
| `/admin/accounts` | `AdminAccounts` | accounts |
| `/admin/oversight` | `AdminOversight` | oversight |
| `/admin/profile` | `AdminProfile` | profile |

Preview-only admin mirrors also exist under `/exposed/admin`.

### School IT workspace routes

Mounted under `/workspace` with `AppLayout`.

| Path | Name |
|---|---|
| `/workspace` | `SchoolItHome` |
| `/workspace/users` | `SchoolItUsers` |
| `/workspace/users/import` | `SchoolItImportStudents` |
| `/workspace/users/department/:departmentId` | `SchoolItDepartmentPrograms` |
| `/workspace/users/department/:departmentId/program/:programId` | `SchoolItProgramStudents` |
| `/workspace/users/unassigned` | `SchoolItUnassignedStudents` |
| `/workspace/student-council` | `SchoolItStudentCouncil` |
| `/workspace/schedule` | `SchoolItSchedule` |
| `/workspace/schedule/monitor` | `SchoolItAttendanceMonitor` |
| `/workspace/schedule/reports` | `SchoolItEventReports` |
| `/workspace/schedule/:id` | `SchoolItEventDetail` |
| `/workspace/settings` | `SchoolItSettings` |
| `/workspace/profile` | `SchoolItProfile` |

Preview-only workspace mirrors also exist under `/exposed/workspace`.

### Governance routes

Mounted under `/governance` with `AppLayout`.

| Path | Name | Notes |
|---|---|---|
| `/governance` | `SgDashboard` | governance overview |
| `/governance/students` | `SgStudents` | student-focused governance section |
| `/governance/admin` | `SgAdmin` | governance admin section |
| `/governance/events` | `SgEvents` | event workspace |
| `/governance/create-unit` | `SgCreateUnit` | unit creation |
| `/governance/events/sanctions` | `SgSanctionsDashboard` | sanctions dashboard |
| `/governance/events/:eventId/sanctions/students` | `SgSanctionedStudents` | sanctioned students list |
| `/governance/events/:eventId/sanctions/students/:userId` | `SgStudentSanctionDetail` | student sanction detail |
| `/governance/events/:id` | `SgEventDetail` | event detail |
| `/governance/gather` | `SgGatherWelcome` | gather landing |
| `/governance/gather/attendance` | `SgGatherAttendance` | gather attendance |

Preview-only governance mirrors also exist under `/exposed/governance`.

Legacy `/sg` and `/exposed/sg` paths now redirect to governance routes.

## Navigation Guard Behavior

The router guard enforces session and role rules in this order:

1. unauthenticated access to auth-required routes redirects to `Login`
2. authenticated users with required password change are forced to `ChangePassword`
3. authenticated users with a pending privileged face step are forced to `PrivilegedFaceVerification`
4. authenticated flows initialize the dashboard session before allowing role workspaces
5. users who still need face enrollment are forced to `FaceRegistration` unless the route explicitly allows bypass
6. role-specific routes are constrained so:
   - admins are redirected away from student and School IT routes
   - School IT users are redirected away from student routes
   - privileged sessions are redirected to their default route instead of the student dashboard
   - non-admin users cannot enter `/admin`
   - non-School IT users cannot enter `/workspace`

## Layout Model

`AppLayout.vue` is the shared shell for authenticated workspace routes.

Main layout pieces:

- side navigation for desktop
- top-level content region for workspace views
- mobile navigation for mobile devices
- shared route transitions and navigation-state handling

## Platform-aware View Loading

The router does not hardcode a single view implementation for every route. Instead it uses:

- `authView(...)`
- `dashboardView(...)`
- `toolsView(...)`
- `createPlatformView(...)`

That allows the route tree to stay stable while the frontend resolves desktop or mobile implementations behind the same logical page.

## Current Frontend Structure Highlights

Important April 2026 frontend changes now reflected in the route tree:

- privileged face MFA route moved to `/privileged/face`
- profile security and face-update flows live outside the old `/dashboard/profile/security` pattern
- governance event and sanctions routes are now first-class routes under `/governance/events...`
- preview workspaces mirror real admin, School IT, dashboard, and governance routes under `/exposed/*`
- student sanctions are now part of the standard dashboard flow through `/dashboard/sanctions`

## Related Docs

- `../api/frontend-integration.md`
- `../frontend/README.md`
- `../../changelog/frontend.md`
