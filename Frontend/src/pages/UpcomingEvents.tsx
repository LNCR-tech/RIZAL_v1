import { useDeferredValue, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { NavbarStudent } from "../components/NavbarStudent";
import { NavbarStudentSSG } from "../components/NavbarStudentSSG";
import { NavbarStudentSSGEventOrganizer } from "../components/NavbarStudentSSGEventOrganizer";
import { FaArrowRight, FaSearch } from "react-icons/fa";
import {
  fetchEventsByStatus,
  fetchMyAttendanceRecords,
  type AttendanceRecord,
  type Event,
} from "../api/eventsApi";
import "../css/UpcomingEvents.css";

interface UpcomingEventsProps {
  role: string;
}

type Department = NonNullable<Event["departments"]>[number];
type Program = NonNullable<Event["programs"]>[number];
type AttendanceActionState = "sign_in" | "sign_out" | "done";

export const UpcomingEvents: React.FC<UpcomingEventsProps> = ({ role }) => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState("");
  const [events, setEvents] = useState<Event[]>([]);
  const [attendanceRecords, setAttendanceRecords] = useState<AttendanceRecord[]>(
    []
  );
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const deferredSearchTerm = useDeferredValue(searchTerm);

  useEffect(() => {
    const loadEvents = async () => {
      setIsLoading(true);
      try {
        const [ongoingEvents, upcomingEvents, myAttendanceRecords] =
          await Promise.all([
          fetchEventsByStatus("ongoing"),
          fetchEventsByStatus("upcoming"),
          fetchMyAttendanceRecords(),
        ]);

        const mergedEvents = [...ongoingEvents, ...upcomingEvents].sort(
          (left, right) => {
            if (left.status !== right.status) {
              return left.status === "ongoing" ? -1 : 1;
            }

            return (
              new Date(left.start_datetime).getTime() -
              new Date(right.start_datetime).getTime()
            );
          }
        );

        setEvents(mergedEvents);
        setAttendanceRecords(myAttendanceRecords);
      } catch (error) {
        console.error("Error fetching events:", error);
      } finally {
        setIsLoading(false);
      }
    };

    loadEvents();
  }, []);

  const latestAttendanceByEvent = useMemo(() => {
    const recordsByEvent = new Map<number, AttendanceRecord>();

    for (const record of attendanceRecords) {
      const existing = recordsByEvent.get(record.event_id);
      if (!existing) {
        recordsByEvent.set(record.event_id, record);
        continue;
      }

      if (
        new Date(record.time_in).getTime() > new Date(existing.time_in).getTime()
      ) {
        recordsByEvent.set(record.event_id, record);
      }
    }

    return recordsByEvent;
  }, [attendanceRecords]);

  const formatDateTime = (datetime: string) => {
    const date = new Date(datetime);
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatDepartments = (departments?: Department[]) => {
    const safeDepartments = departments ?? [];
    return safeDepartments.map((d) => d.name).join(", ") || "N/A";
  };

  const formatPrograms = (programs?: Program[]) => {
    const safePrograms = programs ?? [];
    return safePrograms.map((p) => p.name).join(", ") || "N/A";
  };

  const hasGeofence = (event: Event) =>
    event.geo_latitude != null &&
    event.geo_longitude != null &&
    event.geo_radius_m != null;

  const filteredEvents = events.filter(
    (event) =>
      event.name.toLowerCase().includes(deferredSearchTerm.toLowerCase())
  );

  const getAttendanceActionState = (event: Event): AttendanceActionState => {
    const latestRecord = latestAttendanceByEvent.get(event.id);
    if (!latestRecord) {
      return "sign_in";
    }

    if (latestRecord.time_out) {
      return "done";
    }

    return "sign_out";
  };

  return (
    <div className="upcoming-page">
      {role === "student-ssg" ? (
        <NavbarStudentSSG />
      ) : role === "student-ssg-eventorganizer" ? (
        <NavbarStudentSSGEventOrganizer />
      ) : (
        <NavbarStudent />
      )}

      <div className="upcoming-container">
        <div className="upcoming-header">
          <h2>Upcoming Events</h2>
          <p className="subtitle">View upcoming and ongoing events</p>
        </div>

        <div className="search-filter-section">
          <div className="search-box">
            <FaSearch className="search-icon" />
            <input
              type="text"
              placeholder="Search events..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>
        </div>

        <div className="table-responsive">
          <table className="upcoming-table">
            <thead>
              <tr>
                <th>Event Name</th>
                <th>Department(s)</th>
                <th>Program(s)</th>
                <th>Date & Time</th>
                <th>Location</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={7}>Loading events...</td>
                </tr>
              ) : filteredEvents.length > 0 ? (
                filteredEvents.map((event) => (
                  <tr key={event.id}>
                    <td data-label="Event Name">{event.name}</td>
                    <td data-label="Department(s)">
                      {formatDepartments(event.departments)}
                    </td>
                    <td data-label="Program(s)">
                      {formatPrograms(event.programs)}
                    </td>
                    <td data-label="Date & Time">
                      {formatDateTime(event.start_datetime)} -{" "}
                      {formatDateTime(event.end_datetime)}
                    </td>
                    <td data-label="Location">{event.location}</td>
                    <td data-label="Status">
                      <span className={`status-badge ${event.status}`}>
                        {event.status.charAt(0).toUpperCase() +
                          event.status.slice(1)}
                      </span>
                    </td>
                    <td data-label="Action">
                      {event.status === "ongoing" ? (
                        hasGeofence(event) ? (
                          getAttendanceActionState(event) === "done" ? (
                            <span className="upcoming-action-placeholder">
                              Done
                            </span>
                          ) : (
                            <button
                              type="button"
                              className="upcoming-action-button"
                              onClick={() =>
                                navigate(
                                  `/student_event_checkin?eventId=${event.id}`
                                )
                              }
                            >
                              <FaArrowRight />
                              {getAttendanceActionState(event) === "sign_out"
                                ? "Sign Out"
                                : "Sign In"}
                            </button>
                          )
                        ) : (
                          <button
                            type="button"
                            className="upcoming-action-button"
                            disabled
                          >
                            <FaArrowRight />
                            Unavailable
                          </button>
                        )
                      ) : (
                        <span className="upcoming-action-placeholder">
                          Opens when ongoing
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="no-results">
                    No upcoming or ongoing events found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default UpcomingEvents;
