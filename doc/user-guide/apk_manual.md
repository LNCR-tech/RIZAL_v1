# AURA APK User Manual

[<- Back to doc index](../README.md)

> **Status:** ACTIVE
> **Last Updated:** 2026-04-25

---

## Purpose

This manual explains how to install and use the AURA Android APK for daily attendance and school operations.

---

## SSOT Note

Canonical role routing and workspace mapping are maintained in:
- [docs/user/navigation.md](../../docs/user/navigation.md)
- [docs/user/overview.md](../../docs/user/overview.md)

If this manual conflicts with those pages, follow `docs/user/*`.

---

## Who Should Use This

- Students
- Campus Admin / School IT users
- Governance / SSG officers
- Platform/Admin users (if enabled by your school)

Your available menus depend on your assigned role.

---

## Device Requirements

- Android 7.0 (API 24) or newer
- Stable internet connection (Wi-Fi or mobile data)
- Working camera for face attendance and face registration
- Enough free storage for app install and updates

---

## Install the APK

1. Get the latest `app-debug.apk` or release APK from your school IT or deployment admin.
2. On your Android phone, allow installation from unknown sources for the app you use to open APK files (Files, Chrome, etc.).
3. Open the APK file and tap `Install`.
4. Wait for install to complete, then tap `Open`.

If Android blocks the install, open `Settings` > `Security` (or `Apps` > `Special access` > `Install unknown apps`) and allow it, then retry.

---

## Update the APK

1. Download the newer APK version.
2. Install it using the same package name (`com.aura.app`).
3. Confirm update when prompted.

Updating this way normally keeps your app data and account session, but log in again if the session expires.

---

## First-Time Setup

1. Launch `AURA`.
2. Grant permissions when prompted:
   - `Camera`: required for face registration and face attendance scanning.
   - `Location`: may be required for attendance/location validation depending on school policy.
   - `Notifications` (if shown): allows school alerts on supported builds.
3. Sign in using your assigned school credentials.
4. If required, change your temporary password on first login.
5. Complete face registration if your school uses face attendance.

---

## Daily Usage Flow

### Student

1. Open the app and sign in.
2. Go to `Dashboard` to view today's events.
3. Open `Schedule` to see upcoming events and details.
4. Check attendance status in event attendance pages and `Analytics`.
5. Use `Chat` if enabled for your account.

### Campus Admin / School IT

1. Sign in to the `Workspace` area.
2. Manage users, departments, programs, and student imports.
3. Monitor attendance and event schedules.
4. Review school settings and reports as needed.

### Governance / SSG Officer

1. Sign in to `Governance`.
2. Create/manage events and attendance settings.
3. Use event attendance screens during live activities.
4. Review governance reports and sanctions workflows where enabled.

---

## Face Attendance Flow (APK)

1. Open the event attendance screen.
2. Start scan/capture.
3. Allow camera access if prompted.
4. Keep the face centered and well lit.
5. Wait for match result and attendance confirmation.

If scan fails, switch to manual attendance with officer/admin assistance.

---

## Troubleshooting

| Issue | Likely Cause | What To Do |
|---|---|---|
| APK will not install | Unknown sources not allowed | Enable `Install unknown apps` for the source app, then retry |
| Cannot log in | Wrong credentials or inactive account | Recheck username/password, then contact Campus Admin |
| Camera does not open | Camera permission denied | Enable camera permission in Android app settings |
| Face scan fails often | Poor lighting, angle, or missing face profile | Improve lighting/position, then re-register face if needed |
| Data does not load | No internet or backend unavailable | Check connection, then retry; report outage to IT |
| Attendance marked late unexpectedly | Event time window already shifted | Ask event officer/admin to verify event attendance windows |

---

## Security and Good Practice

- Do not share your login credentials.
- Log out when using a shared device.
- Update to the latest APK provided by your school.
- Report lost/stolen devices to Campus Admin immediately.

---

## Quick User Checklist

- [ ] APK installed successfully
- [ ] Logged in with school account
- [ ] Password changed (if first login)
- [ ] Camera/location permissions granted as needed
- [ ] Face profile registered (if required)
- [ ] Able to open schedule and attendance pages
