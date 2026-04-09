import { watchEffect } from 'vue'
import { useRouter } from 'vue-router'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useIdleTimeout } from '@/composables/useIdleTimeout.js'

export function useProtectedShellSession() {
  const router = useRouter()
  const {
    currentUser,
    isAdminSession,
    isSchoolItSession,
    clearDashboardSession,
  } = useDashboardSession()

  const { start: startIdleTimer, stop: stopIdleTimer } = useIdleTimeout(() => {
    clearDashboardSession()
    router.push({ name: 'Login' })
    alert('For your security, you have been automatically signed out due to inactivity.')
  }, {
    immediate: false,
    timeoutMs: 10 * 60 * 1000,
  })

  watchEffect(() => {
    const user = currentUser.value
    if (user && (isAdminSession(user) || isSchoolItSession(user))) {
      startIdleTimer()
      return
    }

    stopIdleTimer()
  })
}

