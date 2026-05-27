import { ref, computed, onMounted, onBeforeMount } from 'vue'
import { useRouter } from 'vue-router'
import { applyTheme, loadUnbrandedTheme } from '@/config/theme.js'
import { verifyResetCode, resolveApiBaseUrl } from '@/services/backendApi.js'

export function useVerifyResetCodeViewModel() {
  const code = ref('')
  const isLoading = ref(false)
  const message = ref('')
  const isSuccess = ref(false)
  const isMounted = ref(false)
  const router = useRouter()

  const email = sessionStorage.getItem('reset_email') || ''

  const messageClass = computed(() => {
    return isSuccess.value
      ? 'text-green-600 text-xs text-center mt-1 mobile-login__message mobile-login__message--success'
      : 'text-red-500 text-xs text-center mt-1 mobile-login__message'
  })

  onBeforeMount(() => {
    if (!email) {
      router.replace({ name: 'ForgotPassword' })
      return
    }
    applyTheme(loadUnbrandedTheme())
  })

  onMounted(() => {
    setTimeout(() => {
      isMounted.value = true
    }, 50)
  })

  async function handleSubmit() {
    const trimmed = code.value.trim()
    if (!trimmed) {
      message.value = 'Please enter the code sent to your email'
      isSuccess.value = false
      return
    }

    isLoading.value = true
    message.value = ''
    isSuccess.value = false

    try {
      const response = await verifyResetCode(resolveApiBaseUrl(), email, trimmed)
      sessionStorage.setItem('reset_token', response.reset_token)
      router.push({ name: 'ResetPassword' })
    } catch (error) {
      if (error?.status === 429) {
        message.value = 'Too many requests. Please try again later.'
      } else if (error?.status === 400) {
        message.value = 'Invalid or expired code. Please check and try again.'
      } else {
        message.value = error?.message || 'An error occurred. Please try again.'
      }
      isSuccess.value = false
    } finally {
      isLoading.value = false
    }
  }

  function goBack() {
    router.push({ name: 'ForgotPassword' })
  }

  return {
    code,
    email,
    isLoading,
    message,
    messageClass,
    isMounted,
    handleSubmit,
    goBack,
  }
}
