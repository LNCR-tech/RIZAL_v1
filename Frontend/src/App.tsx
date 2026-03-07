import { Routes, Route, Navigate } from "react-router-dom";
import Home from "./components/Home";
import ProtectedRoute from "./components/ProtectedRoute";
import AdminDashboard from "./dashboard/AdminDashboard";
import StudentDashboard from "./dashboard/StudentDashboard";
import SSGDashboard from "./dashboard/SSGDashboard";
import EventOrganizerDashboard from "./dashboard/EventOrganizerDashboard";
import { StudentSsgDashboard } from "./dashboard/StudentSsgDashboard";
import StudentSsgEventOrganizerDashboard from "./dashboard/StudentSsgEventOrganizerDashboard";
import HomeUser from "./pages/HomeUser";
import { UpcomingEvents } from "./pages/UpcomingEvents";
import { EventsAttended } from "./pages/EventsAttended";
import { Events } from "./pages/Events";
import { Records } from "./pages/Records";
import { Profile } from "./pages/Profile";
import Reports from "./pages/Reports";
import { CreateEvent } from "./pages/CreateEvent";
import { ManageEvent } from "./pages/ManageEvent";
import Unauthorized from "./components/Unauthorized"; // Import Unauthorized Page
import ErrorBoundary from "../src/components/ErrorBoundary";
import FaceScan from "../src/pages/FaceScan";
import { ManualAttendance } from "../src/pages/ManualAttendance";
import AcademicManagement from "../src/pages/AcademicManagement";
import SchoolITDashboard from "./dashboard/SchoolITDashboard";
import SchoolBrandingSettings from "./pages/SchoolBrandingSettings";
import SchoolImportUsers from "./pages/SchoolImportUsers";
import SchoolPasswordResetRequests from "./pages/SchoolPasswordResetRequests";
import ChangePassword from "./pages/ChangePassword";
import AdminSchoolManagement from "./pages/AdminSchoolManagement";
import ManageUsers from "./pages/ManageUsers";
import AuditLogs from "./pages/AuditLogs";
import NotificationCenter from "./pages/NotificationCenter";
import SecurityCenter from "./pages/SecurityCenter";
import SubscriptionCenter from "./pages/SubscriptionCenter";
import DataGovernance from "./pages/DataGovernance";

const App = () => {
  return (
    <ErrorBoundary>
      <Routes>
        {/* Public Route */}
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Home />} />
        <Route path="/change-password" element={<ChangePassword />} />

        {/* Admin Routes */}
        <Route element={<ProtectedRoute allowedRoles={["admin"]} />}>
          <Route path="/admin_dashboard" element={<AdminDashboard />} />
          <Route path="/admin_home" element={<HomeUser role="admin" />} />
          <Route path="/admin_reports" element={<Reports />} />
          <Route
            path="/admin_manage_users"
            element={
              <ErrorBoundary>
                <AdminSchoolManagement />
              </ErrorBoundary>
            }
          />
          <Route
            path="/admin_school_management"
            element={<Navigate to="/admin_manage_users" replace />}
          />
          <Route path="/admin_audit_logs" element={<AuditLogs />} />
          <Route path="/admin_notifications" element={<NotificationCenter />} />
          <Route path="/admin_security" element={<SecurityCenter />} />
          <Route path="/admin_subscription" element={<SubscriptionCenter />} />
          <Route path="/admin_governance" element={<DataGovernance />} />
          <Route path="/admin_profile" element={<Profile role="admin" />} />
        </Route>

        {/* Student Routes */}
        <Route element={<ProtectedRoute allowedRoles={["student"]} />}>
          <Route path="/student_dashboard" element={<StudentDashboard />} />
          <Route path="/student_home" element={<HomeUser role="student" />} />
          <Route
            path="/student_upcoming_events"
            element={<UpcomingEvents role="student" />}
          />
          <Route
            path="/student_events_attended"
            element={<EventsAttended role="student" />}
          />
          <Route path="/student_profile" element={<Profile role="student" />} />
        </Route>

        {/* School IT Routes */}
        <Route element={<ProtectedRoute allowedRoles={["school_IT"]} />}>
          <Route path="/school_it_dashboard" element={<SchoolITDashboard />} />
          <Route path="/school_it_home" element={<SchoolITDashboard />} />
          <Route path="/school_it_events" element={<Events role="school_IT" />} />
          <Route
            path="/school_it_create_department_program"
            element={
              <ErrorBoundary>
                <AcademicManagement role="school_IT" />
              </ErrorBoundary>
            }
          />
          <Route path="/school_it_branding" element={<SchoolBrandingSettings />} />
          <Route path="/school_it_import_users" element={<SchoolImportUsers />} />
          <Route path="/school_it_password_resets" element={<SchoolPasswordResetRequests />} />
          <Route path="/school_it_manage_users" element={<ManageUsers />} />
          <Route path="/school_it_audit_logs" element={<AuditLogs />} />
          <Route path="/school_it_notifications" element={<NotificationCenter />} />
          <Route path="/school_it_security" element={<SecurityCenter />} />
          <Route path="/school_it_subscription" element={<SubscriptionCenter />} />
          <Route path="/school_it_governance" element={<DataGovernance />} />
          <Route path="/school_it_profile" element={<Profile role="school_IT" />} />
        </Route>

        {/* SSG Routes */}
        <Route element={<ProtectedRoute allowedRoles={["ssg"]} />}>
          <Route path="/ssg_dashboard" element={<SSGDashboard />} />
          <Route path="/ssg_home" element={<HomeUser role="ssg" />} />
          <Route path="/ssg_events" element={<Events role="ssg" />} />
          <Route path="/ssg_records" element={<Records role="ssg" />} />
          <Route
            path="/ssg_manual_attendance"
            element={<ManualAttendance role="ssg" />}
          />
          <Route path="/ssg_profile" element={<Profile role="ssg" />} />
        </Route>

        {/* Event Organizer Routes */}
        <Route element={<ProtectedRoute allowedRoles={["event-organizer"]} />}>
          <Route
            path="/event_organizer_dashboard"
            element={<EventOrganizerDashboard />}
          />
          <Route
            path="/event_organizer_home"
            element={<HomeUser role="event-organizer" />}
          />
          <Route
            path="/event_organizer_create_event"
            element={<CreateEvent role="event-organizer" />}
          />
          <Route
            path="/event_organizer_manage_event"
            element={<ManageEvent role="event-organizer" />}
          />
          <Route
            path="/event_organizer_profile"
            element={<Profile role="event-organizer" />}
          />
        </Route>

        {/* Student + SSG Routes */}
        <Route element={<ProtectedRoute allowedRoles={["student", "ssg"]} />}>
          <Route
            path="/student_ssg_dashboard"
            element={<StudentSsgDashboard />}
          />
          <Route
            path="/studentssg_home"
            element={<HomeUser role="student-ssg" />}
          />
          <Route
            path="/studentssg_upcoming_events"
            element={<UpcomingEvents role="student-ssg" />}
          />
          <Route
            path="/studentssg_events_attended"
            element={<EventsAttended role="student-ssg" />}
          />
          <Route
            path="/studentssg_events"
            element={<Events role="student-ssg" />}
          />
          <Route
            path="/studentssg_attendance"
            element={<ManualAttendance role="student-ssg" />}
          />
          <Route
            path="/studentssg_records"
            element={<Records role="student-ssg" />}
          />
          <Route
            path="/studentssg_face_scan"
            element={<FaceScan role="student-ssg" />}
          />
          <Route
            path="/studentssg_manual_attendance"
            element={<ManualAttendance role="student-ssg" />}
          />
          <Route
            path="/studentssg_profile"
            element={<Profile role="student-ssg" />}
          />
        </Route>

        {/* Student + SSG + Event Organizer Routes */}
        <Route
          element={
            <ProtectedRoute
              allowedRoles={["student", "ssg", "event-organizer"]}
            />
          }
        >
          <Route
            path="/student_ssg_eventorganizer_dashboard"
            element={<StudentSsgEventOrganizerDashboard />}
          />

          <Route
            path="/student_ssg_eventorganizer_home"
            element={<HomeUser role="student-ssg-eventorganizer" />}
          />
          <Route
            path="/student_ssg_eventorganizer_upcoming_events"
            element={<UpcomingEvents role="student-ssg-eventorganizer" />}
          />
          <Route
            path="/student_ssg_eventorganizer_events_attended"
            element={<EventsAttended role="student-ssg-eventorganizer" />}
          />
          <Route
            path="/student_ssg_eventorganizer_events"
            element={<Events role="student-ssg-eventorganizer" />}
          />
          <Route
            path="/student_ssg_eventorganizer_manual_attendance"
            element={<ManualAttendance role="student-ssg-eventorganizer" />}
          />
          <Route
            path="/student_ssg_eventorganizer_records"
            element={<Records role="student-ssg-eventorganizer" />}
          />

          <Route
            path="/student_ssg_eventorganizer_create_event"
            element={<CreateEvent role="student-ssg-eventorganizer" />}
          />
          <Route
            path="/student_ssg_eventorganizer_manage_event"
            element={<ManageEvent role="student-ssg-eventorganizer" />}
          />
          <Route
            path="/student_ssg_eventorganizer_profile"
            element={<Profile role="student-ssg-eventorganizer" />}
          />
        </Route>

        {/* Unauthorized Page (Accessible to Everyone) */}
        <Route path="/unauthorized" element={<Unauthorized />} />

        {/* Catch-all Route: Redirects undefined routes to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </ErrorBoundary>
  );
};

export default App;
