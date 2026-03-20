function toFiniteNumber(value) {
  const normalized = Number(value)
  return Number.isFinite(normalized) ? normalized : null
}

export function filterWorkspaceEntitiesBySchool(items, activeSchoolId) {
  if (!Array.isArray(items)) return []

  const normalizedSchoolId = toFiniteNumber(activeSchoolId)
  if (normalizedSchoolId == null) return items

  const hasExplicitSchoolScope = items.some((item) => toFiniteNumber(item?.school_id) != null)
  if (!hasExplicitSchoolScope) {
    return items
  }

  return items.filter((item) => toFiniteNumber(item?.school_id) === normalizedSchoolId)
}
