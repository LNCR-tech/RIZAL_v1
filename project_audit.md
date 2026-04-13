# Project Audit: Student Attendance System (Aura Project)

This document provides a comprehensive audit of the **Aura Student Attendance System**, detailing its architecture, technology stack, and core modules.

---

## 1. Project Overview
The Aura Project is an enterprise-grade Student Attendance and Governance Management System. It leverages biometric face recognition, geolocation, and a robust RBAC (Role-Based Access Control) system to manage student attendance, organizational governance (SSG/SG), and administrative tasks.

- **Primary Goal:** To provide secure, automated, and verifiable attendance tracking and governance management for educational institutions.
- **Key Users:** Platform Admins, School Administrators (Campus Admins), Students, and Governance Members (SSG/SG).

---

## 2. System Architecture
The system follows a modern decoupled architecture:

### **Frontend (Vue SPA & Mobile)**
- **Framework:** Vue.js 3 (Vite-based)
- **Styling:** TailwindCSS 4
- **State Management:** Pinia
- **Mobile Support:** Capacitor (for Android/iOS builds)
- **Key Capabilities:**
  - Real-time face detection/capture (MediaPipe, InsightFace)
  - Interactive dashboards with Chart.js
  - PDF report generation (jsPDF)
  - Map-based geolocation display (Leaflet)
  - PWA capabilities (Service Workers)

### **Backend (API Service)**
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL (Relational Data)
- **Asynchronous Processing:** Celery with Redis (Task Queue)
- **Biometric Processing:** InsightFace & ONNX Runtime (MiniFASNetV2 for anti-spoofing)
- **Documentation:** Automatic OpenAPI/Swagger UI

### **AI Assistant Service**
- **Purpose:** Natural language interface for administrative actions and data querying.
- **Protocol:** MCP (Model Context Protocol)
- **Capabilities:**
  - Student record queries
  - Bulk import actions
  - Governance policy enforcement

---

## 3. Core Modules & Features

### **A. Authentication & Security**
- **Mechanism:** OAuth2 with JWT (JSON Web Tokens).
- **Security Features:**
  - Mandatory password change policies for new accounts.
  - Face-gated access for privileged roles (School IT/Admins).
  - Liveness detection (Anti-spoofing) during face verification.
  - Session validation and audit logging of login history.

### **B. Biometric Attendance (Face Recognition)**
- **Workflow:**
  1. **Registration:** Student captures a reference face profile.
  2. **Verification:** System computes embeddings (InsightFace) and compares them against stored profiles.
  3. **Liveness Check:** Ensures the face is real (not a photo/video) using MiniFASNetV2.
- **Attendance Modes:** 
  - **Quick Attendance:** Individual student sign-in/out.
  - **Public Attendance:** Group scanning using a fixed kiosk/camera.

### **C. Governance & Role Management**
- **Hierarchy:** Supports complex organizational structures (Departments -> Programs -> Students).
- **SSG/SG Integration:** Specialized roles for Student Government members with permissions for event management and announcement broadcasting.
- **Permission Matrix:** Granular control over who can view reports, manage events, or trigger sanctions.

### **D. Sanctions & Discipline**
- **Feature Set:**
  - Tracking of student violations and disciplinary actions.
  - Integration with attendance data to trigger automatic warnings.
  - Sanction governance permissions for specific administrators.

### **E. Administrative & Import Tools**
- **Bulk Import:** High-performance student import via Excel (`.xlsx`) using Celery background workers.
- **Branding:** Per-school white-labeling (Logos, Primary/Secondary colors).
- **Reporting:** Exportable attendance and governance reports in PDF and spreadsheet formats.

---

## 4. Infrastructure & Deployment
- **Containerization:** Docker & Docker Compose for orchestrated service deployment.
- **Service Mesh:**
  - `db`: PostgreSQL 15
  - `redis`: Redis 7
  - `backend`: FastAPI application
  - `worker/beat`: Celery background processing
  - `assistant`: AI interface
  - `mailpit`: SMTP testing interface for local development
- **Migrations:** Alembic for database schema versioning.

---

## 5. Technology Stack Summary

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | Vue 3, Vite, Pinia, TailwindCSS, Capacitor, Chart.js, Leaflet |
| **Backend** | Python 3, FastAPI, SQLAlchemy, Pydantic, Celery |
| **AI/Biometrics** | InsightFace, ONNX Runtime, MediaPipe, FAISS (for vector search) |
| **Data/Messaging** | PostgreSQL, Redis |
| **Testing/QA** | Pytest (Backend), Shell-based smoke tests (Frontend) |
| **DevOps** | Docker, Docker Compose, Nginx, GitHub Actions (CI) |

---

## 6. Audit Observations
- **Modularity:** The project is well-structured into separate domains (Attendance, Governance, Sanctions).
- **Security-First:** Heavy emphasis on face liveness and role-based gating for sensitive actions.
- **Scalability:** Uses background workers (Celery) for heavy tasks like student imports and face embedding computations.
- **Maintainability:** Clear separation of Models, Schemas, Routers, and Services in the backend.
