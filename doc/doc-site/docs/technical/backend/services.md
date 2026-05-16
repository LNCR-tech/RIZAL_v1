---
sidebar_position: 3
title: Services
---

# Backend Services

🔒 **Restricted**: Developer documentation

## Service Layer

Business logic is separated into service modules.

## Core Services

### AuthService
Handles authentication and authorization:
- User login/logout
- Token generation/validation
- Password hashing
- Role verification

### FaceService
Face recognition operations:
- Face enrollment
- Face verification
- Embedding generation
- Anti-spoofing detection

### AttendanceService
Attendance tracking:
- Check-in validation
- Geofence verification
- Duplicate check-in prevention
- Attendance record creation

### NotificationService
Push notifications:
- Event reminders
- Attendance confirmations
- System alerts

### SanctionService
Sanction management:
- Automated sanction tracking
- Violation detection
- Sanction reporting

### ReportService
Report generation:
- Attendance reports
- Student reports
- Export to PDF/Excel

## Usage Example

```python
from app.services.attendance_service import AttendanceService

# Check in user to event
result = await AttendanceService.check_in(
    user_id=1,
    event_id=5,
    method="face",
    location={"lat": 14.5995, "lng": 120.9842}
)
```
