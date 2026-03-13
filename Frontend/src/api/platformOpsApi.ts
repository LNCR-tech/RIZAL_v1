import { buildApiUrl } from "./apiUrl";

const getAuthToken = () =>
  localStorage.getItem("authToken") ||
  localStorage.getItem("token") ||
  localStorage.getItem("access_token");

const withAuthHeaders = () => {
  const token = getAuthToken();
  if (!token) throw new Error("No authentication token found");
  return { Authorization: `Bearer ${token}` };
};

const parseError = async (response: Response, fallback: string): Promise<string> => {
  const body = await response.json().catch(() => null);
  if (!body) return fallback;
  if (typeof body.detail === "string" && body.detail.trim()) return body.detail;
  if (typeof body.message === "string" && body.message.trim()) return body.message;
  return fallback;
};

const toQuery = (params: Record<string, string | number | boolean | null | undefined>) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && `${value}`.trim() !== "") {
      query.set(key, String(value));
    }
  });
  return query.toString();
};

export interface AuditLogItem {
  id: number;
  school_id: number;
  actor_user_id?: number | null;
  action: string;
  status: string;
  details?: string | null;
  details_json?: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditLogSearchResponse {
  total: number;
  items: AuditLogItem[];
}

export const fetchAuditLogs = async (params: {
  q?: string;
  action?: string;
  status?: string;
  actor_user_id?: number;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}): Promise<AuditLogSearchResponse> => {
  const query = toQuery(params);
  const response = await fetch(buildApiUrl(`/api/audit-logs${query ? `?${query}` : ""}`), {
    method: "GET",
    headers: withAuthHeaders(),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to fetch audit logs"));
  return (await response.json()) as AuditLogSearchResponse;
};

export interface NotificationPreference {
  user_id: number;
  email_enabled: boolean;
  sms_enabled: boolean;
  sms_number?: string | null;
  notify_missed_events: boolean;
  notify_low_attendance: boolean;
  notify_account_security: boolean;
  notify_subscription: boolean;
  updated_at: string;
}

export interface NotificationLogItem {
  id: number;
  school_id?: number | null;
  user_id?: number | null;
  category: string;
  channel: string;
  status: string;
  subject: string;
  message: string;
  error_message?: string | null;
  metadata_json?: Record<string, unknown> | null;
  created_at: string;
}

export interface NotificationDispatchSummary {
  processed_users: number;
  sent: number;
  failed: number;
  skipped: number;
  category: string;
}

export const fetchNotificationPreferences = async (): Promise<NotificationPreference> => {
  const response = await fetch(buildApiUrl("/api/notifications/preferences/me"), {
    method: "GET",
    headers: withAuthHeaders(),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to fetch preferences"));
  return (await response.json()) as NotificationPreference;
};

export const updateNotificationPreferences = async (
  payload: Partial<NotificationPreference>
): Promise<NotificationPreference> => {
  const response = await fetch(buildApiUrl("/api/notifications/preferences/me"), {
    method: "PUT",
    headers: {
      ...withAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to update preferences"));
  return (await response.json()) as NotificationPreference;
};

export const fetchNotificationLogs = async (params: {
  school_id?: number;
  category?: string;
  status?: string;
  user_id?: number;
  limit?: number;
}): Promise<NotificationLogItem[]> => {
  const query = toQuery(params);
  const response = await fetch(buildApiUrl(`/api/notifications/logs${query ? `?${query}` : ""}`), {
    method: "GET",
    headers: withAuthHeaders(),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to fetch notification logs"));
  return (await response.json()) as NotificationLogItem[];
};

export const sendTestNotification = async (message?: string): Promise<NotificationDispatchSummary> => {
  const response = await fetch(buildApiUrl("/api/notifications/test"), {
    method: "POST",
    headers: {
      ...withAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ channel: "email", message }),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to send test notification"));
  return (await response.json()) as NotificationDispatchSummary;
};

export const dispatchMissedEventsNotifications = async (
  params: { school_id?: number; lookback_days?: number } = {}
): Promise<NotificationDispatchSummary> => {
  const query = toQuery(params);
  const response = await fetch(
    buildApiUrl(`/api/notifications/dispatch/missed-events${query ? `?${query}` : ""}`),
    {
      method: "POST",
      headers: withAuthHeaders(),
    }
  );
  if (!response.ok) throw new Error(await parseError(response, "Failed to dispatch missed event alerts"));
  return (await response.json()) as NotificationDispatchSummary;
};

export const dispatchLowAttendanceNotifications = async (
  params: { school_id?: number; threshold_percent?: number; min_records?: number } = {}
): Promise<NotificationDispatchSummary> => {
  const query = toQuery(params);
  const response = await fetch(
    buildApiUrl(`/api/notifications/dispatch/low-attendance${query ? `?${query}` : ""}`),
    {
      method: "POST",
      headers: withAuthHeaders(),
    }
  );
  if (!response.ok) throw new Error(await parseError(response, "Failed to dispatch low attendance alerts"));
  return (await response.json()) as NotificationDispatchSummary;
};

export interface MfaStatus {
  user_id: number;
  mfa_enabled: boolean;
  trusted_device_days: number;
  updated_at: string;
}

export interface UserSessionItem {
  id: string;
  token_jti: string;
  ip_address?: string | null;
  user_agent?: string | null;
  created_at: string;
  last_seen_at: string;
  revoked_at?: string | null;
  expires_at: string;
  is_current: boolean;
}

export interface LoginHistoryItem {
  id: number;
  user_id?: number | null;
  school_id?: number | null;
  email_attempted: string;
  success: boolean;
  auth_method: string;
  failure_reason?: string | null;
  ip_address?: string | null;
  user_agent?: string | null;
  created_at: string;
}

export const fetchMfaStatus = async (): Promise<MfaStatus> => {
  const response = await fetch(buildApiUrl("/auth/security/mfa-status"), {
    method: "GET",
    headers: withAuthHeaders(),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to fetch MFA status"));
  return (await response.json()) as MfaStatus;
};

export const updateMfaStatus = async (
  payload: { mfa_enabled: boolean; trusted_device_days?: number }
): Promise<MfaStatus> => {
  const response = await fetch(buildApiUrl("/auth/security/mfa-status"), {
    method: "PUT",
    headers: { ...withAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to update MFA status"));
  return (await response.json()) as MfaStatus;
};

export const fetchUserSessions = async (): Promise<UserSessionItem[]> => {
  const response = await fetch(buildApiUrl("/auth/security/sessions"), {
    method: "GET",
    headers: withAuthHeaders(),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to fetch sessions"));
  return (await response.json()) as UserSessionItem[];
};

export const revokeUserSession = async (sessionId: string): Promise<void> => {
  const response = await fetch(buildApiUrl(`/auth/security/sessions/${sessionId}/revoke`), {
    method: "POST",
    headers: withAuthHeaders(),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to revoke session"));
};

export const revokeOtherSessions = async (): Promise<number> => {
  const response = await fetch(buildApiUrl("/auth/security/sessions/revoke-others"), {
    method: "POST",
    headers: withAuthHeaders(),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to revoke sessions"));
  const body = (await response.json()) as { revoked_count: number };
  return body.revoked_count;
};

export const fetchLoginHistory = async (limit = 100): Promise<LoginHistoryItem[]> => {
  const response = await fetch(buildApiUrl(`/auth/security/login-history?limit=${limit}`), {
    method: "GET",
    headers: withAuthHeaders(),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to fetch login history"));
  return (await response.json()) as LoginHistoryItem[];
};

export interface SubscriptionMetrics {
  user_count: number;
  event_count_current_month: number;
  import_count_current_month: number;
  user_limit: number;
  event_limit_monthly: number;
  import_limit_monthly: number;
  user_usage_percent: number;
  event_usage_percent: number;
  import_usage_percent: number;
}

export interface SubscriptionSettings {
  school_id: number;
  plan_name: string;
  user_limit: number;
  event_limit_monthly: number;
  import_limit_monthly: number;
  renewal_date?: string | null;
  auto_renew: boolean;
  reminder_days_before: number;
  updated_at: string;
  metrics: SubscriptionMetrics;
}

export const fetchSubscription = async (schoolId?: number): Promise<SubscriptionSettings> => {
  const query = toQuery({ school_id: schoolId });
  const response = await fetch(buildApiUrl(`/api/subscription/me${query ? `?${query}` : ""}`), {
    method: "GET",
    headers: withAuthHeaders(),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to fetch subscription"));
  return (await response.json()) as SubscriptionSettings;
};

export const updateSubscription = async (
  payload: Partial<SubscriptionSettings>,
  schoolId?: number
): Promise<SubscriptionSettings> => {
  const query = toQuery({ school_id: schoolId });
  const response = await fetch(buildApiUrl(`/api/subscription/me${query ? `?${query}` : ""}`), {
    method: "PUT",
    headers: { ...withAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to update subscription"));
  return (await response.json()) as SubscriptionSettings;
};

export const runSubscriptionReminders = async (schoolId?: number): Promise<{
  schools_checked: number;
  reminders_created: number;
  reminders_sent: number;
  reminders_failed: number;
}> => {
  const query = toQuery({ school_id: schoolId });
  const response = await fetch(buildApiUrl(`/api/subscription/run-reminders${query ? `?${query}` : ""}`), {
    method: "POST",
    headers: withAuthHeaders(),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to run reminders"));
  return (await response.json()) as {
    schools_checked: number;
    reminders_created: number;
    reminders_sent: number;
    reminders_failed: number;
  };
};

export interface GovernanceSettings {
  school_id: number;
  attendance_retention_days: number;
  audit_log_retention_days: number;
  import_file_retention_days: number;
  auto_delete_enabled: boolean;
  updated_at: string;
}

export interface ConsentItem {
  id: number;
  user_id: number;
  school_id: number;
  consent_type: string;
  consent_granted: boolean;
  consent_version: string;
  source: string;
  created_at: string;
}

export interface DataRequestItem {
  id: number;
  school_id: number;
  requested_by_user_id?: number | null;
  target_user_id?: number | null;
  request_type: string;
  scope: string;
  status: string;
  reason?: string | null;
  details_json?: Record<string, unknown> | null;
  output_path?: string | null;
  handled_by_user_id?: number | null;
  created_at: string;
  resolved_at?: string | null;
}

export const fetchGovernanceSettings = async (schoolId?: number): Promise<GovernanceSettings> => {
  const query = toQuery({ school_id: schoolId });
  const response = await fetch(buildApiUrl(`/api/governance/settings/me${query ? `?${query}` : ""}`), {
    method: "GET",
    headers: withAuthHeaders(),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to fetch governance settings"));
  return (await response.json()) as GovernanceSettings;
};

export const updateGovernanceSettings = async (
  payload: Partial<GovernanceSettings>,
  schoolId?: number
): Promise<GovernanceSettings> => {
  const query = toQuery({ school_id: schoolId });
  const response = await fetch(buildApiUrl(`/api/governance/settings/me${query ? `?${query}` : ""}`), {
    method: "PUT",
    headers: { ...withAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to update governance settings"));
  return (await response.json()) as GovernanceSettings;
};

export const createConsent = async (payload: {
  consent_type: string;
  consent_granted: boolean;
  consent_version?: string;
  source?: string;
}): Promise<ConsentItem> => {
  const response = await fetch(buildApiUrl("/api/governance/consents/me"), {
    method: "POST",
    headers: { ...withAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to save consent"));
  return (await response.json()) as ConsentItem;
};

export const fetchMyConsents = async (): Promise<ConsentItem[]> => {
  const response = await fetch(buildApiUrl("/api/governance/consents/me"), {
    method: "GET",
    headers: withAuthHeaders(),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to fetch consents"));
  return (await response.json()) as ConsentItem[];
};

export const createDataRequest = async (payload: {
  request_type: "export" | "delete";
  reason?: string;
  target_user_id?: number;
  details_json?: Record<string, unknown>;
}): Promise<DataRequestItem> => {
  const response = await fetch(buildApiUrl("/api/governance/requests"), {
    method: "POST",
    headers: { ...withAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to create data request"));
  return (await response.json()) as DataRequestItem;
};

export const fetchDataRequests = async (params: {
  school_id?: number;
  status?: string;
  request_type?: string;
  limit?: number;
} = {}): Promise<DataRequestItem[]> => {
  const query = toQuery(params);
  const response = await fetch(buildApiUrl(`/api/governance/requests${query ? `?${query}` : ""}`), {
    method: "GET",
    headers: withAuthHeaders(),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to fetch data requests"));
  return (await response.json()) as DataRequestItem[];
};

export const updateDataRequestStatus = async (
  requestId: number,
  payload: { status: "approved" | "rejected" | "completed"; note?: string }
): Promise<DataRequestItem> => {
  const response = await fetch(buildApiUrl(`/api/governance/requests/${requestId}`), {
    method: "PATCH",
    headers: { ...withAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to update data request"));
  return (await response.json()) as DataRequestItem;
};

export const runRetentionCleanup = async (
  payload: { dry_run: boolean },
  schoolId?: number
): Promise<{
  school_id: number;
  dry_run: boolean;
  deleted_audit_logs: number;
  deleted_import_logs: number;
  deleted_notifications: number;
  summary: string;
}> => {
  const query = toQuery({ school_id: schoolId });
  const response = await fetch(buildApiUrl(`/api/governance/run-retention${query ? `?${query}` : ""}`), {
    method: "POST",
    headers: { ...withAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await parseError(response, "Failed to run retention cleanup"));
  return (await response.json()) as {
    school_id: number;
    dry_run: boolean;
    deleted_audit_logs: number;
    deleted_import_logs: number;
    deleted_notifications: number;
    summary: string;
  };
};
