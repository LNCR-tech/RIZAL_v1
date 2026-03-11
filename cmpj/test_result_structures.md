# Automated Test Result Table Structures

This document defines the standardized table formats for logging automated test results. Tests are grouped by the similarity of their required metrics.

## Group A: Core Feature Testing (API Transactions)
*Used for: Authentication, User Profiles, School Settings, Event Creation, Notifications, Audit Logs.*

| Timestamp | Test ID | Iteration | Endpoint | Status | Latency (ms) | Remarks |
| :--- | :--- | :---: | :--- | :--- | :---: | :--- |
| YYYY-MM-DD HH:MM:SS | AUTH_LOGIN | 001 | /auth/login | SUCCESS | 145ms | Admin login successful |
| YYYY-MM-DD HH:MM:SS | AUTH_MFA | 001 | /auth/mfa/verify | SUCCESS | 210ms | MFA bypass successful |

## Group B: Security & Multi-Tenant Isolation
*Used for: Tenant Isolation, Role-Based Access Control (RBAC) Verification.*

| Timestamp | Actor Role | Target School | Action Attempted | Expected | Actual | Lockdown Pass |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| YYYY-MM-DD HH:MM:SS | STUDENT_ROLE | School_B | View_Student_List | 403 Forbidden | 403 Forbidden | ✅ |
| YYYY-MM-DD HH:MM:SS | SCHOOL_IT | School_A | Delete_School_A | 401 Unauthorized | 401 Unauthorized | ✅ |

## Group C: Bulk Data Operations
*Used for: CSV/Excel Imports, Bulk Seeding, Data Retention Cleanup.*

| Timestamp | Job ID | Operation Type | Rows Total | Success | Failure | Duration | Error Report |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| YYYY-MM-DD HH:MM:SS | IMP_001 | Student_Import | 1,000 | 998 | 2 | 12s | view_errors.xlsx |
| YYYY-MM-DD HH:MM:SS | CLN_001 | Retention_Auto | 5,000 | 5,000 | 0 | 4s | N/A |

## Group D: AI & Biometric Biometrics
*Used for: Face Recognition, Encoding Matching, Scanner Logic.*

| Timestamp | Test Image ID | Match ID | Confidence | Encoding Delta | Expected | Result |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| YYYY-MM-DD HH:MM:SS | IMG_S001_A | STUDENT_001 | 98.4% | 0.04 | MATCH | ✅ PASS |
| YYYY-MM-DD HH:MM:SS | IMG_S002_B | STUDENT_999 | 12.1% | 0.89 | NO_MATCH | ✅ PASS |
