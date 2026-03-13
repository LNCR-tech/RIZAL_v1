import React from "react";
import { NavbarEventOrganizer } from "../components/NavbarEventOrganizer";
import DashboardHomeLayout from "../components/DashboardHomeLayout";

// Import colorful icons
import { FaPlus, FaCogs } from "react-icons/fa";

export const EventOrganizerDashboard: React.FC = () => {
  const cards = [
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
  ];

  return (
    <DashboardHomeLayout
      navbar={<NavbarEventOrganizer />}
      title="Welcome Event Organizer!"
      description="Your central hub for managing events, tracking attendance, and staying organized."
      cards={cards}
    />
  );
};

export default EventOrganizerDashboard;
