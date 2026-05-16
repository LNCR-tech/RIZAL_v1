---
sidebar_position: 1
title: Getting Started
---

# Getting Started with Aura

Welcome to Aura, your school's student attendance management system.

## What is Aura?

Aura is a comprehensive attendance tracking system that uses:
- 📸 **Face Recognition** (InsightFace with anti-spoofing)
- 📝 **Manual Entry** (operator-driven)
- 📍 **Geolocation Verification**

## Quick Start Guide

### For Students

#### 1. First Time Setup
1. **Enroll Your Face**: Visit your school's enrollment kiosk
2. **Download Mobile App**: Get the Aura PWA on your device
3. **Login**: Use your school credentials

#### 2. Daily Use
1. **Check Event Schedule**: View upcoming events in the app
2. **Attend Events**: Go to event location within the geofence
3. **Check In**: Use face scan at kiosk or mobile app
4. **View History**: Check your attendance record anytime

### For Event Managers (SSG/SG/ORG)

1. **Create Event**: Set up event details, time, and location
2. **Configure Geofence**: Define check-in area boundaries
3. **Monitor Attendance**: Track real-time check-ins
4. **Generate Reports**: Export attendance data

### For Administrators

1. **School Setup**: Configure organization hierarchy
2. **Import Students**: Bulk upload via Excel
3. **Manage Users**: Assign roles and permissions
4. **View Analytics**: Monitor system-wide attendance

## Quick Links

### User Documentation
- [User Manual Overview](./user-manual/overview) — Complete feature guide
- [Attendance Guide](./user-manual/attendance) — How to check in
- [Events Guide](./user-manual/events) — Managing events
- [Profile Management](./user-manual/profile) — Update your info
- [Mobile App Guide](./mobile-guide) — Mobile installation
- [FAQ](./faq) — Common questions

### Technical Documentation
- [API Reference](/technical/api/overview) — REST API docs (Developers only)
- [Backend Architecture](/technical/backend/architecture) — System design
- [Database Schema](/technical/backend/database) — Data structure
- [Deployment Guide](/technical/deployment/docker) — Production setup

## User Roles

| Role | Description | Access Level |
|------|-------------|-------------|
| **admin** | Platform administrator | Full system access, all schools |
| **campus_admin** | Campus/School administrator & IT | School-level management, technical access, reports |
| **student** | Regular student | View own attendance, check in to events |
| **ssg/sg/org** | Student government officers | Create events, manage attendance, reports |

## Key Features

### 🎭 Face Recognition
- **InsightFace ONNX**: High-accuracy biometric verification
- **Anti-Spoofing**: MiniFASNetV2 prevents photo/video attacks
- **Two Modes**: Self-scan (student) and Gather/kiosk (operator)

### 📍 Geolocation
- **GPS Verification**: Ensure physical presence at events
- **Geofence**: Define check-in boundaries
- **Accuracy Check**: Validate location precision

### 📊 Attendance Tracking
- **Real-time**: Instant check-in confirmation
- **Status Types**: Present, Late, Absent, Excused
- **Sanctions**: Automated violation tracking

### 🏛️ Governance Hierarchy
- **Multi-level**: School → Department → Program → Section
- **Role-based Access**: Scoped permissions
- **Event Management**: SSG/SG/ORG can create events

### 🤖 AI Assistant
- **Natural Language**: Ask questions about attendance
- **MCP Integration**: Live data queries
- **Streaming Responses**: Real-time answers

## Need Help?

- 📖 Check the [FAQ](./faq) for common questions
- 💬 Contact your school's IT support
- 🐛 Report issues to your campus admin
- 📧 Email: support@aura.school (if configured)

## Next Steps

1. **New Users**: Read the [User Manual Overview](./user-manual/overview)
2. **Event Managers**: Learn about [Event Management](./user-manual/events)
3. **Developers**: Explore [Technical Documentation](/technical/api/overview)
4. **Troubleshooting**: Visit [FAQ](./faq) for solutions
