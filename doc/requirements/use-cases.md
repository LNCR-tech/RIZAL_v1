# Use Cases

[<- Back to doc index](../README.md)

> **Status:** MUST HAVE — IN PROGRESS
> **Last Updated:** 2026-04-22

---

## UC-01: User Login

**Actor:** Student / Campus Admin / Platform Admin
**Precondition:** User account exists

**Main Flow:**
1. User navigates to login page.
2. Submits email and password.
3. System validates credentials.
4. System issues JWT and routes user to their role dashboard.

**Alternate Flow — Invalid credentials:**
- Step 3a: User enters wrong email or password → System returns 401 error → User tries again.

---

## UC-02: Campus Admin Bulk Imports Students

**Actor:** Campus Admin
**Precondition:** Excel template has been filled with student data

**Main Flow:**
1. Campus Admin uploads Excel file.
2. System validates rows and returns preview with errors highlighted.
3. Campus Admin reviews and confirms import.
4. System queues background import job.
5. Welcome emails are sent with temporary passwords.
6. Campus Admin polls import status until complete.

**Alternate Flow — Failed rows:**
- Step 4a: Some rows fail validation → Campus Admin retries only failed rows after corrections.

---

## UC-03: SSG Officer Records Attendance

**Actor:** SSG Officer
**Precondition:** Event exists and is in `ongoing` status

**Main Flow:**
1. SSG Officer opens the event attendance page.
2. Searches for a student by name or ID.
3. Records time-in (manual or face-scan).
4. System stores attendance with status (PRESENT / LATE based on window).
5. Time-out can be recorded separately.

---

## UC-04: Face Recognition Attendance Check-In

**Actor:** Student
**Precondition:** Event is active and student has a registered face profile

**Main Flow:**
1. Student approaches the attendance station.
2. System captures the student's face scan.
3. System verifies the face against the registered profile.
4. System records attendance using the matched student identity.

---

## UC-05: Platform Admin Deactivates a School

**Actor:** Platform Admin
**Precondition:** School is currently active

**Main Flow:**
1. Platform Admin changes school status to inactive.
2. System cascades deactivation to the linked Campus Admin account.
3. Active sessions for students of that school are automatically rejected at protected routes.

---

## UC-06: Officer Extends Attendance Override

**Actor:** SSG / SG / ORG Officer (assigned by Campus Admin)
**Precondition:** Event is nearing start time

**Main Flow:**
1. The assigned officer opens the event management page.
2. Sets `present_until_override_at` and/or `late_until_override_at` to a future datetime.
3. System accepts late check-ins beyond the normal threshold until the override time.

---

## UC-07: User Sends a Query to the AI Assistant

**Actor:** Any authenticated user
**Precondition:** User is logged in with a valid JWT

**Main Flow:**
1. User opens the assistant interface.
2. User types a natural language question (e.g. "How many students attended last week's event?").
3. Assistant validates the JWT and extracts user scope.
4. Assistant queries the tenant database through the MCP policy layer.
5. Assistant returns a scoped, role-appropriate answer.

**Alternate Flow — Out of scope query:**
- Step 4a: Query targets restricted columns or another school → Assistant refuses and explains why.
