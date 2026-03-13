import { NavbarStudentSSG } from "../components/NavbarStudentSSG";
import DashboardHomeLayout from "../components/DashboardHomeLayout";

// Import colorful icons
import {
  FaCalendarAlt,
  FaCamera,
  FaCheckCircle,
  FaClipboardList,
  FaChartBar,
  FaPlus,
} from "react-icons/fa";

export const StudentSsgDashboard = () => {
  // Student-SSG card data with colorful icons - matching HomeUser exactly
  const studentSsgCards = [
    {
      title: "Upcoming Events",
      description: "Stay informed about upcoming school events.",
      icon: <FaCalendarAlt style={{ color: "#007bff" }} />,
      link: "/studentssg_upcoming_events",
    },
    {
      title: "Events Attended",
      description: "Check and review the events you've attended.",
      icon: <FaCheckCircle style={{ color: "#28a745" }} />,
      link: "/studentssg_events_attended",
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
      link: "/studentssg_events",
    },
    {
      title: "Records",
      description: "Access records and event history.",
      icon: <FaChartBar style={{ color: "#6c757d" }} />,
      link: "/studentssg_records",
    },
    {
      title: "Manual Attendance",
      description: "Record Attendance",
      icon: <FaPlus style={{ color: "#17a2b8" }} />, // Teal color
      link: "/studentssg_manual_attendance",
    },
  ];

  return (
    <DashboardHomeLayout
      navbar={<NavbarStudentSSG />}
      title="Welcome Student SSG!"
      description="Your central hub for managing events, tracking attendance, and staying organized."
      cards={studentSsgCards}
    />
  );
};

export default StudentSsgDashboard;
