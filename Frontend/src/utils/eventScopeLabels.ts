type NamedScopeItem = {
  name: string;
};

const formatScopeItems = (items?: NamedScopeItem[] | null, allLabel = "All") => {
  const safeItems = items ?? [];
  return safeItems.map((item) => item.name).join(", ") || allLabel;
};

export const formatEventDepartments = (departments?: NamedScopeItem[] | null) =>
  formatScopeItems(departments, "All");

export const formatEventPrograms = (programs?: NamedScopeItem[] | null) =>
  formatScopeItems(programs, "All");

