import { useState } from "react";
import { NavLink } from "react-router-dom";
import {
  FaHome,
  FaCalendarAlt,
  FaClipboardCheck,
  FaRegListAlt,
  FaClipboard,
  FaBars,
  FaTimes,
  FaThList,
  FaUserCheck,
} from "react-icons/fa";
import logoValid8 from "../assets/images/logo-valid83.webp";
import userprofile from "../assets/images/userprofile.png";
import { useRoleSidebarLayout } from "../hooks/useRoleSidebarLayout";
import { useGovernanceAccess } from "../hooks/useGovernanceAccess";
import "../css/NavbarStudentSSG.css";

export const NavbarStudentSSG = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const { hasPermission, loading } = useGovernanceAccess();

  useRoleSidebarLayout({ isExpanded, sidebarOpen });

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  const navLinks = [
    {
      path: "/studentssg_home",
      icon: <FaHome />,
      text: "Home",
      visible: true,
    },
    {
      path: "/studentssg_upcoming_events",
      icon: <FaCalendarAlt />,
      text: "Upcoming Events",
      visible: true,
    },
    {
      path: "/student_event_checkin",
      icon: <FaUserCheck />,
      text: "Event Sign In",
      visible: true,
    },
    {
      path: "/studentssg_events_attended",
      icon: <FaClipboardCheck />,
      text: "Events Attended",
      visible: true,
    },
    {
      path: "/studentssg_events",
      icon: <FaRegListAlt />,
      text: "Events",
      visible: hasPermission("manage_events"),
    },
    {
      path: "/studentssg_records",
      icon: <FaClipboard />,
      text: "Records",
      visible: hasPermission("manage_attendance"),
    },
    {
      path: "/studentssg_manual_attendance",
      icon: <FaUserCheck />,
      text: "Manual Attendance",
      visible: hasPermission("manage_attendance"),
    },
  ].filter((item) => item.visible);

  const hasGovernanceFeatures = navLinks.some((item) =>
    ["/studentssg_events", "/studentssg_records", "/studentssg_manual_attendance"].includes(item.path)
  );

  return (
    <>
      {/* Hamburger Icon - Only shows when sidebar is closed */}
      {!sidebarOpen && (
        <div className="ssg-hamburger" onClick={toggleSidebar}>
          <FaBars />
        </div>
      )}

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={toggleSidebar}></div>
      )}

      {/* Sidebar */}
      <div
        className={`ssg-sidebar ${sidebarOpen ? "open" : ""} ${
          isExpanded ? "expanded" : "collapsed"
        }`}
      >
        {/* Header with Logo, Title, and Close Button */}
        <div className="ssg-sidebar-header">
          <div className="header-content-wrapper">
            <img src={logoValid8} alt="Valid 8 logo" className="sidebar-logo" />
            <h1 className="ssg-title">
              Student
              <br />
              Officer
            </h1>
          </div>
          {sidebarOpen && (
            <button className="sidebar-close-btn" onClick={toggleSidebar}>
              <FaTimes />
            </button>
          )}
        </div>

        {/* Navigation Links */}
        <nav className="ssg-nav">
          <ul className="ssg-nav-menu">
            {/* Menu Toggle Button */}
            <li className="menu-toggle-item">
              <button
                className="ssg-nav-link menu-toggle-btn"
                onClick={toggleExpand}
                title={isExpanded ? "Collapse menu" : "Expand menu"}
              >
                <FaThList className="nav-icon" />
                <span className="nav-text">Menu</span>
              </button>
            </li>
            {navLinks.map((item) => (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  className={({ isActive }) =>
                    isActive ? "ssg-nav-link active" : "ssg-nav-link"
                  }
                  onClick={() => setSidebarOpen(false)}
                  title={item.text}
                >
                  <div className="nav-icon">{item.icon}</div>
                  <span className="nav-text">{item.text}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        {!loading && !hasGovernanceFeatures && (
          <div className="px-3 pb-3 text-light small">
            No SSG governance features are assigned yet. Ask Campus Admin to grant permissions.
          </div>
        )}

        {/* User Profile Section */}
        <div className="ssg-sidebar-footer">
          <NavLink
            to="/studentssg_profile"
            className={({ isActive }) =>
              isActive ? "ssg-profile-link active" : "ssg-profile-link"
            }
            onClick={() => setSidebarOpen(false)}
            title="Profile"
          >
            <img
              src={userprofile}
              alt="user profile"
              className="ssg-profile-img"
            />
            <span className="profile-text">Profile</span>
          </NavLink>
        </div>
      </div>

      {/* Main Content Area */}
      <div
        className={`ssg-content ${sidebarOpen ? "shifted" : ""} ${
          isExpanded ? "content-expanded" : "content-collapsed"
        }`}
      ></div>
    </>
  );
};

export default NavbarStudentSSG;
