import { useMemo, useState } from "react";
import { NavLink } from "react-router-dom";
import {
  FaBars,
  FaBullhorn,
  FaChartPie,
  FaClipboard,
  FaRegListAlt,
  FaSitemap,
  FaThList,
  FaTimes,
  FaUserCheck,
  FaUserGraduate,
} from "react-icons/fa";

import logoValid8 from "../assets/images/logo-valid83.webp";
import userprofile from "../assets/images/userprofile.png";
import {
  GovernancePermissionCode,
  GovernanceUnitType,
} from "../api/governanceHierarchyApi";
import { useGovernanceWorkspace } from "../hooks/useGovernanceWorkspace";
import { useRoleSidebarLayout } from "../hooks/useRoleSidebarLayout";
import "../css/NavbarSSG.css";

const SIDEBAR_CONFIG: Record<
  GovernanceUnitType,
  {
    dashboardPath: string;
    announcementsPath: string;
    studentsPath: string;
    eventsPath: string;
    recordsPath: string;
    manualAttendancePath: string;
    profilePath: string;
    managePath?: string;
    manageLabel?: string;
    manageVisibility?: (
      hasPermission: (permission: GovernancePermissionCode) => boolean
    ) => boolean;
  }
> = {
  SSG: {
    dashboardPath: "/ssg_dashboard",
    announcementsPath: "/ssg_announcements",
    studentsPath: "/ssg_students",
    eventsPath: "/ssg_events",
    recordsPath: "/ssg_records",
    manualAttendancePath: "/ssg_manual_attendance",
    profilePath: "/ssg_profile",
    managePath: "/ssg_manage_sg",
    manageLabel: "Manage SG",
    manageVisibility: (hasPermission) =>
      hasPermission("create_sg") || hasPermission("manage_members") || hasPermission("assign_permissions"),
  },
  SG: {
    dashboardPath: "/sg_dashboard",
    announcementsPath: "/sg_announcements",
    studentsPath: "/sg_students",
    eventsPath: "/sg_events",
    recordsPath: "/sg_records",
    manualAttendancePath: "/sg_manual_attendance",
    profilePath: "/sg_profile",
    managePath: "/sg_manage_org",
    manageLabel: "Manage ORG",
    manageVisibility: (hasPermission) =>
      hasPermission("create_org") || hasPermission("manage_members") || hasPermission("assign_permissions"),
  },
  ORG: {
    dashboardPath: "/org_dashboard",
    announcementsPath: "/org_announcements",
    studentsPath: "/org_students",
    eventsPath: "/org_events",
    recordsPath: "/org_records",
    manualAttendancePath: "/org_manual_attendance",
    profilePath: "/org_profile",
  },
};

interface GovernanceSidebarProps {
  unitType: GovernanceUnitType;
}

export const GovernanceSidebar = ({ unitType }: GovernanceSidebarProps) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const {
    accessLoading,
    campusName,
    hasPermission,
    logoUrl,
    officerName,
    officerPosition,
    accessUnit,
    governanceUnit,
    fallbackUnitLabel,
  } = useGovernanceWorkspace(unitType);
  const config = SIDEBAR_CONFIG[unitType];

  useRoleSidebarLayout({ isExpanded, sidebarOpen });

  const navLinks = useMemo(() => {
    const items = [
      { path: config.dashboardPath, icon: <FaChartPie />, text: "Dashboard", visible: true },
      {
        path: config.announcementsPath,
        icon: <FaBullhorn />,
        text: "Announcements",
        visible: hasPermission("manage_announcements"),
      },
      {
        path: config.studentsPath,
        icon: <FaUserGraduate />,
        text: "Students",
        visible: hasPermission("view_students") || hasPermission("manage_students"),
      },
      {
        path: config.eventsPath,
        icon: <FaRegListAlt />,
        text: "Events",
        visible: hasPermission("manage_events"),
      },
      {
        path: config.recordsPath,
        icon: <FaClipboard />,
        text: "Records",
        visible: hasPermission("manage_attendance"),
      },
      {
        path: config.manualAttendancePath,
        icon: <FaUserCheck />,
        text: "Manual Attendance",
        visible: hasPermission("manage_attendance"),
      },
    ];

    if (config.managePath && config.manageLabel && config.manageVisibility?.(hasPermission)) {
      items.push({
        path: config.managePath,
        icon: <FaSitemap />,
        text: config.manageLabel,
        visible: true,
      });
    }

    return items.filter((item) => item.visible);
  }, [config, hasPermission]);

  const hasGovernanceFeatures = navLinks.some((item) => item.path !== config.dashboardPath);
  const unitCode = governanceUnit?.unit_code || accessUnit?.unit_code || unitType;
  const unitName = governanceUnit?.unit_name || accessUnit?.unit_name || fallbackUnitLabel;

  return (
    <>
      {!sidebarOpen && (
        <div className="ssg-hamburger" onClick={() => setSidebarOpen(true)}>
          <FaBars />
        </div>
      )}

      {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)}></div>}

      <div
        className={`ssg-sidebar ${sidebarOpen ? "open" : ""} ${
          isExpanded ? "expanded" : "collapsed"
        }`}
      >
        <div className="ssg-sidebar-header">
          <div className="header-content-wrapper">
            <img src={logoUrl || logoValid8} alt="Campus logo" className="sidebar-logo" />
            <div className="ssg-title-wrap">
              <span className="ssg-unit-chip">{unitCode}</span>
              <h1 className="ssg-title">{unitName}</h1>
              <p className="ssg-campus-name">{campusName}</p>
            </div>
          </div>
          {sidebarOpen && (
            <button className="sidebar-close-btn" onClick={() => setSidebarOpen(false)}>
              <FaTimes />
            </button>
          )}
        </div>

        <nav className="ssg-nav">
          <ul className="ssg-nav-menu">
            <li className="menu-toggle-item">
              <button
                className="ssg-nav-link menu-toggle-btn"
                onClick={() => setIsExpanded((current) => !current)}
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
                  className={({ isActive }) => (isActive ? "ssg-nav-link active" : "ssg-nav-link")}
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

        {!accessLoading && !hasGovernanceFeatures && (
          <div className="ssg-sidebar-note">
            No {unitType} features are assigned yet. Ask the parent governance manager to grant permissions.
          </div>
        )}

        <div className="ssg-sidebar-footer">
          <div className="ssg-officer-summary">
            <img src={userprofile} alt="user profile" className="ssg-profile-img" />
            <div className="ssg-officer-copy">
              <strong>{officerName}</strong>
              <span>{officerPosition}</span>
            </div>
          </div>
          <NavLink
            to={config.profilePath}
            className={({ isActive }) => (isActive ? "ssg-profile-link active" : "ssg-profile-link")}
            onClick={() => setSidebarOpen(false)}
            title="Profile"
          >
            <span className="profile-text">View Profile</span>
          </NavLink>
        </div>
      </div>

      <div
        className={`ssg-content ${sidebarOpen ? "shifted" : ""} ${
          isExpanded ? "content-expanded" : "content-collapsed"
        }`}
      ></div>
    </>
  );
};

export default GovernanceSidebar;
