import { NavLink } from "react-router-dom";
import {
  FaBell,
  FaClipboardList,
  FaDatabase,
  FaFileImport,
  FaHome,
  FaKey,
  FaPalette,
  FaRegListAlt,
  FaShieldAlt,
  FaSitemap,
  FaUserShield,
  FaUserCircle,
  FaUsers,
} from "react-icons/fa";
import logoValid8 from "../assets/images/logo-valid83.webp";
import { useUser } from "../context/UserContext";
import { normalizeLogoUrl } from "../api/schoolSettingsApi";

const NavbarSchoolIT = () => {
  const { branding } = useUser();
  const logo = normalizeLogoUrl(branding?.logo_url) || logoValid8;
  const schoolName = branding?.school_name || "School IT";

  return (
    <nav
      className="navbar navbar-expand-lg navbar-dark"
      style={{ backgroundColor: "var(--primary-color, #162F65)" }}
    >
      <div className="container-fluid">
        <NavLink to="/school_it_home" className="navbar-brand d-flex align-items-center gap-2">
          <img
            src={logo}
            alt={`${schoolName} logo`}
            style={{ width: 32, height: 32, borderRadius: "50%" }}
          />
          <span>{schoolName}</span>
        </NavLink>

        <button
          className="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#schoolItNavbar"
          aria-controls="schoolItNavbar"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon"></span>
        </button>

        <div className="collapse navbar-collapse" id="schoolItNavbar">
          <ul className="navbar-nav ms-auto mb-2 mb-lg-0">
            <li className="nav-item">
              <NavLink to="/school_it_home" className="nav-link">
                <FaHome className="me-2" />
                Home
              </NavLink>
            </li>
            <li className="nav-item">
              <NavLink to="/school_it_events" className="nav-link">
                <FaRegListAlt className="me-2" />
                Events
              </NavLink>
            </li>
            <li className="nav-item">
              <NavLink to="/school_it_create_department_program" className="nav-link">
                <FaSitemap className="me-2" />
                Departments & Programs
              </NavLink>
            </li>
            <li className="nav-item">
              <NavLink to="/school_it_branding" className="nav-link">
                <FaPalette className="me-2" />
                Branding
              </NavLink>
            </li>
            <li className="nav-item">
              <NavLink to="/school_it_import_users" className="nav-link">
                <FaFileImport className="me-2" />
                Import Users
              </NavLink>
            </li>
            <li className="nav-item">
              <NavLink to="/school_it_password_resets" className="nav-link">
                <FaKey className="me-2" />
                Password Requests
              </NavLink>
            </li>
            <li className="nav-item">
              <NavLink to="/school_it_manage_users" className="nav-link">
                <FaUsers className="me-2" />
                Manage Users
              </NavLink>
            </li>
            <li className="nav-item">
              <NavLink to="/school_it_audit_logs" className="nav-link">
                <FaClipboardList className="me-2" />
                Audit Logs
              </NavLink>
            </li>
            <li className="nav-item">
              <NavLink to="/school_it_notifications" className="nav-link">
                <FaBell className="me-2" />
                Notifications
              </NavLink>
            </li>
            <li className="nav-item">
              <NavLink to="/school_it_security" className="nav-link">
                <FaShieldAlt className="me-2" />
                Security
              </NavLink>
            </li>
            <li className="nav-item">
              <NavLink to="/school_it_face_verification" className="nav-link">
                <FaUserShield className="me-2" />
                Facial Verification
              </NavLink>
            </li>
            <li className="nav-item">
              <NavLink to="/school_it_subscription" className="nav-link">
                <FaRegListAlt className="me-2" />
                Subscription
              </NavLink>
            </li>
            <li className="nav-item">
              <NavLink to="/school_it_governance" className="nav-link">
                <FaDatabase className="me-2" />
                Governance
              </NavLink>
            </li>
            <li className="nav-item">
              <NavLink to="/school_it_profile" className="nav-link">
                <FaUserCircle className="me-2" />
                Profile
              </NavLink>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  );
};

export default NavbarSchoolIT;
