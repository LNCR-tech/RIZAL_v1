import { NavbarStudentSSGEventOrganizer } from "../components/NavbarStudentSSGEventOrganizer";
import DashboardHomeLayout from "../components/DashboardHomeLayout";

// Import colorful icons
import {
  FaCalendarAlt,
  FaCamera,
  FaCheckCircle,
  FaUsers,
  FaClipboardList,
  FaPlus,
  FaCogs,
  FaChartBar,
} from "react-icons/fa";

const StudentSsgEventDashboard = () => {
  // Student-SSG-EventOrganizer card data - matching HomeUser exactly
  const studentSsgEventOrganizerCards = [
    {
      title: "Upcoming Events",
      description: "Stay informed about upcoming school events.",
      icon: <FaCalendarAlt style={{ color: "#007bff" }} />,
      link: "/student_ssg_eventorganizer_upcoming_events",
    },
    {
      title: "Events Attended",
      description: "Check and review the events you've attended.",
      icon: <FaCheckCircle style={{ color: "#28a745" }} />,
      link: "/student_ssg_eventorganizer_events_attended",
    },
    {
      title: "Event Sign In",
      description: "Verify your live face and location before attendance.",
      icon: <FaCamera style={{ color: "#162f65" }} />,
      link: "/student_event_checkin",
    },
    {
      title: "Events",
      description: "View and manage currently ongoing events.",
      icon: <FaClipboardList style={{ color: "#ffc107" }} />,
      link: "/student_ssg_eventorganizer_events",
    },
    {
      title: "Manual Attendance",
      description: "Record Attendance",
      icon: <FaUsers style={{ color: "#17a2b8" }} />,
      link: "/student_ssg_eventorganizer_manual_attendance",
    },
    {
      title: "Records",
      description: "Access records and event history.",
      icon: <FaChartBar style={{ color: "#6c757d" }} />,
      link: "/student_ssg_eventorganizer_records",
    },
    {
      title: "Create Event",
      description: "Plan and schedule new events.",
      icon: <FaPlus style={{ color: "#007bff" }} />,
      link: "/student_ssg_eventorganizer_create_event",
    },
    {
      title: "Manage Events",
      description: "Modify, update, or remove existing events.",
      icon: <FaCogs style={{ color: "#6f42c1" }} />,
      link: "/student_ssg_eventorganizer_manage_event",
    },
  ];

  return (
    <DashboardHomeLayout
      navbar={<NavbarStudentSSGEventOrganizer />}
      title="Welcome Student SSG Event Organizer!"
      description="Your central hub for managing events, tracking attendance, and staying organized."
      cards={studentSsgEventOrganizerCards}
    />
  );
};

export default StudentSsgEventDashboard;
