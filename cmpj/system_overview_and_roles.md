# VALID8 System Overview and Role Definitions

This document provide a comprehensive breakdown of the VALID8 Event Attendance Management System, its users, and the specific capabilities associated with each role.

## 1. What is the purpose of this website?
**VALID8** is an automated Event Attendance Management System designed for universities. The platform establishes a secure and fraud-resistant environment for tracking student presence at campus events.

Key features include:
*   **Biometric Verification**: AI face recognition identifies and confirms student identity.
*   **Tenant Isolation**: Multi-school database segregation ensures school-level data independence.
*   **Automated Auditing**: Every administrative action is recorded for compliance and transparency.
*   **Data Governance**: Built-in retention policies manage student records and attendance history.

## 2. Platform Users
The system is accessible to the following user groups:
*   **Students**: Register for events and monitor personal attendance data.
*   **Student Leaders (SSG)**: Organize events and manage logistical entries.
*   **School Staff/IT**: Manage school student data and oversee operational settings.
*   **Platform Administrators**: Manage the global system, school deployments, and subscriptions.

## 3. User Roles
The system utilizes a Role-Based Access Control (RBAC) model with four primary roles:
*   **System Administrator (Admin)**: The top-tier role with global platform control.
*   **School IT**: The primary administrator for a specific school tenant.
*   **Event Organizer / SSG**: Users responsible for event staging and execution.
*   **Student**: The fundamental user level.

## 4. Capability Matrix

| Role | Core Capabilities |
| :--- | :--- |
| **Student** | Biometric face encoding registration, personal attendance history tracking, and password reset requests. |
| **SSG / Organizer** | Event creation and management, face-based attendance scanning, manual verification, and event reporting. |
| **School IT** | Bulk student data import (Excel), password reset approval, and school-wide audit log access. |
| **System Admin** | School tenant management, School IT account creation, and platform-wide governance configuration. |

## 5. Interface & Navigation

*   **Student Dashboard**: Provides access to attendance records and the face registration module.
*   **Organizer Interface**: Focuses on event management lists and the scanning module for check-ins.
*   **School IT Panel**: Centralized access for student list management, bulk imports, and audit logs.
*   **System Admin Hub**: Global settings for schools, subscriptions, and platform security.

## 6. Functional Features
*   **Biometric Registration**: Interface for capturing and encoding student facial features for identity verification.
*   **Bulk Import Center**: A validation-heavy module for importing student records via Excel.
*   **MFA (Multi-Factor Authentication)**: Mandatory email-delivered verification codes for high-privilege accounts.
*   **Tenant Isolation**: Strict cross-school data restrictions enforced at the database and API layers.
