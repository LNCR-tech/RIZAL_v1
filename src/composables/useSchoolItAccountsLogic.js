import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useAuth } from '@/composables/useAuth.js'
import { useSchoolItWorkspaceData } from '@/composables/useSchoolItWorkspaceData.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useTheme } from '@/composables/useTheme.js'

export function useSchoolItAccountsLogic() {
  const { logout } = useAuth()
  const { currentUser, initializeDashboardSession } = useDashboardSession()
  const {
    itAccounts,
    lastItPasswordReset,
    statuses,
    initializeSchoolItWorkspaceData,
    refreshSchoolItWorkspaceData,
    resetSchoolItAccountPassword,
  } = useSchoolItWorkspaceData()

  const searchQuery = ref('')
  const feedback = reactive({ type: 'success', message: '' })
  let feedbackTimeoutId = null

  const displayName = computed(() => {
    const user = currentUser.value
    return [user?.first_name, user?.last_name].filter(Boolean).join(' ').trim() || user?.email || 'Campus Admin'
  })
  const avatarUrl = computed(() => currentUser.value?.avatar_url || '')
  const initials = computed(() => abbreviate(displayName.value, 2))
  const schoolName = computed(() => currentUser.value?.school_name || 'My Campus')

  const filteredAccounts = computed(() => {
    const query = searchQuery.value.toLowerCase().trim()
    if (!query) return itAccounts.value
    return itAccounts.value.filter((item) => {
      return (
        item.email?.toLowerCase().includes(query) ||
        item.first_name?.toLowerCase().includes(query) ||
        item.last_name?.toLowerCase().includes(query)
      )
    })
  })

  useTheme()

  watch(lastItPasswordReset, (value) => {
    if (value?.temporary_password) {
      pushFeedback('success', `Temporary password for ${value.email || 'administrator'}: ${value.temporary_password}`)
    }
  })

  onMounted(async () => {
    await initializeDashboardSession().catch(() => null)
    await initializeSchoolItWorkspaceData().catch((error) => pushFeedback('error', error?.message || 'Unable to load accounts.'))
  })

  async function handleLogout() { await logout() }
  async function refreshAccounts() { await refreshSchoolItWorkspaceData().catch(() => null) }

  async function handleResetPassword(account) {
    if (!confirm(`Are you sure you want to reset the password for ${formatPersonName(account.first_name, account.last_name)}?`)) return
    try {
      await resetSchoolItAccountPassword(account.user_id)
    } catch (error) {
      pushFeedback('error', error?.message || 'Unable to reset password.')
    }
  }

  function formatPersonName(firstName, lastName) { return [firstName, lastName].filter(Boolean).join(' ').trim() || 'Administrator' }
  function abbreviate(value, maxLetters = 4) { const words = String(value || '').trim().match(/[A-Za-z0-9]+/g) || []; return words.slice(0, maxLetters).map((word) => word[0]?.toUpperCase() || '').join('.') || 'AD' }

  function pushFeedback(type, message) {
    if (feedbackTimeoutId) window.clearTimeout(feedbackTimeoutId)
    feedback.type = type
    feedback.message = message
    // Use the longer 10s timeout to ensure passwords can be read
    feedbackTimeoutId = window.setTimeout(() => { feedback.type = 'success'; feedback.message = '' }, 10000) 
  }

  return {
    searchQuery,
    feedback,
    filteredAccounts,
    displayName,
    avatarUrl,
    initials,
    schoolName,
    statuses,
    refreshAccounts,
    handleResetPassword,
    handleLogout,
    formatPersonName,
    abbreviate
  }
}
