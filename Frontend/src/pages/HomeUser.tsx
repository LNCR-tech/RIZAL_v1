import React from "react";
import { NavbarStudent } from "../components/NavbarStudent";
import { NavbarStudentSSG } from "../components/NavbarStudentSSG";
import { NavbarEventOrganizer } from "../components/NavbarEventOrganizer";
import { NavbarStudentSSGEventOrganizer } from "../components/NavbarStudentSSGEventOrganizer";
import { NavbarSSG } from "../components/NavbarSSG";
import NavbarAdmin from "../components/NavbarAdmin";
import DashboardHomeLayout, {
  DashboardCardItem,
} from "../components/DashboardHomeLayout";

// Import colorful icons
import {
  FaCalendarAlt,
  FaCheckCircle,
  FaUsers,
  FaClipboardList,
  FaPlus,
  FaCogs,
  FaChartBar,
  FaSchool,
  FaUserShield,
  FaCamera,
} from "react-icons/fa";

interface HomeUserProps {
  role: string;
}

export const HomeUser: React.FC<HomeUserProps> = ({ role }) => {
  const cardData: Record<string, DashboardCardItem[]> = {
    student: [
      {
        title: "Upcoming Events",
        description: "Stay informed about upcoming school events.",
        icon: <FaCalendarAlt style={{ color: "#007bff" }} />, // Blue color
        link: "/student_upcoming_events",
      },
      {
        title: "Events Attended",
        description: "Check and review the events you've attended.",
        icon: <FaCheckCircle style={{ color: "#28a745" }} />, // Green color
        link: "/student_events_attended",
      },
      {
        title: "Event Sign In",
        description: "Verify your live face and location before attendance.",
        icon: <FaCamera style={{ color: "#162f65" }} />,
        link: "/student_event_checkin",
      },
    ],
    ssg: [
      {
        title: "Events",
        description: "View and manage currently ongoing events.",
        icon: <FaClipboardList style={{ color: "#ffc107" }} />, // Yellow color
        link: "/ssg_events",
      },
      {
        title: "Records",
        description: "Access records and event history.",
        icon: <FaChartBar style={{ color: "#6c757d" }} />, // Gray color
        link: "/ssg_records",
      },
      {
        title: "Manual Attendance",
        description: "Records Attendance.",
        icon: <FaUsers style={{ color: "#6c757d" }} />, // Gray color
        link: "/ssg_manual_attendance",
      },
    ],
    "event-organizer": [
      {
        title: "Create Event",
        description: "Plan and schedule new events.",
        icon: <FaPlus style={{ color: "#007bff" }} />, // Blue color
        link: "/event_organizer_create_event",
      },
      {
        title: "Manage Events",
        description: "Modify, update, or remove existing events.",
        icon: <FaCogs style={{ color: "#6f42c1" }} />, // Purple color
        link: "/event_organizer_manage_event",
      },
    ],
    admin: [
      {
        title: "Manage Schools & SCHOOL_IT",
        description: "Create schools and manage SCHOOL_IT accounts.",
        icon: <FaSchool style={{ color: "#dc3545" }} />, // Red color
        link: "/admin_manage_users",
      },
      {
        title: "Facial Verification",
        description: "Manage live face enrollment and anti-spoof verification for privileged accounts.",
        icon: <FaUserShield style={{ color: "#162f65" }} />,
        link: "/admin_face_verification",
      },
    ],
    "student-ssg": [
      {
        title: "Upcoming Events",
        description: "Stay informed about upcoming school events.",
        icon: <FaCalendarAlt style={{ color: "#007bff" }} />,
        link: "/studentssg_upcoming_events",
      },
      {
        title: "Events Attended",
        description: "Check and review the events you've attended.",
        icon: <FaCheckCircle style={{ color: "#28a745" }} />, // Green color
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
        title: "Manual Attendance",
        description: "Record Attendance",
        icon: <FaUsers style={{ color: "#17a2b8" }} />, // Teal color
        link: "/studentssg_manual_attendance",
      },
      {
        title: "Records",
        description: "Access records and event history.",
        icon: <FaChartBar style={{ color: "#6c757d" }} />, // Gray color
        link: "/studentssg_records",
      },
    ],
    "student-ssg-eventorganizer": [
      {
        title: "Upcoming Events",
        description: "Stay informed about upcoming school events.",
        icon: <FaCalendarAlt style={{ color: "#007bff" }} />,
        link: "/student_ssg_eventorganizer_upcoming_events",
      },
      {
        title: "Events Attended",
        description: "Check and review the events you've attended.",
        icon: <FaCheckCircle style={{ color: "#28a745" }} />, // Green color
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
        description: "Record Attendance.",
        icon: <FaPlus style={{ color: "#17a2b8" }} />, // Teal color
        link: "/student_ssg_eventorganizer_manual_attendance",
      },
      {
        title: "Records",
        description: "Access records and event history.",
        icon: <FaChartBar style={{ color: "#6c757d" }} />, // Gray color
        link: "/student_ssg_eventorganizer_records",
      },
      {
        title: "Create Event",
        description: "Plan and schedule new events.",
        icon: <FaPlus style={{ color: "#007bff" }} />, // Blue color
        link: "/student_ssg_eventorganizer_create_event",
      },
      {
        title: "Manage Events",
        description: "Modify, update, or remove existing events.",
        icon: <FaCogs style={{ color: "#6f42c1" }} />, // Purple color
        link: "/student_ssg_eventorganizer_manage_event",
      },
    ],
  };

  const cards = cardData[role] || cardData.student;
  const titles: Record<string, string> = {
    admin: "Welcome Admin!",
    student: "Welcome Student!",
    ssg: "Welcome SSG!",
    "event-organizer": "Welcome Event Organizer!",
    "student-ssg": "Welcome Student SSG!",
    "student-ssg-eventorganizer": "Welcome Student SSG Event Organizer!",
  };
  const title = titles[role] || "Welcome!";
  const navbar =
    role === "student-ssg-eventorganizer" ? (
      <NavbarStudentSSGEventOrganizer />
    ) : role === "student-ssg" ? (
      <NavbarStudentSSG />
    ) : role === "event-organizer" ? (
      <NavbarEventOrganizer />
    ) : role === "ssg" ? (
      <NavbarSSG />
    ) : role === "student" ? (
      <NavbarStudent />
    ) : role === "admin" ? (
      <NavbarAdmin />
    ) : null;

  return (
    <DashboardHomeLayout
      navbar={navbar}
      title={title}
      description="Your central hub for managing events, tracking attendance, and staying organized."
      cards={cards}
    />
  );
};

export default HomeUser;
