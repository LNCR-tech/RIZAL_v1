export type AnnouncementStatus = "draft" | "published" | "archived";

export interface SsgAnnouncementRecord {
  id: string;
  schoolId: number;
  title: string;
  body: string;
  status: AnnouncementStatus;
  authorName: string;
  createdAt: string;
  updatedAt: string;
}

export interface StudentGovernanceNotesRecord {
  schoolId: number;
  userId: number;
  tags: string[];
  notes: string;
  updatedAt: string;
}

const ANNOUNCEMENTS_KEY = "valid8.ssg.announcements";
const STUDENT_NOTES_KEY = "valid8.ssg.student-notes";
export const SSG_WORKSPACE_STORE_EVENT = "valid8:ssg-workspace-store";

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
  window.dispatchEvent(new Event(SSG_WORKSPACE_STORE_EVENT));
};

export const getStoredAnnouncements = (schoolId: number): SsgAnnouncementRecord[] => {
  const all = readJson<SsgAnnouncementRecord[]>(ANNOUNCEMENTS_KEY, []);
  return all
    .filter((item) => item.schoolId === schoolId)
    .sort((left, right) => Date.parse(right.updatedAt) - Date.parse(left.updatedAt));
};

export const saveAnnouncementRecord = (
  schoolId: number,
  announcement: Omit<SsgAnnouncementRecord, "id" | "schoolId" | "createdAt" | "updatedAt"> & {
    id?: string;
  }
): SsgAnnouncementRecord => {
  const all = readJson<SsgAnnouncementRecord[]>(ANNOUNCEMENTS_KEY, []);
  const now = new Date().toISOString();
  const existingIndex = all.findIndex(
    (item) => item.id === announcement.id && item.schoolId === schoolId
  );

  const record: SsgAnnouncementRecord =
    existingIndex >= 0
      ? {
          ...all[existingIndex],
          ...announcement,
          schoolId,
          updatedAt: now,
        }
      : {
          id: announcement.id ?? `announcement-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          schoolId,
          title: announcement.title,
          body: announcement.body,
          status: announcement.status,
          authorName: announcement.authorName,
          createdAt: now,
          updatedAt: now,
        };

  const next = existingIndex >= 0 ? [...all] : [...all, record];
  if (existingIndex >= 0) next[existingIndex] = record;
  writeJson(ANNOUNCEMENTS_KEY, next);
  return record;
};

export const deleteAnnouncementRecord = (schoolId: number, announcementId: string) => {
  const all = readJson<SsgAnnouncementRecord[]>(ANNOUNCEMENTS_KEY, []);
  writeJson(
    ANNOUNCEMENTS_KEY,
    all.filter((item) => !(item.schoolId === schoolId && item.id === announcementId))
  );
};

export const getStoredStudentGovernanceNotes = (
  schoolId: number,
  userId: number
): StudentGovernanceNotesRecord => {
  const all = readJson<StudentGovernanceNotesRecord[]>(STUDENT_NOTES_KEY, []);
  const existing = all.find((item) => item.schoolId === schoolId && item.userId === userId);
  return (
    existing ?? {
      schoolId,
      userId,
      tags: [],
      notes: "",
      updatedAt: new Date().toISOString(),
    }
  );
};

export const saveStudentGovernanceNotes = (
  schoolId: number,
  userId: number,
  payload: {
    tags: string[];
    notes: string;
  }
): StudentGovernanceNotesRecord => {
  const all = readJson<StudentGovernanceNotesRecord[]>(STUDENT_NOTES_KEY, []);
  const now = new Date().toISOString();
  const record: StudentGovernanceNotesRecord = {
    schoolId,
    userId,
    tags: payload.tags,
    notes: payload.notes,
    updatedAt: now,
  };
  const existingIndex = all.findIndex((item) => item.schoolId === schoolId && item.userId === userId);
  const next = existingIndex >= 0 ? [...all] : [...all, record];
  if (existingIndex >= 0) next[existingIndex] = record;
  writeJson(STUDENT_NOTES_KEY, next);
  return record;
};
