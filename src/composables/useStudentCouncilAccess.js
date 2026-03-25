import { computed, ref, watch } from 'vue'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { getGovernanceAccess, getCampusSsgSetup } from '@/services/backendApi.js'
import { isStudentCouncilUser, resolveStudentCouncilAcronym } from '@/services/studentCouncilManagement.js'

export function useStudentCouncilAccess() {
  const { dashboardState, apiBaseUrl, token } = useDashboardSession()
  const acronym = ref('')
  const governanceMember = ref(false)

  const isCouncilMember = computed(() => {
    return isStudentCouncilUser(dashboardState.user) || governanceMember.value
  })

  watch(
    [apiBaseUrl, token, () => dashboardState.initialized],
    async ([url, authToken, isInit]) => {
      if (!isInit || !url || !authToken) {
        acronym.value = ''
        governanceMember.value = false
        return
      }

      // 1. Check if user is already recognized via profile/roles
      const knownFromProfile = isStudentCouncilUser(dashboardState.user)

      // 2. If not recognized from profile, check governance access endpoint
      if (!knownFromProfile) {
        try {
          const accessPayload = await getGovernanceAccess(url, authToken)
          const units = Array.isArray(accessPayload?.units) ? accessPayload.units : []
          const ssgUnit = units.find((u) => String(u?.unit_type || '').toUpperCase() === 'SSG')
          if (ssgUnit) {
            governanceMember.value = true
          } else {
            governanceMember.value = false
            acronym.value = ''
            return
          }
        } catch {
          governanceMember.value = false
          acronym.value = ''
          return
        }
      }

      // 3. Resolve the acronym dynamically via campus SSG setup
      try {
        const setup = await getCampusSsgSetup(url, authToken)
        if (setup?.unit) {
          acronym.value = resolveStudentCouncilAcronym(setup.unit)
        } else if (dashboardState.user?.ssg_profile) {
          acronym.value = resolveStudentCouncilAcronym(dashboardState.user.ssg_profile)
        } else {
          acronym.value = 'SSG'
        }
      } catch {
        if (dashboardState.user?.ssg_profile) {
          acronym.value = resolveStudentCouncilAcronym(dashboardState.user.ssg_profile)
        } else {
          acronym.value = 'SSG'
        }
      }
    },
    { immediate: true }
  )

  return {
    isCouncilMember,
    acronym,
  }
}
