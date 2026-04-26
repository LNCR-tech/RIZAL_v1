<template>
  <section class="school-it-settings">
    <div class="school-it-settings__shell">
      <SchoolItTopHeader
        :avatar-url="avatarUrl"
        :school-name="schoolName"
        :display-name="displayName"
        :initials="initials"
        @logout="handleLogout"
      />

      <div class="school-it-settings__body">
        <section class="school-it-settings__preview-card dashboard-enter dashboard-enter--1">
          <p class="school-it-settings__preview-label">UI Preview</p>

          <div
            class="school-it-settings__phone"
            :class="{
              'school-it-settings__phone--dark': previewMode === 'dark',
              'school-it-settings__phone--light': previewMode === 'light',
              'school-it-settings__phone--animating': previewAnimating,
            }"
          >
            <div class="school-it-settings__phone-top">
              <span class="school-it-settings__phone-pill school-it-settings__phone-pill--short" />
            </div>

            <div class="school-it-settings__phone-middle">
              <span class="school-it-settings__phone-pill school-it-settings__phone-pill--wide" />
              <span
                class="school-it-settings__phone-pill school-it-settings__phone-pill--accent"
                :style="{ backgroundColor: draft.secondary_color }"
              />
            </div>

            <div
              class="school-it-settings__phone-card school-it-settings__phone-card--primary"
              :style="{ backgroundColor: draft.primary_color }"
            />

            <div class="school-it-settings__phone-card school-it-settings__phone-card--surface" />

            <div class="school-it-settings__phone-nav">
              <span class="school-it-settings__phone-nav-dot" />
              <span class="school-it-settings__phone-nav-triangle" />
              <span class="school-it-settings__phone-nav-slot" />
            </div>
          </div>

          <div class="school-it-settings__mode-switch" role="tablist" aria-label="Preview mode">
            <span
              class="school-it-settings__mode-thumb"
              :class="{ 'school-it-settings__mode-thumb--dark': previewMode === 'dark' }"
              aria-hidden="true"
            />
            <button
              class="school-it-settings__mode-button"
              :class="{ 'school-it-settings__mode-button--active': previewMode === 'light' }"
              type="button"
              @click="setPreviewMode('light')"
            >
              Light
            </button>
            <button
              class="school-it-settings__mode-button"
              :class="{ 'school-it-settings__mode-button--active': previewMode === 'dark' }"
              type="button"
              @click="setPreviewMode('dark')"
            >
              Dark
            </button>
          </div>
        </section>

        <section class="school-it-settings__logo-card dashboard-enter dashboard-enter--2">
          <div class="school-it-settings__logo-copy">
            <div class="school-it-settings__logo-mark">
              <img
                v-if="logoDisplaySrc"
                :src="logoDisplaySrc"
                alt="University Logo"
                class="school-it-settings__logo-image"
              >
              <span v-else class="school-it-settings__logo-fallback">{{ schoolInitials }}</span>
            </div>

            <span class="school-it-settings__logo-label">University Logo</span>
          </div>

          <button
            class="school-it-settings__icon-action"
            type="button"
            :disabled="isSavingLogo || controlsDisabled"
            aria-label="Upload university logo"
            @click="openLogoPicker"
          >
            <LoaderCircle v-if="isSavingLogo" :size="18" class="school-it-settings__spinner" />
            <Upload v-else :size="20" />
          </button>

          <input
            ref="logoInputEl"
            class="sr-only"
            type="file"
            accept=".png,.jpg,.jpeg,.svg,image/png,image/jpeg,image/svg+xml"
            @change="handleLogoChange"
          >
        </section>

        <section class="school-it-settings__color-grid dashboard-enter dashboard-enter--3">
          <article class="school-it-settings__color-card">
            <div class="school-it-settings__color-top">
              <span
                class="school-it-settings__color-swatch"
                :style="{ backgroundColor: draft.primary_color }"
              />

              <div class="school-it-settings__color-copy">
                <span class="school-it-settings__color-title">Primary</span>
                <span class="school-it-settings__color-title">Color</span>
              </div>
            </div>

            <button
              class="school-it-settings__action-pill"
              type="button"
              :disabled="isSavingPrimary || controlsDisabled"
              @click="openColorPicker('primary')"
            >
              {{ isSavingPrimary ? 'Saving...' : 'Select Color' }}
            </button>

            <input
              ref="primaryInputEl"
              class="sr-only"
              type="color"
              :value="draft.primary_color"
              @input="handleColorInput('primary', $event)"
            >
          </article>

          <article class="school-it-settings__color-card">
            <div class="school-it-settings__color-top">
              <span
                class="school-it-settings__color-swatch"
                :style="{ backgroundColor: draft.secondary_color }"
              />

              <div class="school-it-settings__color-copy">
                <span class="school-it-settings__color-title">Secondary</span>
                <span class="school-it-settings__color-title">Color</span>
              </div>
            </div>

            <button
              class="school-it-settings__action-pill"
              type="button"
              :disabled="isSavingSecondary || controlsDisabled"
              @click="openColorPicker('secondary')"
            >
              {{ isSavingSecondary ? 'Saving...' : 'Select Color' }}
            </button>

            <input
              ref="secondaryInputEl"
              class="sr-only"
              type="color"
              :value="draft.secondary_color"
              @input="handleColorInput('secondary', $event)"
            >
          </article>
        </section>

        <p
          v-if="feedback.message"
          class="school-it-settings__feedback dashboard-enter dashboard-enter--4"
          :class="{
            'school-it-settings__feedback--error': feedback.type === 'error',
            'school-it-settings__feedback--success': feedback.type === 'success',
          }"
        >
          {{ feedback.message }}
        </p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { LoaderCircle, Upload } from 'lucide-vue-next'
import SchoolItTopHeader from '@/components/dashboard/SchoolItTopHeader.vue'
import { useAuth } from '@/composables/useAuth.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { usePreviewTheme } from '@/composables/usePreviewTheme.js'
import { schoolItPreviewData } from '@/data/schoolItPreview.js'
import { resolveBackendMediaUrl, withMediaCacheKey } from '@/services/backendMedia.js'
import { updateSchoolBranding } from '@/services/backendApi.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const {
  apiBaseUrl,
  token,
  currentUser,
  schoolSettings,
  initializeDashboardSession,
  refreshSchoolSettings,
  applySchoolSettingsSnapshot,
} = useDashboardSession()
const { logout } = useAuth()
const route = useRoute()

const previewSettings = reactive(cloneSchoolSettings(schoolItPreviewData.schoolSettings))
const draft = reactive(cloneSchoolSettings(schoolItPreviewData.schoolSettings))
const previewMode = ref('light')
const previewAnimating = ref(false)
const logoInputEl = ref(null)
const primaryInputEl = ref(null)
const secondaryInputEl = ref(null)
const pendingField = ref('')
const localLogoUrl = ref('')
const feedback = reactive({
  type: '',
  message: '',
})
const logoRefreshKey = ref(0)

let feedbackTimeoutId = null
let previewAnimationTimeoutId = null

const isPreviewWorkspace = computed(() => props.preview || route.path.startsWith('/exposed/workspace'))
const activeUser = computed(() => (isPreviewWorkspace.value ? schoolItPreviewData.user : currentUser.value))
const activeSchoolSettings = computed(() => (isPreviewWorkspace.value ? previewSettings : schoolSettings.value))

usePreviewTheme(() => isPreviewWorkspace.value, previewSettings)

const displayName = computed(() => {
  const user = activeUser.value
  if (!user) return 'School IT'
  return [user.first_name, user.last_name].filter(Boolean).join(' ').trim() || user.email || 'School IT'
})

const schoolName = computed(() => (
  activeSchoolSettings.value?.school_name
  || activeUser.value?.school_name
  || 'University Name'
))

const schoolInitials = computed(() => abbreviateName(schoolName.value))
const initials = computed(() => abbreviateName(displayName.value, 2))
const avatarUrl = computed(() => activeUser.value?.avatar_url || '')
const remoteLogoSrc = computed(() => {
  const resolved = resolveBackendMediaUrl(activeSchoolSettings.value?.logo_url, apiBaseUrl.value)
  return withMediaCacheKey(resolved, activeSchoolSettings.value?.updated_at || logoRefreshKey.value || '')
})
const logoDisplaySrc = computed(() => localLogoUrl.value || remoteLogoSrc.value || '')
const controlsDisabled = computed(() => !isPreviewWorkspace.value && !activeSchoolSettings.value)

const isSavingPrimary = computed(() => pendingField.value === 'primary')
const isSavingSecondary = computed(() => pendingField.value === 'secondary')
const isSavingLogo = computed(() => pendingField.value === 'logo')

watch(
  activeSchoolSettings,
  (value) => {
    if (!value) return

    draft.school_id = value.school_id ?? null
    draft.school_name = value.school_name || 'University Name'
    draft.school_code = value.school_code || ''
    draft.logo_url = value.logo_url || ''
    draft.primary_color = value.primary_color || '#AAFF00'
    draft.secondary_color = value.secondary_color || '#FF4D4F'
  },
  { immediate: true, deep: true }
)

onMounted(async () => {
  if (isPreviewWorkspace.value) return

  if (!schoolSettings.value) {
    await initializeDashboardSession().catch(() => null)
  }

  if (token.value) {
    await refreshSchoolSettings().catch(() => null)
  }
})

onBeforeUnmount(() => {
  clearFeedbackTimer()
  clearPreviewAnimationTimer()
  revokeLocalLogo()
})

async function handleLogout() {
  await logout()
}

function setPreviewMode(mode) {
  if (previewMode.value === mode) return
  previewMode.value = mode
}

function openLogoPicker() {
  if (controlsDisabled.value) return
  logoInputEl.value?.click()
}

function openColorPicker(kind) {
  if (controlsDisabled.value) return
  if (kind === 'primary') {
    primaryInputEl.value?.click()
    return
  }

  secondaryInputEl.value?.click()
}

async function handleColorInput(kind, event) {
  const nextValue = String(event?.target?.value || '').trim()
  if (!nextValue) return

  const previousValue = kind === 'primary' ? draft.primary_color : draft.secondary_color
  if (kind === 'primary') {
    draft.primary_color = nextValue
  } else {
    draft.secondary_color = nextValue
  }

  if (isPreviewWorkspace.value) {
    if (kind === 'primary') {
      previewSettings.primary_color = nextValue
    } else {
      previewSettings.secondary_color = nextValue
    }
    pushFeedback('success', `${kind === 'primary' ? 'Primary' : 'Secondary'} color updated in preview.`)
    return
  }

  const saved = await persistBranding(kind)
  if (!saved) {
    if (kind === 'primary') {
      draft.primary_color = previousValue
    } else {
      draft.secondary_color = previousValue
    }
  }
}

async function handleLogoChange(event) {
  const file = event?.target?.files?.[0] || null
  if (!file) return

  try {
    validateLogoFile(file)
    updateLocalLogoPreview(file)

    if (isPreviewWorkspace.value) {
      previewSettings.logo_url = localLogoUrl.value
      pushFeedback('success', 'University logo updated in preview.')
      return
    }

    const saved = await persistBranding('logo', file)
    if (!saved) {
      revokeLocalLogo()
    }
  } catch (error) {
    revokeLocalLogo()
    pushFeedback('error', error?.message || 'Unable to use the selected logo.')
  } finally {
    if (event?.target) {
      event.target.value = ''
    }
  }
}

async function persistBranding(kind, logoFile = null) {
  if (!token.value) {
    pushFeedback('error', 'No authenticated session is available right now.')
    return false
  }

  pendingField.value = kind

  try {
    const updated = await updateSchoolBranding(apiBaseUrl.value, token.value, {
      school_name: draft.school_name,
      primary_color: draft.primary_color,
      secondary_color: draft.secondary_color,
      school_code: draft.school_code || '',
    }, logoFile)

    applySchoolSettingsSnapshot(updated)

    if (logoFile) {
      revokeLocalLogo()
      logoRefreshKey.value += 1
    }

    pushFeedback('success', kind === 'logo' ? 'University logo updated.' : 'Branding updated.')
    return true
  } catch (error) {
    pushFeedback('error', error?.message || 'Unable to update school branding right now.')
    return false
  } finally {
    pendingField.value = ''
  }
}

function updateLocalLogoPreview(file) {
  revokeLocalLogo()
  localLogoUrl.value = URL.createObjectURL(file)
}

function revokeLocalLogo() {
  if (localLogoUrl.value?.startsWith('blob:')) {
    URL.revokeObjectURL(localLogoUrl.value)
  }
  localLogoUrl.value = ''
}

function validateLogoFile(file) {
  const normalizedName = String(file?.name || '').toLowerCase()
  const supportedExtensions = ['.png', '.jpg', '.jpeg', '.svg']
  if (!supportedExtensions.some((extension) => normalizedName.endsWith(extension))) {
    throw new Error('Logo must be PNG, JPG, JPEG, or SVG.')
  }

  const maxBytes = 2 * 1024 * 1024
  if (Number(file?.size) > maxBytes) {
    throw new Error('Logo exceeds the 2MB upload limit.')
  }
}

function pushFeedback(type, message) {
  clearFeedbackTimer()
  feedback.type = type
  feedback.message = message

  feedbackTimeoutId = window.setTimeout(() => {
    feedback.type = ''
    feedback.message = ''
  }, 3200)
}

function clearFeedbackTimer() {
  if (feedbackTimeoutId) {
    window.clearTimeout(feedbackTimeoutId)
    feedbackTimeoutId = null
  }
}

function clearPreviewAnimationTimer() {
  if (previewAnimationTimeoutId) {
    window.clearTimeout(previewAnimationTimeoutId)
    previewAnimationTimeoutId = null
  }
}

watch(previewMode, (nextMode, previousMode) => {
  if (nextMode === previousMode) return

  previewAnimating.value = true
  clearPreviewAnimationTimer()
  previewAnimationTimeoutId = window.setTimeout(() => {
    previewAnimating.value = false
    previewAnimationTimeoutId = null
  }, 420)
})

function cloneSchoolSettings(value = {}) {
  return {
    school_id: value?.school_id ?? null,
    school_name: value?.school_name || 'University Name',
    school_code: value?.school_code || '',
    logo_url: value?.logo_url || '',
    primary_color: value?.primary_color || '#AAFF00',
    secondary_color: value?.secondary_color || '#FF4D4F',
  }
}

function abbreviateName(value, maxLetters = 4) {
  const words = String(value || '').trim().match(/[A-Za-z0-9]+/g) || []
  if (!words.length) return 'UN'

  const firstWord = words[0] || ''
  if (/^[A-Z]{2,10}$/.test(firstWord)) {
    return firstWord.slice(0, maxLetters).toUpperCase()
  }

  return words
    .slice(0, maxLetters)
    .map((word) => word[0]?.toUpperCase() || '')
    .join('')
}
</script>

<style scoped>
.school-it-settings{min-height:100vh;padding:30px 28px 120px;font-family:'Manrope',sans-serif}
.school-it-settings__shell{width:100%;max-width:1120px;margin:0 auto}
.school-it-settings__body{display:flex;flex-direction:column;gap:18px;max-width:560px;margin:24px auto 0}
.school-it-settings__preview-card,.school-it-settings__logo-card,.school-it-settings__color-card{background:var(--color-surface);border-radius:32px;box-shadow:0 18px 40px rgba(15,23,42,.04)}
.school-it-settings__preview-card{padding:18px 18px 16px;display:flex;flex-direction:column;align-items:center}
.school-it-settings__preview-label{margin:0 0 10px;font-size:12px;font-weight:500;line-height:1;color:var(--color-text-secondary)}
.school-it-settings__phone{width:min(100%,166px);aspect-ratio:166/302;border-radius:30px;padding:14px 12px 12px;display:flex;flex-direction:column;gap:10px;position:relative;overflow:hidden;background:#EDEDED;box-shadow:inset 0 1px 0 rgba(255,255,255,.42),0 12px 24px rgba(15,23,42,.05);transform:translateZ(0);transition:background-color .38s cubic-bezier(.22,1,.36,1),box-shadow .38s cubic-bezier(.22,1,.36,1)}
.school-it-settings__phone::before,.school-it-settings__phone::after{content:"";position:absolute;inset:0;border-radius:inherit;pointer-events:none;transition:opacity .38s cubic-bezier(.22,1,.36,1),transform .38s cubic-bezier(.22,1,.36,1)}
.school-it-settings__phone::before{background:radial-gradient(80% 62% at 26% 10%,rgba(255,255,255,.78) 0%,rgba(255,255,255,.24) 42%,rgba(255,255,255,0) 76%);opacity:.92}
.school-it-settings__phone::after{background:linear-gradient(180deg,rgba(255,255,255,.18) 0%,rgba(255,255,255,.06) 32%,rgba(0,0,0,.03) 100%);opacity:.8}
.school-it-settings__phone--dark{background:#242615;box-shadow:inset 0 1px 0 rgba(255,255,255,.06),0 12px 24px rgba(0,0,0,.14)}
.school-it-settings__phone--dark::before{opacity:.2;transform:translate3d(6px,-4px,0)}
.school-it-settings__phone--dark::after{opacity:.3}
.school-it-settings__phone--animating{animation:school-it-settings-phone-settle .42s cubic-bezier(.22,1,.36,1)}
.school-it-settings__phone-top,.school-it-settings__phone-middle{display:flex;align-items:center;gap:8px}
.school-it-settings__phone-top,.school-it-settings__phone-middle,.school-it-settings__phone-card,.school-it-settings__phone-nav{position:relative;z-index:1}
.school-it-settings__phone-middle{justify-content:space-between}
.school-it-settings__phone-pill{display:block;height:24px;border-radius:999px;background:#FFFFFF;box-shadow:inset 0 1px 0 rgba(255,255,255,.52);transition:background-color .38s cubic-bezier(.22,1,.36,1),opacity .26s ease,transform .38s cubic-bezier(.22,1,.36,1),box-shadow .38s cubic-bezier(.22,1,.36,1)}
.school-it-settings__phone--dark .school-it-settings__phone-pill{background:#FAFAFA}
.school-it-settings__phone-pill--short{width:50px}
.school-it-settings__phone-pill--wide{flex:1;max-width:86px}
.school-it-settings__phone-pill--accent{width:36px;flex:none;box-shadow:none}
.school-it-settings__phone-card{border-radius:16px;box-shadow:inset 0 1px 0 rgba(255,255,255,.3);transition:background-color .38s cubic-bezier(.22,1,.36,1),transform .38s cubic-bezier(.22,1,.36,1),box-shadow .38s cubic-bezier(.22,1,.36,1)}
.school-it-settings__phone-card--primary{height:84px}
.school-it-settings__phone-card--surface{height:70px;background:#FFFFFF}
.school-it-settings__phone--dark .school-it-settings__phone-card--surface{background:#FFFFFF}
.school-it-settings__phone-nav{margin-top:auto;align-self:center;width:min(100%,104px);height:23px;border-radius:999px;background:#060606;display:grid;grid-template-columns:1fr 1fr 1fr;align-items:center;justify-items:center;padding:0 10px;box-shadow:inset 0 1px 0 rgba(255,255,255,.06),0 8px 14px rgba(0,0,0,.08);transition:transform .38s cubic-bezier(.22,1,.36,1),box-shadow .38s cubic-bezier(.22,1,.36,1)}
.school-it-settings__phone-nav-dot{width:12px;height:12px;border-radius:999px;background:var(--color-primary)}
.school-it-settings__phone-nav-triangle{width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-bottom:10px solid var(--color-primary)}
.school-it-settings__phone-nav-slot{width:10px;height:10px;border-radius:2px;background:var(--color-primary)}
.school-it-settings__mode-switch{margin-top:18px;padding:4px;background:#ECEBE7;border-radius:999px;display:inline-grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:4px;min-width:138px;position:relative;overflow:hidden;isolation:isolate;box-shadow:inset 0 1px 0 rgba(255,255,255,.72)}
.school-it-settings__mode-thumb{position:absolute;top:4px;left:4px;width:calc(50% - 4px);height:36px;border-radius:999px;background:#8E8E8E;box-shadow:0 8px 16px rgba(15,23,42,.12),inset 0 1px 0 rgba(255,255,255,.18);transform:translateX(0);transition:transform .36s cubic-bezier(.22,1,.36,1),background-color .28s ease,box-shadow .28s ease}
.school-it-settings__mode-thumb--dark{transform:translateX(calc(100% + 4px));background:#767676}
.school-it-settings__mode-button{min-width:64px;height:36px;border:none;border-radius:999px;background:transparent;color:#5E5E5E;font-size:14px;font-weight:500;position:relative;z-index:1;transition:color .26s ease,transform .18s ease}
.school-it-settings__mode-button--active{color:#FFFFFF}
.school-it-settings__mode-button:active{transform:scale(.97)}
.school-it-settings__logo-card{padding:16px 18px;display:flex;align-items:center;justify-content:space-between;gap:16px}
.school-it-settings__logo-copy{display:flex;align-items:center;gap:18px;min-width:0}
.school-it-settings__logo-mark{width:52px;height:52px;border-radius:999px;background:#F2F2F0;display:grid;place-items:center;overflow:hidden;flex-shrink:0}
.school-it-settings__logo-image{width:100%;height:100%;object-fit:cover}
.school-it-settings__logo-fallback{font-size:16px;font-weight:800;letter-spacing:-.04em;color:var(--color-text-primary)}
.school-it-settings__logo-label{min-width:0;font-size:14px;font-weight:500;color:var(--color-text-primary)}
.school-it-settings__icon-action{width:58px;height:42px;border:none;border-radius:18px;background:#F1F1EE;color:var(--color-text-primary);display:grid;place-items:center;flex-shrink:0;transition:transform .16s ease,background-color .16s ease}
.school-it-settings__icon-action:disabled{opacity:.72}
.school-it-settings__icon-action:not(:disabled):active{transform:scale(.96)}
.school-it-settings__spinner{animation:school-it-settings-spin .9s linear infinite}
.school-it-settings__color-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.school-it-settings__color-card{padding:18px 16px 16px;display:flex;flex-direction:column;gap:24px;min-height:192px}
.school-it-settings__color-top{display:flex;align-items:center;gap:14px}
.school-it-settings__color-swatch{width:84px;height:84px;border-radius:18px;flex-shrink:0}
.school-it-settings__color-copy{display:flex;flex-direction:column;gap:1px}
.school-it-settings__color-title{font-size:15px;font-weight:500;line-height:1.12;color:var(--color-text-primary)}
.school-it-settings__action-pill{margin-top:auto;height:42px;border:none;border-radius:999px;background:#F1F1EE;color:var(--color-text-primary);font-size:14px;font-weight:500;transition:transform .16s ease,background-color .16s ease}
.school-it-settings__action-pill:disabled{opacity:.72}
.school-it-settings__action-pill:not(:disabled):active{transform:scale(.985)}
.school-it-settings__feedback{margin:2px 6px 0;font-size:13px;font-weight:500;line-height:1.4;text-align:center}
.school-it-settings__feedback--success{color:#15803D}
.school-it-settings__feedback--error{color:#D92D20}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}

@keyframes school-it-settings-spin{to{transform:rotate(360deg)}}
@keyframes school-it-settings-phone-settle{
  0%{transform:scale(.975) translate3d(0,3px,0)}
  58%{transform:scale(1.012) translate3d(0,0,0)}
  100%{transform:scale(1) translate3d(0,0,0)}
}

@media (max-width: 767px){
  .school-it-settings{padding:26px 18px 118px}
  .school-it-settings__body{max-width:420px}
}

@media (max-width: 460px){
  .school-it-settings__body{gap:16px}
  .school-it-settings__preview-card{padding:16px 14px 14px;border-radius:28px}
  .school-it-settings__phone{width:min(100%,134px);border-radius:26px;padding:12px 10px 10px}
  .school-it-settings__phone-pill{height:20px}
  .school-it-settings__phone-card--primary{height:72px}
  .school-it-settings__phone-card--surface{height:60px}
  .school-it-settings__mode-switch{margin-top:16px;min-width:132px}
  .school-it-settings__mode-button{height:34px;font-size:13px}
  .school-it-settings__logo-card{padding:15px 14px;border-radius:28px}
  .school-it-settings__logo-copy{gap:14px}
  .school-it-settings__logo-mark{width:48px;height:48px}
  .school-it-settings__color-grid{gap:12px}
  .school-it-settings__color-card{padding:16px 12px 14px;gap:18px;min-height:176px;border-radius:28px}
  .school-it-settings__color-top{gap:12px}
  .school-it-settings__color-swatch{width:72px;height:72px;border-radius:16px}
  .school-it-settings__color-title{font-size:14px}
}

@media (max-width: 360px){
  .school-it-settings{padding-inline:14px}
  .school-it-settings__logo-label{font-size:13px}
  .school-it-settings__color-grid{grid-template-columns:1fr}
  .school-it-settings__color-card{min-height:164px}
}
</style>
