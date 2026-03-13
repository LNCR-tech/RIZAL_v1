import React from "react";
import { NavbarSSG } from "../components/NavbarSSG";
import DashboardHomeLayout from "../components/DashboardHomeLayout";

// Import colorful icons
import { FaClipboardList, FaUsers, FaChartBar } from "react-icons/fa";

export const SSGDashboard: React.FC = () => {
  const cards = [
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
  ];

  return (
    <DashboardHomeLayout
      navbar={<NavbarSSG />}
      title="Welcome SSG!"
      description="Your central hub for managing events, tracking attendance, and staying organized."
      cards={cards}
    />
  );
};

export default SSGDashboard;
