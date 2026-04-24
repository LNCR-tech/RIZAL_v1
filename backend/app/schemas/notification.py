"""Use: Defines request and response data shapes for notification API data.
Where to use: Use this in routers and services when validating or returning notification API data.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class NotificationPreferenceResponse(BaseModel):
    user_id: int
    email_enabled: bool
    sms_enabled: bool
    sms_number: Optional[str] = None
    notify_missed_events: bool
    notify_low_attendance: bool
    notify_account_security: bool
    notify_subscription: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationPreferenceUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    sms_number: Optional[str] = Field(default=None, max_length=40)
    notify_missed_events: Optional[bool] = None
    notify_low_attendance: Optional[bool] = None
    notify_account_security: Optional[bool] = None
    notify_subscription: Optional[bool] = None


class NotificationLogItem(BaseModel):
    id: int
    school_id: Optional[int] = None
    user_id: Optional[int] = None
    category: str
    channel: str
    status: str
    subject: str
    message: str
    error_message: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationTestRequest(BaseModel):
    channel: str = Field(default="email", pattern="^(email|sms)$")
    message: Optional[str] = Field(default=None, max_length=1000)


class NotificationDispatchSummary(BaseModel):
    processed_users: int
    sent: int
    failed: int
    skipped: int
    category: str


class SecurityNotificationRequest(BaseModel):
    user_id: int
    subject: str = Field(min_length=3, max_length=255)
    message: str = Field(min_length=3, max_length=5000)
