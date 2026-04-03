# Notification System Refactor Guide

## Purpose

This document describes the refactoring applied to the backend notification system to improve control, reduce unnecessary notifications, and introduce role-based filtering.

---

## Overview

The notification system was updated to:

* prevent unnecessary notifications (e.g., login spam)
* enforce role-based notification delivery
* improve overall flow and maintainability

---

## Role-Based Notification Filtering

A filtering function was introduced:

```python
is_notification_allowed(user, category)
```

### Behavior

* **Students** only receive:

  * `event_reminder`
  * `attendance`
  * `missed_events`
  * `low_attendance`

* **Admins**:

  * allowed to receive all notification categories

* Other roles:

  * notifications are skipped by default

---

## Notification Flow Update

The main notification function:

```python
send_notification_to_user(...)
```

Now includes an early exit condition:

```python
if not is_notification_allowed(user, category):
    return "skipped"
```

### Effect

* prevents unnecessary processing
* avoids sending irrelevant notifications
* improves system efficiency

---

## Account Security Notification Control

The function:

```python
send_account_security_notification(...)
```

was updated to only send notifications when:

* user preference allows it
* the event is marked as suspicious

```python
if not metadata_json or not metadata_json.get("suspicious"):
    return "skipped"
```

---

## Notification Channels

The system maintains support for:

* in-app notifications
* email notifications
* SMS notifications (placeholder)

Each channel logs its result using:

```python
create_notification_log(...)
```

---

## Logging Behavior

All notifications are logged with:

* status: `sent`, `failed`, or `skipped`
* channel: `email`, `sms`, `in_app`, or `none`

This ensures traceability and debugging support.

---

## No Changes Applied To

The following components were intentionally not modified:

* `email_service/` (email delivery system)
* `alembic/` and `migrations/` (database history)
* `config.py` (core configuration)

---

## Summary

The notification system is now:

* more controlled
* role-aware
* less prone to spam
* easier to maintain

---

## Author

Backend Developer – Notification Refactor
