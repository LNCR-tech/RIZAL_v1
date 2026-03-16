import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import SsgFeatureShell from "../components/SsgFeatureShell";
import {
  type Event as EventRecord,
  type EventAttendanceWithStudent,
  type EventStatsResponse,
  fetchEventAttendancesWithStudents,
  fetchEventById,
  fetchEventStats,
  GovernanceContext,
  openSignOutOverride,
} from "../api/eventsApi";
import { useGovernanceWorkspace } from "../hooks/useGovernanceWorkspace";
import {
  formatManilaDateTime,
  getDerivedAbsenceCutoff,
} from "../utils/eventAttendanceWindow";
import { getGovernanceEventsPath } from "../utils/governanceEventPaths";
import { formatEventDepartments, formatEventPrograms } from "../utils/eventScopeLabels";
import "../css/SsgWorkspace.css";
import "../css/SsgFeatureShell.css";

interface GovernanceEventDetailsPageProps {
  unitType: GovernanceContext;
}

const formatDateTime = (datetime: string) => formatManilaDateTime(datetime);

const formatOptionalNumber = (value?: number | null, suffix = "") =>
  value == null ? "Not set" : `${value}${suffix}`;

const GovernanceEventDetailsPage = ({ unitType }: GovernanceEventDetailsPageProps) => {
  const { eventId } = useParams<{ eventId: string }>();
  const parsedEventId = Number(eventId);
  const { hasPermission } = useGovernanceWorkspace(unitType);
  const canViewAttendances = hasPermission("manage_attendance");
  const [overrideLoading, setOverrideLoading] = useState(false);
  const [overrideMessage, setOverrideMessage] = useState<string | null>(null);
  const [eventRecord, setEventRecord] = useState<EventRecord | null>(null);
  const [stats, setStats] = useState<EventStatsResponse | null>(null);
  const [attendees, setAttendees] = useState<EventAttendanceWithStudent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!Number.isFinite(parsedEventId) || parsedEventId <= 0) {
      setError("Invalid event ID.");
      setLoading(false);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setError(null);

    Promise.all([
      fetchEventById(parsedEventId, unitType),
      fetchEventStats(parsedEventId, unitType),
      canViewAttendances
        ? fetchEventAttendancesWithStudents(parsedEventId, unitType)
        : Promise.resolve<EventAttendanceWithStudent[]>([]),
    ])
      .then(([eventDetails, eventStats, attendanceRows]) => {
        if (!isMounted) {
          return;
        }
        setEventRecord(eventDetails);
        setStats(eventStats);
        setAttendees(attendanceRows);
        setOverrideMessage(null);
      })
      .catch((requestError) => {
        if (!isMounted) {
          return;
        }
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Failed to load the event details."
        );
      })
      .finally(() => {
        if (!isMounted) {
          return;
        }
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [canViewAttendances, parsedEventId, unitType]);

  const statCards = useMemo(() => {
    const presentCount = stats?.statuses.present?.count ?? 0;
    const lateCount = stats?.statuses.late?.count ?? 0;
    const absentCount = stats?.statuses.absent?.count ?? 0;

    return [
      {
        label: "Status",
        value: eventRecord?.status ? eventRecord.status.toUpperCase() : "--",
        hint: "Current workflow status for this event",
      },
      {
        label: "Attendance",
        value: stats?.total ?? 0,
        hint: "Recorded attendance entries for this event",
      },
      {
        label: "Present / Late",
        value: `${presentCount} / ${lateCount}`,
        hint: "Current attendance breakdown",
      },
      {
        label: "Absent",
        value: absentCount,
        hint: "Students marked absent for this event",
      },
    ];
  }, [eventRecord?.status, stats]);

  const handleOpenSignOutOverride = async () => {
    if (!eventRecord) {
      return;
    }

    const suggestedMinutes =
      eventRecord.sign_out_grace_minutes != null && eventRecord.sign_out_grace_minutes > 0
        ? `${eventRecord.sign_out_grace_minutes}`
        : "";
    const rawValue = window.prompt(
      "Enter how many minutes sign-out should stay open from now. Leave blank or cancel to keep the scheduled sign-out time.",
      suggestedMinutes
    );

    if (rawValue == null || !rawValue.trim()) {
      setOverrideMessage("Scheduled sign-out timing remains unchanged.");
      return;
    }

    const overrideMinutes = Number(rawValue.trim());
    if (
      !Number.isFinite(overrideMinutes) ||
      !Number.isInteger(overrideMinutes) ||
      overrideMinutes < 1 ||
      overrideMinutes > 1440
    ) {
      setOverrideMessage("Enter a whole number between 1 and 1440 minutes.");
      return;
    }

    try {
      setOverrideLoading(true);
      setOverrideMessage(null);
      const updatedEvent = await openSignOutOverride(
        eventRecord.id,
        overrideMinutes,
        unitType
      );
      setEventRecord(updatedEvent);
      setOverrideMessage(
        `Sign-out override is now open for ${overrideMinutes} minute(s).`
      );
    } catch (requestError) {
      setOverrideMessage(
        requestError instanceof Error
          ? requestError.message
          : "Failed to open the sign-out override."
      );
    } finally {
      setOverrideLoading(false);
    }
  };

  return (
    <SsgFeatureShell
      eyebrow={`${unitType} / Events / Details`}
      title={eventRecord?.name || "Event details"}
      description="Review the full event scope, schedule, location settings, and attendance snapshot for this governance event."
      stats={statCards}
      unitType={unitType}
      actions={
        <Link to={getGovernanceEventsPath(unitType)} className="btn btn-light">
          Back to Events
        </Link>
      }
    >
      {error ? <div className="alert alert-danger mb-0">{error}</div> : null}
      {overrideMessage ? <div className="alert alert-info mb-0">{overrideMessage}</div> : null}

      {loading ? (
        <div className="ssg-feature-empty">Loading event details...</div>
      ) : eventRecord ? (
        <div className="ssg-feature-stack">
          <section className="ssg-feature-card">
            <div className="ssg-feature-card__header">
              <div>
                <h2 className="ssg-feature-card__title">Schedule and venue</h2>
                <p className="ssg-feature-card__subtitle">
                  Core event timing and venue information for this {unitType} event.
                </p>
              </div>
              {canViewAttendances ? (
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => void handleOpenSignOutOverride()}
                  disabled={overrideLoading}
                >
                  {overrideLoading ? "Opening..." : "Open Sign-Out Override"}
                </button>
              ) : null}
            </div>

            <div className="ssg-feature-form-grid">
              <div className="ssg-feature-field">
                <label>Location</label>
                <div className="ssg-muted-note">{eventRecord.location}</div>
              </div>
              <div className="ssg-feature-field">
                <label>Status</label>
                <div className="ssg-muted-note">{eventRecord.status}</div>
              </div>
              <div className="ssg-feature-field">
                <label>Start</label>
                <div className="ssg-muted-note">{formatDateTime(eventRecord.start_datetime)}</div>
              </div>
              <div className="ssg-feature-field">
                <label>End</label>
                <div className="ssg-muted-note">{formatDateTime(eventRecord.end_datetime)}</div>
              </div>
              <div className="ssg-feature-field">
                <label>Early Check-In Window</label>
                <div className="ssg-muted-note">
                  {eventRecord.early_check_in_minutes ?? 0} minute(s)
                </div>
              </div>
              <div className="ssg-feature-field">
                <label>Late Threshold</label>
                <div className="ssg-muted-note">
                  {eventRecord.late_threshold_minutes ?? 0} minute(s)
                </div>
              </div>
              <div className="ssg-feature-field">
                <label>Derived Absence Cutoff</label>
                <div className="ssg-muted-note">
                  {formatDateTime(getDerivedAbsenceCutoff(eventRecord).toISOString())}
                </div>
              </div>
              <div className="ssg-feature-field">
                <label>Sign-Out Window</label>
                <div className="ssg-muted-note">
                  {eventRecord.sign_out_grace_minutes ?? 0} minute(s) after the scheduled end
                </div>
              </div>
              <div className="ssg-feature-field">
                <label>Current Override</label>
                <div className="ssg-muted-note">
                  {eventRecord.sign_out_override_until
                    ? `Open until ${formatDateTime(eventRecord.sign_out_override_until)}`
                    : "No active override"}
                </div>
              </div>
            </div>
          </section>

          <section className="ssg-feature-card">
            <div className="ssg-feature-card__header">
              <div>
                <h2 className="ssg-feature-card__title">Scope</h2>
                <p className="ssg-feature-card__subtitle">
                  Departments and programs included in the event visibility scope.
                </p>
              </div>
            </div>

            <div className="ssg-feature-form-grid">
              <div className="ssg-feature-field">
                <label>Departments</label>
                {eventRecord.departments?.length ? (
                  <div className="ssg-feature-pill-list">
                    {eventRecord.departments.map((department) => (
                      <span key={department.id} className="ssg-feature-pill">
                        {department.name}
                      </span>
                    ))}
                  </div>
                ) : (
                  <div className="ssg-muted-note">{formatEventDepartments(eventRecord.departments)}</div>
                )}
              </div>
              <div className="ssg-feature-field">
                <label>Programs</label>
                {eventRecord.programs?.length ? (
                  <div className="ssg-feature-pill-list">
                    {eventRecord.programs.map((program) => (
                      <span key={program.id} className="ssg-feature-pill">
                        {program.name}
                      </span>
                    ))}
                  </div>
                ) : (
                  <div className="ssg-muted-note">{formatEventPrograms(eventRecord.programs)}</div>
                )}
              </div>
            </div>
          </section>

          <section className="ssg-feature-card">
            <div className="ssg-feature-card__header">
              <div>
                <h2 className="ssg-feature-card__title">Location verification</h2>
                <p className="ssg-feature-card__subtitle">
                  Geofence settings used when students sign in to this event.
                </p>
              </div>
            </div>

            <div className="ssg-feature-form-grid">
              <div className="ssg-feature-field">
                <label>Geofence Required</label>
                <div className="ssg-muted-note">
                  {eventRecord.geo_required ? "Yes, students must be inside the geofence." : "No"}
                </div>
              </div>
              <div className="ssg-feature-field">
                <label>Latitude</label>
                <div className="ssg-muted-note">
                  {formatOptionalNumber(eventRecord.geo_latitude)}
                </div>
              </div>
              <div className="ssg-feature-field">
                <label>Longitude</label>
                <div className="ssg-muted-note">
                  {formatOptionalNumber(eventRecord.geo_longitude)}
                </div>
              </div>
              <div className="ssg-feature-field">
                <label>Radius</label>
                <div className="ssg-muted-note">
                  {formatOptionalNumber(eventRecord.geo_radius_m, " m")}
                </div>
              </div>
              <div className="ssg-feature-field">
                <label>Max Accuracy</label>
                <div className="ssg-muted-note">
                  {formatOptionalNumber(eventRecord.geo_max_accuracy_m, " m")}
                </div>
              </div>
            </div>
          </section>

          <section className="ssg-feature-card">
            <div className="ssg-feature-card__header">
              <div>
                <h2 className="ssg-feature-card__title">Attendance snapshot</h2>
                <p className="ssg-feature-card__subtitle">
                  Current attendance counts recorded for this event.
                </p>
              </div>
            </div>

            <div className="ssg-feature-summary-grid">
              <article className="ssg-feature-summary-card">
                <strong>{stats?.total ?? 0}</strong>
                <span>Total</span>
              </article>
              <article className="ssg-feature-summary-card">
                <strong>{stats?.statuses.present?.count ?? 0}</strong>
                <span>Present</span>
              </article>
              <article className="ssg-feature-summary-card">
                <strong>{stats?.statuses.late?.count ?? 0}</strong>
                <span>Late</span>
              </article>
              <article className="ssg-feature-summary-card">
                <strong>{stats?.statuses.absent?.count ?? 0}</strong>
                <span>Absent</span>
              </article>
              <article className="ssg-feature-summary-card">
                <strong>{stats?.statuses.excused?.count ?? 0}</strong>
                <span>Excused</span>
              </article>
            </div>
          </section>

          <section className="ssg-feature-card">
            <div className="ssg-feature-card__header">
              <div>
                <h2 className="ssg-feature-card__title">Attendance roster</h2>
                <p className="ssg-feature-card__subtitle">
                  Recent attendee records for this event.
                </p>
              </div>
            </div>

            {!canViewAttendances ? (
              <div className="ssg-muted-note">
                Attendance roster access appears when the current officer has
                <strong> manage_attendance</strong>.
              </div>
            ) : attendees.length === 0 ? (
              <div className="ssg-feature-empty">No attendance records are available yet.</div>
            ) : (
              <div className="ssg-feature-table-card">
                <table>
                  <thead>
                    <tr>
                      <th>Student</th>
                      <th>Status</th>
                      <th>Method</th>
                      <th>Time In</th>
                      <th>Time Out</th>
                    </tr>
                  </thead>
                  <tbody>
                    {attendees.map((item) => (
                      <tr key={item.attendance.id}>
                        <td data-label="Student">
                          <strong>{item.student_name}</strong>
                          <div>{item.student_id}</div>
                        </td>
                        <td data-label="Status">
                          <span className="ssg-feature-pill">{item.attendance.status}</span>
                        </td>
                        <td data-label="Method">{item.attendance.method}</td>
                        <td data-label="Time In">{formatDateTime(item.attendance.time_in)}</td>
                        <td data-label="Time Out">
                          {item.attendance.time_out
                            ? formatDateTime(item.attendance.time_out)
                            : "Active / no time out"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      ) : (
        <div className="ssg-feature-empty">Event details are not available.</div>
      )}
    </SsgFeatureShell>
  );
};

export default GovernanceEventDetailsPage;
