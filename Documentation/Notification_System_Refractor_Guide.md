Notification System Refactor Guide

Purpose
This document describes the refactoring applied to the backend notification system to improve control, reduce unnecessary notifications, and introduce role-based filtering.

Overview
• Prevent unnecessary notifications (e.g., login spam)
• Enforce role-based notification delivery
• Improve overall flow and maintainability

Role-Based Notification Filtering
A filtering function was introduced: is_notification_allowed(user, category)

Behavior
• Students only receive: event_reminder, attendance, missed_events, low_attendance
• Admins are allowed to receive all notification categories
• Other roles are skipped by default

Notification Flow Update
The main notification function send_notification_to_user(...) now includes an early exit condition to skip disallowed notifications.

Effect
• Prevents unnecessary processing
• Avoids sending irrelevant notifications
• Improves system efficiency

Account Security Notification Control
The function send_account_security_notification(...) now sends notifications only when user
preferences allow it and the event is marked as suspicious.

Notification Channels
• In-app notifications
• Email notifications
• SMS notifications (placeholder)
Each channel logs its result using create_notification_log(...).

Logging Behavior
• Status: sent, failed, or skipped
• Channel: email, sms, in_app, or none
This ensures traceability and debugging support.

No Changes Applied To
• email_service/ (email delivery system)
• alembic/ and migrations/ (database history)
• config.py (core configuration)

Summary
• More controlled
• Role-aware
• Less prone to spam
• Easier to maintain

Author
Backend Developer – Notification Refactor