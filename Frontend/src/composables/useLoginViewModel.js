import { computed, onBeforeMount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'
import { applyTheme, loadUnbrandedTheme } from '@/config/theme.js'
import { consumeSessionExpiredNotice } from '@/services/sessionExpiry.js'

export function useLoginViewModel() {
  const email = ref('')
  const password = ref('')
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
    await login(email.value, password.value)
  }

  function openQuickAttendance() {
    router.push({ name: 'QuickAttendance' })
  }

  return {
    email,
    password,
    isMounted,
    isLoading,
    visibleMessage,
    handleLogin,
    openQuickAttendance,
  }
}
