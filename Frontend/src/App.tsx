import { Suspense, lazy } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import ErrorBoundary from "./components/ErrorBoundary";

const Home = lazy(() => import("./components/Home"));
const Unauthorized = lazy(() => import("./components/Unauthorized"));
const ChangePassword = lazy(() => import("./pages/ChangePassword"));
const FaceLoginChallenge = lazy(() => import("./pages/FaceLoginChallenge"));
const StudentFaceEnrollment = lazy(
  () => import("./pages/StudentFaceEnrollment")
);
const StudentEventCheckIn = lazy(() => import("./pages/StudentEventCheckIn"));
const HomeUser = lazy(() => import("./pages/HomeUser"));
const UpcomingEvents = lazy(() => import("./pages/UpcomingEvents"));
const EventsAttended = lazy(() => import("./pages/EventsAttended"));
const Events = lazy(() => import("./pages/Events"));
const Records = lazy(() => import("./pages/Records"));
const Profile = lazy(() => import("./pages/Profile"));
const Reports = lazy(() => import("./pages/Reports"));
const CreateEvent = lazy(() => import("./pages/CreateEvent"));
const ManageEvent = lazy(() => import("./pages/ManageEvent"));
const FaceScan = lazy(() => import("./pages/FaceScan"));
const ManualAttendance = lazy(() =>
  import("./pages/ManualAttendance").then((module) => ({
    default: module.ManualAttendance,
  }))
);
const AcademicManagement = lazy(() => import("./pages/AcademicManagement"));
const SchoolBrandingSettings = lazy(
  () => import("./pages/SchoolBrandingSettings")
);
const SchoolImportUsers = lazy(() => import("./pages/SchoolImportUsers"));
const SchoolPasswordResetRequests = lazy(
  () => import("./pages/SchoolPasswordResetRequests")
);
const AdminSchoolManagement = lazy(
  () => import("./pages/AdminSchoolManagement")
);
const ManageUsers = lazy(() => import("./pages/ManageUsers"));
const AuditLogs = lazy(() => import("./pages/AuditLogs"));
const NotificationCenter = lazy(() => import("./pages/NotificationCenter"));
const SecurityCenter = lazy(() => import("./pages/SecurityCenter"));
const FacialVerification = lazy(() => import("./pages/FacialVerification"));
const SubscriptionCenter = lazy(() => import("./pages/SubscriptionCenter"));
const DataGovernance = lazy(() => import("./pages/DataGovernance"));
const AdminDashboard = lazy(() => import("./dashboard/AdminDashboard"));
const StudentDashboard = lazy(() => import("./dashboard/StudentDashboard"));
const SSGDashboard = lazy(() => import("./dashboard/SSGDashboard"));
const EventOrganizerDashboard = lazy(
  () => import("./dashboard/EventOrganizerDashboard")
);
const StudentSsgDashboard = lazy(
  () => import("./dashboard/StudentSsgDashboard")
);
const StudentSsgEventOrganizerDashboard = lazy(
  () => import("./dashboard/StudentSsgEventOrganizerDashboard")
);
const SchoolITDashboard = lazy(() => import("./dashboard/SchoolITDashboard"));

const RouteLoader = () => (
  <div className="route-loader" role="status" aria-live="polite">
    <div className="route-loader__spinner" />
    <p>Loading page...</p>
  </div>
);

const App = () => {
  return (
    <ErrorBoundary>
      <Suspense fallback={<RouteLoader />}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Home />} />
          <Route path="/change-password" element={<ChangePassword />} />
          <Route
            path="/auth/face-verification"
            element={<FaceLoginChallenge />}
          />

          <Route element={<ProtectedRoute allowedRoles={["student"]} />}>
            <Route
              path="/student_face_registration"
              element={<StudentFaceEnrollment />}
            />
            <Route
              path="/student_event_checkin"
              element={<StudentEventCheckIn />}
            />
          </Route>

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
            <Route
              path="/admin_notifications"
              element={<NotificationCenter />}
            />
            <Route path="/admin_security" element={<SecurityCenter />} />
            <Route
              path="/admin_face_verification"
              element={<FacialVerification role="admin" />}
            />
            <Route
              path="/admin_subscription"
              element={<SubscriptionCenter />}
            />
            <Route path="/admin_governance" element={<DataGovernance />} />
            <Route path="/admin_profile" element={<Profile role="admin" />} />
          </Route>

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
            <Route
              path="/student_profile"
              element={<Profile role="student" />}
            />
          </Route>

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
            <Route
              path="/school_it_branding"
              element={<SchoolBrandingSettings />}
            />
            <Route
              path="/school_it_import_users"
              element={<SchoolImportUsers />}
            />
            <Route
              path="/school_it_password_resets"
              element={<SchoolPasswordResetRequests />}
            />
            <Route path="/school_it_manage_users" element={<ManageUsers />} />
            <Route path="/school_it_audit_logs" element={<AuditLogs />} />
            <Route
              path="/school_it_notifications"
              element={<NotificationCenter />}
            />
            <Route path="/school_it_security" element={<SecurityCenter />} />
            <Route
              path="/school_it_face_verification"
              element={<FacialVerification role="school_IT" />}
            />
            <Route
              path="/school_it_subscription"
              element={<SubscriptionCenter />}
            />
            <Route path="/school_it_governance" element={<DataGovernance />} />
            <Route
              path="/school_it_profile"
              element={<Profile role="school_IT" />}
            />
          </Route>

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

          <Route path="/unauthorized" element={<Unauthorized />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </ErrorBoundary>
  );
};

export default App;
