import { ref, computed, onMounted, onBeforeMount } from 'vue'
import { useRouter } from 'vue-router'
import { applyTheme, loadUnbrandedTheme } from '@/config/theme.js'
import { resetPassword, resolveApiBaseUrl } from '@/services/backendApi.js'

export function useResetPasswordViewModel() {
  const newPassword = ref('')
  const confirmPassword = ref('')
  const isLoading = ref(false)
  const message = ref('')
  const isSuccess = ref(false)
  const isMounted = ref(false)
  const router = useRouter()

  const resetToken = sessionStorage.getItem('reset_token') || ''

  const messageClass = computed(() => {
    return isSuccess.value
      ? 'text-green-600 text-xs text-center mt-1 mobile-login__message mobile-login__message--success'
      : 'text-red-500 text-xs text-center mt-1 mobile-login__message'
  })

  onBeforeMount(() => {
    if (!resetToken) {
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
    if (!newPassword.value) {
      message.value = 'Please enter a new password'
      isSuccess.value = false
      return
    }
    if (newPassword.value !== confirmPassword.value) {
      message.value = 'Passwords do not match'
      isSuccess.value = false
      return
    }
    if (newPassword.value.length < 8) {
      message.value = 'Password must be at least 8 characters'
      isSuccess.value = false
      return
    }

    isLoading.value = true
    message.value = ''
    isSuccess.value = false

    try {
      await resetPassword(resolveApiBaseUrl(), resetToken, newPassword.value)
      sessionStorage.removeItem('reset_email')
      sessionStorage.removeItem('reset_token')
      isSuccess.value = true
      message.value = 'Password reset successfully. Redirecting to login...'
      setTimeout(() => {
        router.push({ name: 'Login' })
      }, 2000)
    } catch (error) {
      if (error?.status === 400) {
        message.value = 'This reset link has expired. Please start over.'
      } else if (error?.status === 429) {
        message.value = 'Too many requests. Please try again later.'
      } else {
        message.value = error?.message || 'An error occurred. Please try again.'
      }
      isSuccess.value = false
    } finally {
      isLoading.value = false
    }
  }

  function goBack() {
    router.push({ name: 'VerifyResetCode' })
  }

  return {
    newPassword,
    confirmPassword,
    isLoading,
    message,
    messageClass,
    isMounted,
    handleSubmit,
    goBack,
  }
}
