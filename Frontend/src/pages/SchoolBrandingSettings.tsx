import { useEffect, useMemo, useState } from "react";
import { FaImage, FaSave } from "react-icons/fa";

import NavbarSchoolIT from "../components/NavbarSchoolIT";
import {
  fetchSchoolSettings,
  normalizeLogoUrl,
  SchoolSettings,
  SchoolSettingsUpdatePayload,
  updateSchoolSettings,
} from "../api/schoolSettingsApi";
import { useUser } from "../context/UserContext";

const SchoolBrandingSettings = () => {
  const { setBranding } = useUser();
  const [settings, setSettings] = useState<SchoolSettings | null>(null);
  const [form, setForm] = useState<SchoolSettingsUpdatePayload>({
    school_name: "",
    primary_color: "#162F65",
    secondary_color: "#2C5F9E",
    school_code: "",
  });
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const logoDisplay = useMemo(() => {
    if (logoPreview) return logoPreview;
    return normalizeLogoUrl(settings?.logo_url) || null;
  }, [logoPreview, settings?.logo_url]);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchSchoolSettings();
        setSettings(data);
        setForm({
          school_name: data.school_name,
          primary_color: data.primary_color,
          secondary_color: data.secondary_color || "#2C5F9E",
          school_code: data.school_code || "",
        });
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "No school is assigned to your account. Contact your platform admin."
        );
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const updateField = (key: keyof SchoolSettingsUpdatePayload, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const onLogoChange = (file: File | null) => {
    if (!file) {
      setLogoFile(null);
      setLogoPreview(null);
      return;
    }

    const allowed = [".png", ".jpg", ".jpeg", ".svg"];
    const fileName = file.name.toLowerCase();
    if (!allowed.some((ext) => fileName.endsWith(ext))) {
      setError("Logo must be PNG, JPG, JPEG, or SVG.");
      return;
    }

    const maxBytes = 2 * 1024 * 1024;
    if (file.size > maxBytes) {
      setError("Logo exceeds 2MB max size.");
      return;
    }

    setError(null);
    setLogoFile(file);
    setLogoPreview(URL.createObjectURL(file));
  };

  const handleSubmit = async () => {
    if (!settings) {
      setError("No school is assigned to your account.");
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const updated = await updateSchoolSettings(form, logoFile);
      setSettings(updated);
      setBranding(updated);
      setForm({
        school_name: updated.school_name,
        primary_color: updated.primary_color,
        secondary_color: updated.secondary_color || "#2C5F9E",
        school_code: updated.school_code || "",
      });
      setLogoFile(null);
      setLogoPreview(null);
      setSuccess("School branding updated successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save school branding.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#f5f7fa" }}>
      <NavbarSchoolIT />

      <main className="container py-4">
        <div className="card border-0 shadow-sm">
          <div className="card-body">
            <div className="d-flex justify-content-between align-items-center mb-3">
              <h3 className="mb-0">School Branding Settings</h3>
            </div>

            {loading && <p className="text-muted mb-0">Loading settings...</p>}
            {error && (
              <div className="alert alert-danger" role="alert">
                {error}
              </div>
            )}
            {success && (
              <div className="alert alert-success" role="alert">
                {success}
              </div>
            )}

            {!loading && settings && (
              <div className="row g-3">
                <div className="col-md-8">
                  <label className="form-label">School Name</label>
                  <input
                    type="text"
                    className="form-control"
                    value={form.school_name || ""}
                    onChange={(e) => updateField("school_name", e.target.value)}
                    placeholder="Enter school display name"
                  />
                </div>

                <div className="col-md-4">
                  <label className="form-label">School Code (optional)</label>
                  <input
                    type="text"
                    className="form-control"
                    value={form.school_code || ""}
                    onChange={(e) => updateField("school_code", e.target.value)}
                    placeholder="e.g. ABC-01"
                  />
                </div>

                <div className="col-md-6">
                  <label className="form-label">Primary Color</label>
                  <input
                    type="color"
                    className="form-control form-control-color"
                    value={form.primary_color || "#162F65"}
                    onChange={(e) => updateField("primary_color", e.target.value)}
                  />
                </div>

                <div className="col-md-6">
                  <label className="form-label">Secondary Color</label>
                  <input
                    type="color"
                    className="form-control form-control-color"
                    value={form.secondary_color || "#2C5F9E"}
                    onChange={(e) => updateField("secondary_color", e.target.value)}
                  />
                </div>

                <div className="col-12">
                  <label className="form-label">School Logo (PNG, JPG, JPEG, SVG, max 2MB)</label>
                  <input
                    type="file"
                    className="form-control"
                    accept=".png,.jpg,.jpeg,.svg,image/png,image/jpeg,image/svg+xml"
                    onChange={(e) => onLogoChange(e.target.files?.[0] || null)}
                  />
                </div>

                <div className="col-12">
                  <button
                    className="btn btn-primary"
                    onClick={handleSubmit}
                    disabled={saving}
                    style={{
                      backgroundColor: "var(--primary-color, #162F65)",
                      borderColor: "var(--primary-color, #162F65)",
                    }}
                  >
                    <FaSave className="me-2" />
                    {saving ? "Saving..." : "Save Branding"}
                  </button>
                </div>

                <div className="col-12">
                  <div className="card bg-light border-0">
                    <div className="card-body d-flex align-items-center gap-3">
                      {logoDisplay ? (
                        <img
                          src={logoDisplay}
                          alt="School logo preview"
                          style={{
                            width: 56,
                            height: 56,
                            borderRadius: "50%",
                            objectFit: "cover",
                          }}
                        />
                      ) : (
                        <div
                          style={{
                            width: 56,
                            height: 56,
                            borderRadius: "50%",
                            background: "#e9ecef",
                            display: "grid",
                            placeItems: "center",
                            color: "#6c757d",
                          }}
                        >
                          <FaImage />
                        </div>
                      )}
                      <div>
                        <strong>{form.school_name || settings.school_name || "School Name"}</strong>
                        <p className="text-muted mb-0">Live branding preview</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default SchoolBrandingSettings;
