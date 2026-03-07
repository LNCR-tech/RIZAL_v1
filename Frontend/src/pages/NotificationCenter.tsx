import { useEffect, useState } from "react";

import NavbarAdmin from "../components/NavbarAdmin";
import NavbarSchoolIT from "../components/NavbarSchoolIT";
import {
  dispatchLowAttendanceNotifications,
  dispatchMissedEventsNotifications,
  fetchNotificationLogs,
  fetchNotificationPreferences,
  NotificationDispatchSummary,
  NotificationLogItem,
  NotificationPreference,
  sendTestNotification,
  updateNotificationPreferences,
} from "../api/platformOpsApi";

const normalizeRole = (role: string) => role.trim().toLowerCase().replace(/_/g, "-");

const getStoredRoles = (): string[] => {
  try {
    const raw = localStorage.getItem("user");
    if (!raw) return [];
    const parsed = JSON.parse(raw) as { roles?: string[] };
    return Array.isArray(parsed.roles) ? parsed.roles : [];
  } catch {
    return [];
  }
};

const NotificationCenter = () => {
  const roles = getStoredRoles();
  const isSchoolIT = roles.some((role) => normalizeRole(role) === "school-it");
  const NavbarComponent = isSchoolIT ? NavbarSchoolIT : NavbarAdmin;

  const [preferences, setPreferences] = useState<NotificationPreference | null>(null);
  const [logs, setLogs] = useState<NotificationLogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<NotificationDispatchSummary | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [prefData, logsData] = await Promise.all([
        fetchNotificationPreferences(),
        fetchNotificationLogs({ limit: 100 }),
      ]);
      setPreferences(prefData);
      setLogs(logsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load notification center");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const savePreferences = async () => {
    if (!preferences) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await updateNotificationPreferences(preferences);
      setPreferences(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save preferences");
    } finally {
      setSaving(false);
    }
  };

  const runAction = async (action: () => Promise<NotificationDispatchSummary>) => {
    setError(null);
    try {
      const data = await action();
      setSummary(data);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to dispatch notifications");
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#f8f9fa" }}>
      <NavbarComponent />
      <main className="container py-4">
        <h2 className="mb-3">Notification Center</h2>
        {error && <div className="alert alert-danger">{error}</div>}
        {summary && (
          <div className="alert alert-info">
            <strong>{summary.category}</strong>: processed {summary.processed_users}, sent {summary.sent},
            failed {summary.failed}, skipped {summary.skipped}
          </div>
        )}

        <div className="card mb-4">
          <div className="card-header">Notification Preferences</div>
          <div className="card-body">
            {loading || !preferences ? (
              <p className="mb-0">Loading...</p>
            ) : (
              <>
                <div className="form-check mb-2">
                  <input
                    id="pref-email"
                    type="checkbox"
                    className="form-check-input"
                    checked={preferences.email_enabled}
                    onChange={(e) =>
                      setPreferences((prev) => (prev ? { ...prev, email_enabled: e.target.checked } : prev))
                    }
                  />
                  <label className="form-check-label" htmlFor="pref-email">
                    Email enabled
                  </label>
                </div>
                <div className="form-check mb-2">
                  <input
                    id="pref-missed"
                    type="checkbox"
                    className="form-check-input"
                    checked={preferences.notify_missed_events}
                    onChange={(e) =>
                      setPreferences((prev) =>
                        prev ? { ...prev, notify_missed_events: e.target.checked } : prev
                      )
                    }
                  />
                  <label className="form-check-label" htmlFor="pref-missed">
                    Missed events alerts
                  </label>
                </div>
                <div className="form-check mb-2">
                  <input
                    id="pref-low"
                    type="checkbox"
                    className="form-check-input"
                    checked={preferences.notify_low_attendance}
                    onChange={(e) =>
                      setPreferences((prev) =>
                        prev ? { ...prev, notify_low_attendance: e.target.checked } : prev
                      )
                    }
                  />
                  <label className="form-check-label" htmlFor="pref-low">
                    Low attendance alerts
                  </label>
                </div>
                <div className="form-check mb-3">
                  <input
                    id="pref-security"
                    type="checkbox"
                    className="form-check-input"
                    checked={preferences.notify_account_security}
                    onChange={(e) =>
                      setPreferences((prev) =>
                        prev ? { ...prev, notify_account_security: e.target.checked } : prev
                      )
                    }
                  />
                  <label className="form-check-label" htmlFor="pref-security">
                    Account security alerts
                  </label>
                </div>
                <button className="btn btn-primary" onClick={savePreferences} disabled={saving}>
                  {saving ? "Saving..." : "Save Preferences"}
                </button>
              </>
            )}
          </div>
        </div>

        <div className="card mb-4">
          <div className="card-header">Dispatch Actions</div>
          <div className="card-body d-flex flex-wrap gap-2">
            <button className="btn btn-outline-primary" onClick={() => runAction(() => sendTestNotification())}>
              Send Test
            </button>
            <button
              className="btn btn-outline-warning"
              onClick={() => runAction(() => dispatchMissedEventsNotifications({ lookback_days: 14 }))}
            >
              Run Missed Events
            </button>
            <button
              className="btn btn-outline-danger"
              onClick={() => runAction(() => dispatchLowAttendanceNotifications({ threshold_percent: 75 }))}
            >
              Run Low Attendance
            </button>
          </div>
        </div>

        <div className="card">
          <div className="card-header">Recent Notification Logs</div>
          <div className="table-responsive">
            <table className="table table-sm table-striped mb-0">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Category</th>
                  <th>Channel</th>
                  <th>Status</th>
                  <th>User</th>
                  <th>Created</th>
                  <th>Subject</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td>{log.id}</td>
                    <td>{log.category}</td>
                    <td>{log.channel}</td>
                    <td>{log.status}</td>
                    <td>{log.user_id ?? "-"}</td>
                    <td>{new Date(log.created_at).toLocaleString()}</td>
                    <td>{log.subject}</td>
                  </tr>
                ))}
                {!loading && logs.length === 0 && (
                  <tr>
                    <td colSpan={7} className="text-center py-4">
                      No notification logs yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
};

export default NotificationCenter;
