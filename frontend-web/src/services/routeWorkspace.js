import { resolveSgPreviewVariant } from '@/data/sgPreviewData.js'
import { hasSeenGatherOnboarding } from '@/services/gatherOnboarding.js'

function normalizeContext(value = '') {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, '_')
}

function getRoutePath(routeOrPath = '') {
  if (routeOrPath && typeof routeOrPath === 'object') {
    return String(routeOrPath.path || '')
  }
  return String(routeOrPath || '')
}

export function isGovernancePreviewPath(routeOrPath = null) {
  const path = getRoutePath(routeOrPath)
  return path.startsWith('/exposed/governance') || path.startsWith('/exposed/sg')
}

export function hasGovernancePreviewAccess(routeOrPath = null) {
  if (isGovernancePreviewPath(routeOrPath)) {
    return true
  }

  if (!routeOrPath || typeof routeOrPath !== 'object') {
    return false
  }

  const path = getRoutePath(routeOrPath)
  return path.startsWith('/exposed/dashboard') && routeOrPath?.query?.variant != null
}

function resolveContextFromPath(path = '') {
  const normalizedPath = getRoutePath(path)

  if (normalizedPath.startsWith('/exposed/admin')) return 'admin_preview'
  if (normalizedPath.startsWith('/exposed/workspace')) return 'workspace_preview'
  if (isGovernancePreviewPath(normalizedPath)) return 'governance_preview'
  if (normalizedPath.startsWith('/exposed/dashboard')) return 'dashboard_preview'
  if (normalizedPath.startsWith('/admin')) return 'admin'
  if (normalizedPath.startsWith('/workspace')) return 'workspace'
  if (normalizedPath.startsWith('/governance') || normalizedPath.startsWith('/sg')) return 'governance'
  if (normalizedPath.startsWith('/dashboard')) return 'dashboard'
  return 'dashboard'
}

export function resolveWorkspaceContext(routeOrPath = null) {
  if (routeOrPath && typeof routeOrPath === 'object') {
    const matchedRecords = Array.isArray(routeOrPath.matched) ? [...routeOrPath.matched].reverse() : []
    const matchedContext = matchedRecords
      .map((record) => normalizeContext(record?.meta?.workspaceContext))
      .find(Boolean)

    if (matchedContext) {
      return matchedContext
    }

    const metaContext = normalizeContext(routeOrPath?.meta?.workspaceContext)
    if (metaContext) {
      return metaContext
    }
  }

  return resolveContextFromPath(routeOrPath)
}

export function isPreviewWorkspaceContext(routeOrContext = null) {
  const context = normalizeContext(
    typeof routeOrContext === 'string'
      ? routeOrContext
      : resolveWorkspaceContext(routeOrContext)
  )
  return context.endsWith('_preview')
}

export function isGovernanceWorkspaceContext(routeOrContext = null) {
  const context = normalizeContext(
    typeof routeOrContext === 'string'
      ? routeOrContext
      : resolveWorkspaceContext(routeOrContext)
  )
  return (
    context === 'governance'
    || context === 'governance_preview'
    || context === 'sg'
    || context === 'sg_preview'
  )
}

export function resolveStudentHomeLocation(routeOrPath = null) {
  return isPreviewWorkspaceContext(routeOrPath)
    ? { name: 'PreviewHome' }
    : { name: 'Home' }
}

export function resolveWorkspaceHomeLocation(routeOrPath = null) {
  switch (resolveWorkspaceContext(routeOrPath)) {
    case 'admin':
      return { name: 'AdminHome' }
    case 'admin_preview':
      return { name: 'PreviewAdminHome' }
    case 'workspace':
      return { name: 'SchoolItHome' }
    case 'workspace_preview':
      return { name: 'PreviewSchoolItHome' }
    case 'governance':
    case 'sg':
      return { name: 'SgDashboard' }
    case 'governance_preview':
    case 'sg_preview':
      return withPreservedGovernancePreviewQuery(routeOrPath, { name: 'PreviewSgDashboard' })
    case 'dashboard_preview':
      return { name: 'PreviewHome' }
    default:
      return { name: 'Home' }
  }
}

export function resolveGovernanceWorkspaceLocation(routeOrPath = null) {
  return isPreviewWorkspaceContext(routeOrPath)
    ? withPreservedGovernancePreviewQuery(routeOrPath, { name: 'PreviewSgDashboard' })
    : { name: 'SgDashboard' }
}

export function resolveChatLocation(routeOrPath = null) {
  switch (resolveWorkspaceContext(routeOrPath)) {
    case 'admin':
      return { name: 'AdminAuraChat' }
    case 'admin_preview':
      return { name: 'PreviewAdminAuraChat' }
    case 'workspace':
      return { name: 'SchoolItAuraChat' }
    case 'workspace_preview':
      return { name: 'PreviewSchoolItAuraChat' }
    case 'governance':
    case 'sg':
      return { name: 'SgAuraChat' }
    case 'governance_preview':
    case 'sg_preview':
      return withPreservedGovernancePreviewQuery(routeOrPath, { name: 'PreviewSgAuraChat' })
    case 'dashboard_preview':
      return { name: 'PreviewDashboardAuraChat' }
    default:
      return { name: 'DashboardAuraChat' }
  }
}

export function isGatherWelcomePath(routeOrPath = null) {
  const path = getRoutePath(routeOrPath)
  return path.includes('/gather') && !path.includes('/gather/attendance')
}

export function resolveGatherWelcomeLocation(routeOrPath = null) {
  switch (resolveWorkspaceContext(routeOrPath)) {
    case 'governance':
    case 'sg':
      return { name: 'SgGatherWelcome' }
    case 'governance_preview':
    case 'sg_preview':
      return withPreservedGovernancePreviewQuery(routeOrPath, { name: 'PreviewSgGatherWelcome' })
    case 'dashboard_preview':
      return { name: 'PreviewGatherWelcome' }
    default:
      return { name: 'GatherWelcome' }
  }
}

export function resolveGatherEntryLocation(routeOrPath = null) {
  return hasSeenGatherOnboarding()
    ? resolveGatherAttendanceLocation(routeOrPath)
    : resolveGatherWelcomeLocation(routeOrPath)
}

export function resolveGatherAttendanceLocation(routeOrPath = null) {
  switch (resolveWorkspaceContext(routeOrPath)) {
    case 'governance':
    case 'sg':
      return { name: 'SgGatherAttendance' }
    case 'governance_preview':
    case 'sg_preview':
      return withPreservedGovernancePreviewQuery(routeOrPath, { name: 'PreviewSgGatherAttendance' })
    case 'dashboard_preview':
      return { name: 'PreviewGatherAttendance' }
    default:
      return { name: 'GatherAttendance' }
  }
}

export function resolveEventListLocation(routeOrPath = null) {
  switch (resolveWorkspaceContext(routeOrPath)) {
    case 'governance':
    case 'sg':
      return { name: 'SgEvents' }
    case 'workspace':
      return { name: 'SchoolItSchedule' }
    case 'workspace_preview':
      return { name: 'PreviewSchoolItSchedule' }
    case 'governance_preview':
    case 'sg_preview':
      return withPreservedGovernancePreviewQuery(routeOrPath, { name: 'PreviewSgEvents' })
    case 'dashboard_preview':
      return { name: 'PreviewDashboardSchedule' }
    default:
      return { name: 'Schedule' }
  }
}

export function resolveEventDetailLocation(routeOrPath = null, eventId = null) {
  const normalizedEventId = Number(eventId)
  const params = Number.isFinite(normalizedEventId)
    ? { id: String(normalizedEventId) }
    : {}

  switch (resolveWorkspaceContext(routeOrPath)) {
    case 'governance':
    case 'sg':
      return { name: 'SgEventDetail', params }
    case 'workspace':
      return { name: 'SchoolItEventDetail', params }
    case 'workspace_preview':
      return { name: 'PreviewSchoolItEventDetail', params }
    case 'governance_preview':
    case 'sg_preview':
      return withPreservedGovernancePreviewQuery(routeOrPath, { name: 'PreviewSgEventDetail', params })
    case 'dashboard_preview':
      return { name: 'PreviewEventDetail', params }
    default:
      return { name: 'EventDetail', params }
  }
}

export function resolveAttendanceLocation(routeOrPath = null, eventId = null) {
  const normalizedEventId = Number(eventId)
  const params = Number.isFinite(normalizedEventId)
    ? { id: String(normalizedEventId) }
    : {}

  switch (resolveWorkspaceContext(routeOrPath)) {
    case 'dashboard_preview':
      return { name: 'PreviewAttendance', params }
    case 'workspace_preview':
    case 'governance_preview':
    case 'sg_preview':
    case 'admin_preview':
      return resolveEventDetailLocation(routeOrPath, eventId)
    default:
      return {
        name: 'Attendance',
        params,
      }
  }
}

export function resolveBackFallbackLocation(routeOrPath = null, options = {}) {
  const currentPath = getRoutePath(routeOrPath)

  if (currentPath.includes('/attendance')) {
    return resolveEventDetailLocation(routeOrPath, options?.eventId)
  }

  if (currentPath.includes('/schedule/') || currentPath.includes('/events/')) {
    return resolveEventListLocation(routeOrPath)
  }

  return resolveStudentHomeLocation(routeOrPath)
}

export function hasNavigableHistory(routeOrPath = null) {
  if (typeof window === 'undefined') return false

  const currentPath = getRoutePath(routeOrPath)
  const backTarget = window.history.state?.back

  return Boolean(backTarget && backTarget !== currentPath)
}

export function withPreservedGovernancePreviewQuery(routeOrPath = null, target = null) {
  if (!target || typeof routeOrPath !== 'object') {
    return target
  }

  const currentPath = getRoutePath(routeOrPath)
  const carriesGovernancePreviewVariant =
    isGovernancePreviewPath(currentPath)
    || routeOrPath?.query?.variant != null
  if (!carriesGovernancePreviewVariant) {
    return target
  }

  const variant = resolveSgPreviewVariant(routeOrPath?.query?.variant)

  const targetPath = getRoutePath(target)
  const targetName = typeof target === 'object' ? String(target?.name || '') : ''
  const targetsPreviewRoute = targetPath.startsWith('/exposed/') || targetName.startsWith('Preview')
  if (!targetsPreviewRoute) {
    return target
  }

  return typeof target === 'string'
    ? {
      path: target,
      query: {
        variant,
      },
    }
    : {
      ...target,
      query: {
        variant,
        ...(target?.query || {}),
      },
    }
}

export function toGovernancePath(path = '') {
  const normalizedPath = String(path || '')

  if (normalizedPath === '/sg') return '/governance'
  if (normalizedPath.startsWith('/sg/')) {
    return `/governance/${normalizedPath.slice('/sg/'.length)}`
  }
  if (normalizedPath === '/exposed/sg') return '/exposed/governance'
  if (normalizedPath.startsWith('/exposed/sg/')) {
    return `/exposed/governance/${normalizedPath.slice('/exposed/sg/'.length)}`
  }

  return normalizedPath
}

export function toPreviewGovernancePath(path = '') {
  const canonicalPath = toGovernancePath(path)

  if (canonicalPath === '/governance') return '/exposed/governance'
  if (canonicalPath.startsWith('/governance/')) {
    return `/exposed/governance/${canonicalPath.slice('/governance/'.length)}`
  }

  return canonicalPath
}

export function isCouncilWorkspaceContext(routeOrContext = null) {
  return isGovernanceWorkspaceContext(routeOrContext)
}

export function resolveCouncilWorkspaceLocation(routeOrPath = null) {
  return resolveGovernanceWorkspaceLocation(routeOrPath)
}

export function withPreservedCouncilPreviewQuery(routeOrPath = null, target = null) {
  return withPreservedGovernancePreviewQuery(routeOrPath, target)
}
