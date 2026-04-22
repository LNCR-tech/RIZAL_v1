# Aura — Product Overview

## Purpose
Aura is a school-grade student attendance management system. It automates attendance tracking via face recognition, QR/RFID scanning, and geolocation, and provides governance, reporting, and AI-assisted analytics for educational institutions.

## Key Features
- **Attendance Tracking**: Face scan (InsightFace), RFID, QR code, and geolocation-based check-in flows
- **Event Management**: Create and manage school events with configurable attendance windows and sanctions
- **Face Recognition**: InsightFace-powered biometric enrollment and verification with anti-spoofing (MiniFASNetV2 ONNX)
- **Governance Hierarchy**: Multi-level org units (school → department → program → section) with role-based access
- **Student Import**: Bulk Excel import with validation preview and background processing via Celery
- **Sanctions System**: Automated sanction tracking tied to attendance violations
- **Reports Module**: Attendance, school, student, and system reports with PDF/chart export
- **AI Assistant (Aura)**: Streaming LLM assistant (OpenAI/Gemini) with MCP tool integration for querying live school data
- **Notifications**: In-app notification center with real-time updates
- **PWA + Mobile**: Progressive Web App with Capacitor wrapper for Android native deployment
- **Multi-tenant**: School-scoped data isolation with per-school branding (logo, colors)

## Target Users
| Role | Capabilities |
|------|-------------|
| `admin` | Full system access, school setup, user management |
| `campus_admin` | School-level admin, reports, governance |
| `ssg` / `sg` | Student government officers, event and attendance management |
| `teacher` / `faculty` | Event creation, attendance monitoring for their events |
| `student` | View own attendance, schedule, mobile check-in |
| `school_it` | Technical configuration, import, face enrollment |

## Core Use Cases
1. School admin bootstraps institution, imports students via Excel
2. Faculty creates events; students check in via face scan or QR at kiosk
3. Governance officers monitor attendance dashboards and export reports
4. AI assistant answers natural-language queries about attendance data
5. Sanctions are automatically applied for attendance violations
