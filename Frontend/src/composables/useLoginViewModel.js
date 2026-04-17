import { computed, onBeforeMount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'
import { applyTheme, loadUnbrandedTheme } from '@/config/theme.js'
import { consumeSessionExpiredNotice } from '@/services/sessionExpiry.js'
import { getStoredRememberMePreference } from '@/services/userPreferences.js'

export function useLoginViewModel() {
  const email = ref('')
  const password = ref('')
  const rememberMe = ref(getStoredRememberMePreference())
  const isMounted = ref(false)
  const sessionNotice = ref('')
  const router = useRouter()
  const { login, isLoading, error } = useAuth()
  const visibleMessage = computed(() => error.value || sessionNotice.value)

  onBeforeMount(() => {
    applyTheme(loadUnbrandedTheme())
  })

  onMounted(() => {
    sessionNotice.value = consumeSessionExpiredNotice()

    setTimeout(() => {
      isMounted.value = true
    }, 50)
  })

  async function handleLogin() {
    await login(email.value, password.value, { rememberMe: rememberMe.value })
  }

  function openQuickAttendance() {
    router.push({ name: 'QuickAttendance' })
  }

  return {
    email,
    password,
    rememberMe,
    isMounted,
    isLoading,
    visibleMessage,
    handleLogin,
    openQuickAttendance,
  }
}
