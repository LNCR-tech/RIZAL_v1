from unittest.mock import AsyncMock, patch

import pytest

from lib.deterministic_answers import build_data_answer, detect_data_intent
from lib.deterministic_charts import build_attendance_chart, detect_chart_intent


def test_data_intent_detection_routes_common_questions_to_deterministic_answers():
    # This protects common data questions from unnecessarily falling through to the LLM.
    assert detect_data_intent("What upcoming events do I have?") == "upcoming_events"
    assert detect_data_intent("Show my attendance") == "my_attendance"
    assert detect_data_intent("Did I miss any events?") == "my_absences"
    assert detect_data_intent("Tell me a joke") is None


@pytest.mark.asyncio
async def test_data_answer_lists_upcoming_events_from_backend_data():
    # This protects event-list answers from depending on real AI output.
    with patch(
        "lib.deterministic_answers.request_backend",
        new=AsyncMock(
            return_value={
                "ok": True,
                "data": [
                    {
                        "name": "Leadership Summit",
                        "status": "upcoming",
                        "start_datetime": "2026-06-01T09:00:00Z",
                        "location": "Main Hall",
                    },
                    {
                        "name": "Completed Assembly",
                        "status": "completed",
                        "start_datetime": "2026-05-01T09:00:00Z",
                    },
                ],
            },
        ),
    ) as request_backend:
        answer = await build_data_answer(
            "List upcoming events",
            "Bearer token",
            ["student"],
        )

    assert answer.startswith("Upcoming events:")
    assert "Leadership Summit" in answer
    assert "Completed Assembly" not in answer
    request_backend.assert_awaited_once_with("GET", "/api/events/", "Bearer token")


@pytest.mark.asyncio
async def test_data_answer_reports_student_absences_from_attendance_report():
    # This protects student-scoped absence answers and their backend request sequence.
    async def fake_backend(method, path, authorization):
        if path == "/api/users/me/":
            return {"ok": True, "data": {"student_profile": {"id": 44}}}
        if path == "/api/attendance/students/44/report":
            return {
                "ok": True,
                "data": {
                    "student": {"absent_events": 1},
                    "attendance_records": [
                        {
                            "event_name": "Foundation Day",
                            "event_date": "2026-05-20T08:00:00Z",
                            "display_status": "absent",
                        },
                        {
                            "event_name": "Orientation",
                            "display_status": "present",
                        },
                    ],
                },
            }
        raise AssertionError(f"Unexpected backend path: {path}")

    with patch("lib.deterministic_answers.request_backend", new=AsyncMock(side_effect=fake_backend)):
        answer = await build_data_answer("What events was I absent from?", "Bearer token", ["student"])

    assert "Events you were absent from (1):" in answer
    assert "Foundation Day" in answer
    assert "Orientation" not in answer


@pytest.mark.asyncio
async def test_data_answer_refuses_student_attendance_questions_for_non_students():
    # This protects role boundaries so admin/campus-admin users do not receive student-only attendance summaries.
    with patch("lib.deterministic_answers.request_backend", new=AsyncMock()) as request_backend:
        answer = await build_data_answer("Show my attendance", "Bearer token", ["campus_admin"])

    assert answer is None
    request_backend.assert_not_awaited()


def test_chart_intent_detection_requires_chart_and_data_context():
    # This protects the chart detector from hijacking generic chart-explanation questions.
    assert detect_chart_intent("show a pie chart of my attendance") == {
        "metric": "attendance_status",
        "shape": "pie",
    }
    assert detect_chart_intent("plot attendance trend over time") == {
        "metric": "attendance_trend",
        "shape": "line",
    }
    assert detect_chart_intent("what is a pie chart?") is None


@pytest.mark.asyncio
async def test_attendance_chart_builds_visual_payload_from_student_report():
    # This protects the assistant chart contract consumed by the frontend/mobile renderer.
    async def fake_backend(method, path, authorization):
        if path == "/api/users/me/":
            return {"ok": True, "data": {"student_profile_id": 44}}
        if path == "/api/attendance/students/44/report":
            return {
                "ok": True,
                "data": {
                    "student": {
                        "attended_events": 3,
                        "late_events": 1,
                        "absent_events": 2,
                        "attendance_rate": 67.2,
                    }
                },
            }
        raise AssertionError(f"Unexpected backend path: {path}")

    with patch("lib.deterministic_charts.request_backend", new=AsyncMock(side_effect=fake_backend)):
        chart = await build_attendance_chart(
            {"metric": "attendance_status", "shape": "bar"},
            "Bearer token",
        )

    assert chart["caption"] == "Here's your attendance breakdown."
    assert chart["visual"]["__aura_visual__"] is True
    assert chart["visual"]["type"] == "bar"
    assert chart["visual"]["payload"]["labels"] == ["Present", "Late", "Absent"]
    assert chart["visual"]["payload"]["datasets"][0]["data"] == [3, 1, 2]
    assert chart["visual"]["footer"] == "Attendance rate: 67%."


@pytest.mark.asyncio
async def test_attendance_chart_falls_back_to_raw_attendance_records():
    # This protects chart generation when the backend cannot resolve a student profile id.
    async def fake_backend(method, path, authorization):
        if path == "/api/users/me/":
            return {"ok": True, "data": {}}
        if path == "/api/attendance/students/me":
            return {
                "ok": True,
                "data": [
                    {"status": "present"},
                    {"status": "late"},
                    {"status": "late"},
                ],
            }
        raise AssertionError(f"Unexpected backend path: {path}")

    with patch("lib.deterministic_charts.request_backend", new=AsyncMock(side_effect=fake_backend)):
        chart = await build_attendance_chart(
            {"metric": "attendance_status", "shape": "pie"},
            "Bearer token",
        )

    assert chart["visual"]["type"] == "pie"
    assert chart["visual"]["payload"]["labels"] == ["Present", "Late"]
    assert chart["visual"]["payload"]["datasets"][0]["data"] == [1, 2]
