<template>
  <div class="security-page">
    <main class="security-shell">
      <SecurityHeaderBar
        class="dashboard-enter dashboard-enter--1"
        title="Security"
        :icon="Shield"
        back-label="Back to profile"
        @back="goBack"
      />

      <section class="security-panel dashboard-enter dashboard-enter--2">
        <span class="security-panel__icon">
          <Shield :size="20" />
        </span>
        <div class="security-panel__copy">
          <p class="security-panel__eyebrow">Account Security</p>
          <h2>Manage your password and registered face.</h2>
        </div>
      </section>

      <section class="security-actions" aria-label="Security settings">
        <p v-if="noticeMessage" class="security-notice dashboard-enter dashboard-enter--3">{{ noticeMessage }}</p>

        <div class="security-action-list">
          <button
            v-for="(action, index) in securityActions"
            :key="action.label"
            class="security-action-card dashboard-enter"
            :style="{ '--dashboard-enter-delay': `${index * 80 + 180}ms` }"
            type="button"
            @click="action.handleClick"
          >
            <span class="security-action-card__icon">
              <component :is="action.icon" :size="20" />
            </span>
            <span class="security-action-card__copy">
              <strong>{{ action.label }}</strong>
              <small>{{ action.description }}</small>
            </span>
            <ArrowRight class="security-action-card__arrow" :size="18" />
          </button>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight, KeyRound, ScanFace, Shield } from 'lucide-vue-next'
import SecurityHeaderBar from '@/components/security/SecurityHeaderBar.vue'
import { applyTheme, loadTheme } from '@/config/theme.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { studentDashboardPreviewData } from '@/data/studentDashboardPreview.js'
import { getStoredAuthMeta } from '@/services/localAuth.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const router = useRouter()
const route = useRoute()
const { currentUser, schoolSettings } = useDashboardSession()
const previewNotice = ref('')

const securityActions = [
  {
    label: 'Change Password',
    description: 'Update the password used to sign in.',
    icon: KeyRound,
    handleClick: handlePasswordClick,
  },
  {
    label: 'Change Registered Face',
    description: 'Replace the face used for attendance scans.',
    icon: ScanFace,
    handleClick: handleFaceClick,
  },
]

const noticeMessage = computed(() => {
  if (previewNotice.value) {
    return previewNotice.value
  }
  if (route.query?.done === 'password') {
    return 'Password updated successfully.'
  }
  if (route.query?.done === 'face') {
    return 'Face ID updated successfully.'
  }
  return ''
})

function applySecurityTheme() {
  if (props.preview) {
    const previewSettings = studentDashboardPreviewData.schoolSettings
    applyTheme(loadTheme({
      school_name: previewSettings.school_name,
      school_code: previewSettings.school_code,
      logo_url: previewSettings.logo_url,
      primary_color: previewSettings.primary_color,
      secondary_color: previewSettings.secondary_color,
      accent_color: previewSettings.accent_color,
    }))
    return
  }

  const authMeta = getStoredAuthMeta()
  applyTheme(loadTheme({
    school_name: currentUser.value?.school_name || authMeta?.schoolName || null,
    school_code: currentUser.value?.school_code || authMeta?.schoolCode || null,
    logo_url: schoolSettings.value?.logo_url || authMeta?.logoUrl || null,
    primary_color: schoolSettings.value?.primary_color || authMeta?.primaryColor || '#AAFF00',
    secondary_color: schoolSettings.value?.secondary_color || authMeta?.secondaryColor || '#FFD400',
    accent_color: schoolSettings.value?.accent_color || authMeta?.accentColor || '#000000',
  }))
}

function handlePasswordClick() {
  if (props.preview) {
    previewNotice.value = 'Sign in with a real student account to change the password.'
    return
  }

  router.push({ name: 'ProfileSecurityPassword' })
}

function handleFaceClick() {
  if (props.preview) {
    previewNotice.value = 'Sign in with a real student account to update the registered face.'
    return
  }

  router.push({ name: 'ProfileSecurityFace' })
}

function goBack() {
  router.push({ name: props.preview ? 'PreviewDashboardProfile' : 'Profile' })
}

watch(
  () => [
    currentUser.value?.school_name,
    currentUser.value?.school_code,
    schoolSettings.value?.logo_url,
    schoolSettings.value?.primary_color,
    schoolSettings.value?.secondary_color,
    schoolSettings.value?.accent_color,
  ],
  () => {
    applySecurityTheme()
  },
  { immediate: true }
)

onMounted(() => {
  applySecurityTheme()
})
</script>

<style scoped>
.security-page {
  min-height: 100vh;
  background: var(--color-bg, #ebebeb);
  padding: calc(env(safe-area-inset-top, 0px) + 22px) 18px calc(env(safe-area-inset-bottom, 0px) + 28px);
  font-family: 'Manrope', sans-serif;
}

.security-shell {
  width: min(100%, 420px);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.security-panel {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 18px;
  border-radius: 28px;
  background:
    radial-gradient(circle at 92% 8%, color-mix(in srgb, var(--color-primary, #aaff00) 30%, transparent), transparent 34%),
    var(--color-surface, #ffffff);
  box-shadow: 0 18px 44px rgba(10, 10, 10, 0.08);
}

.security-panel__icon {
  width: 46px;
  height: 46px;
  flex-shrink: 0;
  border-radius: 18px;
  background: var(--color-primary, #aaff00);
  color: var(--color-primary-text, #0a0a0a);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.security-panel__copy {
  min-width: 0;
}

.security-panel__eyebrow {
  margin: 1px 0 5px;
  color: color-mix(in srgb, var(--color-text-primary, #0a0a0a) 62%, transparent);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.security-panel h2 {
  margin: 0;
  max-width: 260px;
  color: var(--color-text-primary, #0a0a0a);
  font-size: clamp(24px, 8vw, 34px);
  font-weight: 900;
  line-height: 0.94;
  letter-spacing: -0.07em;
}

.security-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.security-action-list {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.security-notice {
  margin: 0;
  padding: 12px 14px;
  border-radius: 18px;
  background: color-mix(in srgb, var(--color-primary, #aaff00) 17%, var(--color-surface, #ffffff));
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text-primary, #0a0a0a);
}

.security-action-card {
  width: 100%;
  min-height: 76px;
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 14px;
  padding: 10px 14px 10px 10px;
  border: none;
  border-radius: 24px;
  background: var(--color-surface, #ffffff);
  color: var(--color-text-primary, #0a0a0a);
  box-shadow: 0 12px 30px rgba(10, 10, 10, 0.07);
  cursor: pointer;
  text-align: left;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
  transition: transform 0.18s ease, box-shadow 0.18s ease, opacity 0.18s ease;
}

.security-action-card:hover {
  box-shadow: 0 16px 36px rgba(10, 10, 10, 0.1);
}

.security-action-card:active {
  transform: scale(0.985);
}

.security-action-card:focus-visible {
  outline: none;
  box-shadow:
    0 0 0 3px color-mix(in srgb, var(--color-primary, #aaff00) 34%, transparent),
    0 16px 36px rgba(10, 10, 10, 0.1);
}

.security-action-card__icon {
  width: 56px;
  height: 56px;
  border-radius: 20px;
  background: var(--color-nav, #0a0a0a);
  color: var(--color-nav-text, #ffffff);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.security-action-card__copy {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.security-action-card__copy strong {
  color: var(--color-text-primary, #0a0a0a);
  font-size: 15px;
  font-weight: 850;
  letter-spacing: -0.03em;
}

.security-action-card__copy small {
  color: color-mix(in srgb, var(--color-text-primary, #0a0a0a) 56%, transparent);
  font-size: 12px;
  font-weight: 650;
  line-height: 1.2;
}

.security-action-card__arrow {
  color: color-mix(in srgb, var(--color-text-primary, #0a0a0a) 44%, transparent);
}

@media (min-width: 900px) {
  .security-page {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 48px 24px;
  }

  .security-shell {
    gap: 18px;
  }

  .security-actions {
    min-height: auto;
  }

  .security-notice {
    text-align: left;
  }
}
</style>
