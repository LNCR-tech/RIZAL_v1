import { useEffect, useState } from "react";

import NavbarSchoolIT from "../components/NavbarSchoolIT";
import {
  approvePasswordResetRequest,
  fetchPasswordResetRequests,
  PasswordResetRequestItem,
} from "../api/passwordResetApi";

const formatRoleLabel = (role: string): string => {
  const normalized = role.trim().toLowerCase().replace(/_/g, "-");
  if (normalized === "school-it") return "School IT";
  if (normalized === "event-organizer") return "Event Organizer";
  if (normalized === "ssg") return "SSG";
  if (normalized === "admin") return "Admin";
  if (normalized === "student") return "Student";
  return role;
};

const SchoolPasswordResetRequests = () => {
  const [requests, setRequests] = useState<PasswordResetRequestItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [processingRequestId, setProcessingRequestId] = useState<number | null>(null);

  const loadRequests = async (silent = false) => {
    if (!silent) setIsLoading(true);
    setError(null);
    try {
      const data = await fetchPasswordResetRequests();
      setRequests(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load password reset requests");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadRequests();
  }, []);

  const handleApprove = async (requestId: number, email: string) => {
    const confirmed = window.confirm(
      `Approve password reset for ${email}? A temporary password will be generated and sent by email.`
    );
    if (!confirmed) return;

    setProcessingRequestId(requestId);
    setError(null);
    setSuccess(null);
    try {
      const result = await approvePasswordResetRequest(requestId);
      setSuccess(result.message);
      setRequests((prev) => prev.filter((item) => item.id !== requestId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to approve request");
    } finally {
      setProcessingRequestId(null);
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#f5f7fa" }}>
      <NavbarSchoolIT />

      <main className="container py-4">
        <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
          <div>
            <h3 className="mb-1">Password Reset Requests</h3>
            <p className="text-muted mb-0">
              Approve user requests and send a temporary password automatically by email.
            </p>
          </div>
          <button
            className="btn btn-outline-primary"
            onClick={() => {
              setIsRefreshing(true);
              loadRequests(true);
            }}
            disabled={isRefreshing || isLoading}
          >
            {isRefreshing ? "Refreshing..." : "Refresh"}
          </button>
        </div>

        {error && <div className="alert alert-danger">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        <div className="card border-0 shadow-sm">
          <div className="card-body">
            {isLoading ? (
              <p className="text-muted mb-0">Loading pending requests...</p>
            ) : requests.length === 0 ? (
              <p className="text-muted mb-0">No pending password reset requests.</p>
            ) : (
              <div className="table-responsive">
                <table className="table align-middle mb-0">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Roles</th>
                      <th>Requested</th>
                      <th className="text-end">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {requests.map((item) => (
                      <tr key={item.id}>
                        <td>
                          {[item.first_name, item.last_name].filter(Boolean).join(" ") || "Unknown User"}
                        </td>
                        <td>{item.email}</td>
                        <td>
                          <div className="d-flex flex-wrap gap-1">
                            {item.roles.map((role) => (
                              <span key={`${item.id}-${role}`} className="badge bg-secondary">
                                {formatRoleLabel(role)}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td>{new Date(item.requested_at).toLocaleString()}</td>
                        <td className="text-end">
                          <button
                            className="btn btn-sm btn-primary"
                            onClick={() => handleApprove(item.id, item.email)}
                            disabled={processingRequestId === item.id}
                          >
                            {processingRequestId === item.id
                              ? "Approving..."
                              : "Approve & Send Password"}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default SchoolPasswordResetRequests;
