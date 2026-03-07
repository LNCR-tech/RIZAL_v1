const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface PasswordResetRequestItem {
  id: number;
  user_id: number;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  roles: string[];
  status: string;
  requested_at: string;
}

export interface PasswordResetApprovalResponse {
  id: number;
  user_id: number;
  status: string;
  resolved_at: string;
  message: string;
}

const getAuthToken = () =>
  localStorage.getItem("authToken") ||
  localStorage.getItem("token") ||
  localStorage.getItem("access_token");

const withAuthHeaders = () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found");
  }
  return {
    Authorization: `Bearer ${token}`,
  };
};

const extractErrorMessage = async (response: Response, fallback: string): Promise<string> => {
  if (response.status === 401) {
    localStorage.removeItem("authToken");
    localStorage.removeItem("token");
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    localStorage.removeItem("userData");
  }

  const body = await response.json().catch(() => null);
  if (!body) return fallback;
  if (typeof body.detail === "string" && body.detail.trim().length > 0) return body.detail;
  if (typeof body.message === "string" && body.message.trim().length > 0) return body.message;
  return fallback;
};

export const fetchPasswordResetRequests = async (): Promise<PasswordResetRequestItem[]> => {
  const response = await fetch(`${BASE_URL}/auth/password-reset-requests`, {
    method: "GET",
    headers: withAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, "Failed to load password reset requests"));
  }

  return (await response.json()) as PasswordResetRequestItem[];
};

export const approvePasswordResetRequest = async (
  requestId: number
): Promise<PasswordResetApprovalResponse> => {
  const response = await fetch(`${BASE_URL}/auth/password-reset-requests/${requestId}/approve`, {
    method: "POST",
    headers: withAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, "Failed to approve password reset request"));
  }

  return (await response.json()) as PasswordResetApprovalResponse;
};
