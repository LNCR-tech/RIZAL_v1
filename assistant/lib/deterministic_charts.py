"""Deterministic chart generation (COEDIGO-style).

When the user asks for a chart, we detect it with regex, pull the data straight
from the backend API with their bearer token, and build a Chart.js-style spec the
Flutter app already renders (assistant_chart.dart). The LLM is never involved, so
this is fast and reliable even on a tiny local model.

Currently covers a STUDENT's attendance (status breakdown / trend / event types).
Returns None when it can't build one, so the caller falls back to the normal LLM.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, Optional

from .auth import request_backend

_CHART_RE = re.compile(r"\b(chart|graph|plot|visuali[sz]e|pie|bar|breakdown|trend)\b", re.I)
_ATTEND_RE = re.compile(r"\b(attendance|attend|present|absent|late|excused|miss(?:ed|ing)?)\b", re.I)
_EVENT_RE = re.compile(r"\bevents?\b", re.I)
_MINE_RE = re.compile(r"\b(my|me|mine)\b", re.I)
_TREND_RE = re.compile(r"\b(trend|over time|monthly|by month|history|timeline)\b", re.I)
_TYPE_RE = re.compile(r"\b(type|types|category|categories|kind)\b", re.I)


def detect_chart_intent(message: Optional[str]) -> Optional[Dict[str, str]]:
    """Return {'metric','shape'} for a chart request, else None."""
    m = message or ""
    if not _CHART_RE.search(m):
        return None
    # Require some data context so "what is a bar chart?" doesn't trigger it.
    if not (_ATTEND_RE.search(m) or _EVENT_RE.search(m) or _MINE_RE.search(m)):
        return None
    if _TREND_RE.search(m):
        return {"metric": "attendance_trend", "shape": "line"}
    if _EVENT_RE.search(m) and _TYPE_RE.search(m):
        return {"metric": "event_type", "shape": "doughnut"}
    if re.search(r"\bline\b", m, re.I):
        return {"metric": "attendance_trend", "shape": "line"}
    shape = "bar" if re.search(r"\bbar\b", m, re.I) else "pie"
    return {"metric": "attendance_status", "shape": shape}


def _visual(type_: str, title: str, labels, data, label: str = "", footer: str = "") -> Dict[str, Any]:
    return {
        "__aura_visual__": True,
        "type": type_,
        "title": title,
        "payload": {"labels": list(labels), "datasets": [{"label": label, "data": list(data)}]},
        "footer": footer,
    }


async def _resolve_profile_id(authorization: str) -> Optional[int]:
    r = await request_backend("GET", "/api/users/me/", authorization)
    if not r.get("ok") or not isinstance(r.get("data"), dict):
        return None
    d = r["data"]
    for key in ("student_profile", "studentProfile", "profile"):
        p = d.get(key)
        if isinstance(p, dict) and p.get("id") is not None:
            try:
                return int(p["id"])
            except (TypeError, ValueError):
                pass
    for key in ("student_profile_id", "studentProfileId", "profile_id"):
        if d.get(key) is not None:
            try:
                return int(d[key])
            except (TypeError, ValueError):
                pass
    return None


def _rate_footer(student: Dict[str, Any]) -> str:
    rate = student.get("attendance_rate")
    try:
        return f"Attendance rate: {round(float(rate))}%." if rate is not None else ""
    except (TypeError, ValueError):
        return ""


def _from_report(report: Dict[str, Any], intent: Dict[str, str]) -> Optional[Dict[str, Any]]:
    student = report.get("student") if isinstance(report.get("student"), dict) else {}
    metric = intent["metric"]

    if metric == "attendance_trend":
        monthly = report.get("monthly_stats")
        if not isinstance(monthly, dict) or not monthly:
            return None
        months = sorted(monthly.keys())
        data = []
        for mo in months:
            row = monthly.get(mo) or {}
            data.append(int(row.get("present", row.get("attended", row.get("total", 0))) or 0))
        if not any(data):
            return None
        return {"caption": "Here's your attendance over time.",
                "visual": _visual("line", "Attendance over time", months, data, "Present",
                                  _rate_footer(student))}

    if metric == "event_type":
        ets = report.get("event_type_stats")
        if not isinstance(ets, dict):
            return None
        items = [(str(k), int(v or 0)) for k, v in ets.items() if v]
        if not items:
            return None
        return {"caption": "Here are your events by type.",
                "visual": _visual("doughnut", "Events by type",
                                  [k for k, _ in items], [v for _, v in items])}

    # default: status breakdown
    pairs = [("Present", "attended_events"), ("Late", "late_events"),
             ("Absent", "absent_events"), ("Excused", "excused_events"),
             ("Incomplete", "incomplete_events")]
    labels, data = [], []
    for lab, key in pairs:
        v = int(student.get(key, 0) or 0)
        if v:
            labels.append(lab)
            data.append(v)
    if not data:
        return None
    shape = intent["shape"] if intent["shape"] in ("pie", "bar", "doughnut") else "pie"
    return {"caption": "Here's your attendance breakdown.",
            "visual": _visual(shape, "Attendance breakdown", labels, data, "Events",
                              _rate_footer(student))}


def _from_raw(records, intent: Dict[str, str]) -> Optional[Dict[str, Any]]:
    if not isinstance(records, list):
        return None
    counts: Counter = Counter()
    for rec in records:
        if isinstance(rec, dict):
            st = rec.get("effective_status") or rec.get("status") or "present"
            counts[str(st).title()] += 1
    if not counts:
        return None
    shape = intent["shape"] if intent["shape"] in ("pie", "bar", "doughnut") else "pie"
    return {"caption": "Here's your attendance breakdown.",
            "visual": _visual(shape, "Attendance breakdown",
                              list(counts.keys()), list(counts.values()), "Events")}


async def build_attendance_chart(intent: Dict[str, str], authorization: Optional[str]) -> Optional[Dict[str, Any]]:
    """Fetch data + return {'visual','caption'}, or None to fall back to the LLM."""
    if not authorization:
        return None
    pid = await _resolve_profile_id(authorization)
    if pid is not None:
        r = await request_backend("GET", f"/api/attendance/students/{pid}/report", authorization)
        if r.get("ok") and isinstance(r.get("data"), dict):
            built = _from_report(r["data"], intent)
            if built:
                return built
    # Fallback: raw attendance list (token-only; no absences, but still a chart).
    r = await request_backend("GET", "/api/attendance/students/me", authorization)
    if r.get("ok"):
        return _from_raw(r.get("data"), intent)
    return None
