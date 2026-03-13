import React from "react";
import { NavbarAdmin } from "../components/NavbarAdmin";
import DashboardHomeLayout from "../components/DashboardHomeLayout";

// Import colorful icons
import {
  FaSchool,
  FaUserShield,
} from "react-icons/fa";

export const AdminDashboard: React.FC = () => {
  const cards = [
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
  ];

  return (
    <DashboardHomeLayout
      navbar={<NavbarAdmin />}
      title="Welcome Admin!"
      description="Your central hub for creating and managing schools and SCHOOL_IT accounts."
      cards={cards}
    />
  );
};

export default AdminDashboard;
