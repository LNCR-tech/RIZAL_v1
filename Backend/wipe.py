"""Wipes ALL records from every application table. Schemas are preserved."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal


def wipe_all() -> None:
    from app.models.attendance import Attendance
    from app.models.event import Event
    from app.models.governance_hierarchy import (
        GovernanceAnnouncement,
        GovernanceMember,
        GovernanceMemberPermission,
        GovernancePermission,
        GovernanceStudentNote,
        GovernanceUnit,
        GovernanceUnitPermission,
    )
    from app.models.import_job import BulkImportError, BulkImportJob, EmailDeliveryLog
    from app.models.password_reset_request import PasswordResetRequest
    from app.models.platform_features import (
        DataGovernanceSetting,
        DataRequest,
        DataRetentionRunLog,
        LoginHistory,
        MfaChallenge,
        NotificationLog,
        SchoolSubscriptionReminder,
        SchoolSubscriptionSetting,
        UserAppPreference,
        UserFaceProfile,
        UserNotificationPreference,
        UserPrivacyConsent,
        UserSecuritySetting,
        UserSession,
    )
    from app.models.program import Program
    from app.models.department import Department
    from app.models.role import Role
    from app.models.sanctions import (
        ClearanceDeadline,
        EventSanctionConfig,
        SanctionItem,
        SanctionRecord,
    )
    from app.models.school import School, SchoolSetting
    from app.models.user import StudentProfile, User, UserRole

    db = SessionLocal()
    try:
        print("Wiping all database records...")

        # Leaf tables first (no dependents)
        db.query(Attendance).delete()
        db.query(SanctionItem).delete()
        db.query(SanctionRecord).delete()
        db.query(ClearanceDeadline).delete()
        db.query(EventSanctionConfig).delete()
        db.query(GovernanceStudentNote).delete()
        db.query(GovernanceAnnouncement).delete()
        db.query(GovernanceMemberPermission).delete()
        db.query(GovernanceMember).delete()
        db.query(GovernanceUnitPermission).delete()
        db.query(GovernancePermission).delete()
        db.query(GovernanceUnit).delete()
        db.query(BulkImportError).delete()
        db.query(EmailDeliveryLog).delete()
        db.query(BulkImportJob).delete()
        db.query(PasswordResetRequest).delete()
        db.query(LoginHistory).delete()
        db.query(UserSession).delete()
        db.query(MfaChallenge).delete()
        db.query(NotificationLog).delete()
        db.query(UserFaceProfile).delete()
        db.query(UserNotificationPreference).delete()
        db.query(UserAppPreference).delete()
        db.query(UserSecuritySetting).delete()
        db.query(UserPrivacyConsent).delete()
        db.query(DataRequest).delete()
        db.query(DataRetentionRunLog).delete()
        db.query(DataGovernanceSetting).delete()
        db.query(SchoolSubscriptionReminder).delete()
        db.query(SchoolSubscriptionSetting).delete()
        db.query(StudentProfile).delete()
        db.query(UserRole).delete()
        db.query(User).delete()
        db.query(Event).delete()
        db.query(Program).delete()
        db.query(Department).delete()
        db.query(SchoolSetting).delete()
        db.query(School).delete()
        db.query(Role).delete()

        db.commit()
        print("Done. All records wiped.")
    except Exception as exc:
        db.rollback()
        print(f"Wipe failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    confirm = input("This will DELETE ALL DATA. Type 'yes' to confirm: ").strip().lower()
    if confirm != "yes":
        print("Aborted.")
        sys.exit(0)
    wipe_all()
