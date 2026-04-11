import { FormEvent, useEffect, useMemo, useState } from "react";
import NavbarAdmin from "../components/NavbarAdmin";
import NavbarSchoolIT from "../components/NavbarSchoolIT";
import NavbarORG from "../components/NavbarORG";
import NavbarSG from "../components/NavbarSG";
import NavbarSSG from "../components/NavbarSSG";
import { NavbarStudent } from "../components/NavbarStudent";
import { fetchAcademicCatalog } from "../api/academicApi";
import { fetchStudentAttendanceOverview } from "../api/attendanceApi";
import { fetchAllEvents, type Event as SchoolEvent } from "../api/eventsApi";
import {
  fetchGovernanceUnits,
  type GovernanceUnitSummary,
  type GovernanceUnitType,
} from "../api/governanceHierarchyApi";
import {
  fetchCurrentUserProfile,
  fetchSchoolScopedUsers,
  type SchoolScopedUserWithRelations,
} from "../api/userApi";
import { useGovernanceAccess } from "../hooks/useGovernanceAccess";
import { readStoredUserSession } from "../lib/auth/storedUser";
import { apiJsonRequest, apiRequest, extractApiErrorMessage } from "../lib/api/client";
import { normalizeRole } from "../utils/roleUtils";

type GovernanceContext = "SSG" | "SG" | "ORG";
type Audience = "platform_admin" | "campus_or_school_admin" | "student" | "manage_attendance";
type RunnerKey =
  | "event_report"
  | "event_attendee_roster"
  | "event_status_mix"
  | "event_late_burden"
  | "event_incomplete_signout"
  | "at_risk_attendance"
  | "top_absentees"
  | "top_late_students"
  | "attendance_leaderboard"
  | "attendance_recovery"
  | "attendance_decline_alert"
  | "no_show_event_report"
  | "event_execution_quality"
  | "event_completion_vs_cancellation"
  | "attendance_by_day_of_week"
  | "attendance_by_time_block"
  | "year_level_distribution"
  | "repeat_participation"
  | "first_time_vs_repeat"
  | "school_kpi_dashboard"
  | "students_overview"
  | "student_report"
  | "student_report_log"
  | "student_monthly"
  | "student_event_type_mix"
  | "student_stats"
  | "attendance_summary"
  | "summary_unique_students"
  | "summary_unique_events"
  | "student_record_collection"
  | "personal_history"
  | "import_preview"
  | "import_status"
  | "import_failed_rows"
  | "audit_logs"
  | "notification_logs"
  | "notification_dispatch"
  | "governance_overview"
  | "retention_run";

type ReportFieldType =
  | "event"
  | "student"
  | "department"
  | "program"
  | "governance_unit"
  | "user"
  | "text"
  | "number"
  | "date"
  | "select"
  | "checkbox"
  | "file";

type ReportFormValues = Record<string, string | boolean | File | null>;

interface FieldOption {
  value: string;
  label: string;
}

interface ReportField {
  key: string;
  label: string;
  type: ReportFieldType;
  required?: boolean;
  placeholder?: string;
  defaultValue?: string | boolean;
  options?: FieldOption[];
}

interface ReportSpec {
  id: string;
  title: string;
  purpose: string;
  endpointLabel: string;
  runner: RunnerKey;
  audiences: Audience[];
  fields: ReportField[];
}

interface Capabilities {
  isPlatformAdmin: boolean;
  isCampusAdmin: boolean;
  isSchoolAdmin: boolean;
  isStudent: boolean;
  hasManageAttendance: boolean;
  schoolId: number | null;
  governanceContexts: GovernanceContext[];
}

interface OptionSources {
  events: FieldOption[];
  students: FieldOption[];
  departments: FieldOption[];
  programs: FieldOption[];
  governanceUnits: FieldOption[];
  users: FieldOption[];
}

const STATUS_OPTIONS: FieldOption[] = [
  { value: "all", label: "All statuses" },
  { value: "present", label: "Present" },
  { value: "late", label: "Late" },
  { value: "absent", label: "Absent" },
  { value: "excused", label: "Excused" },
  { value: "incomplete", label: "Incomplete" },
];

const GROUP_BY_OPTIONS: FieldOption[] = [
  { value: "day", label: "Day" },
  { value: "week", label: "Week" },
  { value: "month", label: "Month" },
  { value: "year", label: "Year" },
];

const DISPATCH_OPTIONS: FieldOption[] = [
  { value: "missed-events", label: "Missed Events Dispatch" },
  { value: "low-attendance", label: "Low Attendance Dispatch" },
  { value: "event-reminders", label: "Event Reminders Dispatch" },
];

const F_EVENT: ReportField[] = [{ key: "event_id", label: "Event", type: "event", required: true }];
const F_STUDENT: ReportField[] = [{ key: "student_id", label: "Student", type: "student", required: true }];
const F_DATE_RANGE: ReportField[] = [
  { key: "start_date", label: "Start Date", type: "date" },
  { key: "end_date", label: "End Date", type: "date" },
];
const F_SUMMARY_SCOPE: ReportField[] = [
  ...F_DATE_RANGE,
  { key: "department_id", label: "Department", type: "department" },
  { key: "program_id", label: "Program", type: "program" },
];
const F_COMPARE_PERIODS: ReportField[] = [
  { key: "current_start_date", label: "Current Start Date", type: "date", required: true },
  { key: "current_end_date", label: "Current End Date", type: "date", required: true },
  { key: "previous_start_date", label: "Previous Start Date", type: "date", required: true },
  { key: "previous_end_date", label: "Previous End Date", type: "date", required: true },
];

const REPORTS: ReportSpec[] = [
  { id: "event-attendance-summary", title: "Event Attendance Summary", purpose: "Quick health check of one event.", endpointLabel: "GET /api/attendance/events/{event_id}/report", runner: "event_report", audiences: ["campus_or_school_admin", "manage_attendance"], fields: F_EVENT },
  { id: "event-program-breakdown", title: "Event Program Breakdown", purpose: "Compare outcomes across programs.", endpointLabel: "GET /api/attendance/events/{event_id}/report", runner: "event_report", audiences: ["campus_or_school_admin", "manage_attendance"], fields: F_EVENT },
  { id: "event-attendee-roster", title: "Event Attendee Roster", purpose: "Show who has attendance records in an event.", endpointLabel: "GET /api/attendance/events/{event_id}/attendances-with-students", runner: "event_attendee_roster", audiences: ["campus_or_school_admin", "manage_attendance"], fields: [...F_EVENT, { key: "status", label: "Status", type: "select", options: STATUS_OPTIONS, defaultValue: "all" }, { key: "limit", label: "Max Rows", type: "number", defaultValue: "100" }] },
  { id: "event-status-mix", title: "Event Status Mix", purpose: "See attendance quality distribution.", endpointLabel: "Derived from /api/attendance/events/{event_id}/report", runner: "event_status_mix", audiences: ["campus_or_school_admin", "manage_attendance"], fields: F_EVENT },
  { id: "event-late-burden", title: "Event Late Burden", purpose: "Measure tardiness.", endpointLabel: "Derived from /api/attendance/events/{event_id}/report", runner: "event_late_burden", audiences: ["campus_or_school_admin", "manage_attendance"], fields: F_EVENT },
  { id: "event-incomplete-signout-report", title: "Event Incomplete Sign-Out Report", purpose: "Detect sign-out process gaps.", endpointLabel: "Derived from /api/attendance/events/{event_id}/report", runner: "event_incomplete_signout", audiences: ["campus_or_school_admin", "manage_attendance"], fields: F_EVENT },
  { id: "student-attendance-overview-list", title: "Student Attendance Overview List", purpose: "Scan students quickly.", endpointLabel: "GET /api/attendance/students/overview", runner: "students_overview", audiences: ["campus_or_school_admin", "manage_attendance"], fields: [{ key: "search", label: "Search", type: "text", placeholder: "Name or student ID" }, ...F_SUMMARY_SCOPE, { key: "skip", label: "Skip", type: "number", defaultValue: "0" }, { key: "limit", label: "Limit", type: "number", defaultValue: "100" }] },
  { id: "student-attendance-performance-card", title: "Student Attendance Performance Card", purpose: "Full summary for one student.", endpointLabel: "GET /api/attendance/students/{student_id}/report", runner: "student_report", audiences: ["student", "campus_or_school_admin", "manage_attendance"], fields: [...F_STUDENT, ...F_DATE_RANGE, { key: "event_type", label: "Event Type", type: "text" }] },
  { id: "student-attendance-event-log", title: "Student Attendance Event Log", purpose: "Auditable event-by-event history.", endpointLabel: "GET /api/attendance/students/{student_id}/report", runner: "student_report_log", audiences: ["student", "campus_or_school_admin", "manage_attendance"], fields: [...F_STUDENT, ...F_DATE_RANGE, { key: "status", label: "Status", type: "select", options: STATUS_OPTIONS, defaultValue: "all" }] },
  { id: "student-monthly-attendance-trend", title: "Student Monthly Attendance Trend", purpose: "Monitor progress over time.", endpointLabel: "GET /api/attendance/students/{student_id}/report", runner: "student_monthly", audiences: ["student", "campus_or_school_admin", "manage_attendance"], fields: [...F_STUDENT, ...F_DATE_RANGE] },
  { id: "student-event-type-attendance-mix", title: "Student Event-Type Attendance Mix", purpose: "See behavior by event category.", endpointLabel: "GET /api/attendance/students/{student_id}/report and /stats", runner: "student_event_type_mix", audiences: ["student", "campus_or_school_admin", "manage_attendance"], fields: [...F_STUDENT, ...F_DATE_RANGE] },
  { id: "student-status-distribution", title: "Student Status Distribution", purpose: "Status split snapshot for one student.", endpointLabel: "GET /api/attendance/students/{student_id}/stats", runner: "student_stats", audiences: ["student", "campus_or_school_admin", "manage_attendance"], fields: [...F_STUDENT, ...F_DATE_RANGE, { key: "group_by", label: "Group By", type: "select", options: GROUP_BY_OPTIONS, defaultValue: "month" }] },
  { id: "student-trend-by-period", title: "Student Trend by Period", purpose: "Time-series tracking.", endpointLabel: "GET /api/attendance/students/{student_id}/stats", runner: "student_stats", audiences: ["student", "campus_or_school_admin", "manage_attendance"], fields: [...F_STUDENT, ...F_DATE_RANGE, { key: "group_by", label: "Group By", type: "select", options: GROUP_BY_OPTIONS, defaultValue: "month" }] },
  { id: "school-attendance-summary", title: "School Attendance Summary", purpose: "Overall school attendance snapshot.", endpointLabel: "GET /api/attendance/summary", runner: "attendance_summary", audiences: ["campus_or_school_admin", "manage_attendance"], fields: F_SUMMARY_SCOPE },
  { id: "school-unique-student-participation", title: "School Unique Student Participation", purpose: "Measure student reach.", endpointLabel: "Derived from GET /api/attendance/summary", runner: "summary_unique_students", audiences: ["campus_or_school_admin", "manage_attendance"], fields: F_SUMMARY_SCOPE },
  { id: "school-unique-event-coverage", title: "School Unique Event Coverage", purpose: "Measure event coverage.", endpointLabel: "Derived from GET /api/attendance/summary", runner: "summary_unique_events", audiences: ["campus_or_school_admin", "manage_attendance"], fields: F_SUMMARY_SCOPE },
  { id: "department-attendance-slice", title: "Department Attendance Slice", purpose: "Department-level attendance quality.", endpointLabel: "GET /api/attendance/summary?department_id=...", runner: "attendance_summary", audiences: ["campus_or_school_admin", "manage_attendance"], fields: [{ key: "department_id", label: "Department", type: "department", required: true }, ...F_DATE_RANGE] },
  { id: "program-attendance-slice", title: "Program Attendance Slice", purpose: "Program-level attendance quality.", endpointLabel: "GET /api/attendance/summary?program_id=...", runner: "attendance_summary", audiences: ["campus_or_school_admin", "manage_attendance"], fields: [{ key: "program_id", label: "Program", type: "program", required: true }, ...F_DATE_RANGE] },
  { id: "student-record-collection", title: "Student Record Collection", purpose: "Pull records for selected students.", endpointLabel: "GET /api/attendance/students/records", runner: "student_record_collection", audiences: ["campus_or_school_admin", "manage_attendance"], fields: [{ key: "student_ids", label: "Student IDs", type: "text", placeholder: "Comma-separated student IDs" }, { key: "event_id", label: "Event", type: "event" }, { key: "status", label: "Status", type: "select", options: STATUS_OPTIONS, defaultValue: "all" }, { key: "skip", label: "Skip", type: "number", defaultValue: "0" }, { key: "limit", label: "Limit", type: "number", defaultValue: "100" }] },
  { id: "personal-attendance-history", title: "Personal Attendance History", purpose: "Student self-service transparency.", endpointLabel: "GET /api/attendance/me/records", runner: "personal_history", audiences: ["student"], fields: [{ key: "event_id", label: "Event", type: "event" }, { key: "status", label: "Status", type: "select", options: STATUS_OPTIONS, defaultValue: "all" }, { key: "skip", label: "Skip", type: "number", defaultValue: "0" }, { key: "limit", label: "Limit", type: "number", defaultValue: "100" }] },
  { id: "import-preview-quality-report", title: "Import Preview Quality Report", purpose: "Validate import readiness before commit.", endpointLabel: "POST /api/admin/import-students/preview", runner: "import_preview", audiences: ["campus_or_school_admin"], fields: [{ key: "import_file", label: "Import File (.csv/.xlsx)", type: "file", required: true }] },
  { id: "import-job-progress-report", title: "Import Job Progress Report", purpose: "Track bulk import execution.", endpointLabel: "GET /api/admin/import-status/{job_id}", runner: "import_status", audiences: ["campus_or_school_admin"], fields: [{ key: "job_id", label: "Import Job ID", type: "text", required: true }] },
  { id: "import-failed-rows-report", title: "Import Failed Rows Report", purpose: "Resolve failed imports.", endpointLabel: "GET /api/admin/import-status/{job_id}", runner: "import_failed_rows", audiences: ["campus_or_school_admin"], fields: [{ key: "job_id", label: "Import Job ID", type: "text", required: true }] },
  { id: "audit-activity-report", title: "Audit Activity Report", purpose: "Accountability and governance.", endpointLabel: "GET /api/audit-logs", runner: "audit_logs", audiences: ["platform_admin", "campus_or_school_admin"], fields: [{ key: "q", label: "Search", type: "text" }, { key: "action", label: "Action", type: "text" }, { key: "status", label: "Status", type: "text" }, { key: "actor_user_id", label: "Actor User", type: "user" }, { key: "actor_user_id_manual", label: "Actor User ID (manual)", type: "number" }, ...F_DATE_RANGE, { key: "limit", label: "Limit", type: "number", defaultValue: "100" }, { key: "offset", label: "Offset", type: "number", defaultValue: "0" }] },
  { id: "notification-log-report", title: "Notification Log Report", purpose: "Check delivery behavior.", endpointLabel: "GET /api/notifications/logs", runner: "notification_logs", audiences: ["platform_admin", "campus_or_school_admin"], fields: [{ key: "category", label: "Category", type: "text" }, { key: "status", label: "Status", type: "text" }, { key: "user_id", label: "User", type: "user" }, { key: "user_id_manual", label: "User ID (manual)", type: "number" }, { key: "limit", label: "Limit", type: "number", defaultValue: "100" }] },
  { id: "notification-dispatch-outcome", title: "Notification Dispatch Outcome", purpose: "Monitor campaign results.", endpointLabel: "POST /api/notifications/dispatch/*", runner: "notification_dispatch", audiences: ["platform_admin", "campus_or_school_admin"], fields: [{ key: "dispatch_type", label: "Dispatch Type", type: "select", options: DISPATCH_OPTIONS, defaultValue: "missed-events" }, { key: "school_id", label: "School ID", type: "number" }, { key: "lookback_days", label: "Lookback Days", type: "number", defaultValue: "14" }, { key: "threshold_percent", label: "Threshold Percent", type: "number", defaultValue: "75" }, { key: "min_records", label: "Min Records", type: "number", defaultValue: "3" }, { key: "lead_hours", label: "Lead Hours", type: "number", defaultValue: "24" }] },
  { id: "governance-unit-dashboard-overview", title: "Governance Unit Dashboard Overview", purpose: "Unit-level governance monitoring.", endpointLabel: "GET /api/governance/units/{governance_unit_id}/dashboard-overview", runner: "governance_overview", audiences: ["platform_admin", "campus_or_school_admin", "manage_attendance"], fields: [{ key: "governance_unit_id", label: "Governance Unit", type: "governance_unit", required: true }, { key: "governance_unit_id_manual", label: "Governance Unit ID (manual)", type: "number" }] },
  { id: "data-retention-run-summary", title: "Data Retention Run Summary", purpose: "Data compliance monitoring.", endpointLabel: "POST /api/governance/run-retention", runner: "retention_run", audiences: ["platform_admin", "campus_or_school_admin"], fields: [{ key: "dry_run", label: "Dry Run", type: "checkbox", defaultValue: true }, { key: "school_id", label: "School ID (required for platform admin)", type: "number" }] },
  { id: "at-risk-attendance-list", title: "At-Risk Attendance List", purpose: "Identify students needing intervention.", endpointLabel: "GET /api/reports/attendance/at-risk", runner: "at_risk_attendance", audiences: ["campus_or_school_admin", "manage_attendance"], fields: [...F_SUMMARY_SCOPE, { key: "threshold", label: "At-Risk Threshold (%)", type: "number", defaultValue: "75" }, { key: "min_events", label: "Min Events", type: "number", defaultValue: "3" }, { key: "limit", label: "Limit", type: "number", defaultValue: "100" }] },
  { id: "top-absentees", title: "Top Absentees", purpose: "Rank students by absent count.", endpointLabel: "GET /api/reports/attendance/top-absentees", runner: "top_absentees", audiences: ["campus_or_school_admin", "manage_attendance"], fields: [...F_SUMMARY_SCOPE, { key: "limit", label: "Limit", type: "number", defaultValue: "50" }] },
  { id: "top-late-students", title: "Top Late Students", purpose: "Rank students by late count or late rate.", endpointLabel: "GET /api/reports/attendance/top-late", runner: "top_late_students", audiences: ["campus_or_school_admin", "manage_attendance"], fields: [...F_SUMMARY_SCOPE, { key: "metric", label: "Ranking Metric", type: "select", options: [{ value: "count", label: "Late Count" }, { value: "rate", label: "Late Rate" }], defaultValue: "count" }, { key: "min_events", label: "Min Events", type: "number", defaultValue: "3" }, { key: "limit", label: "Limit", type: "number", defaultValue: "50" }] },
  { id: "attendance-leaderboard", title: "Attendance Leaderboard", purpose: "Rank students by attendance rate.", endpointLabel: "GET /api/reports/attendance/leaderboard", runner: "attendance_leaderboard", audiences: ["student", "campus_or_school_admin", "manage_attendance"], fields: [...F_SUMMARY_SCOPE, { key: "min_events", label: "Min Events", type: "number", defaultValue: "3" }, { key: "limit", label: "Limit", type: "number", defaultValue: "100" }] },
  { id: "attendance-recovery-report", title: "Attendance Recovery Report", purpose: "Find students whose attendance improved.", endpointLabel: "GET /api/reports/attendance/recovery", runner: "attendance_recovery", audiences: ["campus_or_school_admin", "manage_attendance"], fields: [...F_COMPARE_PERIODS, { key: "department_id", label: "Department", type: "department" }, { key: "program_id", label: "Program", type: "program" }, { key: "min_events_per_period", label: "Min Events Per Period", type: "number", defaultValue: "2" }, { key: "limit", label: "Limit", type: "number", defaultValue: "100" }] },
  { id: "attendance-decline-alert", title: "Attendance Decline Alert", purpose: "Highlight students with attendance drop-offs.", endpointLabel: "GET /api/reports/attendance/decline-alerts", runner: "attendance_decline_alert", audiences: ["campus_or_school_admin", "manage_attendance"], fields: [...F_COMPARE_PERIODS, { key: "department_id", label: "Department", type: "department" }, { key: "program_id", label: "Program", type: "program" }, { key: "decline_threshold", label: "Decline Threshold (%)", type: "number", defaultValue: "10" }, { key: "min_events_per_period", label: "Min Events Per Period", type: "number", defaultValue: "2" }, { key: "limit", label: "Limit", type: "number", defaultValue: "100" }] },
  { id: "no-show-event-report", title: "No-Show Event Report", purpose: "Flag events with high no-show rates.", endpointLabel: "GET /api/reports/events/no-show", runner: "no_show_event_report", audiences: ["campus_or_school_admin", "manage_attendance"], fields: [{ key: "event_id", label: "Event (optional)", type: "event" }, ...F_SUMMARY_SCOPE] },
  { id: "event-execution-quality-report", title: "Event Execution Quality Report", purpose: "Check incomplete sign-out and late burden by event.", endpointLabel: "GET /api/reports/events/execution-quality", runner: "event_execution_quality", audiences: ["campus_or_school_admin", "manage_attendance"], fields: [{ key: "event_id", label: "Event (optional)", type: "event" }, ...F_SUMMARY_SCOPE] },
  { id: "event-completion-vs-cancellation", title: "Event Completion vs Cancellation Report", purpose: "Track completed vs cancelled events.", endpointLabel: "GET /api/reports/events/completion-vs-cancellation", runner: "event_completion_vs_cancellation", audiences: ["campus_or_school_admin", "manage_attendance"], fields: F_SUMMARY_SCOPE },
  { id: "attendance-by-day-of-week", title: "Attendance by Day of Week", purpose: "Find weekdays with lower attendance.", endpointLabel: "GET /api/reports/attendance/by-day-of-week", runner: "attendance_by_day_of_week", audiences: ["campus_or_school_admin", "manage_attendance"], fields: F_SUMMARY_SCOPE },
  { id: "attendance-by-time-block", title: "Attendance by Time Block", purpose: "Detect check-in timing and lateness patterns.", endpointLabel: "GET /api/reports/attendance/by-time-block", runner: "attendance_by_time_block", audiences: ["campus_or_school_admin", "manage_attendance"], fields: F_SUMMARY_SCOPE },
  { id: "year-level-attendance-distribution", title: "Year Level Attendance Distribution", purpose: "Compare attendance quality by year level.", endpointLabel: "GET /api/reports/attendance/year-level-distribution", runner: "year_level_distribution", audiences: ["campus_or_school_admin", "manage_attendance"], fields: F_SUMMARY_SCOPE },
  { id: "repeat-participation-report", title: "Repeat Participation Report", purpose: "Measure engagement depth across students.", endpointLabel: "GET /api/reports/attendance/repeat-participation", runner: "repeat_participation", audiences: ["campus_or_school_admin", "manage_attendance"], fields: F_SUMMARY_SCOPE },
  { id: "first-time-vs-repeat-attendee-report", title: "First-Time vs Repeat Attendee Report", purpose: "Measure first-time versus repeat attendance per event.", endpointLabel: "GET /api/reports/events/first-time-vs-repeat", runner: "first_time_vs_repeat", audiences: ["campus_or_school_admin", "manage_attendance"], fields: [{ key: "event_id", label: "Event (optional)", type: "event" }, ...F_SUMMARY_SCOPE] },
  { id: "school-kpi-dashboard-report", title: "School KPI Dashboard Report", purpose: "Executive attendance KPI snapshot.", endpointLabel: "GET /api/reports/school/kpi-dashboard", runner: "school_kpi_dashboard", audiences: ["campus_or_school_admin", "manage_attendance"], fields: F_SUMMARY_SCOPE },
];

const isRecord = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === "object" && !Array.isArray(value);

const asString = (values: ReportFormValues, key: string) =>
  typeof values[key] === "string" ? values[key].trim() : "";

const asOptionalNumber = (values: ReportFormValues, key: string) => {
  const raw = asString(values, key);
  if (!raw) return undefined;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : undefined;
};

const asRequiredNumber = (values: ReportFormValues, key: string, label: string) => {
  const parsed = asOptionalNumber(values, key);
  if (parsed === undefined) {
    throw new Error(`${label} is required.`);
  }
  return parsed;
};

const asBoolean = (values: ReportFormValues, key: string, fallback = false) =>
  typeof values[key] === "boolean" ? values[key] : fallback;

const parseDateStart = (value: string) => (value ? `${value}T00:00:00` : undefined);
const parseDateEnd = (value: string) => (value ? `${value}T23:59:59` : undefined);

const buildQuery = (
  params: Record<string, string | number | boolean | Array<string | number> | undefined | null>
) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === null || value === undefined || value === "") return;
    if (Array.isArray(value)) {
      value.forEach((item) => {
        if (`${item}`.trim()) query.append(key, String(item));
      });
      return;
    }
    query.set(key, String(value));
  });
  const text = query.toString();
  return text ? `?${text}` : "";
};

const withGovernance = (
  governanceContext: GovernanceContext | "",
  params: Record<string, string | number | boolean | Array<string | number> | undefined | null> = {}
) => ({
  ...params,
  governance_context: governanceContext || undefined,
});

const apiGet = async <T,>(
  path: string,
  params: Record<string, string | number | boolean | Array<string | number> | undefined | null> = {},
  fallback = "Failed to run report"
) =>
  apiJsonRequest<T>(`${path}${buildQuery(params)}`, { auth: true, method: "GET" }, fallback);

const apiPost = async <T,>(
  path: string,
  body: unknown,
  params: Record<string, string | number | boolean | Array<string | number> | undefined | null> = {},
  fallback = "Failed to run report"
) =>
  apiJsonRequest<T>(
    `${path}${buildQuery(params)}`,
    { auth: true, method: "POST", json: body },
    fallback
  );

const apiPostForm = async <T,>(path: string, formData: FormData, fallback: string) => {
  const response = await apiRequest(path, { auth: true, method: "POST", body: formData });
  if (!response.ok) throw new Error(await extractApiErrorMessage(response, fallback));
  return (await response.json()) as T;
};

const getEventLabel = (event: SchoolEvent) => {
  const parsed = new Date(event.start_datetime);
  const dateText = Number.isNaN(parsed.getTime()) ? event.start_datetime : parsed.toLocaleDateString();
  return `${event.name} (${dateText})`;
};

const canSeeReport = (report: ReportSpec, caps: Capabilities) =>
  report.audiences.some((audience) => {
    if (audience === "platform_admin") return caps.isPlatformAdmin;
    if (audience === "campus_or_school_admin") return caps.isCampusAdmin || caps.isSchoolAdmin;
    if (audience === "student") return caps.isStudent;
    if (audience === "manage_attendance") return caps.hasManageAttendance;
    return false;
  });

const executeReport = async (
  report: ReportSpec,
  values: ReportFormValues,
  governanceContext: GovernanceContext | "",
  caps: Capabilities
) => {
  const loadEventReport = async () => {
    const eventId = asRequiredNumber(values, "event_id", "Event");
    return apiGet<Record<string, unknown>>(
      `/api/attendance/events/${eventId}/report`,
      withGovernance(governanceContext)
    );
  };

  const loadSummary = async () =>
    apiGet<Record<string, unknown>>("/api/attendance/summary", {
      start_date: asString(values, "start_date") || undefined,
      end_date: asString(values, "end_date") || undefined,
      department_id: asOptionalNumber(values, "department_id"),
      program_id: asOptionalNumber(values, "program_id"),
    });

  switch (report.runner) {
    case "event_report":
      return loadEventReport();
    case "event_attendee_roster": {
      const eventId = asRequiredNumber(values, "event_id", "Event");
      const status = asString(values, "status") || "all";
      const maxRows = asOptionalNumber(values, "limit") ?? 100;
      const rows = await apiGet<Array<Record<string, unknown>>>(
        `/api/attendance/events/${eventId}/attendances-with-students`,
        withGovernance(governanceContext)
      );
      const filtered = status === "all"
        ? rows
        : rows.filter((row) => {
            const attendance = (row.attendance ?? {}) as Record<string, unknown>;
            const rowStatus = String(attendance.display_status ?? attendance.status ?? "").toLowerCase();
            return rowStatus === status.toLowerCase();
          });
      return { total_rows: filtered.length, rows: filtered.slice(0, Math.max(1, maxRows)) };
    }
    case "event_status_mix": {
      const result = await loadEventReport();
      const total = Number(result.total_participants ?? 0);
      const late = Number(result.late_attendees ?? 0);
      const incomplete = Number(result.incomplete_attendees ?? 0);
      const absent = Number(result.absentees ?? 0);
      const present = Math.max(0, Number(result.attendees ?? 0) - late);
      const toRate = (value: number) => (total > 0 ? Number(((value / total) * 100).toFixed(2)) : 0);
      return {
        event_name: result.event_name,
        total_participants: total,
        present,
        late,
        incomplete,
        absent,
        present_rate: toRate(present),
        late_rate: toRate(late),
        incomplete_rate: toRate(incomplete),
        absent_rate: toRate(absent),
        raw_report: result,
      };
    }
    case "event_late_burden": {
      const result = await loadEventReport();
      const total = Number(result.total_participants ?? 0);
      const late = Number(result.late_attendees ?? 0);
      return {
        event_name: result.event_name,
        late_attendees: late,
        total_participants: total,
        late_rate: total > 0 ? Number(((late / total) * 100).toFixed(2)) : 0,
        raw_report: result,
      };
    }
    case "event_incomplete_signout": {
      const result = await loadEventReport();
      const total = Number(result.total_participants ?? 0);
      const incomplete = Number(result.incomplete_attendees ?? 0);
      return {
        event_name: result.event_name,
        incomplete_attendees: incomplete,
        total_participants: total,
        incomplete_rate: total > 0 ? Number(((incomplete / total) * 100).toFixed(2)) : 0,
        raw_report: result,
      };
    }
    case "at_risk_attendance":
      return apiGet<Record<string, unknown>>(
        "/api/reports/attendance/at-risk",
        withGovernance(governanceContext, {
          start_date: asString(values, "start_date") || undefined,
          end_date: asString(values, "end_date") || undefined,
          department_id: asOptionalNumber(values, "department_id"),
          program_id: asOptionalNumber(values, "program_id"),
          threshold: asOptionalNumber(values, "threshold"),
          min_events: asOptionalNumber(values, "min_events"),
          limit: asOptionalNumber(values, "limit"),
        })
      );
    case "top_absentees":
      return apiGet<Record<string, unknown>>(
        "/api/reports/attendance/top-absentees",
        withGovernance(governanceContext, {
          start_date: asString(values, "start_date") || undefined,
          end_date: asString(values, "end_date") || undefined,
          department_id: asOptionalNumber(values, "department_id"),
          program_id: asOptionalNumber(values, "program_id"),
          limit: asOptionalNumber(values, "limit"),
        })
      );
    case "top_late_students":
      return apiGet<Record<string, unknown>>(
        "/api/reports/attendance/top-late",
        withGovernance(governanceContext, {
          start_date: asString(values, "start_date") || undefined,
          end_date: asString(values, "end_date") || undefined,
          department_id: asOptionalNumber(values, "department_id"),
          program_id: asOptionalNumber(values, "program_id"),
          metric: asString(values, "metric") || "count",
          min_events: asOptionalNumber(values, "min_events"),
          limit: asOptionalNumber(values, "limit"),
        })
      );
    case "attendance_leaderboard":
      return apiGet<Record<string, unknown>>(
        "/api/reports/attendance/leaderboard",
        withGovernance(governanceContext, {
          start_date: asString(values, "start_date") || undefined,
          end_date: asString(values, "end_date") || undefined,
          department_id: asOptionalNumber(values, "department_id"),
          program_id: asOptionalNumber(values, "program_id"),
          min_events: asOptionalNumber(values, "min_events"),
          limit: asOptionalNumber(values, "limit"),
        })
      );
    case "attendance_recovery":
      return apiGet<Record<string, unknown>>(
        "/api/reports/attendance/recovery",
        withGovernance(governanceContext, {
          current_start_date: asString(values, "current_start_date") || undefined,
          current_end_date: asString(values, "current_end_date") || undefined,
          previous_start_date: asString(values, "previous_start_date") || undefined,
          previous_end_date: asString(values, "previous_end_date") || undefined,
          department_id: asOptionalNumber(values, "department_id"),
          program_id: asOptionalNumber(values, "program_id"),
          min_events_per_period: asOptionalNumber(values, "min_events_per_period"),
          limit: asOptionalNumber(values, "limit"),
        })
      );
    case "attendance_decline_alert":
      return apiGet<Record<string, unknown>>(
        "/api/reports/attendance/decline-alerts",
        withGovernance(governanceContext, {
          current_start_date: asString(values, "current_start_date") || undefined,
          current_end_date: asString(values, "current_end_date") || undefined,
          previous_start_date: asString(values, "previous_start_date") || undefined,
          previous_end_date: asString(values, "previous_end_date") || undefined,
          department_id: asOptionalNumber(values, "department_id"),
          program_id: asOptionalNumber(values, "program_id"),
          decline_threshold: asOptionalNumber(values, "decline_threshold"),
          min_events_per_period: asOptionalNumber(values, "min_events_per_period"),
          limit: asOptionalNumber(values, "limit"),
        })
      );
    case "no_show_event_report":
      return apiGet<Record<string, unknown>>(
        "/api/reports/events/no-show",
        withGovernance(governanceContext, {
          event_id: asOptionalNumber(values, "event_id"),
          start_date: asString(values, "start_date") || undefined,
          end_date: asString(values, "end_date") || undefined,
          department_id: asOptionalNumber(values, "department_id"),
          program_id: asOptionalNumber(values, "program_id"),
        })
      );
    case "event_execution_quality":
      return apiGet<Record<string, unknown>>(
        "/api/reports/events/execution-quality",
        withGovernance(governanceContext, {
          event_id: asOptionalNumber(values, "event_id"),
          start_date: asString(values, "start_date") || undefined,
          end_date: asString(values, "end_date") || undefined,
          department_id: asOptionalNumber(values, "department_id"),
          program_id: asOptionalNumber(values, "program_id"),
        })
      );
    case "event_completion_vs_cancellation":
      return apiGet<Record<string, unknown>>(
        "/api/reports/events/completion-vs-cancellation",
        withGovernance(governanceContext, {
          start_date: asString(values, "start_date") || undefined,
          end_date: asString(values, "end_date") || undefined,
          department_id: asOptionalNumber(values, "department_id"),
          program_id: asOptionalNumber(values, "program_id"),
        })
      );
    case "attendance_by_day_of_week":
      return apiGet<Record<string, unknown>>(
        "/api/reports/attendance/by-day-of-week",
        withGovernance(governanceContext, {
          start_date: asString(values, "start_date") || undefined,
          end_date: asString(values, "end_date") || undefined,
          department_id: asOptionalNumber(values, "department_id"),
          program_id: asOptionalNumber(values, "program_id"),
        })
      );
    case "attendance_by_time_block":
      return apiGet<Record<string, unknown>>(
        "/api/reports/attendance/by-time-block",
        withGovernance(governanceContext, {
          start_date: asString(values, "start_date") || undefined,
          end_date: asString(values, "end_date") || undefined,
          department_id: asOptionalNumber(values, "department_id"),
          program_id: asOptionalNumber(values, "program_id"),
        })
      );
    case "year_level_distribution":
      return apiGet<Record<string, unknown>>(
        "/api/reports/attendance/year-level-distribution",
        withGovernance(governanceContext, {
          start_date: asString(values, "start_date") || undefined,
          end_date: asString(values, "end_date") || undefined,
          department_id: asOptionalNumber(values, "department_id"),
          program_id: asOptionalNumber(values, "program_id"),
        })
      );
    case "repeat_participation":
      return apiGet<Record<string, unknown>>(
        "/api/reports/attendance/repeat-participation",
        withGovernance(governanceContext, {
          start_date: asString(values, "start_date") || undefined,
          end_date: asString(values, "end_date") || undefined,
          department_id: asOptionalNumber(values, "department_id"),
          program_id: asOptionalNumber(values, "program_id"),
        })
      );
    case "first_time_vs_repeat":
      return apiGet<Record<string, unknown>>(
        "/api/reports/events/first-time-vs-repeat",
        withGovernance(governanceContext, {
          event_id: asOptionalNumber(values, "event_id"),
          start_date: asString(values, "start_date") || undefined,
          end_date: asString(values, "end_date") || undefined,
          department_id: asOptionalNumber(values, "department_id"),
          program_id: asOptionalNumber(values, "program_id"),
        })
      );
    case "school_kpi_dashboard":
      return apiGet<Record<string, unknown>>(
        "/api/reports/school/kpi-dashboard",
        withGovernance(governanceContext, {
          start_date: asString(values, "start_date") || undefined,
          end_date: asString(values, "end_date") || undefined,
          department_id: asOptionalNumber(values, "department_id"),
          program_id: asOptionalNumber(values, "program_id"),
        })
      );
    case "students_overview":
      return apiGet<Array<Record<string, unknown>>>(
        "/api/attendance/students/overview",
        withGovernance(governanceContext, {
          search: asString(values, "search") || undefined,
          department_id: asOptionalNumber(values, "department_id"),
          program_id: asOptionalNumber(values, "program_id"),
          start_date: asString(values, "start_date") || undefined,
          end_date: asString(values, "end_date") || undefined,
          skip: asOptionalNumber(values, "skip"),
          limit: asOptionalNumber(values, "limit"),
        })
      );
    case "student_report":
      return apiGet<Record<string, unknown>>(
        `/api/attendance/students/${asRequiredNumber(values, "student_id", "Student")}/report`,
        withGovernance(governanceContext, {
          start_date: asString(values, "start_date") || undefined,
          end_date: asString(values, "end_date") || undefined,
          event_type: asString(values, "event_type") || undefined,
        })
      );
    case "student_report_log":
      return apiGet<Record<string, unknown>>(
        `/api/attendance/students/${asRequiredNumber(values, "student_id", "Student")}/report`,
        withGovernance(governanceContext, {
          start_date: asString(values, "start_date") || undefined,
          end_date: asString(values, "end_date") || undefined,
          status:
            asString(values, "status") && asString(values, "status") !== "all"
              ? asString(values, "status")
              : undefined,
        })
      );
    case "student_monthly": {
      const reportData = await apiGet<Record<string, unknown>>(
        `/api/attendance/students/${asRequiredNumber(values, "student_id", "Student")}/report`,
        withGovernance(governanceContext, {
          start_date: asString(values, "start_date") || undefined,
          end_date: asString(values, "end_date") || undefined,
        })
      );
      return { student: reportData.student, monthly_stats: reportData.monthly_stats, raw_report: reportData };
    }
    case "student_event_type_mix": {
      const studentId = asRequiredNumber(values, "student_id", "Student");
      const [reportData, statsData] = await Promise.all([
        apiGet<Record<string, unknown>>(
          `/api/attendance/students/${studentId}/report`,
          withGovernance(governanceContext, {
            start_date: asString(values, "start_date") || undefined,
            end_date: asString(values, "end_date") || undefined,
          })
        ),
        apiGet<Record<string, unknown>>(`/api/attendance/students/${studentId}/stats`, {
          start_date: asString(values, "start_date") || undefined,
          end_date: asString(values, "end_date") || undefined,
        }),
      ]);
      return {
        event_type_stats: reportData.event_type_stats ?? {},
        event_type_breakdown: statsData.event_type_breakdown ?? [],
        raw_report: reportData,
        raw_stats: statsData,
      };
    }
    case "student_stats":
      return apiGet<Record<string, unknown>>(
        `/api/attendance/students/${asRequiredNumber(values, "student_id", "Student")}/stats`,
        {
          start_date: asString(values, "start_date") || undefined,
          end_date: asString(values, "end_date") || undefined,
          group_by: asString(values, "group_by") || "month",
        }
      );
    case "attendance_summary":
      return loadSummary();
    case "summary_unique_students": {
      const summaryResult = await loadSummary();
      const summary = isRecord(summaryResult.summary) ? summaryResult.summary : {};
      return { unique_students: summary.unique_students ?? 0, raw_summary: summaryResult };
    }
    case "summary_unique_events": {
      const summaryResult = await loadSummary();
      const summary = isRecord(summaryResult.summary) ? summaryResult.summary : {};
      return { unique_events: summary.unique_events ?? 0, raw_summary: summaryResult };
    }
    case "student_record_collection": {
      const rawStudentIds = asString(values, "student_ids");
      const studentIds = rawStudentIds
        ? rawStudentIds.split(",").map((value) => value.trim()).filter(Boolean)
        : undefined;
      const status = asString(values, "status");
      return apiGet<Array<Record<string, unknown>>>("/api/attendance/students/records", {
        student_ids: studentIds,
        event_id: asOptionalNumber(values, "event_id"),
        status: status && status !== "all" ? status : undefined,
        skip: asOptionalNumber(values, "skip"),
        limit: asOptionalNumber(values, "limit"),
      });
    }
    case "personal_history": {
      const status = asString(values, "status");
      return apiGet<Array<Record<string, unknown>>>("/api/attendance/me/records", {
        event_id: asOptionalNumber(values, "event_id"),
        status: status && status !== "all" ? status : undefined,
        skip: asOptionalNumber(values, "skip"),
        limit: asOptionalNumber(values, "limit"),
      });
    }
    case "import_preview": {
      const file = values.import_file;
      if (!(file instanceof File)) throw new Error("Import file is required.");
      const formData = new FormData();
      formData.append("file", file);
      return apiPostForm<Record<string, unknown>>(
        "/api/admin/import-students/preview",
        formData,
        "Failed to preview import file"
      );
    }
    case "import_status": {
      const jobId = asString(values, "job_id");
      if (!jobId) throw new Error("Import Job ID is required.");
      return apiGet<Record<string, unknown>>(`/api/admin/import-status/${encodeURIComponent(jobId)}`);
    }
    case "import_failed_rows": {
      const jobId = asString(values, "job_id");
      if (!jobId) throw new Error("Import Job ID is required.");
      const statusData = await apiGet<Record<string, unknown>>(
        `/api/admin/import-status/${encodeURIComponent(jobId)}`
      );
      return {
        job_id: statusData.job_id,
        state: statusData.state,
        failed_count: statusData.failed_count,
        errors: statusData.errors ?? [],
        failed_report_download_url: statusData.failed_report_download_url ?? null,
        raw_status: statusData,
      };
    }
    case "audit_logs":
      return apiGet<Record<string, unknown>>("/api/audit-logs", {
        q: asString(values, "q") || undefined,
        action: asString(values, "action") || undefined,
        status: asString(values, "status") || undefined,
        actor_user_id: asOptionalNumber(values, "actor_user_id") ?? asOptionalNumber(values, "actor_user_id_manual"),
        start_date: parseDateStart(asString(values, "start_date")),
        end_date: parseDateEnd(asString(values, "end_date")),
        limit: asOptionalNumber(values, "limit"),
        offset: asOptionalNumber(values, "offset"),
      });
    case "notification_logs":
      return apiGet<Array<Record<string, unknown>>>("/api/notifications/logs", {
        category: asString(values, "category") || undefined,
        status: asString(values, "status") || undefined,
        user_id: asOptionalNumber(values, "user_id") ?? asOptionalNumber(values, "user_id_manual"),
        limit: asOptionalNumber(values, "limit"),
      });
    case "notification_dispatch": {
      const dispatchType = asString(values, "dispatch_type") || "missed-events";
      const schoolId = asOptionalNumber(values, "school_id");
      if (dispatchType === "low-attendance") {
        return apiPost<Record<string, unknown>>(
          "/api/notifications/dispatch/low-attendance",
          {},
          {
            school_id: schoolId,
            threshold_percent: asOptionalNumber(values, "threshold_percent"),
            min_records: asOptionalNumber(values, "min_records"),
          }
        );
      }
      if (dispatchType === "event-reminders") {
        return apiPost<Record<string, unknown>>(
          "/api/notifications/dispatch/event-reminders",
          {},
          {
            school_id: schoolId,
            lead_hours: asOptionalNumber(values, "lead_hours"),
          }
        );
      }
      return apiPost<Record<string, unknown>>(
        "/api/notifications/dispatch/missed-events",
        {},
        {
          school_id: schoolId,
          lookback_days: asOptionalNumber(values, "lookback_days"),
        }
      );
    }
    case "governance_overview": {
      const unitId =
        asOptionalNumber(values, "governance_unit_id") ??
        asOptionalNumber(values, "governance_unit_id_manual");
      if (unitId === undefined) throw new Error("Governance Unit is required.");
      return apiGet<Record<string, unknown>>(`/api/governance/units/${unitId}/dashboard-overview`);
    }
    case "retention_run": {
      const schoolId = asOptionalNumber(values, "school_id");
      if (caps.isPlatformAdmin && schoolId === undefined) {
        throw new Error("School ID is required for platform admin retention runs.");
      }
      return apiPost<Record<string, unknown>>(
        "/api/governance/run-retention",
        { dry_run: asBoolean(values, "dry_run", true) },
        { school_id: schoolId }
      );
    }
  }
};

const ReportsLab = () => {
  type StudentOptionRow = Awaited<ReturnType<typeof fetchStudentAttendanceOverview>>[number];

  const [session, setSession] = useState(() => readStoredUserSession());
  const normalizedRoles = useMemo(() => (session?.roles ?? []).map(normalizeRole), [session]);
  const governance = useGovernanceAccess({ enabled: Boolean(session) });

  const capabilities = useMemo<Capabilities>(() => {
    const hasAdmin = normalizedRoles.includes("admin");
    const schoolId = session?.schoolId ?? null;
    const contexts = new Set<GovernanceContext>();
    governance.access?.units.forEach((unit) => {
      if (unit.permission_codes.includes("manage_attendance")) {
        contexts.add(unit.unit_type as GovernanceContext);
      }
    });

    return {
      isPlatformAdmin: hasAdmin && schoolId === null,
      isCampusAdmin: normalizedRoles.includes("campus-admin"),
      isSchoolAdmin: hasAdmin && schoolId !== null,
      isStudent: normalizedRoles.includes("student"),
      hasManageAttendance: contexts.size > 0,
      schoolId,
      governanceContexts: Array.from(contexts.values()),
    };
  }, [governance.access, normalizedRoles, session]);

  const governanceNavbarType = useMemo<GovernanceUnitType | null>(() => {
    if (capabilities.governanceContexts.includes("SSG")) return "SSG";
    if (capabilities.governanceContexts.includes("SG")) return "SG";
    if (capabilities.governanceContexts.includes("ORG")) return "ORG";
    return null;
  }, [capabilities.governanceContexts]);

  const [governanceContext, setGovernanceContext] = useState<GovernanceContext | "">("");
  const [events, setEvents] = useState<SchoolEvent[]>([]);
  const [students, setStudents] = useState<StudentOptionRow[]>([]);
  const [departments, setDepartments] = useState<Array<{ id: number; name: string }>>([]);
  const [programs, setPrograms] = useState<Array<{ id: number; name: string }>>([]);
  const [governanceUnits, setGovernanceUnits] = useState<GovernanceUnitSummary[]>([]);
  const [users, setUsers] = useState<SchoolScopedUserWithRelations[]>([]);
  const [ownStudentId, setOwnStudentId] = useState<number | null>(null);
  const [loadingSelectors, setLoadingSelectors] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedReportId, setSelectedReportId] = useState("");
  const [values, setValues] = useState<ReportFormValues>({});
  const [result, setResult] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [lastRunAt, setLastRunAt] = useState<Date | null>(null);

  useEffect(() => {
    const syncSession = () => setSession(readStoredUserSession());
    window.addEventListener("storage", syncSession);
    window.addEventListener("focus", syncSession);
    document.addEventListener("visibilitychange", syncSession);
    return () => {
      window.removeEventListener("storage", syncSession);
      window.removeEventListener("focus", syncSession);
      document.removeEventListener("visibilitychange", syncSession);
    };
  }, []);

  useEffect(() => {
    if (capabilities.governanceContexts.length === 0) {
      setGovernanceContext("");
      return;
    }
    setGovernanceContext((current) => {
      if (current && capabilities.governanceContexts.includes(current)) {
        return current;
      }
      if (capabilities.isCampusAdmin || capabilities.isSchoolAdmin || capabilities.isPlatformAdmin) {
        return "";
      }
      return capabilities.governanceContexts[0];
    });
  }, [capabilities]);

  useEffect(() => {
    let cancelled = false;
    const loadStaticSelectors = async () => {
      setLoadingSelectors(true);
      try {
        const results = await Promise.allSettled([
          fetchAcademicCatalog(),
          capabilities.isCampusAdmin || capabilities.isSchoolAdmin || capabilities.isPlatformAdmin || capabilities.isStudent
            ? fetchGovernanceUnits()
            : Promise.resolve([] as GovernanceUnitSummary[]),
          capabilities.isCampusAdmin || capabilities.isSchoolAdmin
            ? fetchSchoolScopedUsers({ limit: 300 })
            : Promise.resolve([] as SchoolScopedUserWithRelations[]),
          capabilities.isStudent ? fetchCurrentUserProfile() : Promise.resolve(null),
        ]);
        if (cancelled) return;

        const catalog = results[0];
        if (catalog.status === "fulfilled") {
          setDepartments(catalog.value.departments);
          setPrograms(catalog.value.programs);
        } else {
          setDepartments([]);
          setPrograms([]);
        }

        const units = results[1];
        setGovernanceUnits(units.status === "fulfilled" ? units.value : []);

        const usersResult = results[2];
        setUsers(usersResult.status === "fulfilled" ? usersResult.value : []);

        const profile = results[3];
        if (profile.status === "fulfilled" && profile.value?.student_profile?.id) {
          setOwnStudentId(profile.value.student_profile.id);
        } else {
          setOwnStudentId(null);
        }
      } finally {
        if (!cancelled) setLoadingSelectors(false);
      }
    };
    loadStaticSelectors();
    return () => {
      cancelled = true;
    };
  }, [
    capabilities.isCampusAdmin,
    capabilities.isPlatformAdmin,
    capabilities.isSchoolAdmin,
    capabilities.isStudent,
  ]);

  useEffect(() => {
    let cancelled = false;
    const loadAttendanceSelectors = async () => {
      const selectedContext = governanceContext || undefined;
      const canFetchScopedStudents =
        capabilities.isCampusAdmin || capabilities.isSchoolAdmin || capabilities.hasManageAttendance;
      const [eventsResult, studentsResult] = await Promise.allSettled([
        fetchAllEvents(false, selectedContext),
        canFetchScopedStudents
          ? fetchStudentAttendanceOverview({ governanceContext: selectedContext })
          : Promise.resolve([] as StudentOptionRow[]),
      ]);
      if (cancelled) return;
      setEvents(eventsResult.status === "fulfilled" ? eventsResult.value : []);
      setStudents(studentsResult.status === "fulfilled" ? studentsResult.value : []);
    };
    loadAttendanceSelectors();
    return () => {
      cancelled = true;
    };
  }, [
    capabilities.hasManageAttendance,
    capabilities.isCampusAdmin,
    capabilities.isSchoolAdmin,
    governanceContext,
  ]);

  const visibleReports = useMemo(
    () =>
      REPORTS.filter((report) => canSeeReport(report, capabilities)).filter((report) => {
        if (!search.trim()) return true;
        const term = search.toLowerCase().trim();
        return (
          report.title.toLowerCase().includes(term) ||
          report.purpose.toLowerCase().includes(term) ||
          report.endpointLabel.toLowerCase().includes(term)
        );
      }),
    [capabilities, search]
  );

  useEffect(() => {
    if (!visibleReports.length) {
      setSelectedReportId("");
      return;
    }
    setSelectedReportId((current) =>
      current && visibleReports.some((report) => report.id === current)
        ? current
        : visibleReports[0].id
    );
  }, [visibleReports]);

  const selectedReport = useMemo(
    () => visibleReports.find((report) => report.id === selectedReportId) ?? null,
    [selectedReportId, visibleReports]
  );

  const optionSources = useMemo<OptionSources>(() => {
    const studentOptions = students.map((student) => ({
      value: String(student.id),
      label: `${student.student_id ?? "N/A"} - ${student.full_name}`,
    }));
    if (!studentOptions.length && ownStudentId !== null) {
      studentOptions.push({
        value: String(ownStudentId),
        label: `My Student Profile (${ownStudentId})`,
      });
    }
    return {
      events: events.map((event) => ({ value: String(event.id), label: getEventLabel(event) })),
      students: studentOptions,
      departments: departments.map((department) => ({ value: String(department.id), label: department.name })),
      programs: programs.map((program) => ({ value: String(program.id), label: program.name })),
      governanceUnits: governanceUnits.map((unit) => ({
        value: String(unit.id),
        label: `${unit.unit_code} - ${unit.unit_name} (${unit.unit_type})`,
      })),
      users: users.map((user) => ({ value: String(user.id), label: `${user.id} - ${user.email}` })),
    };
  }, [departments, events, governanceUnits, ownStudentId, programs, students, users]);

  useEffect(() => {
    if (!selectedReport) {
      setValues({});
      setResult(null);
      setError(null);
      return;
    }
    const nextValues: ReportFormValues = {};
    selectedReport.fields.forEach((field) => {
      if (field.defaultValue !== undefined) {
        nextValues[field.key] = field.defaultValue;
      }
    });
    if (selectedReport.fields.some((field) => field.key === "student_id") && ownStudentId !== null) {
      nextValues.student_id = String(ownStudentId);
    }
    setValues(nextValues);
    setResult(null);
    setError(null);
  }, [ownStudentId, selectedReport]);

  useEffect(() => {
    if (!selectedReport) return;
    setValues((current) => {
      const next = { ...current };
      const ensureDefault = (field: ReportField, options: FieldOption[]) => {
        if (!options.length) return;
        const existing = next[field.key];
        if (typeof existing === "string" && existing.trim()) return;
        next[field.key] = options[0].value;
      };
      selectedReport.fields.forEach((field) => {
        if (field.type === "event") ensureDefault(field, optionSources.events);
        if (field.type === "student") ensureDefault(field, optionSources.students);
        if (field.type === "department") ensureDefault(field, optionSources.departments);
        if (field.type === "program") ensureDefault(field, optionSources.programs);
        if (field.type === "governance_unit") ensureDefault(field, optionSources.governanceUnits);
        if (field.type === "user") ensureDefault(field, optionSources.users);
        if (field.type === "select" && field.options?.length) ensureDefault(field, field.options);
      });
      return next;
    });
  }, [optionSources, selectedReport]);

  const updateValue = (key: string, value: string | boolean | File | null) => {
    setValues((current) => ({ ...current, [key]: value }));
  };

  const getFieldOptions = (field: ReportField): FieldOption[] => {
    if (field.type === "event") return optionSources.events;
    if (field.type === "student") return optionSources.students;
    if (field.type === "department") return optionSources.departments;
    if (field.type === "program") return optionSources.programs;
    if (field.type === "governance_unit") return optionSources.governanceUnits;
    if (field.type === "user") return optionSources.users;
    return field.options ?? [];
  };

  const runSelectedReport = async (submitEvent: FormEvent) => {
    submitEvent.preventDefault();
    if (!selectedReport) return;
    setRunning(true);
    setError(null);
    setResult(null);
    try {
      const output = await executeReport(selectedReport, values, governanceContext, capabilities);
      setResult(output);
      setLastRunAt(new Date());
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : "Failed to run report");
    } finally {
      setRunning(false);
    }
  };

  const tableRows = useMemo(() => {
    if (Array.isArray(result) && result.every(isRecord)) return result;
    if (isRecord(result) && Array.isArray(result.rows) && result.rows.every(isRecord)) {
      return result.rows;
    }
    if (isRecord(result) && Array.isArray(result.items) && result.items.every(isRecord)) {
      return result.items;
    }
    return [] as Record<string, unknown>[];
  }, [result]);

  const tableColumns = useMemo(() => (tableRows.length ? Object.keys(tableRows[0]) : []), [tableRows]);

  const governanceContextOptions = useMemo(() => {
    const base = capabilities.governanceContexts.map((context) => ({ value: context, label: context }));
    if (!base.length) return base;
    if (capabilities.isCampusAdmin || capabilities.isSchoolAdmin || capabilities.isPlatformAdmin) {
      return [{ value: "", label: "School Scope (No Governance Context)" }, ...base];
    }
    return base;
  }, [capabilities]);

  const NavbarComponent = useMemo(() => {
    if (capabilities.isCampusAdmin) return NavbarSchoolIT;
    if (capabilities.isPlatformAdmin || capabilities.isSchoolAdmin) return NavbarAdmin;
    if (governanceNavbarType === "SSG") return NavbarSSG;
    if (governanceNavbarType === "SG") return NavbarSG;
    if (governanceNavbarType === "ORG") return NavbarORG;
    return NavbarStudent;
  }, [capabilities, governanceNavbarType]);

  return (
    <div style={{ minHeight: "100vh", background: "#f3f5f8" }}>
      <NavbarComponent />
      <main className="container-fluid py-3">
        <div className="row g-3">
          <section className="col-12 col-lg-4 col-xl-3">
            <div className="card shadow-sm h-100">
              <div className="card-body d-flex flex-column gap-3">
                <div>
                  <h1 className="h5 mb-1">Reports Lab</h1>
                  <p className="text-muted mb-0">Functional report testing page.</p>
                </div>

                <input
                  className="form-control"
                  placeholder="Search reports..."
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                />

                {governanceContextOptions.length > 0 && (
                  <div>
                    <label className="form-label mb-1">Governance Context</label>
                    <select
                      className="form-select"
                      value={governanceContext}
                      onChange={(event) => setGovernanceContext(event.target.value as GovernanceContext | "")}
                    >
                      {governanceContextOptions.map((option) => (
                        <option key={option.value || "none"} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div className="list-group flex-grow-1" style={{ maxHeight: "66vh", overflowY: "auto" }}>
                  {visibleReports.length === 0 ? (
                    <div className="text-muted small px-2 py-3">No reports available.</div>
                  ) : (
                    visibleReports.map((report) => (
                      <button
                        key={report.id}
                        type="button"
                        className={`list-group-item list-group-item-action text-start ${
                          report.id === selectedReportId ? "active" : ""
                        }`}
                        onClick={() => setSelectedReportId(report.id)}
                      >
                        <strong className="d-block">{report.title}</strong>
                        <small className={report.id === selectedReportId ? "text-white-50" : "text-muted"}>
                          {report.endpointLabel}
                        </small>
                      </button>
                    ))
                  )}
                </div>
              </div>
            </div>
          </section>

          <section className="col-12 col-lg-8 col-xl-9">
            <div className="card shadow-sm mb-3">
              <div className="card-body">
                {selectedReport ? (
                  <>
                    <h2 className="h5 mb-1">{selectedReport.title}</h2>
                    <p className="text-muted mb-1">{selectedReport.purpose}</p>
                    <code>{selectedReport.endpointLabel}</code>

                    <form className="row g-3 mt-1" onSubmit={runSelectedReport}>
                      {selectedReport.fields.map((field) => {
                        const fieldValue = values[field.key];
                        const options = getFieldOptions(field);

                        if (field.type === "checkbox") {
                          return (
                            <div key={field.key} className="col-12">
                              <div className="form-check">
                                <input
                                  id={field.key}
                                  className="form-check-input"
                                  type="checkbox"
                                  checked={typeof fieldValue === "boolean" ? fieldValue : Boolean(field.defaultValue)}
                                  onChange={(event) => updateValue(field.key, event.target.checked)}
                                />
                                <label className="form-check-label" htmlFor={field.key}>
                                  {field.label}
                                </label>
                              </div>
                            </div>
                          );
                        }

                        if (field.type === "file") {
                          return (
                            <div key={field.key} className="col-12">
                              <label className="form-label">{field.label}</label>
                              <input
                                className="form-control"
                                type="file"
                                accept=".csv,.xlsx"
                                required={field.required}
                                onChange={(event) => updateValue(field.key, event.target.files?.[0] ?? null)}
                              />
                            </div>
                          );
                        }

                        if (
                          field.type === "event" ||
                          field.type === "student" ||
                          field.type === "department" ||
                          field.type === "program" ||
                          field.type === "governance_unit" ||
                          field.type === "user" ||
                          field.type === "select"
                        ) {
                          return (
                            <div key={field.key} className="col-12 col-md-6 col-xl-4">
                              <label className="form-label">{field.label}</label>
                              <select
                                className="form-select"
                                required={field.required}
                                value={typeof fieldValue === "string" ? fieldValue : ""}
                                onChange={(event) => updateValue(field.key, event.target.value)}
                              >
                                <option value="">Select {field.label}</option>
                                {options.map((option) => (
                                  <option key={`${field.key}:${option.value}`} value={option.value}>
                                    {option.label}
                                  </option>
                                ))}
                              </select>
                            </div>
                          );
                        }

                        const inputType =
                          field.type === "number" ? "number" : field.type === "date" ? "date" : "text";

                        return (
                          <div key={field.key} className="col-12 col-md-6 col-xl-4">
                            <label className="form-label">{field.label}</label>
                            <input
                              className="form-control"
                              type={inputType}
                              placeholder={field.placeholder}
                              required={field.required}
                              value={typeof fieldValue === "string" ? fieldValue : ""}
                              onChange={(event) => updateValue(field.key, event.target.value)}
                            />
                          </div>
                        );
                      })}

                      <div className="col-12 d-flex align-items-center gap-2">
                        <button className="btn btn-primary" type="submit" disabled={running || !selectedReport}>
                          {running ? "Running..." : "Run Report"}
                        </button>
                        {loadingSelectors && <span className="text-muted small">Loading selectors...</span>}
                        {lastRunAt && <span className="text-muted small">Last run: {lastRunAt.toLocaleString()}</span>}
                      </div>
                    </form>
                  </>
                ) : (
                  <div className="text-muted">No report selected.</div>
                )}
              </div>
            </div>

            <div className="card shadow-sm">
              <div className="card-body">
                <h3 className="h6 mb-3">Report Output</h3>
                {error && <div className="alert alert-danger">{error}</div>}
                {!error && result === null && <div className="text-muted">Run a report to view results.</div>}
                {!error && result !== null && (
                  <>
                    {tableRows.length > 0 && tableColumns.length > 0 && (
                      <div className="table-responsive mb-3 border rounded">
                        <table className="table table-sm table-striped mb-0">
                          <thead>
                            <tr>
                              {tableColumns.map((column) => (
                                <th key={column}>{column}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {tableRows.slice(0, 100).map((row, index) => (
                              <tr key={`row-${index}`}>
                                {tableColumns.map((column) => (
                                  <td key={`${index}-${column}`}>
                                    {typeof row[column] === "object"
                                      ? JSON.stringify(row[column])
                                      : String(row[column] ?? "")}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                    <details open>
                      <summary>Raw JSON</summary>
                      <pre
                        className="bg-dark text-light rounded p-3 mt-2 mb-0"
                        style={{ maxHeight: "52vh", overflowY: "auto", fontSize: "0.8rem" }}
                      >
                        {JSON.stringify(result, null, 2)}
                      </pre>
                    </details>
                  </>
                )}
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
};

export default ReportsLab;
