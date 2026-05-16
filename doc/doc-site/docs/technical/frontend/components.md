---
sidebar_position: 2
title: Components
---

# Frontend Components

**Restricted**: Technical documentation

## Overview

Aura frontend components should stay aligned with the actual attendance workflow: face scan as the primary check-in method, geolocation validation, and manual operator entry as the fallback.

## Core components

### FaceScanner

Face recognition camera component:

- Requests camera access.
- Captures the user's face.
- Sends the image or embedding payload for validation.
- Shows success, retry, and failure states.
- Handles anti-spoofing or liveness feedback when returned by the backend.

### GeofenceStatus

Location validation component:

- Requests location permission.
- Displays GPS accuracy.
- Shows whether the user is inside the event boundary.
- Explains blocked check-in states when location is unavailable or outside the geofence.

### ManualAttendanceEntry

Operator fallback component:

- Searches for a student.
- Selects attendance status.
- Captures a reason or note.
- Submits the manual record for audit-friendly tracking.

### EventCard

Event display component:

- Shows event title, schedule, location, and status.
- Provides check-in actions when the event is active.
- Shows role-aware management actions for SSG, SG, ORG, campus admin, and admin users.

### AttendanceTable

Attendance records component:

- Supports sorting, filtering, and pagination.
- Shows check-in method, status, timestamp, and operator notes when available.
- Exports or links to reports for authorized roles.

## Usage example

```jsx
<FaceScanner
  eventId={event.id}
  onSuccess={handleCheckInSuccess}
  onError={handleCheckInError}
/>
```

## Styling

Components should use shared design tokens where possible and avoid one-off color systems. Keep operational screens dense, readable, and predictable.
