import type { AttendanceRecord, Event } from "../api/eventsApi";

export type EventWindowStage =
  | "before_check_in"
  | "early_check_in"
  | "late_check_in"
  | "absent_check_in"
  | "sign_out_open"
  | "closed";

export type StudentEventActionState =
  | "not_open"
  | "sign_in"
  | "waiting_sign_out"
  | "sign_out"
  | "missed_check_in"
  | "done"
  | "closed";

const MANILA_TIMEZONE = "Asia/Manila";
const MANILA_OFFSET_SUFFIX = "+08:00";
const TIMEZONE_PATTERN = /([zZ]|[+-]\d{2}:\d{2})$/;

const clampMinutes = (value: number | null | undefined) =>
  Math.max(0, Number.isFinite(value) ? Number(value) : 0);

export const parseEventDateTime = (value?: string | null) => {
  if (!value) {
    return new Date(Number.NaN);
  }

  const normalizedValue = TIMEZONE_PATTERN.test(value)
    ? value
    : `${value}${MANILA_OFFSET_SUFFIX}`;
  return new Date(normalizedValue);
};

export const formatManilaDateTime = (value?: string | null) => {
  const parsed = parseEventDateTime(value);
  if (!Number.isFinite(parsed.getTime())) {
    return "Not set";
  }

  return parsed.toLocaleString("en-PH", {
    timeZone: MANILA_TIMEZONE,
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
};

export const getDerivedAbsenceCutoff = (event: Pick<Event, "start_datetime" | "late_threshold_minutes">) => {
  const start = parseEventDateTime(event.start_datetime);
  return new Date(start.getTime() + clampMinutes(event.late_threshold_minutes) * 60_000);
};

export const getEventWindowStage = (
  event: Pick<
    Event,
    | "start_datetime"
    | "end_datetime"
    | "early_check_in_minutes"
    | "late_threshold_minutes"
    | "sign_out_grace_minutes"
    | "sign_out_override_until"
  >,
  now = new Date()
): EventWindowStage => {
  const start = parseEventDateTime(event.start_datetime);
  const end = parseEventDateTime(event.end_datetime);
  const earlyCheckInOpensAt = new Date(
    start.getTime() - clampMinutes(event.early_check_in_minutes) * 60_000
  );
  const lateThresholdTime = getDerivedAbsenceCutoff(event);
  const normalSignOutClose = new Date(
    end.getTime() + clampMinutes(event.sign_out_grace_minutes) * 60_000
  );
  const overrideUntil = parseEventDateTime(event.sign_out_override_until);
  const hasOverride = Number.isFinite(overrideUntil.getTime());
  const overrideActive = hasOverride && now.getTime() <= overrideUntil.getTime();
  const effectiveSignOutClose = hasOverride
    ? new Date(Math.max(normalSignOutClose.getTime(), overrideUntil.getTime()))
    : normalSignOutClose;

  if (now.getTime() < earlyCheckInOpensAt.getTime()) {
    return "before_check_in";
  }
  if (overrideActive) {
    return "sign_out_open";
  }
  if (now.getTime() < start.getTime()) {
    return "early_check_in";
  }
  if (now.getTime() <= lateThresholdTime.getTime()) {
    return "late_check_in";
  }
  if (now.getTime() < end.getTime()) {
    return "absent_check_in";
  }
  if (now.getTime() <= effectiveSignOutClose.getTime()) {
    return "sign_out_open";
  }
  return "closed";
};

export const getStudentEventActionState = (
  event: Pick<
    Event,
    | "start_datetime"
    | "end_datetime"
    | "early_check_in_minutes"
    | "late_threshold_minutes"
    | "sign_out_grace_minutes"
    | "sign_out_override_until"
  >,
  latestRecord?: Pick<AttendanceRecord, "time_out"> | null,
  now = new Date()
): StudentEventActionState => {
  if (latestRecord?.time_out) {
    return "done";
  }

  const stage = getEventWindowStage(event, now);
  if (latestRecord) {
    if (stage === "sign_out_open") {
      return "sign_out";
    }
    if (stage === "closed") {
      return "closed";
    }
    return "waiting_sign_out";
  }

  if (stage === "before_check_in") {
    return "not_open";
  }
  if (stage === "early_check_in" || stage === "late_check_in" || stage === "absent_check_in") {
    return "sign_in";
  }
  if (stage === "sign_out_open") {
    return "missed_check_in";
  }
  return "closed";
};
