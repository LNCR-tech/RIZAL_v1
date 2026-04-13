<template>
  <div class="profile-page">

    <!-- ── Header ─────────────────────────────────────────────────────── -->
    <header class="profile-header dashboard-enter dashboard-enter--1">
      <button class="icon-btn" aria-label="Go back" @click="router.back()">
        <ArrowLeft :size="18" />
      </button>
      <h1 class="profile-header__title">Profile</h1>
      <button class="icon-btn" aria-label="Settings">
        <Settings :size="18" />
      </button>
    </header>

    <!-- ── Edit Profile Overlay ──────────────────────────────────────── -->
    <Transition name="edit-slide">
      <div v-if="isEditing" class="edit-overlay">

        <!-- Overlay header -->
        <header class="profile-header">
          <button class="icon-btn" aria-label="Cancel" @click="cancelEdit">
            <ArrowLeft :size="18" />
          </button>
          <h1 class="profile-header__title">Edit Profile</h1>
          <div style="width:40px" />
        </header>

        <!-- Avatar + upload -->
        <div class="edit-avatar-wrap">
          <div class="avatar-wrap" style="width:110px;height:110px;margin-bottom:0">
            <img
              v-if="editPreview || (avatarUrl && !avatarError)"
              :src="editPreview || avatarUrl"
              alt="Profile photo"
              class="avatar-img"
            />
            <div v-else class="avatar-fallback">{{ initials }}</div>
            <!-- Upload icon -->
            <button
              class="avatar-edit-btn"
              aria-label="Upload photo"
              @click="triggerPhotoUpload"
            >
              <Upload :size="12" />
            </button>
            <!-- Hidden file input -->
            <input
              ref="photoInput"
              type="file"
              accept="image/*"
              class="sr-only"
              @change="onPhotoSelected"
            />
          </div>
        </div>

        <!-- Form fields -->
        <form class="edit-form" @submit.prevent="saveProfile">

          <!-- University (read-only) -->
          <div class="edit-field edit-field--readonly">
            <span class="edit-field__value">{{ schoolName }}</span>
            <img
              v-if="schoolLogoSrc && !schoolLogoUnavailable"
              :src="schoolLogoSrc"
              alt="School logo"
              class="edit-field__logo"
              @error="handleSchoolLogoError"
            />
          </div>

          <!-- Email -->
          <div class="edit-field">
            <input
              v-model="editForm.email"
              type="email"
              placeholder="Email"
              class="edit-input"
            />
          </div>

          <!-- First Name -->
          <div class="edit-field">
            <input
              v-model="editForm.firstName"
              type="text"
              placeholder="First Name"
              class="edit-input"
            />
          </div>

          <!-- Last Name -->
          <div class="edit-field">
            <input
              v-model="editForm.lastName"
              type="text"
              placeholder="Last Name"
              class="edit-input"
            />
          </div>

          <!-- Middle Name -->
          <div class="edit-field">
            <input
              v-model="editForm.middleName"
              type="text"
              placeholder="Middle Name (Optional)"
              class="edit-input"
            />
          </div>

          <!-- Actions -->
          <div class="edit-actions">
            <button type="button" class="edit-cancel-btn" @click="cancelEdit">
              Cancel
            </button>
            <button type="submit" class="edit-save-btn" :disabled="isSaving">
              <ArrowRight :size="16" />
              <span>{{ isSaving ? 'Saving…' : 'Save' }}</span>
            </button>
          </div>

        </form>
      </div>
    </Transition>

    <!-- ── Main layout ────────────────────────────────────────────────── -->
    <div class="profile-layout">

      <!-- LEFT COLUMN (desktop) / TOP SECTION (mobile) -->
      <section class="profile-left dashboard-enter dashboard-enter--2">

        <!-- Avatar -->
        <div class="avatar-wrap">
          <img
            v-if="avatarPreview || (avatarUrl && !avatarError)"
            :src="avatarPreview || avatarUrl"
            :alt="fullName"
            class="avatar-img"
            @error="avatarError = true"
          />
          <div v-else class="avatar-fallback">
            {{ initials }}
          </div>
          <!-- Edit / pencil button → opens edit mode -->
          <button
            class="avatar-edit-btn"
            aria-label="Edit profile"
            @click="openEdit"
          >
            <Pencil :size="12" />
          </button>
        </div>

        <!-- Name & School -->
        <div class="avatar-info">
          <h2 class="avatar-name">{{ fullName }}</h2>
          <p class="avatar-school">{{ schoolName }}</p>
        </div>

      </section>

      <!-- RIGHT COLUMN (desktop) / MIDDLE SECTION (mobile) -->
      <section class="profile-right dashboard-enter dashboard-enter--3">

        <!-- Stat cards -->
        <div class="stat-cards">
          <!-- Events Attended -->
          <div class="stat-card stat-card--primary">
            <span class="stat-card__number">{{ eventsAttended }}</span>
            <span class="stat-card__label">Total Event<br>Attended</span>
          </div>
          <!-- Events Missed -->
          <div class="stat-card stat-card--surface">
            <span class="stat-card__number">{{ eventsMissed }}</span>
            <span class="stat-card__label">Total Event<br>Missed</span>
          </div>
        </div>

        <!-- App Settings card -->
        <div class="settings-card">
          <p class="settings-card__title">App Setting</p>

          <!-- Notifications row -->
          <div class="settings-row">
            <span class="settings-icon"><Bell :size="16" /></span>
            <span class="settings-row__label">Notifications</span>
            <button
              class="settings-toggle"
              :class="{ 'settings-toggle--on': notificationsEnabled }"
              @click="notificationsEnabled = !notificationsEnabled"
              :aria-pressed="notificationsEnabled"
              aria-label="Toggle notifications"
            >
              <span class="settings-toggle__knob" />
            </button>
          </div>

          <div class="settings-divider" />

          <div class="settings-row">
            <span class="settings-icon"><Moon :size="16" /></span>
            <span class="settings-row__label">Dark Mode</span>
            <button
              class="settings-toggle"
              :class="{ 'settings-toggle--on': isDarkMode }"
              type="button"
              :aria-pressed="isDarkMode"
              aria-label="Toggle dark mode"
              @click="toggleDarkMode"
            >
              <span class="settings-toggle__knob" />
            </button>
          </div>

          <div class="settings-divider" />

          <!-- Font Size row -->
          <div class="settings-row">
            <span class="settings-icon settings-icon--text">Aa</span>
            <span class="settings-row__label">Font Size</span>
          <div class="font-size-slider-wrap">
              <span class="font-size-label font-size-label--small">Aa</span>

              <!-- Custom slider with spring thumb animation -->
              <div
                class="custom-slider-track"
                ref="sliderTrack"
                tabindex="0"
                role="slider"
                :aria-valuenow="fontSize"
                :aria-valuemin="FONT_SIZE_MIN"
                :aria-valuemax="FONT_SIZE_MAX"
                :aria-valuetext="`${fontSize}%`"
                aria-label="Font size"
                @pointerdown.prevent="onSliderPointerDown"
                @pointermove="onSliderPointerMove"
                @pointerup="onSliderPointerUp"
                @pointercancel="onSliderPointerUp"
                @lostpointercapture="endSliderDrag()"
                @keydown="onSliderKeyDown"
              >
                <div
                  class="custom-slider-thumb"
                  :class="{
                    'custom-slider-thumb--bounce': isBouncing,
                    'custom-slider-thumb--dragging': isSliderDragging,
                  }"
                  :style="{ left: thumbPercent + '%' }"
                />
              </div>

              <span class="font-size-label font-size-label--large">Aa</span>
            </div>
          </div>
        </div>

        <!-- Action rows — below App Setting on mobile & desktop -->
        <div class="action-cards">
          <button class="action-row" @click="handleSecurity">
            <span class="action-row__left">
              <span class="action-icon"><Shield :size="16" /></span>
              <span class="action-label">Security</span>
            </span>
            <ChevronRight :size="16" class="action-chevron" />
          </button>

          <button class="action-row action-row--danger" @click="handleSignOut">
            <span class="action-row__left">
              <span class="action-label action-label--danger">Sign Out</span>
            </span>
            <ChevronRight :size="16" class="action-chevron action-chevron--danger" />
          </button>
        </div>

      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowLeft, ArrowRight, Settings, Pencil, Upload,
  Shield, ChevronRight, Bell, Moon
} from 'lucide-vue-next'

import { defaultTheme, isDarkMode, toggleDarkMode } from '@/config/theme.js'
import { usePreviewTheme } from '@/composables/usePreviewTheme.js'
import { useAuth } from '@/composables/useAuth.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { studentDashboardPreviewData } from '@/data/studentDashboardPreview.js'
import { getMyNotificationPreferences, updateMyNotificationPreferences } from '@/services/backendApi.js'
import {
  DEFAULT_FONT_SIZE,
  FONT_SIZE_MAX,
  FONT_SIZE_MIN,
  FONT_SIZE_STEP,
  getStoredFontSize,
  snapFontSize,
  storeFontSizePreference,
} from '@/services/userPreferences.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

// ── Router ───────────────────────────────────────────────────────────
const router = useRouter()

// ── Auth ─────────────────────────────────────────────────────────────
const { logout } = useAuth()
const {
  apiBaseUrl,
  currentUser: sessionCurrentUser,
  schoolSettings: sessionSchoolSettings,
  attendanceRecords: sessionAttendanceRecords,
  saveCurrentUserProfile,
  token,
} = useDashboardSession()

const previewUser = ref(JSON.parse(JSON.stringify(studentDashboardPreviewData.user)))
const previewSchoolSettings = ref(studentDashboardPreviewData.schoolSettings)
const previewAttendanceRecords = ref(studentDashboardPreviewData.attendanceRecords)

const user = computed(() => props.preview ? previewUser.value : sessionCurrentUser.value)
const activeSchoolSettings = computed(() => props.preview ? previewSchoolSettings.value : sessionSchoolSettings.value)
const activeAttendanceRecords = computed(() => props.preview ? previewAttendanceRecords.value : sessionAttendanceRecords.value)
const schoolName = computed(() => activeSchoolSettings.value?.school_name ?? 'University Name')

usePreviewTheme(() => props.preview, activeSchoolSettings)

// ── Derived ───────────────────────────────────────────────────────────
const fullName = computed(() =>
  [user.value.first_name, user.value.middle_name, user.value.last_name]
    .filter(Boolean).join(' ')
)

const initials = computed(() => {
  const f = user.value.first_name?.[0] ?? ''
  const l = user.value.last_name?.[0] ?? ''
  return (f + l).toUpperCase() || '?'
})

// Avatar: backend will provide photo_url on UserWithRelations
const avatarUrl    = computed(() => user.value.student_profile?.photo_url ?? null)
const avatarError  = ref(false)
const avatarPreview = ref(null) // shown on main view after successful save

// School logo for the readonly field
const schoolLogo = computed(() => activeSchoolSettings.value?.logo_url ?? null)
const schoolLogoError = ref(false)
const schoolLogoUnavailable = ref(false)
const schoolLogoSrc = computed(() => (
  schoolLogoError.value
    ? defaultTheme.schoolLogo
    : schoolLogo.value || defaultTheme.schoolLogo
))

const eventsAttended = computed(() =>
  activeAttendanceRecords.value.filter((attendance) => {
    const status = String(attendance?.status ?? '').toLowerCase()
    return status === 'present' || status === 'late'
  }).length
)
const eventsMissed = computed(() =>
  activeAttendanceRecords.value.filter((attendance) => String(attendance?.status ?? '').toLowerCase() === 'absent').length
)

// ── Custom slider logic ────────────────────────────────────────────────
const sliderTrack = ref(null)
const isBouncing  = ref(false)
const isSliderDragging = ref(false)

// Thumb position as % of the track width
const thumbPercent = computed(() =>
  ((fontSize.value - FONT_SIZE_MIN) / (FONT_SIZE_MAX - FONT_SIZE_MIN)) * 100
)

function setValueFromX(clientX) {
  const trackElement = sliderTrack.value
  if (!trackElement) return

  const rect = trackElement.getBoundingClientRect()
  if (!rect.width) return

  const ratio = Math.min(1, Math.max(0, (clientX - rect.left) / rect.width))
  fontSize.value = snapFontSize(FONT_SIZE_MIN + ratio * (FONT_SIZE_MAX - FONT_SIZE_MIN))
}

function triggerBounce() {
  isBouncing.value = false
  // Force reflow so the class toggle re-triggers the animation
  void sliderTrack.value?.offsetWidth
  isBouncing.value = true
  setTimeout(() => { isBouncing.value = false }, 600)
}

function endSliderDrag(pointerId = null) {
  isSliderDragging.value = false
  if (pointerId != null) {
    sliderTrack.value?.releasePointerCapture?.(pointerId)
  }
}

function onSliderPointerMove(event) {
  if (!isSliderDragging.value) return
  setValueFromX(event.clientX)
}

function onSliderPointerUp(event) {
  if (!isSliderDragging.value) return
  endSliderDrag(event.pointerId)
  triggerBounce()
}

function onSliderPointerDown(event) {
  sliderTrack.value?.focus?.()
  isSliderDragging.value = true
  sliderTrack.value?.setPointerCapture?.(event.pointerId)
  setValueFromX(event.clientX)
}

function onSliderKeyDown(event) {
  const key = event.key
  const nextBy = (delta) => {
    fontSize.value = snapFontSize(fontSize.value + delta)
    triggerBounce()
  }

  if (key === 'ArrowLeft' || key === 'ArrowDown') {
    event.preventDefault()
    nextBy(-FONT_SIZE_STEP)
  } else if (key === 'ArrowRight' || key === 'ArrowUp') {
    event.preventDefault()
    nextBy(FONT_SIZE_STEP)
  } else if (key === 'Home') {
    event.preventDefault()
    fontSize.value = FONT_SIZE_MIN
    triggerBounce()
  } else if (key === 'End') {
    event.preventDefault()
    fontSize.value = FONT_SIZE_MAX
    triggerBounce()
  }
}

const fontSize = ref(getStoredFontSize() || DEFAULT_FONT_SIZE)

// Apply + persist whenever slider changes
watch(fontSize, val => {
  const normalizedValue = storeFontSizePreference(val)
  if (normalizedValue !== val) {
    fontSize.value = normalizedValue
  }
})

const notificationsEnabled = ref(
  JSON.parse(localStorage.getItem('aura_notif_enabled') ?? 'true')
)
const notificationPreferenceReady = ref(Boolean(props.preview))
const notificationPreferenceSyncing = ref(false)

async function savePreferences(payload) {
  if ('notifications_enabled' in payload) {
    localStorage.setItem('aura_notif_enabled', JSON.stringify(Boolean(payload.notifications_enabled)))
  }

  if (props.preview) return
  if (!apiBaseUrl.value || !token.value) return

  notificationPreferenceSyncing.value = true
  try {
    const updated = await updateMyNotificationPreferences(apiBaseUrl.value, token.value, {
      email_enabled: Boolean(payload.notifications_enabled),
    })
    notificationsEnabled.value = Boolean(updated?.email_enabled)
  } finally {
    notificationPreferenceSyncing.value = false
  }
}

watch(
  [() => props.preview, apiBaseUrl, token, () => user.value?.id],
  async ([previewMode, url, authToken, userId]) => {
    if (previewMode) {
      notificationPreferenceReady.value = true
      return
    }

    if (!url || !authToken || !Number.isFinite(Number(userId))) {
      notificationPreferenceReady.value = false
      return
    }

    notificationPreferenceSyncing.value = true
    try {
      const preference = await getMyNotificationPreferences(url, authToken)
      notificationsEnabled.value = Boolean(preference?.email_enabled)
      localStorage.setItem('aura_notif_enabled', JSON.stringify(Boolean(preference?.email_enabled)))
      notificationPreferenceReady.value = true
    } catch {
      notificationPreferenceReady.value = true
    } finally {
      notificationPreferenceSyncing.value = false
    }
  },
  { immediate: true }
)

watch(notificationsEnabled, async (enabled) => {
  if (!notificationPreferenceReady.value || notificationPreferenceSyncing.value) return
  await savePreferences({ notifications_enabled: enabled })
})

watch(schoolLogo, () => {
  schoolLogoError.value = false
  schoolLogoUnavailable.value = false
})

function handleSchoolLogoError() {
  if (!schoolLogoError.value) {
    schoolLogoError.value = true
    return
  }

  schoolLogoUnavailable.value = true
}

// ── Edit Profile ──────────────────────────────────────────────────────
const isEditing   = ref(false)
const isSaving    = ref(false)
const photoInput  = ref(null)
const editPreview = ref(null)
const editForm    = ref({})

function openEdit() {
  editForm.value = {
    email:      user.value.email ?? '',
    firstName:  user.value.first_name ?? '',
    lastName:   user.value.last_name ?? '',
    middleName: user.value.middle_name ?? '',
  }
  editPreview.value = avatarPreview.value
  isEditing.value   = true
}

function cancelEdit() {
  isEditing.value   = false
  editPreview.value = null
}

function triggerPhotoUpload() {
  photoInput.value?.click()
}

function onPhotoSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (editPreview.value) URL.revokeObjectURL(editPreview.value)
  editPreview.value = URL.createObjectURL(file)
}

async function saveProfile() {
  isSaving.value = true
  try {
    if (props.preview) {
      previewUser.value = {
        ...previewUser.value,
        email: editForm.value.email.trim(),
        first_name: editForm.value.firstName.trim(),
        last_name: editForm.value.lastName.trim(),
        middle_name: editForm.value.middleName.trim() || null,
      }
      if (editPreview.value) previewUser.value.avatar_url = editPreview.value
      if (editPreview.value) avatarPreview.value = editPreview.value
      isEditing.value = false
      return
    }

    await saveCurrentUserProfile({
      email: editForm.value.email.trim(),
      first_name: editForm.value.firstName.trim(),
      last_name: editForm.value.lastName.trim(),
      middle_name: editForm.value.middleName.trim() || null,
    })
    if (editPreview.value) avatarPreview.value = editPreview.value

    isEditing.value = false
  } finally {
    isSaving.value = false
  }
}

// ── Handlers ──────────────────────────────────────────────────────────
function handleSecurity() {
  if (props.preview) return
  router.push({ name: 'ProfileSecurity' })
}

async function handleSignOut() {
  if (props.preview) {
    router.replace('/exposed/dashboard')
    return
  }
  await logout()
  router.replace('/')
}
</script>

<style scoped>
/* ── Page shell ──────────────────────────────────────────────────── */
.profile-page {
  min-height: 100vh;
  padding: 0 22px 100px;
  font-family: 'Manrope', sans-serif;
  background: var(--color-bg);
}

/* ── Header ──────────────────────────────────────────────────────── */
.profile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 0 24px;
}

.profile-header__title {
  font-size: 17px;
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.2px;
}

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: var(--color-surface);
  color: var(--color-text-always-dark);
  cursor: pointer;
  transition: opacity 0.15s ease;
  flex-shrink: 0;
}

.icon-btn:hover { opacity: 0.75; }

/* ── Layout ──────────────────────────────────────────────────────── */
.profile-layout {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ── Avatar ──────────────────────────────────────────────────────── */
.profile-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
}

.avatar-wrap {
  position: relative;
  width: 110px;
  height: 110px;
  margin-bottom: 14px;
}

.avatar-img,
.avatar-fallback {
  width: 110px;
  height: 110px;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: var(--color-banner-text);
  font-size: 36px;
  font-weight: 800;
}

.avatar-edit-btn {
  position: absolute;
  bottom: 4px;
  right: 4px;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: none;
  background: var(--color-surface);
  color: var(--color-text-always-dark);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.avatar-edit-btn:hover { opacity: 0.75; }

.avatar-info {
  text-align: center;
  margin-bottom: 24px;
}

.avatar-name {
  font-size: 22px;
  font-weight: 800;
  color: var(--color-text-primary);
  letter-spacing: -0.4px;
}

.avatar-school {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-muted);
  margin-top: 4px;
}

/* ── Action cards ────────────────────────────────────────────────── */
.action-cards {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.action-row {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px;
  border-radius: 20px;
  border: none;
  background: var(--color-surface);
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.action-row:hover { opacity: 0.8; }

.action-row__left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.action-icon {
  color: var(--color-text-always-dark);
  opacity: 0.5;
  display: flex;
}

.action-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-always-dark);
}

.action-label--danger {
  color: #e53535;
}

.action-chevron {
  color: var(--color-text-always-dark);
  opacity: 0.4;
}

.action-chevron--danger {
  color: #e53535;
  opacity: 1;
}

/* ── Right column ────────────────────────────────────────────────── */
.profile-right {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* ── Stat cards ──────────────────────────────────────────────────── */
.stat-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.stat-card {
  border-radius: 24px;
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat-card--primary {
  background: var(--color-primary);
}

.stat-card--surface {
  background: var(--color-surface);
}

.stat-card__number {
  font-size: 36px;
  font-weight: 900;
  letter-spacing: -1px;
  line-height: 1;
  color: var(--color-text-always-dark);
}

.stat-card--primary .stat-card__number {
  color: var(--color-banner-text);
}

.stat-card__label {
  font-size: 12px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--color-text-always-dark);
  opacity: 0.75;
}

.stat-card--primary .stat-card__label {
  color: var(--color-banner-text);
  opacity: 0.85;
}

/* ── Settings card ───────────────────────────────────────────────── */
.settings-card {
  background: var(--color-surface);
  border-radius: 24px;
  padding: 18px 18px 16px;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.settings-card__title {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-always-dark);
  margin-bottom: 14px;
}

.settings-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.settings-divider {
  height: 1px;
  background: rgba(0, 0, 0, 0.07);
  margin: 4px 0;
}

.settings-icon {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: rgba(0,0,0,0.07);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--color-text-always-dark);
  opacity: 0.5;
}

.settings-icon--text {
  font-size: 11px;
  font-weight: 800;
  opacity: 0.4;
}

.settings-row__label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-always-dark);
  flex: 1;
}

/* ── Settings toggles ────────────────────────────────────────────── */
.settings-toggle {
  width: 42px;
  height: 24px;
  border-radius: 999px;
  border: none;
  background: rgba(0,0,0,0.12);
  cursor: pointer;
  position: relative;
  transition: background 0.25s ease;
  flex-shrink: 0;
}

.settings-toggle--on {
  background: var(--color-primary);
}

.settings-toggle__knob {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.settings-toggle--on .settings-toggle__knob {
  transform: translateX(18px);
}

/* ── Font size slider ────────────────────────────────────────────── */
.font-size-slider-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.font-size-label {
  font-weight: 800;
  color: var(--color-text-always-dark);
  opacity: 0.5;
  flex-shrink: 0;
}

.font-size-label--small { font-size: 11px; }
.font-size-label--large { font-size: 17px; }

/* ── Custom font-size slider ─────────────────────────────────────── */
.custom-slider-track {
  flex: 1;
  position: relative;
  height: 10px;
  border-radius: 999px;
  background: var(--color-primary);
  cursor: pointer;
  /* Enough vertical overflow for tall thumb */
  overflow: visible;
  touch-action: none;
  user-select: none;
  -webkit-user-select: none;
  outline: none;
}

.custom-slider-track:focus-visible {
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-primary) 25%, transparent);
}

.custom-slider-thumb {
  position: absolute;
  top: 50%;
  width: 6px;
  height: 28px;
  border-radius: 999px;
  background: var(--color-text-always-dark);
  transform: translate(-50%, -50%);
  /* Smooth glide — spring easing */
  transition: left 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
  cursor: grab;
  pointer-events: none; /* track handles events */
}

.custom-slider-thumb--dragging {
  transition: none;
  cursor: grabbing;
}

/* Bounce keyframe — triggered on click/tap */
.custom-slider-thumb--bounce {
  animation: thumb-bounce 0.55s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

@keyframes thumb-bounce {
  0%   { transform: translate(-50%, -50%) scaleY(1);    }
  30%  { transform: translate(-50%, -50%) scaleY(1.35); }
  60%  { transform: translate(-50%, -50%) scaleY(0.88); }
  80%  { transform: translate(-50%, -50%) scaleY(1.10); }
  100% { transform: translate(-50%, -50%) scaleY(1);    }
}

/* ── Edit Profile Overlay ────────────────────────────────────────── */
.edit-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: #EBEBEB; /* Match wireframe background */
  z-index: 100;
  display: flex;
  flex-direction: column;
  padding: 0 16px 40px;
  overflow-y: auto;
}
.edit-slide-enter-active,
.edit-slide-leave-active {
  /* Liquid smooth easing (Expo Out curve) instead of bounce */
  transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.4s ease-out;
}
.edit-slide-enter-from,
.edit-slide-leave-to {
  transform: translateY(100%);
  opacity: 0;
}

.edit-avatar-wrap {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  margin-bottom: 40px;
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 400px;
  margin: 0 auto;
  width: 100%;
}

.edit-field {
  display: flex;
  align-items: center;
  background: #ffffff;
  border-radius: 999px;
  padding: 16px 24px;
  min-height: 56px;
}

.edit-field--readonly {
  justify-content: space-between;
}

.edit-field__value {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-always-dark);
}

.edit-field__logo {
  height: 24px;
  width: auto;
  object-fit: contain;
}

.edit-input {
  width: 100%;
  border: none;
  background: transparent;
  outline: none;
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-always-dark);
  font-family: inherit;
}
.edit-input::placeholder {
  color: rgba(0,0,0,0.4);
}

.edit-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16px;
  padding: 0 8px;
}

.edit-cancel-btn {
  background: none;
  border: none;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-always-dark);
  opacity: 0.7;
  cursor: pointer;
  padding: 12px;
}

.edit-save-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--color-primary);
  border: none;
  border-radius: 999px;
  padding: 8px 24px 8px 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-always-dark);
  cursor: pointer;
  transition: transform 0.15s ease;
}
.edit-save-btn:active {
  transform: scale(0.96);
}

/* Save button inner black circle */
.edit-save-btn :first-child {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--color-text-always-dark);
  color: #fff;
  border-radius: 50%;
}

/* ── Desktop layout (md+) ────────────────────────────────────────── */
@media (min-width: 768px) {
  .profile-page {
    padding: 0 36px 40px;
  }

  .profile-layout {
    flex-direction: row;
    align-items: flex-start;
    gap: 32px;
  }

  .profile-left {
    min-width: 240px;
    width: 240px;
    flex-shrink: 0;
    align-items: center;
  }

  .profile-right {
    flex: 1;
    max-width: 420px;
  }

  .avatar-wrap {
    width: 120px;
    height: 120px;
  }

  .avatar-img,
  .avatar-fallback {
    width: 120px;
    height: 120px;
  }
}
</style>
