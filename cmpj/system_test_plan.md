# VALID8 System Test Plan

This document outlines the required verification tests for the VALID8 platform and the number of successful attempts needed to consider each feature "stable."

## 1. Authentication and Access Control
| Feature to Test | Manual Attempts | Automated Iterations | Error Cases to Test |
| :--- | :---: | :---: | :--- |
| **Standard Login** | 3 | 100+ | Invalid password, non-existent email. |
| **MFA Verification** | 3 | 100+ | Wrong code, expired code, re-using code. |
| **JWT Token Validation** | 3 | 50+ | Access with no token, expired token. |
| **Password Reset Request** | 3 | 50+ | Reset for non-existent email. |
| **Password Reset Approval** | 3 | 50+ | Double approval of same request. |

## 2. User & Profile Management
| Feature to Test | Manual Attempts | Automated Iterations | Error Cases to Test |
| :--- | :---: | :---: | :--- |
| **Single User Creation** | 3 | 50+ | Duplicate email, missing fields. |
| **Biometric Registration** | 3 | 50+ | Duplicate face data. |
| **Profile Updates** | 3 | 50+ | Duplicate email in profile. |

## 3. School and Multi-Tenancy
| Feature to Test | Manual Attempts | Automated Iterations | Error Cases to Test |
| :--- | :---: | :---: | :--- |
| **School Tenant Creation** | 3 | 20+ | Duplicate school code. |
| **Tenant Isolation Check** | 5 | 200+ | Cross-school data access attempts. |
| **Subscription Limit Check** | 3 | 50+ | Exceeding user limits. |

## 4. Import Center
| Feature to Test | Manual Attempts | Automated Iterations | Error Cases to Test |
| :--- | :---: | :---: | :--- |
| **Bulk Student Import** | 3 | 20+ | Malformed file, duplicate IDs. |
| **Import Error Reporting** | 3 | 20+ | Checking error log accuracy. |
| **Retry Failed Rows** | 3 | 20+ | Invalid retry data. |

## 5. Event and Attendance Operations
| Feature to Test | Manual Attempts | Automated Iterations | Error Cases to Test |
| :--- | :---: | :---: | :--- |
| **Event Creation** | 3 | 100+ | Overlapping events. |
| **Face Recognition Log** | 5 | 500+ | Mocking face matches via API. |
| **Attendance Override** | 3 | 50+ | Unauthorized override attempts. |
| **Attendance Export** | 3 | 20+ | Exporting while data is moving. |

## 6. System Infrastructure & Governance
| Feature to Test | Successful Attempts | Error Cases to Test |
| :--- | :---: | :--- |
| **Audit Log Generation** | 3 | Performing an action and verifying it appears in the log. |
| **Notification Delivery** | 3 | Sending notification with no recipient email. |

## 7. Automated Test Logging
To keep data clean across different table structures, automated results will be saved into 4 distinct files:

1.  **Group A (Core API)**: `cmpj/logs_core_api.psv`
2.  **Group B (Security)**: `cmpj/logs_security.psv`
3.  **Group C (Bulk Specs)**: `cmpj/logs_bulk_ops.psv`
4.  **Group D (Biometrics)**: `cmpj/logs_biometrics.psv`

*   **Format**: **PSV (Pipe-Separated Values)**.
*   **Spreadsheet Compatibility**: YES. You can import `.psv` files into **Microsoft Excel** and **Google Sheets** by clicking "Import" or "Open" and selecting "Other" or "Custom" for the delimiter, then typing the pipe symbol `|`.

