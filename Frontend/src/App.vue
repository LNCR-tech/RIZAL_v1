<template>
  <div class="app-safe-area">
    <Transition name="app-boot-fade">
      <div v-if="showInitialBootScreen" class="app-boot-screen" aria-live="polite">
        <AppBootLoader />
      </div>
    </Transition>

    <!-- Offline Banner -->
    <Transition name="offline-banner">
      <div v-if="!networkOnline" class="offline-banner">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="1" y1="1" x2="23" y2="23" />
          <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55" />
          <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39" />
          <path d="M10.71 5.05A16 16 0 0 1 22.56 9" />
          <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88" />
          <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
          <line x1="12" y1="20" x2="12.01" y2="20" />
        </svg>
        <span>You're offline</span>
      </div>
    </Transition>

    <section v-if="fatalErrorMessage" class="app-fatal-screen">
      <div class="app-fatal-card">
        <h1 class="app-fatal-title">Aura needs a refresh</h1>
        <p class="app-fatal-message">{{ fatalErrorMessage }}</p>
        <div class="app-fatal-actions">
          <button type="button" class="app-fatal-btn app-fatal-btn--primary" @click="reloadApp">
            Reload app
          </button>
          <button type="button" class="app-fatal-btn" @click="goToLogin">
            Go to login
          </button>
        </div>
      </div>
    </section>

    <RouterView v-else />

    <Transition name="mobile-fullscreen-hint">
      <button
        v-if="mobileFullscreenHintVisible"
        type="button"
        class="mobile-fullscreen-hint"
        @click="requestMobileFullscreen"
      >
        Tap anywhere to enter fullscreen
      </button>
    </Transition>

    <NotificationsPanel
      :is-open="showNotifications"
      :notifications="notifications"
      :loading="notificationsLoading"
      :error="notificationsError"
      @close="showNotifications = false"
    />

    <SanctionsDeadlineWarningModal
      :open="sanctionsWarningOpen"
      :pending-count="sanctionsWarningPendingCount"
      :deadline="sanctionsWarningDeadline"
      @dismiss="handleSanctionsWarningDismiss"
    />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import AppBootLoader from '@/components/ui/AppBootLoader.vue'
import { mobileFullscreenHintVisible, requestMobileFullscreen } from '@/services/mobileFullscreen.js'
import { isOnline } from '@/composables/useNetworkStatus.js'
import { appFatalErrorMessage, clearAppFatalError } from '@/services/appBootstrap.js'
import { isNavigationPending } from '@/services/navigationState.js'
import { clearDashboardSession, useDashboardSession } from '@/composables/useDashboardSession.js'
import NotificationsPanel from '@/components/dashboard/NotificationsPanel.vue'
import SanctionsDeadlineWarningModal from '@/components/dashboard/SanctionsDeadlineWarningModal.vue'
import { useNotifications } from '@/composables/useNotifications.js'
import { getActiveClearanceDeadline, getMySanctions } from '@/services/backendApi.js'

const router = useRouter()
const route = useRoute()
const networkOnline = computed(() => isOnline.value)
const {
  showNotifications,
  notifications,
  notificationsLoading,
  notificationsError,
  syncNotificationSession,
} = useNotifications()
const fatalErrorMessage = computed(() => appFatalErrorMessage.value)
const hasResolvedInitialRoute = ref(false)
const showInitialBootScreen = computed(() => !hasResolvedInitialRoute.value && isNavigationPending.value)
const sanctionsWarningOpen = ref(false)
const sanctionsWarningPendingCount = ref(0)
const sanctionsWarningDeadline = ref(null)
const sanctionsWarningCheckInFlight = ref(false)
const sanctionsWarningCheckedUserId = ref(null)

const {
  dashboardState,
  apiBaseUrl,
  token,
  currentUser,
} = useDashboardSession()

const isStudentSession = computed(() => {
  const user = currentUser.value
  if (!user) return false
  if (user.student_profile) return true

  const roles = Array.isArray(user.roles) ? user.roles : []
  return roles.some((entry) => {
    const roleName = String(entry?.role?.name || entry?.name || entry || '').trim().toLowerCase()
    return roleName === 'student'
  })
})

watch(
  isNavigationPending,
  (pending) => {
    if (!pending) {
      hasResolvedInitialRoute.value = true
    }
  },
  { immediate: true }
)

watch(
  [() => dashboardState.initialized, apiBaseUrl, token, () => currentUser.value?.id],
  async ([initialized, url, authToken, userId]) => {
    const hasActiveSession = initialized && url && authToken && Number.isFinite(Number(userId))
    await syncNotificationSession({
      baseUrl: hasActiveSession ? url : '',
      token: hasActiveSession ? authToken : '',
      sessionKey: hasActiveSession ? `user:${Number(userId)}` : '',
    })
  },
  { immediate: true }
)

watch(
  [() => dashboardState.initialized, apiBaseUrl, token, () => currentUser.value?.id, isStudentSession],
  async ([initialized, url, authToken, userId, studentSession]) => {
    if (!initialized || !url || !authToken || !studentSession || !Number.isFinite(Number(userId))) return
    if (sanctionsWarningCheckedUserId.value === Number(userId) || sanctionsWarningCheckInFlight.value) return

    sanctionsWarningCheckedUserId.value = Number(userId)
    await evaluateSanctionsWarning(url, authToken)
  },
  { immediate: true }
)

function reloadApp() {
  clearAppFatalError()
  window.location.reload()
}

function goToLogin() {
  clearDashboardSession()
  clearAppFatalError()
  router.replace({ name: 'Login' }).catch(() => null)
}

function hasPendingSanction(record = null) {
  const overallStatus = String(record?.status || '').trim().toLowerCase()
  if (overallStatus === 'pending') return true

  const items = Array.isArray(record?.items) ? record.items : []
  return items.some((item) => String(item?.status || '').trim().toLowerCase() === 'pending')
}

async function evaluateSanctionsWarning(url, authToken) {
  sanctionsWarningCheckInFlight.value = true

  try {
    const [deadline, sanctions] = await Promise.all([
      getActiveClearanceDeadline(url, authToken).catch(() => null),
      getMySanctions(url, authToken).catch(() => []),
    ])

    const deadlineStatus = String(deadline?.status || '').trim().toLowerCase()
    if (!deadline || (deadlineStatus && deadlineStatus !== 'active')) return

    const pendingCount = Array.isArray(sanctions)
      ? sanctions.filter((record) => hasPendingSanction(record)).length
      : 0

    if (pendingCount <= 0) return

    sanctionsWarningPendingCount.value = pendingCount
    sanctionsWarningDeadline.value = deadline
    sanctionsWarningOpen.value = true
  } finally {
    sanctionsWarningCheckInFlight.value = false
  }
}

function handleSanctionsWarningDismiss() {
  sanctionsWarningOpen.value = false

  if (route.name === 'DashboardSanctions') return
  router.push({ name: 'DashboardSanctions' }).catch(() => null)
}
</script>

<style>
.app-safe-area {
  min-height: 100dvh;
  padding-top: env(safe-area-inset-top, 0px);
}

.app-boot-screen,
.app-fatal-screen {
  position: fixed;
  inset: 0;
  z-index: 11000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.app-fatal-screen {
  padding: 24px;
}

.app-boot-screen {
  background: var(--color-surface, #ffffff);
}

.app-fatal-card {
  width: min(100%, 360px);
  border-radius: 24px;
  padding: 28px 24px;
  background: rgba(255,255,255,0.92);
  box-shadow: 0 18px 48px rgba(10,10,10,0.08);
  text-align: center;
  font-family: 'Manrope', sans-serif;
}

.app-fatal-title {
  margin: 0;
  color: #0A0A0A;
  font-size: 22px;
  font-weight: 800;
}

.app-fatal-message {
  margin: 10px 0 0;
  color: #555555;
  font-size: 14px;
  line-height: 1.55;
}

.app-fatal-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 20px;
  flex-wrap: wrap;
}

.app-fatal-btn {
  min-width: 132px;
  border: none;
  border-radius: 999px;
  padding: 12px 18px;
  font-family: 'Manrope', sans-serif;
  font-size: 14px;
  font-weight: 700;
  color: #0A0A0A;
  background: rgba(10,10,10,0.08);
  cursor: pointer;
}

.app-fatal-btn--primary {
  background: var(--color-primary, #0A0A0A);
  color: var(--color-primary-text, #FFFFFF);
}

.app-boot-fade-enter-active,
.app-boot-fade-leave-active {
  transition: opacity 0.22s ease;
}

.app-boot-fade-enter-from,
.app-boot-fade-leave-to {
  opacity: 0;
}

/* Offline Banner */
.offline-banner {
  position: fixed;
  top: env(safe-area-inset-top, 0px);
  left: 0;
  right: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(30, 30, 32, 0.92);
  color: #f5f5f5;
  font-family: 'Manrope', sans-serif;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.01em;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.offline-banner-enter-active,
.offline-banner-leave-active {
  transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.3s ease;
}

.offline-banner-enter-from,
.offline-banner-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}
</style>
