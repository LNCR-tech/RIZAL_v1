import { useRoute, useRouter } from 'vue-router'
import { withPreservedGovernancePreviewQuery } from '@/services/routeWorkspace.js'

const ROOT_PATH_MATCHES = new Set([
  '/dashboard',
  '/exposed/dashboard',
  '/workspace',
  '/exposed/workspace',
  '/admin',
  '/exposed/admin',
  '/governance',
  '/exposed/governance',
  '/sg',
  '/exposed/sg',
])

export function useMobileBottomNav() {
  const router = useRouter()
  const route = useRoute()

  function isActive(item) {
    const path = String(item?.route || '')
    if (!path) return false

    if (ROOT_PATH_MATCHES.has(path)) {
      return route.path === path || route.path === `${path}/`
    }

    const matchPrefixes = Array.isArray(item?.matchPrefixes) ? item.matchPrefixes : []
    return route.path.startsWith(path) || matchPrefixes.some((prefix) => route.path.startsWith(prefix))
  }

  function navigate(target) {
    const nextLocation = withPreservedGovernancePreviewQuery(route, target)
    const resolvedTarget = router.resolve(nextLocation)
    if (route.fullPath === resolvedTarget.fullPath) return
    router.push(nextLocation)
  }

  return {
    route,
    isActive,
    navigate,
  }
}
