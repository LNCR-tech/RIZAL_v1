# VALID8 System Test Plan

This document outlines required verification tests for the VALID8 platform and the number of attempts needed to consider each feature stable.

## 0. Stability Criteria (Acceptance Thresholds)

- Manual attempts: 100% pass required; any critical error is a fail.
- Automated iterations: >= 98% success rate; no critical errors.
- Error cases: 100% must return expected status codes and messages.
- Multi-tenant isolation: 0 cross-tenant data leaks in 200+ attempts.

## 1. Authentication and Access Control

- Standard login
- MFA verification (if enabled)
- Face verification (admin and campus admin)
- Password reset flows

## 2. Governance and Permissions

- Campus SSG setup
- Governance member assignment
- Permission enforcement for SG/ORG
- Governance student access scoping

## 3. Events and Attendance

- Event creation
- Event time status
- Attendance window decisions

## 4. Import Center

- Bulk student import preview

## 5. System Health

- `/health` response and DB connectivity

## 6. Logging

- Confirm PSV logs are created under `cmpj/`.

