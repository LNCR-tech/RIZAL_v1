"""Use: Handles subscription and billing state API endpoints.
Where to use: Use this through the FastAPI app when the frontend or an API client needs subscription and billing state features.
Role: Router layer. It receives HTTP requests, checks access rules, and returns API responses.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.timezones import utc_now
from app.core.security import (
    get_current_admin_or_campus_admin,
    get_role_lookup_names,
    has_any_role,
)
from app.core.dependencies import get_db
from app.models.event import Event
from app.models.import_job import BulkImportJob
from app.models.platform_features import SchoolSubscriptionReminder, SchoolSubscriptionSetting
from app.models.role import Role
from app.models.school import School
from app.models.user import User, UserRole
from app.schemas.subscription import (
    ReminderRunResult,
    SchoolSubscriptionResponse,
    SchoolSubscriptionUpdate,
    SubscriptionUsageMetrics,
)
from app.services.notification_center_service import send_notification_to_user

router = APIRouter(prefix="/api/subscription", tags=["subscription"])


def _resolve_school_id(current_user: User, requested_school_id: int | None = None) -> int:
    actor_school_id = getattr(current_user, "school_id", None)
    is_platform_admin = has_any_role(current_user, ["admin"]) and actor_school_id is None
    if is_platform_admin:
        if requested_school_id is None:
            raise HTTPException(status_code=400, detail="school_id is required for platform admin")
        return requested_school_id
    if actor_school_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a school")
    return actor_school_id


def _get_or_create_subscription_setting(db: Session, school_id: int) -> SchoolSubscriptionSetting:
    setting = (
        db.query(SchoolSubscriptionSetting)
        .filter(SchoolSubscriptionSetting.school_id == school_id)
        .first()
    )
    if setting:
        return setting

    school = db.query(School).filter(School.id == school_id).first()
    if school is None:
        raise HTTPException(status_code=404, detail="School not found")

    setting = SchoolSubscriptionSetting(
        school_id=school_id,
        plan_name=getattr(school, "subscription_plan", "free") or "free",
        renewal_date=getattr(school, "subscription_end", None),
    )
    db.add(setting)
    db.flush()
    return setting


def _month_window(reference: datetime | None = None) -> tuple[datetime, datetime]:
    now = reference or utc_now()
    month_start = datetime(now.year, now.month, 1)
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)
    return month_start, next_month


def _build_metrics(db: Session, *, school_id: int, setting: SchoolSubscriptionSetting) -> SubscriptionUsageMetrics:
    month_start, next_month = _month_window()
    user_count = (
        db.query(func.count(User.id))
        .filter(User.school_id == school_id)
        .scalar()
        or 0
    )
    event_count_current_month = (
        db.query(func.count(Event.id))
        .filter(
            Event.school_id == school_id,
            Event.start_datetime >= month_start,
            Event.start_datetime < next_month,
        )
        .scalar()
        or 0
    )
    import_count_current_month = (
        db.query(func.count(BulkImportJob.id))
        .filter(
            BulkImportJob.target_school_id == school_id,
            BulkImportJob.created_at >= month_start,
            BulkImportJob.created_at < next_month,
        )
        .scalar()
        or 0
    )

    def pct(value: int, limit: int) -> float:
        if limit <= 0:
            return 0.0
        return round((value / limit) * 100, 2)

    return SubscriptionUsageMetrics(
        user_count=int(user_count),
        event_count_current_month=int(event_count_current_month),
        import_count_current_month=int(import_count_current_month),
        user_limit=setting.user_limit,
        event_limit_monthly=setting.event_limit_monthly,
        import_limit_monthly=setting.import_limit_monthly,
        user_usage_percent=pct(int(user_count), int(setting.user_limit)),
        event_usage_percent=pct(int(event_count_current_month), int(setting.event_limit_monthly)),
        import_usage_percent=pct(int(import_count_current_month), int(setting.import_limit_monthly)),
    )


@router.get("/me", response_model=SchoolSubscriptionResponse)
def get_school_subscription(
    school_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_admin_or_campus_admin),
    db: Session = Depends(get_db),
):
    scoped_school_id = _resolve_school_id(current_user, school_id)

    setting = _get_or_create_subscription_setting(db, scoped_school_id)
    db.commit()
    db.refresh(setting)
    metrics = _build_metrics(db, school_id=scoped_school_id, setting=setting)

    return SchoolSubscriptionResponse(
        school_id=setting.school_id,
        plan_name=setting.plan_name,
        user_limit=setting.user_limit,
        event_limit_monthly=setting.event_limit_monthly,
        import_limit_monthly=setting.import_limit_monthly,
        renewal_date=setting.renewal_date,
        auto_renew=setting.auto_renew,
        reminder_days_before=setting.reminder_days_before,
        updated_at=setting.updated_at,
        metrics=metrics,
    )


@router.put("/me", response_model=SchoolSubscriptionResponse)
def update_school_subscription(
    payload: SchoolSubscriptionUpdate,
    school_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_admin_or_campus_admin),
    db: Session = Depends(get_db),
):
    scoped_school_id = _resolve_school_id(current_user, school_id)

    setting = _get_or_create_subscription_setting(db, scoped_school_id)

    for field in [
        "plan_name",
        "user_limit",
        "event_limit_monthly",
        "import_limit_monthly",
        "renewal_date",
        "auto_renew",
        "reminder_days_before",
    ]:
        value = getattr(payload, field)
        if value is not None:
            setattr(setting, field, value)

    setting.updated_by_user_id = current_user.id
    db.commit()
    db.refresh(setting)
    metrics = _build_metrics(db, school_id=scoped_school_id, setting=setting)

    return SchoolSubscriptionResponse(
        school_id=setting.school_id,
        plan_name=setting.plan_name,
        user_limit=setting.user_limit,
        event_limit_monthly=setting.event_limit_monthly,
        import_limit_monthly=setting.import_limit_monthly,
        renewal_date=setting.renewal_date,
        auto_renew=setting.auto_renew,
        reminder_days_before=setting.reminder_days_before,
        updated_at=setting.updated_at,
        metrics=metrics,
    )


@router.post("/run-reminders", response_model=ReminderRunResult)
def run_subscription_reminders(
    school_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_admin_or_campus_admin),
    db: Session = Depends(get_db),
):
    actor_school_id = getattr(current_user, "school_id", None)
    is_platform_admin = has_any_role(current_user, ["admin"]) and actor_school_id is None

    if is_platform_admin and school_id is None:
        settings_rows = db.query(SchoolSubscriptionSetting).all()
    else:
        scoped_school_id = _resolve_school_id(current_user, school_id)
        settings_rows = (
            db.query(SchoolSubscriptionSetting)
            .filter(SchoolSubscriptionSetting.school_id == scoped_school_id)
            .all()
        )

    schools_checked = 0
    reminders_created = 0
    reminders_sent = 0
    reminders_failed = 0
    today = date.today()

    for setting in settings_rows:
        schools_checked += 1
        if setting.renewal_date is None:
            continue

        days_until_renewal = (setting.renewal_date - today).days
        if days_until_renewal < 0 or days_until_renewal > setting.reminder_days_before:
            continue

        recent_existing = (
            db.query(SchoolSubscriptionReminder)
            .filter(
                SchoolSubscriptionReminder.school_id == setting.school_id,
                SchoolSubscriptionReminder.reminder_type == "renewal_warning",
                SchoolSubscriptionReminder.created_at >= utc_now() - timedelta(hours=24),
            )
            .first()
        )
        if recent_existing:
            continue

        reminder = SchoolSubscriptionReminder(
            school_id=setting.school_id,
            reminder_type="renewal_warning",
            due_at=utc_now(),
            status="pending",
        )
        db.add(reminder)
        db.flush()
        reminders_created += 1

        recipients = (
            db.query(User)
            .join(User.roles)
            .join(UserRole.role)
            .filter(
                User.school_id == setting.school_id,
                User.is_active.is_(True),
                Role.name.in_(("admin", *get_role_lookup_names("campus_admin"))),
            )
            .options(joinedload(User.roles).joinedload(UserRole.role))
            .all()
        )
        subject = "Subscription Renewal Reminder"
        message = (
            f"Your school subscription renewal date is {setting.renewal_date.isoformat()} "
            f"({days_until_renewal} day(s) remaining)."
        )
        sent_for_school = False
        failed_for_school = False
        for user in recipients:
            status_value = send_notification_to_user(
                db,
                user=user,
                school_id=setting.school_id,
                category="subscription_renewal",
                subject=subject,
                message=message,
                metadata_json={
                    "renewal_date": setting.renewal_date.isoformat(),
                    "days_until_renewal": days_until_renewal,
                },
            )
            if status_value == "sent":
                sent_for_school = True
            elif status_value == "failed":
                failed_for_school = True

        if sent_for_school:
            reminder.status = "sent"
            reminder.sent_at = utc_now()
            reminders_sent += 1
        elif failed_for_school:
            reminder.status = "failed"
            reminder.error_message = "All notifications failed for target recipients."
            reminders_failed += 1
        else:
            reminder.status = "pending"

    db.commit()
    return ReminderRunResult(
        schools_checked=schools_checked,
        reminders_created=reminders_created,
        reminders_sent=reminders_sent,
        reminders_failed=reminders_failed,
    )

