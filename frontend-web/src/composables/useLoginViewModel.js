import { computed, onBeforeMount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'
import { useGoogleLogin } from '@/composables/useGoogleLogin.js'
import { applyTheme, loadUnbrandedTheme } from '@/config/theme.js'
import { consumeSessionExpiredNotice } from '@/services/sessionExpiry.js'

export function useLoginViewModel() {
  const email = ref('')
  const password = ref('')
  const isMounted = ref(false)
  const sessionNotice = ref('')
  const router = useRouter()
  const { login, isLoading, error } = useAuth()
  const {
    loginWithGoogleCredential,
    isLoading: googleLoading,
    error: googleError,
  } = useGoogleLogin()
  const visibleMessage = computed(() => error.value || googleError.value || sessionNotice.value)

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

  async function handleGoogleCredential(credential) {
    await loginWithGoogleCredential(credential)
  }

  function goToForgotPassword() {
    router.push({ name: 'ForgotPassword' })
  }

  return {
    email,
    password,
    isMounted,
    isLoading,
    googleLoading,
    visibleMessage,
    handleLogin,
    handleGoogleCredential,
    goToForgotPassword,
  }
}
