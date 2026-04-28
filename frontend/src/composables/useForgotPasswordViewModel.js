import { ref, computed, onMounted, onBeforeMount } from 'vue'
import { useRouter } from 'vue-router'
import { applyTheme, loadUnbrandedTheme } from '@/config/theme.js'
import { apiClient } from '@/services/api.js'

export function useForgotPasswordViewModel() {
  const email = ref('')
  const isLoading = ref(false)
  const message = ref('')
  const isSuccess = ref(false)
  const isMounted = ref(false)
  const router = useRouter()

  const messageClass = computed(() => {
    return isSuccess.value 
      ? 'text-green-600 text-xs text-center mt-1 mobile-login__message mobile-login__message--success'
      : 'text-red-500 text-xs text-center mt-1 mobile-login__message'
  })

  onBeforeMount(() => {
    applyTheme(loadUnbrandedTheme())
  })

  onMounted(() => {
    setTimeout(() => {
      isMounted.value = true
    }, 50)
  })

  async function handleSubmit() {
    if (!email.value.trim()) {
      message.value = 'Please enter your email address'
      isSuccess.value = false
      return
    }

    isLoading.value = true
    message.value = ''
    isSuccess.value = false

    try {
      const response = await apiClient.post('/auth/forgot-password', {
        email: email.value.trim()
      })
      
      message.value = response.data.message || 'If an eligible student account exists, its password has been reset to the default password.'
      isSuccess.value = true
      
      setTimeout(() => {
        router.push({ name: 'Login' })
      }, 3000)
    } catch (error) {
      if (error.response?.status === 429) {
        message.value = 'Too many requests. Please try again later.'
      } else {
        message.value = error.response?.data?.detail || 'An error occurred. Please try again.'
      }
      isSuccess.value = false
    } finally {
      isLoading.value = false
    }
  }

  function goBack() {
    router.push({ name: 'Login' })
  }

  return {
    email,
    isLoading,
    message,
    messageClass,
    isMounted,
    handleSubmit,
    goBack,
  }
}
