export const formatUserDisplayName = (user: {
  first_name?: string | null;
  middle_name?: string | null;
  last_name?: string | null;
  email?: string | null;
}) => {
  const parts = [user.first_name, user.middle_name, user.last_name]
    .map((value) => value?.trim())
    .filter(Boolean);
  return parts.length ? parts.join(" ") : user.email || "Unknown User";
};

export const getInitials = (name: string) =>
  name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("");

export const getAvatarToneClass = (seed: number) => {
  const tones = [
    "ssg-avatar--blue",
    "ssg-avatar--gold",
    "ssg-avatar--teal",
    "ssg-avatar--coral",
    "ssg-avatar--slate",
  ];
  return tones[Math.abs(seed) % tones.length];
};

export const toStatusToneClass = (status: string) => {
  const normalized = status.toLowerCase();
  if (normalized === "published" || normalized === "active") return "ssg-badge--published";
  if (normalized === "draft") return "ssg-badge--draft";
  if (normalized === "archived") return "ssg-badge--archived";
  return "ssg-badge--member";
};

export const formatDateLabel = (value: string) =>
  new Intl.DateTimeFormat("en-PH", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));

export const truncateText = (value: string, length: number) =>
  value.length > length ? `${value.slice(0, length - 1)}...` : value;
