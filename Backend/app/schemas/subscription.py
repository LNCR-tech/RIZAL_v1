"""Use: Defines request and response data shapes for subscription API data.
Where to use: Use this in routers and services when validating or returning subscription API data.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SubscriptionUsageMetrics(BaseModel):
    user_count: int
    event_count_current_month: int
    import_count_current_month: int
    user_limit: int
    event_limit_monthly: int
    import_limit_monthly: int
    user_usage_percent: float
    event_usage_percent: float
    import_usage_percent: float


class SchoolSubscriptionResponse(BaseModel):
    school_id: int
    plan_name: str
    user_limit: int
    event_limit_monthly: int
    import_limit_monthly: int
    renewal_date: Optional[date] = None
    auto_renew: bool
    reminder_days_before: int
    updated_at: datetime
    metrics: SubscriptionUsageMetrics

    model_config = ConfigDict(from_attributes=True)


class SchoolSubscriptionUpdate(BaseModel):
    plan_name: Optional[str] = Field(default=None, min_length=2, max_length=50)
    user_limit: Optional[int] = Field(default=None, ge=1, le=1000000)
    event_limit_monthly: Optional[int] = Field(default=None, ge=1, le=1000000)
    import_limit_monthly: Optional[int] = Field(default=None, ge=1, le=1000000)
    renewal_date: Optional[date] = None
    auto_renew: Optional[bool] = None
    reminder_days_before: Optional[int] = Field(default=None, ge=1, le=60)


class ReminderRunResult(BaseModel):
    schools_checked: int
    reminders_created: int
    reminders_sent: int
    reminders_failed: int
