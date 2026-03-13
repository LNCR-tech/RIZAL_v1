import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import NavbarAdmin from "../components/NavbarAdmin";
import {
  adminCreateSchoolWithSchoolIT,
  adminListSchoolItAccounts,
  adminListSchools,
  adminResetSchoolItPassword,
  adminSetSchoolItActiveStatus,
  AdminSchoolItCreatePayload,
  SchoolITAccountSummary,
  SchoolSummary,
} from "../api/schoolSettingsApi";
import "../css/AdminSchoolManagement.css";

const defaultForm: AdminSchoolItCreatePayload = {
  school_name: "",
  primary_color: "#162F65",
  secondary_color: "#2C5F9E",
  school_code: "",
  school_it_email: "",
  school_it_first_name: "",
  school_it_middle_name: "",
  school_it_last_name: "",
  school_it_password: "",
};

const AdminSchoolManagement = () => {
  const navigate = useNavigate();
  const [form, setForm] = useState<AdminSchoolItCreatePayload>(defaultForm);
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [schools, setSchools] = useState<SchoolSummary[]>([]);
  const [schoolItAccounts, setSchoolItAccounts] = useState<SchoolITAccountSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [generatedPassword, setGeneratedPassword] = useState<string | null>(null);

  const handleApiError = (err: unknown, fallback: string) => {
    const message = err instanceof Error ? err.message : fallback;
    setError(message);
    if (message.toLowerCase().includes("session expired")) {
      navigate("/login");
    }
  };

  const refreshData = async () => {
    const [schoolsData, schoolItData] = await Promise.all([
      adminListSchools(),
      adminListSchoolItAccounts(),
    ]);
    setSchools(schoolsData);
    setSchoolItAccounts(schoolItData);
  };

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        await refreshData();
      } catch (err) {
        handleApiError(err, "Failed to load school management data");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const setField = (key: keyof AdminSchoolItCreatePayload, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleCreate = async () => {
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    setGeneratedPassword(null);
    try {
      const response = await adminCreateSchoolWithSchoolIT(form, logoFile);
      setSuccess(
        `Created school "${response.school.school_name}" with SCHOOL_IT account ${response.school_it_email}.`
      );
      if (response.generated_temporary_password) {
        setGeneratedPassword(response.generated_temporary_password);
      }
      setForm(defaultForm);
      setLogoFile(null);
      await refreshData();
    } catch (err) {
      handleApiError(err, "Failed to create school and SCHOOL_IT");
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleSchoolItStatus = async (account: SchoolITAccountSummary) => {
    setError(null);
    setSuccess(null);
    try {
      await adminSetSchoolItActiveStatus(account.user_id, !account.is_active);
      await refreshData();
    } catch (err) {
      handleApiError(err, "Failed to update SCHOOL_IT status");
    }
  };

  const handleResetSchoolItPassword = async (account: SchoolITAccountSummary) => {
    setError(null);
    setSuccess(null);
    setGeneratedPassword(null);
    try {
      const result = await adminResetSchoolItPassword(account.user_id);
      setSuccess(`Password reset for ${result.email}.`);
      setGeneratedPassword(result.temporary_password);
    } catch (err) {
      handleApiError(err, "Failed to reset SCHOOL_IT password");
    }
  };

  return (
    <div className="admin-school-management-page">
      <NavbarAdmin />

      <main className="admin-school-management-main container py-4">
        <div className="row g-3">
          <div className="col-lg-6">
            <div className="card border-0 shadow-sm">
              <div className="card-body">
                <h4 className="mb-3">Create School + SCHOOL_IT</h4>

                {error && <div className="alert alert-danger">{error}</div>}
                {success && <div className="alert alert-success">{success}</div>}
                {generatedPassword && (
                  <div className="alert alert-warning">
                    Temporary password: <strong>{generatedPassword}</strong>
                  </div>
                )}

                <div className="row g-2">
                  <div className="col-12">
                    <label className="form-label">School Name</label>
                    <input
                      className="form-control"
                      value={form.school_name}
                      onChange={(e) => setField("school_name", e.target.value)}
                    />
                  </div>

                  <div className="col-md-6">
                    <label className="form-label">Primary Color</label>
                    <input
                      type="color"
                      className="form-control form-control-color"
                      value={form.primary_color}
                      onChange={(e) => setField("primary_color", e.target.value)}
                    />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label">Secondary Color</label>
                    <input
                      type="color"
                      className="form-control form-control-color"
                      value={form.secondary_color || "#2C5F9E"}
                      onChange={(e) => setField("secondary_color", e.target.value)}
                    />
                  </div>

                  <div className="col-12">
                    <label className="form-label">School Code (optional)</label>
                    <input
                      className="form-control"
                      value={form.school_code || ""}
                      onChange={(e) => setField("school_code", e.target.value)}
                    />
                  </div>

                  <div className="col-12">
                    <label className="form-label">School Logo (optional)</label>
                    <input
                      type="file"
                      className="form-control"
                      accept=".png,.jpg,.jpeg,.svg,image/png,image/jpeg,image/svg+xml"
                      onChange={(e) => setLogoFile(e.target.files?.[0] || null)}
                    />
                  </div>

                  <div className="col-md-6">
                    <label className="form-label">SCHOOL_IT Email</label>
                    <input
                      className="form-control"
                      value={form.school_it_email}
                      onChange={(e) => setField("school_it_email", e.target.value)}
                    />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label">SCHOOL_IT Password (optional)</label>
                    <input
                      className="form-control"
                      value={form.school_it_password || ""}
                      onChange={(e) => setField("school_it_password", e.target.value)}
                    />
                  </div>

                  <div className="col-md-4">
                    <label className="form-label">First Name</label>
                    <input
                      className="form-control"
                      value={form.school_it_first_name}
                      onChange={(e) => setField("school_it_first_name", e.target.value)}
                    />
                  </div>
                  <div className="col-md-4">
                    <label className="form-label">Middle Name</label>
                    <input
                      className="form-control"
                      value={form.school_it_middle_name || ""}
                      onChange={(e) => setField("school_it_middle_name", e.target.value)}
                    />
                  </div>
                  <div className="col-md-4">
                    <label className="form-label">Last Name</label>
                    <input
                      className="form-control"
                      value={form.school_it_last_name}
                      onChange={(e) => setField("school_it_last_name", e.target.value)}
                    />
                  </div>
                </div>

                <button className="btn btn-primary mt-3" onClick={handleCreate} disabled={submitting}>
                  {submitting ? "Creating..." : "Create School + SCHOOL_IT"}
                </button>
              </div>
            </div>
          </div>

          <div className="col-lg-6">
            <div className="card border-0 shadow-sm mb-3">
              <div className="card-body">
                <h5 className="mb-2">Schools</h5>
                {loading ? (
                  <p className="text-muted mb-0">Loading...</p>
                ) : (
                  <div className="table-responsive">
                    <table className="table table-sm">
                      <thead>
                        <tr>
                          <th>School</th>
                          <th>Code</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {schools.map((school) => (
                          <tr key={school.school_id}>
                            <td>{school.school_name}</td>
                            <td>{school.school_code || "-"}</td>
                            <td>{school.active_status ? "Active" : "Suspended"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>

            <div className="card border-0 shadow-sm">
              <div className="card-body">
                <h5 className="mb-2">SCHOOL_IT Accounts</h5>
                {loading ? (
                  <p className="text-muted mb-0">Loading...</p>
                ) : (
                  <div className="table-responsive">
                    <table className="table table-sm align-middle">
                      <thead>
                        <tr>
                          <th>Email</th>
                          <th>School</th>
                          <th>Status</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {schoolItAccounts.map((account) => (
                          <tr key={account.user_id}>
                            <td>{account.email}</td>
                            <td>{account.school_name || "-"}</td>
                            <td>{account.is_active ? "Active" : "Inactive"}</td>
                            <td>
                              <div className="d-flex gap-2">
                                <button
                                  className="btn btn-sm btn-outline-secondary"
                                  onClick={() => handleToggleSchoolItStatus(account)}
                                >
                                  {account.is_active ? "Deactivate" : "Activate"}
                                </button>
                                <button
                                  className="btn btn-sm btn-outline-warning"
                                  onClick={() => handleResetSchoolItPassword(account)}
                                >
                                  Reset Password
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default AdminSchoolManagement;
