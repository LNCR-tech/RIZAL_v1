import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  FaFileImport,
  FaKey,
  FaPalette,
  FaRegListAlt,
  FaSchool,
  FaSitemap,
  FaUserShield,
  FaUsers,
} from "react-icons/fa";

import NavbarSchoolIT from "../components/NavbarSchoolIT";
import { fetchSchoolSettings, normalizeLogoUrl, SchoolSettings } from "../api/schoolSettingsApi";

const SchoolITDashboard = () => {
  const [settings, setSettings] = useState<SchoolSettings | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchSchoolSettings();
        setSettings(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load school settings");
      }
    };

    load();
  }, []);

  return (
    <div style={{ minHeight: "100vh", background: "#f5f7fa" }}>
      <NavbarSchoolIT />

      <main className="container py-4">
        {settings && (
          <section
            className="card border-0 shadow-sm mb-4"
            style={{
              borderLeft: `6px solid ${settings.primary_color}`,
            }}
          >
            <div className="card-body d-flex align-items-center gap-3">
              {settings.logo_url ? (
                <img
                  src={normalizeLogoUrl(settings.logo_url) || undefined}
                  alt={`${settings.school_name} logo`}
                  style={{
                    width: 64,
                    height: 64,
                    borderRadius: "50%",
                    objectFit: "cover",
                    border: "2px solid #e9ecef",
                  }}
                />
              ) : (
                <div
                  style={{
                    width: 64,
                    height: 64,
                    borderRadius: "50%",
                    background: "#e9ecef",
                    display: "grid",
                    placeItems: "center",
                    color: "#6c757d",
                  }}
                >
                  <FaSchool />
                </div>
              )}
              <div>
                <h3 className="mb-1">{settings.school_name}</h3>
                <p className="text-muted mb-0">
                  School IT control center for branding and onboarding workflows.
                </p>
              </div>
            </div>
          </section>
        )}

        {error && (
          <div className="alert alert-warning" role="alert">
            {error}
          </div>
        )}

        <section className="row g-3">
          <div className="col-md-6">
            <Link to="/school_it_events" className="text-decoration-none">
              <div className="card h-100 border-0 shadow-sm">
                <div className="card-body">
                  <h5 className="card-title">
                    <FaRegListAlt className="me-2" />
                    Events
                  </h5>
                  <p className="card-text text-muted mb-0">
                    View school events and monitor schedules and status updates.
                  </p>
                </div>
              </div>
            </Link>
          </div>

          <div className="col-md-6">
            <Link to="/school_it_create_department_program" className="text-decoration-none">
              <div className="card h-100 border-0 shadow-sm">
                <div className="card-body">
                  <h5 className="card-title">
                    <FaSitemap className="me-2" />
                    Departments & Programs
                  </h5>
                  <p className="card-text text-muted mb-0">
                    Create and maintain departments and their associated programs.
                  </p>
                </div>
              </div>
            </Link>
          </div>

          <div className="col-md-6">
            <Link to="/school_it_branding" className="text-decoration-none">
              <div className="card h-100 border-0 shadow-sm">
                <div className="card-body">
                  <h5 className="card-title">
                    <FaPalette className="me-2" />
                    Change UI Color & Branding
                  </h5>
                  <p className="card-text text-muted mb-0">
                    Update school colors, dashboard logo, and school display name.
                  </p>
                </div>
              </div>
            </Link>
          </div>

          <div className="col-md-6">
            <Link to="/school_it_import_users" className="text-decoration-none">
              <div className="card h-100 border-0 shadow-sm">
                <div className="card-body">
                  <h5 className="card-title">
                    <FaFileImport className="me-2" />
                    Import Students via Excel
                  </h5>
                  <p className="card-text text-muted mb-0">
                    Queue large school-scoped student imports with row-level error reporting.
                  </p>
                </div>
              </div>
            </Link>
          </div>

          <div className="col-md-6">
            <Link to="/school_it_password_resets" className="text-decoration-none">
              <div className="card h-100 border-0 shadow-sm">
                <div className="card-body">
                  <h5 className="card-title">
                    <FaKey className="me-2" />
                    Password Reset Requests
                  </h5>
                  <p className="card-text text-muted mb-0">
                    Approve forgot-password requests and automatically send temporary passwords.
                  </p>
                </div>
              </div>
            </Link>
          </div>

          <div className="col-md-6">
            <Link to="/school_it_manage_users" className="text-decoration-none">
              <div className="card h-100 border-0 shadow-sm">
                <div className="card-body">
                  <h5 className="card-title">
                    <FaUsers className="me-2" />
                    Manage Users
                  </h5>
                  <p className="card-text text-muted mb-0">
                    View, edit, and deactivate users within your school scope.
                  </p>
                </div>
              </div>
            </Link>
          </div>

          <div className="col-md-6">
            <Link to="/school_it_face_verification" className="text-decoration-none">
              <div className="card h-100 border-0 shadow-sm">
                <div className="card-body">
                  <h5 className="card-title">
                    <FaUserShield className="me-2" />
                    Facial Verification
                  </h5>
                  <p className="card-text text-muted mb-0">
                    Manage live face enrollment and anti-spoof verification for School IT access.
                  </p>
                </div>
              </div>
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
};

export default SchoolITDashboard;
