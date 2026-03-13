const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const EVENTS_CACHE_TTL_MS = 60_000;

export interface Event {
  id: number;
  name: string;
  location: string;
  geo_latitude?: number | null;
  geo_longitude?: number | null;
  geo_radius_m?: number | null;
  geo_required?: boolean;
  geo_max_accuracy_m?: number | null;
  late_threshold_minutes?: number;
  start_datetime: string;
  end_datetime: string;
  status: EventStatus;
  departments?: Department[];
  programs?: Program[];
  ssg_members?: SSGProfile[];
}

export interface AttendanceRecord {
  id: number;
  event_id: number;
  event_name: string;
  time_in: string;
  time_out: string | null;
  status: "present" | "late" | "absent" | "excused";
  method: "face_scan" | "manual";
  duration_minutes: number | null;
}

interface Department {
  id: number;
  name: string;
}

interface Program {
  id: number;
  name: string;
}

interface SSGProfile {
  id: number;
  user_id: number;
  position: string;
  user: User;
}

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
}

type EventStatus = "upcoming" | "ongoing" | "completed" | "cancelled";

type EventCacheEntry = {
  data: Event[];
  expiresAt: number;
};

const eventsCache = new Map<string, EventCacheEntry>();

const getAuthHeaders = (): HeadersInit => {
  const token =
    localStorage.getItem("authToken") ||
    localStorage.getItem("token") ||
    localStorage.getItem("access_token");

  if (!token) {
    throw new Error("No authentication token found");
  }

  return {
    Authorization: `Bearer ${token}`,
  };
};

const getCachedEvents = (key: string): Event[] | null => {
  const entry = eventsCache.get(key);
  if (!entry) {
    return null;
  }

  if (Date.now() > entry.expiresAt) {
    eventsCache.delete(key);
    return null;
  }

  return entry.data;
};

const setCachedEvents = (key: string, data: Event[]) => {
  eventsCache.set(key, {
    data,
    expiresAt: Date.now() + EVENTS_CACHE_TTL_MS,
  });
};

const hydrateStatusCache = (events: Event[]) => {
  const statuses: EventStatus[] = [
    "upcoming",
    "ongoing",
    "completed",
    "cancelled",
  ];

  for (const status of statuses) {
    setCachedEvents(
      `status:${status}`,
      events.filter((event) => event.status === status)
    );
  }
};

export const fetchAllEvents = async (forceRefresh = false): Promise<Event[]> => {
  const cacheKey = "all";
  const cachedEvents = forceRefresh ? null : getCachedEvents(cacheKey);
  if (cachedEvents) {
    return cachedEvents;
  }

  const response = await fetch(`${BASE_URL}/events/`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error("Network error");

  const data = (await response.json()) as Event[];
  setCachedEvents(cacheKey, data);
  hydrateStatusCache(data);
  return data;
};

export const fetchUpcomingEvents = async (): Promise<Event[]> => {
  return fetchEventsByStatus("upcoming");
};

export const fetchEventsByStatus = async (
  status: EventStatus,
  forceRefresh = false
): Promise<Event[]> => {
  const cacheKey = `status:${status}`;
  const cachedEvents = forceRefresh ? null : getCachedEvents(cacheKey);
  if (cachedEvents) {
    return cachedEvents;
  }

  const allEvents = forceRefresh ? null : getCachedEvents("all");
  if (allEvents) {
    const filteredEvents = allEvents.filter((event) => event.status === status);
    setCachedEvents(cacheKey, filteredEvents);
    return filteredEvents;
  }

  const response = await fetch(`${BASE_URL}/events/?status=${status}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error("Network error");

  const data = (await response.json()) as Event[];
  setCachedEvents(cacheKey, data);
  return data;
};

export const fetchEventsAttended = async (): Promise<Event[]> => {
  const records = await fetchMyAttendanceRecords();

  const latestByEvent = new Map<number, Event>();
  for (const record of records) {
    const eventId = Number(record.event_id);
    if (!Number.isFinite(eventId)) continue;

    latestByEvent.set(eventId, {
      id: eventId,
      name: record.event_name || `Event #${eventId}`,
      location: "N/A",
      start_datetime: record.time_in || "",
      end_datetime: record.time_out || record.time_in || "",
      status: "completed",
    });
  }

  return Array.from(latestByEvent.values());
};

export const fetchMyAttendanceRecords = async (): Promise<AttendanceRecord[]> => {
  const response = await fetch(`${BASE_URL}/attendance/me/records`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error(`Failed to fetch attendance history: ${response.status}`);

  const rows = (await response.json()) as Array<{
    attendances?: Array<{
      event_id: number;
      event_name?: string;
      time_in?: string;
      time_out?: string | null;
    }>;
  }>;

  if (!Array.isArray(rows) || rows.length === 0 || !Array.isArray(rows[0].attendances)) {
    return [];
  }

  return rows[0].attendances as AttendanceRecord[];
};
