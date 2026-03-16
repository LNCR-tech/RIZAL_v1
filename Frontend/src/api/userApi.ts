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
  const raw = await response.text().catch(() => "");
  if (!raw.trim()) return fallback;

  let body:
    | {
        detail?: unknown;
        message?: unknown;
      }
    | null = null;

  try {
    body = JSON.parse(raw) as {
      detail?: unknown;
      message?: unknown;
    };
  } catch {
    return raw.trim() || fallback;
  }

  if (!body || typeof body !== "object") return raw.trim() || fallback;

  if (typeof body.detail === "string" && body.detail.trim()) return body.detail;

  if (body.detail && typeof body.detail === "object") {
    const nestedMessage = (body.detail as { message?: unknown; reason?: unknown }).message;
    if (typeof nestedMessage === "string" && nestedMessage.trim()) return nestedMessage;

    const nestedReason = (body.detail as { reason?: unknown }).reason;
    if (typeof nestedReason === "string" && nestedReason.trim()) return nestedReason;

    return JSON.stringify(body.detail);
  }

  if (typeof body.message === "string" && body.message.trim()) return body.message;

  return raw.trim() || fallback;
};

export interface UserRoleAssignment {
  role: {
    name: string;
  };
}

export interface SchoolScopedUser {
  id: number;
  email: string;
  first_name: string;
  middle_name?: string | null;
  last_name: string;
  school_id?: number | null;
  is_active: boolean;
  created_at: string;
  roles: UserRoleAssignment[];
}

export interface DepartmentSummary {
  id: number;
  name: string;
}

export interface ProgramSummary {
  id: number;
  name: string;
}

export interface StudentProfileSummary {
  id: number;
  student_id?: string | null;
  year_level?: number | null;
  department?: DepartmentSummary | null;
  program?: ProgramSummary | null;
  department_id?: number | null;
  program_id?: number | null;
}

export interface SchoolScopedUserWithRelations extends SchoolScopedUser {
  student_profile?: StudentProfileSummary | null;
}

export const fetchUsersByRole = async (roleName: string): Promise<SchoolScopedUser[]> => {
  const response = await fetch(buildApiUrl(`/users/by-role/${encodeURIComponent(roleName)}`), {
    method: "GET",
    headers: withAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(await parseError(response, `Failed to fetch users for role '${roleName}'`));
  }

  return (await response.json()) as SchoolScopedUser[];
};

export const fetchSchoolScopedUsers = async ({
  skip = 0,
  limit = 300,
}: {
  skip?: number;
  limit?: number;
} = {}): Promise<SchoolScopedUserWithRelations[]> => {
  const response = await fetch(buildApiUrl(`/users/?skip=${skip}&limit=${limit}`), {
    method: "GET",
    headers: withAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(await parseError(response, "Failed to fetch campus users"));
  }

  return (await response.json()) as SchoolScopedUserWithRelations[];
};
