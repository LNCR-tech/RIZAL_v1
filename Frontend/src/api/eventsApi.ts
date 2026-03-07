const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface Event {
  id: number;
  name: string;
  location: string;
  start_datetime: string;
  end_datetime: string;
  status: EventStatus;
  departments?: Department[];
  programs?: Program[];
  ssg_members?: SSGProfile[];
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

export const fetchUpcomingEvents = async (): Promise<Event[]> => {
  const response = await fetch(`${BASE_URL}/events/?status=upcoming`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error("Network error");
  return await response.json();
};

export const fetchEventsByStatus = async (status: EventStatus): Promise<Event[]> => {
  const response = await fetch(`${BASE_URL}/events/?status=${status}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error("Network error");
  return await response.json();
};

export const fetchEventsAttended = async (): Promise<Event[]> => {
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

  const latestByEvent = new Map<number, Event>();
  for (const record of rows[0].attendances) {
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
