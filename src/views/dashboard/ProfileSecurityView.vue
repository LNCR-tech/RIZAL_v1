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

      <section class="security-actions">
        <p v-if="noticeMessage" class="security-notice dashboard-enter dashboard-enter--2">{{ noticeMessage }}</p>

        <div class="security-action-list">
          <SecurityActionPill
            v-for="(action, index) in securityActions"
            :key="action.label"
            class="dashboard-enter"
            :style="{ '--dashboard-enter-delay': `${index * 80 + 180}ms` }"
            :icon="action.icon"
            :label="action.label"
            :full-width="true"
            @click="action.handleClick"
          />
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight, Shield } from 'lucide-vue-next'
import SecurityActionPill from '@/components/security/SecurityActionPill.vue'
import SecurityHeaderBar from '@/components/security/SecurityHeaderBar.vue'
import { applyTheme, loadTheme } from '@/config/theme.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { getStoredAuthMeta } from '@/services/localAuth.js'

const router = useRouter()
const route = useRoute()
const { currentUser, schoolSettings } = useDashboardSession()

const securityActions = [
  {
    label: 'Change Password',
    icon: ArrowRight,
    handleClick: () => router.push({ name: 'ProfileSecurityPassword' }),
  },
  {
    label: 'Update Face ID',
    icon: ArrowRight,
    handleClick: () => router.push({ name: 'ProfileSecurityFace' }),
  },
]

const noticeMessage = computed(() => {
  if (route.query?.done === 'password') {
    return 'Password updated successfully.'
  }
  if (route.query?.done === 'face') {
    return 'Face ID updated successfully.'
  }
  return ''
})

function applySecurityTheme() {
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

function goBack() {
  router.push({ name: 'Profile' })
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
  padding: 44px 24px 32px;
  font-family: 'Manrope', sans-serif;
}

.security-shell {
  width: min(100%, 420px);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 150px;
}

.security-actions {
  display: flex;
  flex-direction: column;
  gap: 18px;
  align-items: flex-start;
  justify-content: center;
  min-height: 52vh;
}

.security-action-list {
  width: min(100%, 268px);
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.security-notice {
  margin: 0 0 2px;
  font-size: 13px;
  font-weight: 600;
  color: color-mix(in srgb, var(--color-primary, #aaff00) 48%, #0a0a0a 52%);
}

@media (min-width: 900px) {
  .security-page {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 48px 24px;
  }

  .security-shell {
    gap: 96px;
  }

  .security-actions {
    min-height: auto;
    align-items: center;
  }

  .security-notice {
    text-align: center;
  }
}
</style>
