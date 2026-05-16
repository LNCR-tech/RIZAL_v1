---
sidebar_position: 3
title: Endpoints
---

# API Endpoints

🔒 **Restricted**: Developer documentation

## Users

### Get Current User
```
GET /api/v1/users/me
```

### List Users
```
GET /api/v1/users?page=1&limit=20
```

### Get User by ID
```
GET /api/v1/users/{user_id}
```

## Events

### List Events
```
GET /api/v1/events
```

### Create Event
```
POST /api/v1/events
```

### Get Event Details
```
GET /api/v1/events/{event_id}
```

## Attendance

### Check In
```
POST /api/v1/attendance/checkin
```

### Get Attendance Records
```
GET /api/v1/attendance/records?user_id={id}
```

## Face Recognition

### Enroll Face
```
POST /api/v1/face/enroll
```

### Verify Face
```
POST /api/v1/face/verify
```

For detailed request/response schemas, see the interactive API docs at `/docs`.
