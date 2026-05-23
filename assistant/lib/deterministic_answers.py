"""Deterministic data answers (COEDIGO-style) — no LLM.

Detects common data questions, fetches REAL data from the backend with the user's
token (the backend already role-scopes it), and formats a short reply. Returns None
to fall back to the LLM. Nothing is hardcoded.

Role-aware: event lists work for any role (the backend returns only what the caller
may see). "My attendance / absences" are student-scoped.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, List, Optional

from .auth import request_backend

_EVENT_RE = re.compile(r"\bevents?\b", re.I)
_UPCOMING_RE = re.compile(r"\b(upcoming|next|future|coming up|scheduled)\b", re.I)
_ONGOING_RE = re.compile(r"\b(ongoing|happening|right now|currently|live|today'?s?)\b", re.I)
_LISTY_RE = re.compile(r"\b(list|what|which|show|all|any|my)\b", re.I)
_ABSENT_RE = re.compile(r"\b(absent|absence|absences|missed|did i miss)\b", re.I)
_ATTEND_RE = re.compile(r"\b(attendance|present|attended)\b", re.I)


def detect_data_intent(message: Optional[str]) -> Optional[str]:
    low = (message or "").lower()
    if _ABSENT_RE.search(low):
        return "my_absences"
    if "my" in low and _ATTEND_RE.search(low):
        return "my_attendance"
    if _EVENT_RE.search(low):
        if _ONGOING_RE.search(low):
            return "ongoing_events"
        if _UPCOMING_RE.search(low):
            return "upcoming_events"
        if _LISTY_RE.search(low):
            return "list_events"
        return "list_events"
    return None


def _as_list(data: Any) -> List[dict]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict) and isinstance(data.get("data"), list):
        return [x for x in data["data"] if isinstance(x, dict)]
    return []


def _fmt_dt(s: Optional[str]) -> str:
    if not s:
        return ""
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).strftime("%b %d, %I:%M %p")
    except (ValueError, TypeError):
        return str(s)[:16]


def _event_line(e: dict) -> str:
    parts = ["• " + str(e.get("name") or "Untitled event")]
    when = _fmt_dt(e.get("start_datetime"))
    if when:
        parts.append(f"({when})")
    loc = e.get("location") or e.get("venue")
    if loc:
        parts.append(f"@ {loc}")
    return " ".join(parts)


def _sort_by_start(events: List[dict], newest_first: bool = False) -> List[dict]:
    return sorted(events, key=lambda e: str(e.get("start_datetime") or ""), reverse=newest_first)


async def _student_report(authorization: str) -> Optional[dict]:
    from .deterministic_charts import _resolve_profile_id
    pid = await _resolve_profile_id(authorization)
    if pid is None:
        return None
    r = await request_backend("GET", f"/api/attendance/students/{pid}/report", authorization)
    if r.get("ok") and isinstance(r.get("data"), dict):
        return r["data"]
    return None


async def build_data_answer(
    message: str, authorization: Optional[str], roles: Optional[List[str]]
) -> Optional[str]:
    if not authorization:
        return None
    intent = detect_data_intent(message)
    if not intent:
        return None
    roles_l = [str(r).lower() for r in (roles or [])]

    # --- Events (any role; the backend returns only what this user may see) ---
    if intent in ("upcoming_events", "ongoing_events", "list_events"):
        path = "/api/events/ongoing" if intent == "ongoing_events" else "/api/events/"
        r = await request_backend("GET", path, authorization)
        if not r.get("ok"):
            return None  # let the LLM respond if we can't reach the data
        events = _as_list(r.get("data"))
        if intent == "upcoming_events":
            events = _sort_by_start(
                [e for e in events if str(e.get("status", "")).lower() == "upcoming"]
            )[:10]
            title = "Upcoming events"
            empty = "You have no upcoming events."
        elif intent == "ongoing_events":
            events = events[:10]
            title = "Happening now"
            empty = "No events are happening right now."
        else:
            events = _sort_by_start(events, newest_first=True)[:10]
            title = "Events"
            empty = "There are no events to show."
        if not events:
            return empty
        return f"{title}:\n" + "\n".join(_event_line(e) for e in events)

    # --- Attendance / absences (student-scoped) ---
    if intent in ("my_absences", "my_attendance"):
        if "student" not in roles_l:
            return None  # let the LLM handle role context for non-students
        report = await _student_report(authorization)
        if report is None:
            return None
        student = report.get("student") or {}
        if intent == "my_absences":
            recs = report.get("attendance_records") or []
            absent = [
                r for r in recs
                if isinstance(r, dict)
                and "absent" in str(r.get("display_status") or r.get("status") or "").lower()
            ]
            if absent:
                lines = []
                for r in absent[:15]:
                    nm = r.get("event_name") or f"Event #{r.get('event_id', '?')}"
                    when = _fmt_dt(r.get("event_date"))
                    lines.append("• " + nm + (f" ({when})" if when else ""))
                return f"Events you were absent from ({len(absent)}):\n" + "\n".join(lines)
            n = int(student.get("absent_events", 0) or 0)
            if n > 0:
                return f"You've been marked absent from {n} event(s)."
            return "Good news — you have no recorded absences."
        # my_attendance
        return (
            "Your attendance so far: "
            f"{int(student.get('attended_events', 0) or 0)} present, "
            f"{int(student.get('late_events', 0) or 0)} late, "
            f"{int(student.get('absent_events', 0) or 0)} absent, "
            f"{int(student.get('excused_events', 0) or 0)} excused "
            f"— rate {round(float(student.get('attendance_rate', 0) or 0))}%."
        )
    return None
