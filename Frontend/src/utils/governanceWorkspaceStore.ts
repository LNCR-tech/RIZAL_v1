import { GovernanceUnitType } from "../api/governanceHierarchyApi";

export type AnnouncementStatus = "draft" | "published" | "archived";

export interface GovernanceAnnouncementRecord {
  id: string;
  schoolId: number;
  governanceUnitId: number;
  governanceUnitType: GovernanceUnitType;
  title: string;
  body: string;
  status: AnnouncementStatus;
  authorName: string;
  createdAt: string;
  updatedAt: string;
}

export interface GovernanceStudentNotesRecord {
  schoolId: number;
  governanceUnitId: number;
  governanceUnitType: GovernanceUnitType;
  userId: number;
  tags: string[];
  notes: string;
  updatedAt: string;
}

interface GovernanceWorkspaceScope {
  schoolId: number;
  governanceUnitId: number;
  governanceUnitType: GovernanceUnitType;
}

const ANNOUNCEMENTS_KEY = "valid8.governance.announcements";
const STUDENT_NOTES_KEY = "valid8.governance.student-notes";
export const GOVERNANCE_WORKSPACE_STORE_EVENT = "valid8:governance-workspace-store";

const readJson = <T>(key: string, fallback: T): T => {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
};

const writeJson = (key: string, value: unknown) => {
  localStorage.setItem(key, JSON.stringify(value));
  window.dispatchEvent(new Event(GOVERNANCE_WORKSPACE_STORE_EVENT));
};

const isSameScope = (
  record: Pick<GovernanceAnnouncementRecord | GovernanceStudentNotesRecord, "schoolId" | "governanceUnitId" | "governanceUnitType">,
  scope: GovernanceWorkspaceScope
) =>
  record.schoolId === scope.schoolId &&
  record.governanceUnitId === scope.governanceUnitId &&
  record.governanceUnitType === scope.governanceUnitType;

export const getStoredGovernanceAnnouncements = (
  scope: GovernanceWorkspaceScope
): GovernanceAnnouncementRecord[] => {
  const all = readJson<GovernanceAnnouncementRecord[]>(ANNOUNCEMENTS_KEY, []);
  return all
    .filter((item) => isSameScope(item, scope))
    .sort((left, right) => Date.parse(right.updatedAt) - Date.parse(left.updatedAt));
};

export const saveGovernanceAnnouncementRecord = (
  scope: GovernanceWorkspaceScope,
  announcement: Omit<
    GovernanceAnnouncementRecord,
    "id" | "schoolId" | "governanceUnitId" | "governanceUnitType" | "createdAt" | "updatedAt"
  > & {
    id?: string;
  }
): GovernanceAnnouncementRecord => {
  const all = readJson<GovernanceAnnouncementRecord[]>(ANNOUNCEMENTS_KEY, []);
  const now = new Date().toISOString();
  const existingIndex = all.findIndex(
    (item) => item.id === announcement.id && isSameScope(item, scope)
  );

  const record: GovernanceAnnouncementRecord =
    existingIndex >= 0
      ? {
          ...all[existingIndex],
          ...announcement,
          ...scope,
          updatedAt: now,
        }
      : {
          id: announcement.id ?? `announcement-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          ...scope,
          title: announcement.title,
          body: announcement.body,
          status: announcement.status,
          authorName: announcement.authorName,
          createdAt: now,
          updatedAt: now,
        };

  const next = existingIndex >= 0 ? [...all] : [...all, record];
  if (existingIndex >= 0) {
    next[existingIndex] = record;
  }
  writeJson(ANNOUNCEMENTS_KEY, next);
  return record;
};

export const deleteGovernanceAnnouncementRecord = (
  scope: GovernanceWorkspaceScope,
  announcementId: string
) => {
  const all = readJson<GovernanceAnnouncementRecord[]>(ANNOUNCEMENTS_KEY, []);
  writeJson(
    ANNOUNCEMENTS_KEY,
    all.filter((item) => !(item.id === announcementId && isSameScope(item, scope)))
  );
};

export const getStoredGovernanceStudentNotes = (
  scope: GovernanceWorkspaceScope,
  userId: number
): GovernanceStudentNotesRecord => {
  const all = readJson<GovernanceStudentNotesRecord[]>(STUDENT_NOTES_KEY, []);
  const existing = all.find((item) => item.userId === userId && isSameScope(item, scope));
  return (
    existing ?? {
      ...scope,
      userId,
      tags: [],
      notes: "",
      updatedAt: new Date().toISOString(),
    }
  );
};

export const saveGovernanceStudentNotes = (
  scope: GovernanceWorkspaceScope,
  userId: number,
  payload: {
    tags: string[];
    notes: string;
  }
): GovernanceStudentNotesRecord => {
  const all = readJson<GovernanceStudentNotesRecord[]>(STUDENT_NOTES_KEY, []);
  const record: GovernanceStudentNotesRecord = {
    ...scope,
    userId,
    tags: payload.tags,
    notes: payload.notes,
    updatedAt: new Date().toISOString(),
  };
  const existingIndex = all.findIndex((item) => item.userId === userId && isSameScope(item, scope));
  const next = existingIndex >= 0 ? [...all] : [...all, record];
  if (existingIndex >= 0) {
    next[existingIndex] = record;
  }
  writeJson(STUDENT_NOTES_KEY, next);
  return record;
};
