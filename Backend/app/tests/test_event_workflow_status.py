from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from app.models.event import EventStatus as ModelEventStatus
from app.services.event_workflow_status import (
    map_time_status_to_workflow_status,
    summarize_event_workflow_status_sync,
    EventWorkflowStatusSyncResult,
    sync_event_workflow_status,
)


def _build_event(status: ModelEventStatus) -> SimpleNamespace:
    return SimpleNamespace(
        status=status,
        start_datetime=datetime(2026, 3, 11, 9, 0, 0),
        end_datetime=datetime(2026, 3, 11, 11, 0, 0),
        late_threshold_minutes=10,
    )


def test_map_time_status_to_workflow_status_matches_event_lifecycle() -> None:
    assert map_time_status_to_workflow_status("upcoming") == ModelEventStatus.UPCOMING
    assert map_time_status_to_workflow_status("open") == ModelEventStatus.ONGOING
    assert map_time_status_to_workflow_status("late") == ModelEventStatus.ONGOING
    assert map_time_status_to_workflow_status("closed") == ModelEventStatus.COMPLETED


def test_sync_event_workflow_status_moves_upcoming_event_to_ongoing() -> None:
    manila = ZoneInfo("Asia/Manila")
    event = _build_event(ModelEventStatus.UPCOMING)

    result = sync_event_workflow_status(
        None,
        event,
        current_time=datetime(2026, 3, 11, 9, 5, 0, tzinfo=manila),
        completion_finalizer=lambda _db, _event: {"created_absent": 0, "marked_absent_no_timeout": 0},
    )

    assert result.changed is True
    assert result.previous_status == ModelEventStatus.UPCOMING
    assert result.current_status == ModelEventStatus.ONGOING
    assert event.status == ModelEventStatus.ONGOING
    assert result.attendance_finalized is False


def test_sync_event_workflow_status_completes_event_and_finalizes_attendance() -> None:
    manila = ZoneInfo("Asia/Manila")
    event = _build_event(ModelEventStatus.ONGOING)
    finalizer_calls: list[tuple[object, object]] = []

    def finalizer(db, event_obj):
        finalizer_calls.append((db, event_obj))
        return {"created_absent": 3, "marked_absent_no_timeout": 1}

    result = sync_event_workflow_status(
        None,
        event,
        current_time=datetime(2026, 3, 11, 11, 30, 0, tzinfo=manila),
        completion_finalizer=finalizer,
    )

    assert result.changed is True
    assert result.current_status == ModelEventStatus.COMPLETED
    assert event.status == ModelEventStatus.COMPLETED
    assert result.attendance_finalized is True
    assert result.finalization_summary == {"created_absent": 3, "marked_absent_no_timeout": 1}
    assert finalizer_calls == [(None, event)]


def test_sync_event_workflow_status_keeps_cancelled_event_terminal() -> None:
    manila = ZoneInfo("Asia/Manila")
    event = _build_event(ModelEventStatus.CANCELLED)

    result = sync_event_workflow_status(
        None,
        event,
        current_time=datetime(2026, 3, 11, 10, 0, 0, tzinfo=manila),
        completion_finalizer=lambda _db, _event: {"created_absent": 99, "marked_absent_no_timeout": 99},
    )

    assert result.changed is False
    assert result.current_status == ModelEventStatus.CANCELLED
    assert event.status == ModelEventStatus.CANCELLED
    assert result.attendance_finalized is False


def test_sync_event_workflow_status_keeps_completed_event_sticky_before_end() -> None:
    manila = ZoneInfo("Asia/Manila")
    event = _build_event(ModelEventStatus.COMPLETED)

    result = sync_event_workflow_status(
        None,
        event,
        current_time=datetime(2026, 3, 11, 9, 1, 0, tzinfo=manila),
        completion_finalizer=lambda _db, _event: {"created_absent": 0, "marked_absent_no_timeout": 0},
    )

    assert result.changed is False
    assert result.current_status == ModelEventStatus.COMPLETED
    assert event.status == ModelEventStatus.COMPLETED
    assert result.attendance_finalized is False


def test_summarize_event_workflow_status_sync_counts_changes_and_finalization() -> None:
    summary = summarize_event_workflow_status_sync(
        [
            EventWorkflowStatusSyncResult(
                changed=True,
                previous_status=ModelEventStatus.UPCOMING,
                current_status=ModelEventStatus.ONGOING,
                computed_time_status="open",
                attendance_finalized=False,
            ),
            EventWorkflowStatusSyncResult(
                changed=True,
                previous_status=ModelEventStatus.ONGOING,
                current_status=ModelEventStatus.COMPLETED,
                computed_time_status="closed",
                attendance_finalized=True,
                finalization_summary={
                    "created_absent": 4,
                    "marked_absent_no_timeout": 2,
                },
            ),
            EventWorkflowStatusSyncResult(
                changed=False,
                previous_status=ModelEventStatus.CANCELLED,
                current_status=ModelEventStatus.CANCELLED,
                computed_time_status="late",
                attendance_finalized=False,
            ),
        ]
    )

    assert summary.scanned_events == 3
    assert summary.changed_events == 2
    assert summary.moved_to_upcoming == 0
    assert summary.moved_to_ongoing == 1
    assert summary.moved_to_completed == 1
    assert summary.attendance_finalized_events == 1
    assert summary.absent_records_created == 4
    assert summary.absent_no_timeout_marked == 2
