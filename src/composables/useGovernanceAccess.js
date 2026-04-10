import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useSgPreviewBundle } from '@/composables/useSgPreviewBundle.js'
import { getGovernanceAccess } from '@/services/backendApi.js'
import {
  normalizeGovernanceContext,
  resolvePreferredGovernanceUnit,
} from '@/services/governanceScope.js'
import { resolveStudentCouncilAcronym } from '@/services/studentCouncilManagement.js'
import {
  hasGovernancePreviewAccess,
  isGovernanceWorkspaceContext,
  resolveGovernanceWorkspaceLocation,
} from '@/services/routeWorkspace.js'

const cachedHasGovernanceAccess = ref(false)
const cachedGovernanceAcronym = ref('')
const cachedGovernanceContext = ref('')
const cachedGovernanceUnitName = ref('')
let hasFetched = false

export function useGovernanceAccess() {
  const route = useRoute()
  const { dashboardState, apiBaseUrl, token } = useDashboardSession()
  const previewGovernanceAccess = computed(() => hasGovernancePreviewAccess(route))
  const { previewBundle } = useSgPreviewBundle(previewGovernanceAccess)

  const hasGovernanceAccess = computed(() => (
    previewGovernanceAccess.value
      ? Boolean(previewBundle.value?.activeUnit)
      : cachedHasGovernanceAccess.value
  ))

  const governanceAcronym = computed(() => {
    if (previewGovernanceAccess.value) {
      return (
        previewBundle.value?.activeUnit?.unit_code
        || resolveStudentCouncilAcronym(previewBundle.value?.activeUnit)
        || ''
      )
    }

    return cachedGovernanceAcronym.value
  })

  const governanceContext = computed(() => {
    if (previewGovernanceAccess.value) {
      return normalizeGovernanceContext(previewBundle.value?.activeUnit?.unit_type)
    }

    return cachedGovernanceContext.value
  })

  const governanceUnitName = computed(() => {
    if (previewGovernanceAccess.value) {
      return String(previewBundle.value?.activeUnit?.unit_name || '').trim()
    }

    return cachedGovernanceUnitName.value
  })

  const governanceWorkspaceLocation = computed(() => (
    resolveGovernanceWorkspaceLocation(route)
  ))

  const isGovernanceWorkspaceActive = computed(() => (
    isGovernanceWorkspaceContext(route)
  ))

  watch(
    [apiBaseUrl, token, () => dashboardState.initialized, previewGovernanceAccess],
    async ([url, authToken, isInitialized, previewActive]) => {
      if (previewActive) return

      if (!isInitialized || !url || !authToken) {
        cachedHasGovernanceAccess.value = false
        cachedGovernanceAcronym.value = ''
        cachedGovernanceContext.value = ''
        cachedGovernanceUnitName.value = ''
        hasFetched = false
        return
      }

      if (hasFetched) {
        getGovernanceAccess(url, authToken).then(updateCache).catch(() => {})
        return
      }

      try {
        updateCache(await getGovernanceAccess(url, authToken))
        hasFetched = true
      } catch {
        cachedHasGovernanceAccess.value = false
        cachedGovernanceAcronym.value = ''
        cachedGovernanceContext.value = ''
        cachedGovernanceUnitName.value = ''
      }
    },
    { immediate: true }
  )

  return {
    hasGovernanceAccess,
    governanceAcronym,
    governanceContext,
    governanceUnitName,
    governanceWorkspaceLocation,
    isGovernanceWorkspaceActive,
  }
}

function updateCache(access = null) {
  const governanceUnit = resolvePreferredGovernanceUnit(access)

  cachedHasGovernanceAccess.value = Boolean(governanceUnit)
  cachedGovernanceAcronym.value = governanceUnit
    ? governanceUnit.unit_code || resolveStudentCouncilAcronym(governanceUnit) || ''
    : ''
  cachedGovernanceContext.value = normalizeGovernanceContext(governanceUnit?.unit_type)
  cachedGovernanceUnitName.value = governanceUnit
    ? String(governanceUnit.unit_name || '').trim()
    : ''
}
