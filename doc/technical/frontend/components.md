# Components Reference

> Every component in the project, grouped by folder.

---

## UI Components (`components/ui/`)

### `BaseButton.vue`

Reusable button used across all pages (login, event cards, etc.).

| Prop      | Type    | Default     | Description                       |
| --------- | ------- | ----------- | --------------------------------- |
| `type`    | String  | `'button'`  | HTML button type                  |
| `variant` | String  | `'primary'` | `'primary'` / `'secondary'` / `'ghost'` |
| `size`    | String  | `'md'`      | `'sm'` / `'md'` / `'lg'`         |
| `loading` | Boolean | `false`     | Shows spinner, disables button    |
| `disabled`| Boolean | `false`     | Disables button                   |

- **Slot**: Default slot for button label.
- Primary variant uses `--color-text-always-dark` as background with white text.

---

### `BaseInput.vue`

Text/email/password input with built-in password visibility toggle.

| Prop          | Type    | Default | Description                   |
| ------------- | ------- | ------- | ----------------------------- |
| `id`          | String  | `''`    | HTML id attribute             |
| `modelValue`  | String  | `''`    | v-model binding               |
| `type`        | String  | `'text'`| `'text'` / `'email'` / `'password'` |
| `placeholder` | String  | `''`    | Placeholder text              |
| `disabled`    | Boolean | `false` | Disables input                |
| `autocomplete`| String  | `'off'` | Browser autocomplete hint     |

| Event              | Payload         | Description          |
| ------------------ | --------------- | -------------------- |
| `update:modelValue`| `string`        | v-model sync         |
| `enter`            | —               | Enter key pressed    |

- Automatically shows an eye icon toggle when `type="password"`.

---

### `AuraChatWindow.vue`

Expandable AI chat widget triggered from the navigation sidebar. Displays a chat interface with typing indicator and canned responses (real AI integration pending).

---

## Navigation Components (`components/navigation/`)

### `SideNav.vue` (Desktop Only)

A fixed, vertically-centered black pill on the left side of the screen.

**Contains:**
- Nav icon buttons defined in `navigationItems.js` (Home, Profile, Schedule, Analytics, School IT, etc.).
- Expandable Aura AI chat widget.

---

- Same nav items as `SideNav` (loaded from `navigationItems.js`).
- Same active state style (glow + dot).
- Hidden on desktop (`md:hidden`).

---

### `MobileBrandedBottomNav.vue` (Mobile Only)

A school-branded version of the bottom navigation bar. Adapts its colors and styling based on the current school theme settings.

---

### `MobileGlassIconNav.vue` (Mobile Only)

A premium navigation bar option featuring translucent glassmorphism effects and modern icon styling.

---

### `navigationItems.js`

Centralized navigation item definitions shared between `SideNav` and `BottomNav`. Contains route names, paths, and icons for all navigation targets including the School IT workspace.

---

## Dashboard Components (`components/dashboard/`)

### `TopBar.vue`

Header bar shown on all dashboard pages.

| Prop          | Type   | Default | Description                  |
| ------------- | ------ | ------- | ---------------------------- |
| `user`        | Object | `null`  | User object from API         |
| `unreadCount` | Number | `0`     | Unread announcement count    |

| Event                 | Description               |
| --------------------- | ------------------------- |
| `toggle-notifications`| Bell icon clicked         |

**Features:**
- Profile pill (avatar/initials + name) — expands on hover/tap to reveal a red **Sign Out** button.
- Notification bell with unread dot badge.
- Dark mode toggle (moon icon).

---

### `UniversityBanner.vue`

A large colored card showing the school's name and logo.

| Prop         | Type   | Default                     | Description       |
| ------------ | ------ | --------------------------- | ----------------- |
| `schoolName` | String | `'University Name'`         | School display name |
| `schoolLogo` | String | `'/logos/university_logo.svg'` | Logo image URL  |

| Event               | Description                    |
| -------------------- | ------------------------------ |
| `announcement-click` | "Latest Announcement" button pressed |

- Background uses `--color-primary`.
- Text color is auto-contrasted via `--color-banner-text`.
- Logo has an `@error` fallback that hides it if the image fails to load.

---

### `EventsCard.vue`

A split card showing the latest upcoming event.

| Prop     | Type  | Default | Description       |
| -------- | ----- | ------- | ----------------- |
| `events` | Array | `[]`    | Array of events   |

| Event      | Payload | Description              |
| ---------- | ------- | ------------------------ |
| `see-event`| Event   | "See Event" button click |

- Left side: "Latest Event" title + CTA button.
- Right side: event name (in primary color), truncated description, and formatted date.
- Filters for `upcoming` or `ongoing` events only.

---

### `EventCard.vue`

Individual event card component with improved layout, date formatting, and mobile responsiveness. Used in event listing sections throughout the dashboard.

---

### `MobileDashboardHome.vue`

A fully redesigned mobile-first dashboard home layout. Replaces the default desktop layout on small screens with a responsive card layout optimized for touch interaction.

---

### `SchoolItMetricRing.vue`

Reusable metric visualization ring component used in the School IT workspace dashboard. Displays circular progress indicators for workspace metrics.

---

### `SchoolItTopHeader.vue`

Top header specific to the School IT workspace, providing workspace-level navigation and context.

---

### `DepartmentProgramRingChart.vue`

Visual chart component for displaying department statistics and program distributions.

---

### `NotificationsPanel.vue`

A pull-out panel that displays context-aware notifications. Triggered by the bell icon in the `TopBar.vue`. Uses `useNotifications.js` to manage the list of active alerts.

---

## Security Components (`components/security/`)

### `SecurityActionPill.vue`

An inline security action trigger component. Used to initiate security-related flows (e.g., re-verification, session management) from within profile and settings views.

---

### `SecurityHeaderBar.vue`

A branded security header bar displayed at the top of privileged/security views. Provides visual context indicating the user is in a security-sensitive area.

---

## Attendance Components (`components/attendance/`)

### `FaceScanPanel.vue`

Camera-based face scan panel component used in attendance tracking. Provides the UI for face detection and scan feedback during attendance check-in.

---

## Council Components (`components/council/`)

### `StudentCouncilMemberStage.vue`

Multi-stage form component for managing individual student council members. Handles member details, role assignment, and validation.

---

### `StudentCouncilSetupStage.vue`

Setup stage component for configuring student council structure. Provides forms for defining council positions, terms, and organizational hierarchy.

---

## Gather Components (`components/gather/`)

### `GatherEventPill.vue`

Compact event representation used in the Gather subsystem's discovery feeds.

### `GatherScanDiscoveryArt.vue`

Animated or static artwork displayed during active event scanning or discovery states.

### `GatherSuccessSheet.vue`

A bottom-sheet view showing success feedback after a successful attendance registration in Gather.

---

## Governance Components (`components/governance/`)

### `GovernanceTrendChart.vue`

Main data visualization component for the Governance workspace, showing trends over time.

### `GovernanceArrivalBars.vue` & `GovernanceBreakdownBars.vue`

Horizontal bar charts for visualizing arrival patterns and categorical breakdowns of governance data.

### `GovernanceCreateSheet.vue`

Action-oriented sheet for creating new governance units, activities, or records.

---

## Generic UI Components (`components/ui/`)

### `GradientText.vue`

Utility component for rendering text with CSS gradients, aligned with the Aura design language.

---

## Auth Views (`views/auth/`)

### `LoginView.vue`

Animated login page with email/password fields, loading state, error display, and "Powered by Aura Ai" branding.

---

### `FaceRegistrationView.vue`

Handles the initial student face enrollment process required for dashboard access. Connects to the device camera using `useFaceScanDetector.js` with improved camera handling and UX flow.

---

### `ChangePasswordView.vue`

Full password change workflow with current/new password fields, validation rules, and confirmation.

---

### `PrivilegedFaceVerificationView.vue`

Secure face verification flow for privileged actions. Used when the system requires re-verification before allowing sensitive operations.

---

## Dashboard Views (`views/dashboard/`)

### `HomeView.vue`

Main dashboard view. Displays:

1. `TopBar` — profile + notifications + dark mode.
2. Page title "Home".
3. Search bar + "Talk to Aura AI" button (mobile only).
4. `UniversityBanner` + `EventsCard` side-by-side (stacked on mobile).
5. Upcoming Events list — each item shows date badge, name, location, and status.

On mobile, `MobileDashboardHome.vue` is used as an alternative layout.

---

### `DashboardView.vue`

Top-level routing shell for the entire `/dashboard` namespace. Acts as a structural pass-through that wraps all student dashboard child routes inside the `AppLayout`. Added in [3.9.0] as part of the desktop/mobile architecture formalization.

---

### `ProfileView.vue`

Student profile page with user details and navigation to sub-views (security settings, face update).

---

### `ProfileSecurityView.vue`

Dedicated security settings view — password management, session overview, and security action triggers.

---

### `ProfileFaceUpdateView.vue`

Face re-enrollment/update flow accessible from the profile. Allows students to update their enrolled face data.

---

### `ScheduleView.vue`

Student schedule view with class timetable display.

---

### `AnalyticsView.vue`

Student analytics view with data visualizations for attendance trends and academic metrics.

---

### `AttendanceView.vue`

Attendance records view showing check-in history and status.

---

### `EventDetailView.vue`

Detailed view for individual events showing full description, date, location, and status.

---

### `PrivilegedComingSoonView.vue`

Placeholder for upcoming privileged features. Displays a "Coming Soon" message for features under development.

---

### School IT Workspace Views

#### `SchoolItHomeView.vue`

School IT workspace landing page with metric rings and an overview of workspace activity.

#### `SchoolItDepartmentProgramsView.vue`

Manage university departments and academic programs.

#### `SchoolItImportStudentsView.vue`

Batch import students via CSV functionality.

#### `SchoolItProgramStudentsView.vue`

Manage and view students assigned to a specific program.

#### `SchoolItSettingsView.vue`

Configuration settings for the School IT workspace.

#### `SchoolItStudentCouncilView.vue`

Full student council management interface with member listing, role assignment via `StudentCouncilMemberStage` and `StudentCouncilSetupStage` components.

#### `SchoolItUsersView.vue`

User management view for the School IT workspace. Handles listing, searching, and managing users.

#### `SchoolItAttendanceMonitorView.vue`

School-wide attendance monitoring dashboard. Displays real-time and historical attendance data across programs and events.

#### `SchoolItEventReportsView.vue`

Event reporting and analytics view for the School IT workspace. Aggregates event data and generates summary reports.

#### `SchoolItScheduleView.vue`

Schedule management view for the School IT workspace. Allows administrators to view and manage institutional schedules.

#### `SchoolItUnassignedStudentsView.vue`

Lists students who exist in the system but have not yet been assigned to a department or program. Provides tools to resolve unassigned status.

#### `WorkspacePlaceholderView.vue`

Placeholder for upcoming workspace views not yet implemented.

#### `GovernanceWorkspaceView.vue`

The unified workspace for the Student Government (SG). Replaced most individual SG views with a modular multi-section view providing analytics and management tools in one place.

#### `GatherWelcomeView.vue` & `GatherAttendanceView.vue`

Core views for the Gather subsystem — the immersive attendance and discovery experience for students and kiosks.

---

### Admin Workspace Views

#### `AdminWorkspaceView.vue`

Root-level workspace management view for administrators. Provides high-level oversight and management tools across all schools and workspaces. Uses `useAdminWorkspaceData.js` composable and `adminDashboardPreview.js` for data.

---

### Student Government (SG) Views

#### `SgDashboardView.vue`

SG main dashboard with an overview of the Student Government's metrics, upcoming events, and announcements. Uses `useSgDashboard.js` composable.

#### `SgAnnouncementsView.vue`

Announcement management for the Student Government. Allows SG officers to create and manage announcements.

#### `SgAttendanceView.vue`

Attendance tracking interface for Student Government events and meetings.

#### `SgCreateUnitView.vue`

Form view for creating and configuring Student Government organizational units (committees, departments, etc.).

#### `SgEventsView.vue`

Event management for the Student Government. Lists and manages SG-organized events.

#### `SgMembersView.vue`

Member management and roster view for the Student Government. Enables viewing, adding, and managing SG members and their roles.

#### `SgStudentsView.vue`

Student membership view for the Student Government. Shows students associated with the SG and their status.

---

## Developer Tools (`views/tools/`)

### `ApiLabView.vue` (`/api-lab`)

A developer tool for testing live backend endpoints directly from the frontend UI. Simulates requests, displays raw JSON responses, and provides endpoint configuration to verify the backend connection.
