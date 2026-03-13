import { useEffect, useState } from "react";
import { FaSearch } from "react-icons/fa";
import { fetchMyAttendanceRecords, type AttendanceRecord } from "../api/eventsApi";
import { NavbarStudent } from "../components/NavbarStudent";
import { NavbarStudentSSG } from "../components/NavbarStudentSSG";
import { NavbarStudentSSGEventOrganizer } from "../components/NavbarStudentSSGEventOrganizer";

interface EventsAttendedProps {
  role: string;
}

const getStatusLabel = (status: AttendanceRecord["status"]) => {
  switch (status) {
    case "present":
      return "Present";
    case "late":
      return "Late";
    case "absent":
      return "Absent";
    case "excused":
      return "Excused";
    default:
      return status;
  }
};

export const EventsAttended: React.FC<EventsAttendedProps> = ({ role }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    const fetchMyAttendance = async () => {
      setIsLoading(true);
      try {
        const data = await fetchMyAttendanceRecords();
        setRecords(data);
      } catch (error) {
        console.error("Error fetching attendance records:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMyAttendance();
  }, []);

  const formatDate = (datetime: string) => {
    return new Date(datetime).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const formatTime = (datetime: string) => {
    return new Date(datetime).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const filteredRecords = records.filter((record) =>
    record.event_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="events-attended">
      {role === "student-ssg" ? (
        <NavbarStudentSSG />
      ) : role === "student-ssg-eventorganizer" ? (
        <NavbarStudentSSGEventOrganizer />
      ) : (
        <NavbarStudent />
      )}

      <div className="container">
        <div className="header">
          <h2>My Attendance Records</h2>
          <p>View your event attendance history</p>
        </div>

        <div className="search-box">
          <FaSearch className="search-icon" />
          <input
            type="text"
            placeholder="Search events..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="records-table">
          <table>
            <thead>
              <tr>
                <th>Event</th>
                <th>Date</th>
                <th>Time In</th>
                <th>Time Out</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="loading">
                    Loading your attendance records...
                  </td>
                </tr>
              ) : filteredRecords.length > 0 ? (
                filteredRecords.map((record) => (
                  <tr key={record.id}>
                    <td>{record.event_name}</td>
                    <td>{formatDate(record.time_in)}</td>
                    <td>{formatTime(record.time_in)}</td>
                    <td>{record.time_out ? formatTime(record.time_out) : "-"}</td>
                    <td>
                      <span className={`status ${record.status}`}>
                        {getStatusLabel(record.status)}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="no-results">
                    {searchTerm
                      ? "No matching records found"
                      : "No attendance records available"}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <style>{`
        .events-attended {
          font-family: Arial, sans-serif;
          max-width: 1200px;
          margin: 0 auto;
          padding: 20px;
        }

        .container {
          margin-top: 20px;
        }

        .header {
          margin-bottom: 20px;
        }

        .header h2 {
          margin: 0;
          font-size: 24px;
          color: var(--primary-color, #162F65);
        }

        .header p {
          margin: 5px 0 0;
          color: var(--secondary-color, #2C5F9E);
        }

        .search-box {
          position: relative;
          margin-bottom: 20px;
          max-width: 400px;
        }

        .search-icon {
          position: absolute;
          left: 10px;
          top: 50%;
          transform: translateY(-50%);
          color: var(--secondary-color, #2C5F9E);
        }

        .search-box input {
          width: 100%;
          padding: 10px 15px 10px 35px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 16px;
        }

        .records-table {
          overflow-x: auto;
        }

        table {
          width: 100%;
          border-collapse: collapse;
          margin-top: 10px;
        }

        th,
        td {
          padding: 12px 15px;
          text-align: left;
          border-bottom: 1px solid #eee;
        }

        th {
          background-color: #f8f9fa;
          font-weight: 600;
        }

        tr:hover {
          background-color: #f5f5f5;
        }

        .status {
          padding: 5px 10px;
          border-radius: 4px;
          font-weight: 500;
        }

        .status.present {
          background-color: #eef6ff;
          color: var(--primary-color, #162F65);
        }

        .status.late {
          background-color: #fff4e5;
          color: #9a6700;
        }

        .status.absent {
          background-color: #ffebee;
          color: #c62828;
        }

        .status.excused {
          background-color: #f0f8ff;
          color: var(--secondary-color, #2C5F9E);
        }

        .loading,
        .no-results {
          text-align: center;
          padding: 20px;
          color: #666;
        }

        @media (max-width: 768px) {
          th,
          td {
            padding: 8px 10px;
            font-size: 14px;
          }
        }
      `}</style>
    </div>
  );
};

export default EventsAttended;
