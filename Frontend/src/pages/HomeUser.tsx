import React from "react";
import { NavbarStudent } from "../components/NavbarStudent";
import { NavbarStudentSSG } from "../components/NavbarStudentSSG";
import { NavbarSSG } from "../components/NavbarSSG";
import NavbarAdmin from "../components/NavbarAdmin";
import { useGovernanceAccess } from "../hooks/useGovernanceAccess";
import DashboardHomeLayout, {
  DashboardCardItem,
} from "../components/DashboardHomeLayout";
import {
  FaCalendarAlt,
  FaCheckCircle,
  FaUsers,
  FaClipboardList,
  FaChartBar,
  FaSchool,
  FaUserShield,
  FaCamera,
} from "react-icons/fa";

interface HomeUserProps {
  role: string;
}

export const HomeUser: React.FC<HomeUserProps> = ({ role }) => {
  const isGovernanceAwareRole = role === "ssg" || role === "student-ssg";
  const { hasPermission } = useGovernanceAccess({
    enabled: isGovernanceAwareRole,
  });

  const studentCards: DashboardCardItem[] = [
    {
      title: "Upcoming Events",
      description: "Stay informed about upcoming school events.",
      icon: <FaCalendarAlt style={{ color: "#007bff" }} />,
      link: "/student_upcoming_events",
    },
    {
      title: "Events Attended",
      description: "Check and review the events you've attended.",
      icon: <FaCheckCircle style={{ color: "#28a745" }} />,
      link: "/student_events_attended",
    },
    {
      title: "Event Sign In",
      description: "Verify your live face and location before attendance.",
      icon: <FaCamera style={{ color: "#162f65" }} />,
      link: "/student_event_checkin",
    },
  ];

  const ssgCards: DashboardCardItem[] = [];
  if (hasPermission("manage_events")) {
    ssgCards.push({
      title: "Events",
      description: "View and manage currently ongoing events.",
      icon: <FaClipboardList style={{ color: "#ffc107" }} />,
      link: role === "ssg" ? "/ssg_events" : "/studentssg_events",
    });
  }
  if (hasPermission("manage_attendance")) {
    ssgCards.push(
      {
        title: "Records",
        description: "Access records and event history.",
        icon: <FaChartBar style={{ color: "#6c757d" }} />,
        link: role === "ssg" ? "/ssg_records" : "/studentssg_records",
      },
      {
        title: "Manual Attendance",
        description: "Record attendance for allowed SSG work.",
        icon: <FaUsers style={{ color: "#17a2b8" }} />,
        link:
          role === "ssg"
            ? "/ssg_manual_attendance"
            : "/studentssg_manual_attendance",
      }
    );
  }

  const cardData: Record<string, DashboardCardItem[]> = {
    student: studentCards,
    ssg: ssgCards,
    admin: [
      {
        title: "Manage Schools & Campus Admin",
        description: "Create schools and manage campus admin accounts.",
        icon: <FaSchool style={{ color: "#dc3545" }} />,
        link: "/admin_manage_users",
      },
      {
        title: "Facial Verification",
        description:
          "Manage live face enrollment and anti-spoof verification for privileged accounts.",
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
        icon: <FaCheckCircle style={{ color: "#28a745" }} />,
        link: "/studentssg_events_attended",
      },
      {
        title: "Event Sign In",
        description: "Verify your live face and location before attendance.",
        icon: <FaCamera style={{ color: "#162f65" }} />,
        link: "/student_event_checkin",
      },
      ...ssgCards,
    ],
  };

  const cards = cardData[role] || cardData.student;
  const titles: Record<string, string> = {
    admin: "Welcome Admin!",
    student: "Welcome Student!",
    ssg: "Welcome SSG!",
    "student-ssg": "Welcome Student SSG!",
  };
  const title = titles[role] || "Welcome!";
  const navbar =
    role === "student-ssg" ? (
      <NavbarStudentSSG />
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
