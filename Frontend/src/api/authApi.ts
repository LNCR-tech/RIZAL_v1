import { applyTheme, clearBranding, saveTheme } from "./schoolSettingsApi";
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const normalizeRoles = (roles: unknown): string[] => {
  if (!Array.isArray(roles)) return [];
  return roles
    .map((role) => (typeof role === "string" ? role.trim() : ""))
    .filter((role) => role.length > 0);
};

const getStoredToken = () =>
  localStorage.getItem("authToken") ||
  localStorage.getItem("token") ||
  localStorage.getItem("access_token");

const authHeaders = () => {
  const token = getStoredToken();
  if (!token) {
    throw new Error("No authentication token found");
  }
  return { Authorization: `Bearer ${token}` };
};

interface AuthResponseBody {
  access_token?: string | null;
  token_type?: string;
  email?: string;
  roles?: string[];
  user_id?: number;
  first_name?: string;
  last_name?: string;
  school_id?: number | null;
  school_name?: string | null;
  school_code?: string | null;
  logo_url?: string | null;
  primary_color?: string | null;
  secondary_color?: string | null;
  accent_color?: string | null;
  must_change_password?: boolean;
  mfa_required?: boolean;
  mfa_challenge_id?: string;
  mfa_expires_at?: string;
  session_id?: string;
}

const storeAuthSuccess = (data: AuthResponseBody) => {
  const normalizedRoles = normalizeRoles(data.roles);
  const mustChangePassword = Boolean(data.must_change_password);
  const token = data.access_token ?? null;

  if (!token) {
    throw new Error("Authentication token was not returned.");
  }

  localStorage.setItem('authToken', token);
  localStorage.setItem('userData', JSON.stringify({
    email: data.email,
    roles: normalizedRoles,
    id: data.user_id,
    firstName: data.first_name,
    lastName: data.last_name,
    schoolId: data.school_id ?? null,
    schoolName: data.school_name ?? null,
    schoolCode: data.school_code ?? null,
    logoUrl: data.logo_url ?? null,
    mustChangePassword,
    sessionId: data.session_id ?? null,
  }));

  if (data.primary_color) {
    const theme = {
      primary_color: data.primary_color,
      secondary_color: data.secondary_color ?? data.primary_color,
    };
    applyTheme(theme);
    saveTheme(theme);
  }

  return {
    token,
    tokenType: data.token_type ?? "bearer",
    email: data.email,
    roles: normalizedRoles,
    id: data.user_id,
    firstName: data.first_name,
    lastName: data.last_name,
    schoolId: data.school_id ?? null,
    schoolName: data.school_name ?? null,
    schoolCode: data.school_code ?? null,
    logoUrl: data.logo_url ?? null,
    primaryColor: data.primary_color ?? null,
    secondaryColor: data.secondary_color ?? null,
    accentColor: data.accent_color ?? null,
    mustChangePassword,
    sessionId: data.session_id ?? null,
    mfaRequired: false,
    mfaChallengeId: null,
    mfaExpiresAt: null,
  };
};

export const login = async (email: string, password: string) => {
  try {
    // Trim inputs
    email = email.trim();
    password = password.trim();

    const response = await fetch(`${BASE_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Incorrect email or password');
      }
      throw new Error(`Network error: ${response.status}`);
    }

    const data = (await response.json()) as AuthResponseBody;
    const normalizedRoles = normalizeRoles(data.roles);

    if (data.mfa_required) {
      return {
        token: null,
        tokenType: data.token_type ?? "mfa",
        email: data.email ?? email,
        roles: normalizedRoles,
        id: data.user_id,
        firstName: data.first_name,
        lastName: data.last_name,
        schoolId: data.school_id ?? null,
        schoolName: data.school_name ?? null,
        schoolCode: data.school_code ?? null,
        logoUrl: data.logo_url ?? null,
        primaryColor: data.primary_color ?? null,
        secondaryColor: data.secondary_color ?? null,
        accentColor: data.accent_color ?? null,
        mustChangePassword: Boolean(data.must_change_password),
        sessionId: null,
        mfaRequired: true,
        mfaChallengeId: data.mfa_challenge_id ?? null,
        mfaExpiresAt: data.mfa_expires_at ?? null,
      };
    }

    return storeAuthSuccess(data);
  } catch (error) {
    console.error('Login error:', error);
    throw new Error(
      error instanceof Error ? error.message : 'Authentication failed'
    );
  }
};

export const verifyMfaChallenge = async (
  email: string,
  challengeId: string,
  code: string
) => {
  const response = await fetch(`${BASE_URL}/auth/mfa/verify`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email: email.trim(),
      challenge_id: challengeId,
      code: code.trim(),
    }),
  });

  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(
      typeof body?.detail === "string" ? body.detail : "Failed to verify MFA code"
    );
  }

  return storeAuthSuccess(body as AuthResponseBody);
};

// Add this helper function to get the token
export const getAuthToken = () => {
  return getStoredToken();
};

// Add this function to clear auth data
export const logout = () => {
  localStorage.removeItem('authToken');
  localStorage.removeItem('access_token');
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  localStorage.removeItem('userData');
  clearBranding();
};

export const changePassword = async (currentPassword: string, newPassword: string) => {
  const response = await fetch(`${BASE_URL}/auth/change-password`, {
    method: "POST",
    headers: {
      ...authHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });

  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (typeof body?.detail === "string") {
      throw new Error(body.detail);
    }
    throw new Error("Failed to change password");
  }

  try {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      const parsed = JSON.parse(storedUser);
      parsed.mustChangePassword = false;
      localStorage.setItem("user", JSON.stringify(parsed));
    }
  } catch {
    // Ignore local storage parsing errors.
  }

  try {
    const storedUserData = localStorage.getItem("userData");
    if (storedUserData) {
      const parsed = JSON.parse(storedUserData);
      parsed.mustChangePassword = false;
      localStorage.setItem("userData", JSON.stringify(parsed));
    }
  } catch {
    // Ignore local storage parsing errors.
  }

  return body;
};

export const requestForgotPassword = async (email: string): Promise<string> => {
  const response = await fetch(`${BASE_URL}/auth/forgot-password`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email: email.trim() }),
  });

  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (typeof body?.detail === "string") {
      throw new Error(body.detail);
    }
    throw new Error("Failed to submit forgot password request");
  }

  return typeof body?.message === "string"
    ? body.message
    : "If the account exists, a password reset request has been submitted.";
};

// Example of how to use the token in API calls
export const updateEvent = async (eventId: number, eventData: any) => {
  const response = await fetch(`${BASE_URL}/events/${eventId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(eventData),
  });

  if (!response.ok) {
    throw new Error(`Failed to update event: ${response.status}`);
  }

  return await response.json();
};
