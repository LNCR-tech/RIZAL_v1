import { computed } from 'vue'
import { useGovernanceAccess } from '@/composables/useGovernanceAccess.js'

export function useStudentCouncilAccess() {
  const {
    hasGovernanceAccess,
    governanceAcronym,
  } = useGovernanceAccess()

  return {
    isCouncilMember: computed(() => hasGovernanceAccess.value),
    acronym: computed(() => governanceAcronym.value),
  }
}
