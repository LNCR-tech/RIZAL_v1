from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.event import Event
from app.models.platform_features import NotificationLog, UserNotificationPreference
from app.models.user import StudentProfile, User
from app.services.attendance_status import ATTENDED_STATUS_VALUES
from app.services.email_service import EmailDeliveryError, send_plain_email


def get_or_create_notification_preference(db: Session, *, user_id: int) -> UserNotificationPreference:
    pref = (
        db.query(UserNotificationPreference)
        .filter(UserNotificationPreference.user_id == user_id)
        .first()
    )
    if pref:
        return pref
    pref = UserNotificationPreference(user_id=user_id)
    db.add(pref)
    db.flush()
    return pref


def create_notification_log(
    db: Session,
    *,
    school_id: int | None,
    user_id: int | None,
    category: str,
    channel: str,
    status: str,
    subject: str,
    message: str,
    error_message: str | None = None,
    metadata_json: dict | None = None,
) -> NotificationLog:
    row = NotificationLog(
        school_id=school_id,
        user_id=user_id,
        category=category,
        channel=channel,
        status=status,
        subject=subject,
        message=message,
        error_message=error_message,
        metadata_json=metadata_json,
    )
    db.add(row)
    db.flush()
    return row


def _send_email_with_log(
    db: Session,
    *,
    recipient: User,
    school_id: int | None,
    category: str,
    subject: str,
    message: str,
    metadata_json: dict | None = None,
) -> str:
    try:
        send_plain_email(
            recipient_email=recipient.email,
            subject=subject,
            body=message,
        )
        create_notification_log(
            db,
            school_id=school_id,
            user_id=recipient.id,
            category=category,
            channel="email",
            status="sent",
            subject=subject,
            message=message,
            metadata_json=metadata_json,
        )
        return "sent"
    except EmailDeliveryError as exc:
        create_notification_log(
            db,
            school_id=school_id,
            user_id=recipient.id,
            category=category,
            channel="email",
            status="failed",
            subject=subject,
            message=message,
            error_message=str(exc),
            metadata_json=metadata_json,
        )
        return "failed"


def _send_sms_with_log(
    db: Session,
    *,
    recipient: User,
    school_id: int | None,
    category: str,
    subject: str,
    message: str,
    sms_number: str | None,
    metadata_json: dict | None = None,
) -> str:
    if not sms_number:
        create_notification_log(
            db,
            school_id=school_id,
            user_id=recipient.id,
            category=category,
            channel="sms",
            status="skipped",
            subject=subject,
            message=message,
            error_message="No SMS number configured",
            metadata_json=metadata_json,
        )
        return "skipped"

    # Placeholder SMS integration.
    create_notification_log(
        db,
        school_id=school_id,
        user_id=recipient.id,
        category=category,
        channel="sms",
        status="failed",
        subject=subject,
        message=message,
        error_message="SMS provider not configured",
        metadata_json=metadata_json,
    )
    return "failed"


def send_notification_to_user(
    db: Session,
    *,
    user: User,
    school_id: int | None,
    category: str,
    subject: str,
    message: str,
    metadata_json: dict | None = None,
) -> str:
    pref = get_or_create_notification_preference(db, user_id=user.id)
    status_values: list[str] = []

    if pref.email_enabled:
        status_values.append(
            _send_email_with_log(
                db,
                recipient=user,
                school_id=school_id,
                category=category,
                subject=subject,
                message=message,
                metadata_json=metadata_json,
            )
        )
    if pref.sms_enabled:
        status_values.append(
            _send_sms_with_log(
                db,
                recipient=user,
                school_id=school_id,
                category=category,
                subject=subject,
                message=message,
                sms_number=pref.sms_number,
                metadata_json=metadata_json,
            )
        )

    if not status_values:
        create_notification_log(
            db,
            school_id=school_id,
            user_id=user.id,
            category=category,
            channel="none",
            status="skipped",
            subject=subject,
            message=message,
            error_message="All channels disabled for user",
            metadata_json=metadata_json,
        )
        return "skipped"

    if "sent" in status_values:
        return "sent"
    if "failed" in status_values:
        return "failed"
    return "skipped"


def send_account_security_notification(
    db: Session,
    *,
    user: User,
    subject: str,
    message: str,
    metadata_json: dict | None = None,
) -> str:
    pref = get_or_create_notification_preference(db, user_id=user.id)
    if not pref.notify_account_security:
        create_notification_log(
            db,
            school_id=getattr(user, "school_id", None),
            user_id=user.id,
            category="account_security",
            channel="none",
            status="skipped",
            subject=subject,
            message=message,
            error_message="User disabled account security notifications",
            metadata_json=metadata_json,
        )
        return "skipped"

    return send_notification_to_user(
        db,
        user=user,
        school_id=getattr(user, "school_id", None),
        category="account_security",
        subject=subject,
        message=message,
        metadata_json=metadata_json,
    )


def _summarize_statuses(statuses: Iterable[str]) -> tuple[int, int, int]:
    sent = 0
    failed = 0
    skipped = 0
    for item in statuses:
        if item == "sent":
            sent += 1
        elif item == "failed":
            failed += 1
        else:
            skipped += 1
    return sent, failed, skipped


def dispatch_missed_event_notifications(
    db: Session,
    *,
    school_id: int,
    lookback_days: int = 14,
) -> dict[str, int]:
    cutoff = datetime.utcnow() - timedelta(days=max(1, lookback_days))

    rows = (
        db.query(
            User,
            func.count(Attendance.id).label("absent_count"),
        )
        .join(StudentProfile, StudentProfile.user_id == User.id)
        .join(Attendance, Attendance.student_id == StudentProfile.id)
        .join(Event, Event.id == Attendance.event_id)
        .filter(
            User.school_id == school_id,
            Event.school_id == school_id,
            Attendance.status == "absent",
            Event.end_datetime >= cutoff,
        )
        .group_by(User.id)
        .all()
    )

    statuses: list[str] = []
    processed = 0
    for user, absent_count in rows:
        processed += 1
        pref = get_or_create_notification_preference(db, user_id=user.id)
        if not pref.notify_missed_events:
            statuses.append("skipped")
            continue

        subject = "Attendance Alert: Missed Events Detected"
        message = (
            f"Hi {user.first_name or 'Student'},\n\n"
            f"Our records show {absent_count} missed event(s) in the last {lookback_days} days.\n"
            "Please coordinate with your school office if this is incorrect.\n\n"
            "Valid8 Attendance System"
        )
        statuses.append(
            send_notification_to_user(
                db,
                user=user,
                school_id=school_id,
                category="missed_events",
                subject=subject,
                message=message,
                metadata_json={"absent_count": int(absent_count), "lookback_days": lookback_days},
            )
        )

    sent, failed, skipped = _summarize_statuses(statuses)
    return {
        "processed_users": processed,
        "sent": sent,
        "failed": failed,
        "skipped": skipped,
    }


def dispatch_low_attendance_notifications(
    db: Session,
    *,
    school_id: int,
    threshold_percent: float = 75.0,
    min_records: int = 3,
) -> dict[str, int]:
    attended_case = case((Attendance.status.in_(ATTENDED_STATUS_VALUES), 1), else_=0)
    rows = (
        db.query(
            User,
            func.count(Attendance.id).label("total_count"),
            func.sum(attended_case).label("attended_count"),
        )
        .join(StudentProfile, StudentProfile.user_id == User.id)
        .join(Attendance, Attendance.student_id == StudentProfile.id)
        .join(Event, Event.id == Attendance.event_id)
        .filter(User.school_id == school_id, Event.school_id == school_id)
        .group_by(User.id)
        .having(func.count(Attendance.id) >= max(1, min_records))
        .all()
    )

    statuses: list[str] = []
    processed = 0

    for user, total_count, attended_count in rows:
        total = int(total_count or 0)
        attended = int(attended_count or 0)
        if total <= 0:
            continue
        attendance_percent = (attended / total) * 100
        if attendance_percent >= threshold_percent:
            continue

        processed += 1
        pref = get_or_create_notification_preference(db, user_id=user.id)
        if not pref.notify_low_attendance:
            statuses.append("skipped")
            continue

        subject = "Attendance Alert: Low Attendance Rate"
        message = (
            f"Hi {user.first_name or 'Student'},\n\n"
            f"Your attendance rate is currently {attendance_percent:.1f}% "
            f"({attended}/{total}) which is below the threshold of {threshold_percent:.1f}%.\n"
            "Please review your recent attendance records.\n\n"
            "Valid8 Attendance System"
        )
        statuses.append(
            send_notification_to_user(
                db,
                user=user,
                school_id=school_id,
                category="low_attendance",
                subject=subject,
                message=message,
                metadata_json={
                    "total_count": total,
                    "attended_count": attended,
                    "threshold_percent": threshold_percent,
                    "attendance_percent": round(attendance_percent, 2),
                },
            )
        )

    sent, failed, skipped = _summarize_statuses(statuses)
    return {
        "processed_users": processed,
        "sent": sent,
        "failed": failed,
        "skipped": skipped,
    }
