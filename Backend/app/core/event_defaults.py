from __future__ import annotations

from typing import Any


DEFAULT_EVENT_EARLY_CHECK_IN_MINUTES = 30
DEFAULT_EVENT_LATE_THRESHOLD_MINUTES = 10
DEFAULT_EVENT_SIGN_OUT_GRACE_MINUTES = 20


def resolve_school_event_default_values(
    school_settings: Any | None,
) -> tuple[int, int, int]:
    return (
        int(
            getattr(
                school_settings,
                "event_default_early_check_in_minutes",
                DEFAULT_EVENT_EARLY_CHECK_IN_MINUTES,
            )
            if school_settings is not None
            else DEFAULT_EVENT_EARLY_CHECK_IN_MINUTES
        ),
        int(
            getattr(
                school_settings,
                "event_default_late_threshold_minutes",
                DEFAULT_EVENT_LATE_THRESHOLD_MINUTES,
            )
            if school_settings is not None
            else DEFAULT_EVENT_LATE_THRESHOLD_MINUTES
        ),
        int(
            getattr(
                school_settings,
                "event_default_sign_out_grace_minutes",
                DEFAULT_EVENT_SIGN_OUT_GRACE_MINUTES,
            )
            if school_settings is not None
            else DEFAULT_EVENT_SIGN_OUT_GRACE_MINUTES
        ),
    )


def resolve_governance_event_default_values(
    *,
    school_settings: Any | None,
    governance_unit: Any | None,
) -> tuple[int, int, int]:
    school_early, school_late, school_sign_out = resolve_school_event_default_values(
        school_settings
    )
    if governance_unit is None:
        return school_early, school_late, school_sign_out

    return (
        int(
            getattr(
                governance_unit,
                "event_default_early_check_in_minutes",
                school_early,
            )
            if getattr(governance_unit, "event_default_early_check_in_minutes", None)
            is not None
            else school_early
        ),
        int(
            getattr(
                governance_unit,
                "event_default_late_threshold_minutes",
                school_late,
            )
            if getattr(governance_unit, "event_default_late_threshold_minutes", None)
            is not None
            else school_late
        ),
        int(
            getattr(
                governance_unit,
                "event_default_sign_out_grace_minutes",
                school_sign_out,
            )
            if getattr(governance_unit, "event_default_sign_out_grace_minutes", None)
            is not None
            else school_sign_out
        ),
    )


def build_event_default_value_map(
    *,
    early_check_in_minutes: int,
    late_threshold_minutes: int,
    sign_out_grace_minutes: int,
) -> dict[str, int]:
    return {
        "early_check_in_minutes": int(early_check_in_minutes),
        "late_threshold_minutes": int(late_threshold_minutes),
        "sign_out_grace_minutes": int(sign_out_grace_minutes),
    }
