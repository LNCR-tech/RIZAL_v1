# Final Documentation Corrections

This note records the current source-of-truth corrections for the Aura doc-site.

## Current attendance methods

Aura documentation should describe only these attendance methods:

- face scan with face recognition and anti-spoofing support
- manual operator entry as a fallback
- geolocation validation for event boundaries

## Current roles

Aura documentation should use these roles:

- `admin`
- `campus_admin`
- `school_it`
- `ssg`
- `sg`
- `org`
- `student`

## Current check-in flow

```text
1. Student goes to the event location.
2. Student uses the kiosk or mobile app for face scan.
3. System validates face, event time, and geofence.
4. Attendance is recorded.
5. If face scan fails, an authorized operator can record manual attendance.
```

## Verification checklist

- User docs describe face scan, manual fallback, and geolocation.
- Role lists match the current Aura roles.
- Technical docs are limited to authorized technical users.
- Docusaurus build completes with `npm run build`.
