<template>
  <div class="password-gate-page">
    <main class="password-gate-shell">
      <section class="password-gate-content">
        <h1 class="password-gate-title">
          Secure Your<br>
          Account
        </h1>
        <p class="password-gate-copy">
          {{ pageCopy }}
        </p>

        <form class="password-form" @submit.prevent="handleSubmit">
          <label class="password-field">
            <input
              v-model="currentPassword"
              class="password-input"
              type="password"
              placeholder="Old Password"
              autocomplete="current-password"
              :disabled="isLoading"
            >
          </label>

          <label class="password-field">
            <input
              v-model="newPassword"
              class="password-input"
              :type="showNewPassword ? 'text' : 'password'"
              placeholder="New Password"
              autocomplete="new-password"
              :disabled="isLoading"
            >
            <button
              type="button"
              class="password-visibility"
              :aria-label="showNewPassword ? 'Hide new password' : 'Show new password'"
              @click="showNewPassword = !showNewPassword"
            >
              <component :is="showNewPassword ? EyeOff : Eye" :size="18" />
            </button>
          </label>

          <label class="password-field">
            <input
              v-model="confirmPassword"
              class="password-input"
              :type="showConfirmPassword ? 'text' : 'password'"
              placeholder="Confirm New Password"
              autocomplete="new-password"
              :disabled="isLoading"
            >
            <button
              type="button"
              class="password-visibility"
              :aria-label="showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'"
              @click="showConfirmPassword = !showConfirmPassword"
            >
              <component :is="showConfirmPassword ? EyeOff : Eye" :size="18" />
            </button>
          </label>

          <p v-if="feedbackMessage" class="password-feedback" :class="feedbackClass">
            {{ feedbackMessage }}
          </p>

          <SecurityActionPill
            :icon="ArrowRight"
            label="Continue"
            type="submit"
            :loading="isLoading"
          />
        </form>
      </section>
    </main>

    <button v-if="isRequiredFlow" class="password-signout" type="button" @click="handleSignOut">
      Sign Out
    </button>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, Eye, EyeOff } from 'lucide-vue-next'
import SecurityActionPill from '@/components/security/SecurityActionPill.vue'
import { changePassword, resolveApiBaseUrl } from '@/services/backendApi.js'
import { applyTheme, loadTheme } from '@/config/theme.js'
import { getStoredAuthMeta, patchStoredAuthMeta } from '@/services/localAuth.js'
import {
  clearDashboardSession,
  getDefaultAuthenticatedRoute,
  initializeDashboardSession,
  sessionNeedsFaceRegistration,
} from '@/composables/useDashboardSession.js'

const props = defineProps({
  flow: {
    type: String,
    default: 'required',
  },
})

const router = useRouter()
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const error = ref('')
const success = ref('')
const isLoading = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)

const isRequiredFlow = computed(() => props.flow !== 'settings')
const authMeta = computed(() => getStoredAuthMeta())
const pageCopy = computed(() =>
  isRequiredFlow.value
    ? 'Update your temporary password to continue.'
    : 'Update your password to keep your account secure.'
)
const feedbackMessage = computed(() => error.value || success.value)
const feedbackClass = computed(() => ({
  'password-feedback--error': Boolean(error.value),
  'password-feedback--success': Boolean(success.value),
}))

function applyPasswordTheme() {
  applyTheme(loadTheme({
    school_name: authMeta.value?.schoolName || null,
    school_code: authMeta.value?.schoolCode || null,
    logo_url: authMeta.value?.logoUrl || null,
    primary_color: authMeta.value?.primaryColor || '#AAFF00',
    secondary_color: authMeta.value?.secondaryColor || '#FFD400',
    accent_color: authMeta.value?.accentColor || '#000000',
  }))
}

async function goToNextStep() {
  await initializeDashboardSession(true)
  if (isRequiredFlow.value) {
    router.replace(
      sessionNeedsFaceRegistration()
        ? { name: 'FaceRegistration' }
        : getDefaultAuthenticatedRoute()
    )
    return
  }

  clearDashboardSession()
  router.replace({ name: 'Login' })
}

async function handleSignOut() {
  clearDashboardSession()
  router.replace({ name: 'Login' })
}

onMounted(async () => {
  applyPasswordTheme()

  const token = localStorage.getItem('aura_token')
  if (!token) {
    router.replace({ name: 'Login' })
    return
  }

  if (isRequiredFlow.value && !authMeta.value?.mustChangePassword) {
    try {
      await goToNextStep()
    } catch {
      clearDashboardSession()
      router.replace({ name: 'Login' })
    }
  }
})

async function handleSubmit() {
  error.value = ''
  success.value = ''

  if (!currentPassword.value || !newPassword.value || !confirmPassword.value) {
    error.value = 'Enter your current password and the new password twice.'
    return
  }

  if (newPassword.value !== confirmPassword.value) {
    error.value = 'The new password fields must match.'
    return
  }

  if (newPassword.value.length < 8) {
    error.value = 'New password must be at least 8 characters.'
    return
  }

  const token = localStorage.getItem('aura_token')
  if (!token) {
    clearDashboardSession()
    router.replace({ name: 'Login' })
    return
  }

  isLoading.value = true

  try {
    await changePassword(resolveApiBaseUrl(), token, {
      current_password: currentPassword.value,
      new_password: newPassword.value,
    })

    patchStoredAuthMeta({
      mustChangePassword: false,
    })

    success.value = isRequiredFlow.value
      ? 'Password updated. Loading your account...'
      : 'Password updated successfully. Signing you out...'

    await goToNextStep()
  } catch (err) {
    error.value = err?.message || 'Failed to change password.'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.password-gate-page {
  min-height: 100vh;
  background: var(--color-bg, #ebebeb);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 28px;
  padding: 36px 22px;
  font-family: 'Manrope', sans-serif;
}

.password-gate-shell {
  width: min(100%, 360px);
}

.password-gate-content {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.password-gate-title {
  margin: 0;
  font-size: clamp(48px, 15vw, 62px);
  line-height: 0.94;
  letter-spacing: -0.07em;
  color: #0a0a0a;
}

.password-gate-copy {
  margin: 0;
  max-width: 220px;
  font-size: 15px;
  line-height: 1.25;
  color: #252522;
}

.password-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 10px;
}

.password-field {
  position: relative;
  display: flex;
  align-items: center;
}

.password-input {
  width: 100%;
  min-height: 60px;
  padding: 0 56px 0 20px;
  border-radius: 999px;
  border: 1.5px solid rgba(10, 10, 10, 0.94);
  background: rgba(255, 255, 255, 0.72);
  color: #111111;
  font-size: 14px;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.password-input::placeholder {
  color: #161616;
  opacity: 1;
}

.password-input:focus {
  border-color: color-mix(in srgb, var(--color-primary, #aaff00) 42%, #0a0a0a 58%);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-primary, #aaff00) 18%, transparent);
}

.password-input:disabled {
  opacity: 0.72;
  cursor: not-allowed;
}

.password-visibility {
  position: absolute;
  right: 18px;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: #595954;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.password-feedback {
  min-height: 20px;
  margin: 8px 0 0;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.35;
  text-align: center;
}

.password-feedback--error {
  color: #e23c3c;
}

.password-feedback--success {
  color: color-mix(in srgb, var(--color-primary, #aaff00) 48%, #111111 52%);
}

.password-signout {
  border: none;
  background: transparent;
  color: #3a3a36;
  font-size: 15px;
  font-weight: 500;
}

@media (min-width: 900px) {
  .password-gate-page {
    padding: 48px 24px;
  }
}
</style>
