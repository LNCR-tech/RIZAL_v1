<template>
  <section class="school-it-users">
    <div class="school-it-users__shell">
      <header class="school-it-users__header dashboard-enter dashboard-enter--1">
        <button
          class="school-it-users__profile"
          :class="{ 'school-it-users__profile--expanded': isProfileExpanded }"
          type="button"
          aria-label="Account actions"
          @click="isProfileExpanded = !isProfileExpanded"
        >
          <span class="school-it-users__profile-main">
            <span class="school-it-users__avatar-wrap">
              <img v-if="avatarUrl" :src="avatarUrl" :alt="displayName" class="school-it-users__avatar">
              <span v-else class="school-it-users__avatar school-it-users__avatar--fallback">{{ initials }}</span>
              <span class="school-it-users__status-dot" aria-hidden="true" />
            </span>
            <span class="school-it-users__profile-copy">
              <span class="school-it-users__eyebrow">Welcome Back</span>
              <span class="school-it-users__name">{{ displayName }}</span>
            </span>
          </span>

          <span class="school-it-users__signout" @click.stop="handleLogout">
            <LogOut :size="18" color="#D92D20" :stroke-width="2.4" />
            <span class="school-it-users__signout-label">Sign Out</span>
          </span>
        </button>

        <button class="school-it-users__notify" type="button" aria-label="Notifications">
          <Bell :size="19" :stroke-width="2" />
        </button>
      </header>

      <div class="school-it-users__body">
        <h1 class="school-it-users__title dashboard-enter dashboard-enter--2">Students</h1>

        <section class="school-it-users__search dashboard-enter dashboard-enter--3">
          <div class="school-it-users__search-row">
            <div class="school-it-users__search-wrap">
              <div class="school-it-users__search-shell" :class="{ 'school-it-users__search-shell--open': searchActive }">
                <div class="school-it-users__search-input-row">
                  <input
                    v-model="searchQuery"
                    type="text"
                    placeholder="Search school data"
                    class="school-it-users__search-input"
                  >
                  <button class="school-it-users__search-icon" type="button" aria-label="Search">
                    <Search :size="18" />
                  </button>
                </div>

                <div class="school-it-users__search-results">
                  <div class="school-it-users__search-results-inner">
                    <template v-if="searchActive">
                      <button
                        v-for="result in searchResults"
                        :key="result.key"
                        class="school-it-users__search-result"
                        type="button"
                        @click="openSearchResult(result)"
                      >
                        <div class="school-it-users__search-result-top">
                          <span class="school-it-users__search-result-name">{{ result.name }}</span>
                          <span class="school-it-users__search-result-type">{{ result.type }}</span>
                        </div>
                        <span class="school-it-users__search-result-meta">{{ result.meta }}</span>
                      </button>
                      <p v-if="!searchResults.length" class="school-it-users__empty">No matching school data found.</p>
                    </template>
                  </div>
                </div>
              </div>
            </div>

            <button
              v-show="!searchActive"
              class="school-it-users__ai-pill"
              :class="{ 'school-it-users__ai-pill--open': isAiOpen }"
              type="button"
              aria-label="Talk to Aura AI"
              :aria-expanded="isAiOpen ? 'true' : 'false'"
              aria-controls="school-it-users-ai-panel"
              @click="toggleAiPanel"
            >
              <img :src="activeAuraLogo" alt="Aura" class="school-it-users__ai-logo">
              <span class="school-it-users__ai-copy">Talk to<br>Aura Ai</span>
            </button>
          </div>

          <Transition
            name="school-it-users-ai-panel"
            @before-enter="onAiPanelBeforeEnter"
            @enter="onAiPanelEnter"
            @after-enter="onAiPanelAfterEnter"
            @before-leave="onAiPanelBeforeLeave"
            @leave="onAiPanelLeave"
            @after-leave="onAiPanelAfterLeave"
          >
            <div
              v-if="isAiOpen && !searchActive"
              id="school-it-users-ai-panel"
              class="school-it-users__ai-panel"
              role="region"
              aria-label="Aura AI chat"
            >
              <div class="school-it-users__ai-panel-inner">
                <div class="school-it-users__ai-shell">
                  <div ref="scrollEl" class="school-it-users__ai-messages">
                    <TransitionGroup name="school-it-users-bubble" tag="div" class="school-it-users__ai-messages-inner">
                      <div
                        v-for="message in messages"
                        :key="message.id"
                        :class="[
                          'school-it-users__bubble',
                          message.sender === 'ai'
                            ? 'school-it-users__bubble--ai'
                            : 'school-it-users__bubble--user',
                        ]"
                      >
                        {{ message.text }}
                      </div>

                      <div
                        v-if="isTyping"
                        key="typing"
                        class="school-it-users__bubble school-it-users__bubble--ai school-it-users__bubble--typing"
                      >
                        <span class="school-it-users__typing-dot" style="animation-delay: 0ms" />
                        <span class="school-it-users__typing-dot" style="animation-delay: 150ms" />
                        <span class="school-it-users__typing-dot" style="animation-delay: 300ms" />
                      </div>
                    </TransitionGroup>
                  </div>

                  <div class="school-it-users__ai-input">
                    <div class="school-it-users__ai-input-row">
                      <input
                        ref="aiInputEl"
                        v-model="inputText"
                        class="school-it-users__ai-input-field"
                        type="text"
                        placeholder="Ask Aura..."
                        :disabled="isTyping"
                        @keyup.enter="sendMessage"
                      >
                      <button
                        class="school-it-users__ai-send"
                        type="button"
                        aria-label="Send message"
                        :disabled="!inputText.trim() || isTyping"
                        @click="sendMessage"
                      >
                        <Send :size="15" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Transition>
        </section>

        <section class="school-it-users__overview dashboard-enter dashboard-enter--4">
          <article
            v-for="card in overviewCards"
            :key="card.id"
            class="school-it-users__hero-card"
            :class="[
              card.variant === 'primary'
                ? 'school-it-users__hero-card--primary'
                : 'school-it-users__hero-card--surface',
            ]"
          >
            <div class="school-it-users__hero-card-copy">
              <h2 class="school-it-users__overview-title" v-html="card.titleHtml" />
              <span v-if="card.meta" class="school-it-users__overview-meta">{{ card.meta }}</span>
            </div>

            <button
              class="school-it-users__hero-card-pill"
              :class="{
                'school-it-users__hero-card-pill--surface': card.variant === 'primary',
              }"
              type="button"
              @click="handleOverviewAction(card)"
            >
              <span class="school-it-users__hero-card-pill-icon">
                <ArrowRight :size="18" />
              </span>
              {{ card.actionLabel }}
            </button>
          </article>
        </section>

        <section
          class="school-it-users__alert dashboard-enter dashboard-enter--5"
          :class="{
            'school-it-users__alert--management': hasStudentCouncilAssigned,
          }"
        >
          <template v-if="hasStudentCouncilAssigned">
            <div class="school-it-users__alert-copy school-it-users__alert-copy--management">
              <h2 class="school-it-users__alert-org-name">{{ studentCouncilDisplayText }}</h2>
            </div>

            <button
              class="school-it-users__action-pill"
              type="button"
              @click="openCouncilManagement"
            >
              <span class="school-it-users__action-pill-icon">
                <ArrowRight :size="18" />
              </span>
              Manage
            </button>
          </template>

          <template v-else>
            <div class="school-it-users__alert-copy">
              <p class="school-it-users__alert-kicker">{{ studentCouncilStatus.kicker }}</p>
              <p class="school-it-users__alert-message">{{ studentCouncilStatus.message }}</p>
            </div>

            <button
              class="school-it-users__action-pill"
              type="button"
              @click="openCouncilManagement"
            >
              <span class="school-it-users__action-pill-icon">
                <ArrowRight :size="18" />
              </span>
              {{ studentCouncilStatus.cta }}
            </button>
          </template>
        </section>

        <section class="school-it-users__department-list">
          <article
            v-for="(department, index) in departmentCards"
            :key="department.id"
            class="school-it-users__department-card dashboard-enter"
            :class="`dashboard-enter--${Math.min(index + 6, 9)}`"
          >
            <div class="school-it-users__department-main">
              <h2 class="school-it-users__department-title">{{ department.name }}</h2>
              <button
                class="school-it-users__action-pill school-it-users__action-pill--inline"
                type="button"
                @click="openDepartment(department)"
              >
                <span class="school-it-users__action-pill-icon">
                  <ArrowRight :size="18" />
                </span>
                View
              </button>
            </div>

            <div class="school-it-users__department-panel">
              <p class="school-it-users__department-label">Departments:</p>
              <ul class="school-it-users__program-list">
                <li
                  v-for="program in department.programs"
                  :key="program.id"
                  class="school-it-users__program-item"
                >
                  {{ program.name }}
                </li>
              </ul>
            </div>
          </article>
        </section>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, Bell, LogOut, Search, Send } from 'lucide-vue-next'
import { activeAuraLogo } from '@/config/theme.js'
import { schoolItPreviewData } from '@/data/schoolItPreview.js'
import { useAuth } from '@/composables/useAuth.js'
import { useChat } from '@/composables/useChat.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useSchoolItWorkspaceData } from '@/composables/useSchoolItWorkspaceData.js'
import { createStudentCouncilStorageKey, loadStudentCouncilState } from '@/services/studentCouncilManagement.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const router = useRouter()
const searchQuery = ref('')
const isProfileExpanded = ref(false)
const isAiOpen = ref(false)
const aiInputEl = ref(null)

const { currentUser, schoolSettings, apiBaseUrl } = useDashboardSession()
const {
  departments,
  programs,
  users,
  campusSsgSetup,
  statuses: workspaceStatuses,
  initializeSchoolItWorkspaceData,
} = useSchoolItWorkspaceData()
const { logout } = useAuth()
const {
  closeAll,
  inputText,
  isTyping,
  messages,
  scrollEl,
  sendMessage,
} = useChat()

const activeUser = computed(() => props.preview ? schoolItPreviewData.user : currentUser.value)
const activeSchoolSettings = computed(() => props.preview ? schoolItPreviewData.schoolSettings : schoolSettings.value)
const activeDepartments = computed(() => props.preview ? schoolItPreviewData.departments : departments.value)
const activePrograms = computed(() => props.preview ? schoolItPreviewData.programs : programs.value)
const activeUsers = computed(() => props.preview ? schoolItPreviewData.users : users.value)

const schoolId = computed(() => Number(activeUser.value?.school_id ?? activeSchoolSettings.value?.school_id))
const avatarUrl = computed(() => activeUser.value?.avatar_url || '')
const displayName = computed(() => {
  const first = activeUser.value?.first_name || ''
  const middle = activeUser.value?.middle_name || ''
  const last = activeUser.value?.last_name || ''
  return [first, middle, last].filter(Boolean).join(' ') || activeUser.value?.email?.split('@')[0] || 'School IT'
})
const initials = computed(() => buildInitials(displayName.value))
const settingsRouteName = computed(() => props.preview ? 'PreviewSchoolItSettings' : 'SchoolItSettings')
const councilRouteName = computed(() => props.preview ? 'PreviewSchoolItStudentCouncil' : 'SchoolItStudentCouncil')
const usersRouteName = computed(() => props.preview ? 'PreviewSchoolItUsers' : 'SchoolItUsers')
const previewCouncilState = computed(() => (
  props.preview
    ? loadStudentCouncilState(createStudentCouncilStorageKey(schoolId.value, true))
    : null
))

const filteredDepartments = computed(() => filterEntitiesBySchool(activeDepartments.value, schoolId.value))
const filteredPrograms = computed(() => filterEntitiesBySchool(activePrograms.value, schoolId.value))
const filteredUsers = computed(() => filterEntitiesBySchool(activeUsers.value, schoolId.value))
const studentUsers = computed(() => filteredUsers.value.filter(isStudentUser))
const pendingResetUsers = computed(() => studentUsers.value.filter((user) => user.must_change_password))
const pendingResetsCountLabel = computed(() => String(pendingResetUsers.value.length))
const pendingResetsMeta = computed(() => {
  const count = pendingResetUsers.value.length
  if (count <= 0) return ''
  return `${count} pending`
})
const overviewCards = computed(() => ([
  {
    id: 'import-users',
    titleHtml: 'Import<br>User',
    variant: 'primary',
    actionLabel: 'Import',
    route: { name: settingsRouteName.value, query: { focus: 'import-users' } },
    meta: '',
  },
  {
    id: 'pending-resets',
    titleHtml: 'Pending<br>Resets',
    variant: 'surface',
    actionLabel: 'Review',
    route: { name: usersRouteName.value, query: { filter: 'pending-resets' } },
    meta: pendingResetsMeta.value,
  },
]))
const studentCouncilRecord = computed(() => {
  if (props.preview) return previewCouncilState.value?.council || null
  return campusSsgSetup.value?.unit || null
})
const studentCouncilState = computed(() => (
  props.preview
    ? (studentCouncilRecord.value?.id ? 'ready' : 'absent')
    : workspaceStatuses.value?.council || 'idle'
))
const hasStudentCouncilAssigned = computed(() => (
  studentCouncilState.value === 'ready' && Boolean(studentCouncilRecord.value?.id)
))
const studentCouncilDisplayText = computed(() => {
  const acronym = String(
    studentCouncilRecord.value?.acronym
    || studentCouncilRecord.value?.unit_code
    || ''
  ).trim()
  const fallbackName = String(
    studentCouncilRecord.value?.name
    || studentCouncilRecord.value?.unit_name
    || 'Student Council'
  ).trim()

  const displayValue = acronym || fallbackName
  return `${displayValue} is set`
})

const studentCouncilStatus = computed(() => {
  if (hasStudentCouncilAssigned.value) {
    return {
      kicker: 'READY',
      message: 'Student Council is already assigned to this Campus',
      cta: 'View Setup',
    }
  }

  if (studentCouncilState.value === 'loading' || studentCouncilState.value === 'idle') {
    return {
      kicker: 'CHECKING',
      message: 'Checking Student Council setup for this Campus',
      cta: 'Open Setup',
    }
  }

  if (studentCouncilState.value === 'blocked') {
    return {
      kicker: 'RESTRICTED',
      message: 'Student Council setup is unavailable until privileged verification is completed',
      cta: 'Open Setup',
    }
  }

  if (studentCouncilState.value === 'error') {
    return {
      kicker: 'UNAVAILABLE',
      message: 'Student Council setup could not be loaded right now',
      cta: 'Open Setup',
    }
  }

  return {
    kicker: 'URGENT',
    message: 'No Student Council assigned to this Campus',
    cta: 'Assign Now',
  }
})

const departmentCards = computed(() => (
  filteredDepartments.value
    .map((department) => ({
      ...department,
      programs: filteredPrograms.value
        .filter((program) => Array.isArray(program.department_ids) && program.department_ids.includes(Number(department.id)))
        .slice(0, 3),
    }))
    .filter((department) => department.programs.length)
))

const searchActive = computed(() => searchQuery.value.trim().length > 0)
const searchResults = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return []

  const userResults = studentUsers.value
    .filter((user) => `${user.first_name} ${user.last_name}`.toLowerCase().includes(query) || String(user.email || '').toLowerCase().includes(query))
    .map((user) => ({
      key: `user-${user.id}`,
      name: `${user.first_name} ${user.last_name}`.trim() || user.email,
      type: 'Student',
      meta: user.student_profile?.student_id || user.email,
      action: () => router.push({ name: settingsRouteName.value, query: { student: user.id } }),
    }))

  const departmentResults = filteredDepartments.value
    .filter((department) => department.name.toLowerCase().includes(query))
    .map((department) => ({
      key: `department-${department.id}`,
      name: department.name,
      type: 'College',
      meta: `${filteredPrograms.value.filter((program) => program.department_ids?.includes(Number(department.id))).length} linked programs`,
      action: () => openDepartment(department),
    }))

  const programResults = filteredPrograms.value
    .filter((program) => program.name.toLowerCase().includes(query))
    .map((program) => ({
      key: `program-${program.id}`,
      name: program.name,
      type: 'Program',
      meta: 'Program setup',
      action: () => router.push({ name: settingsRouteName.value, query: { program: program.id } }),
    }))

  return [...userResults, ...departmentResults, ...programResults].slice(0, 8)
})

const nextFrame = (callback) => requestAnimationFrame(() => requestAnimationFrame(callback))

watch([apiBaseUrl, () => activeUser.value?.id, schoolId, () => props.preview], async ([resolvedApiBaseUrl, userId, , preview]) => {
  if (preview) return
  if (!resolvedApiBaseUrl || !userId) return
  await initializeSchoolItWorkspaceData(true)
}, { immediate: true })

watch(isAiOpen, (open) => {
  if (!open) return
  closeAll()
  nextTick(() => {
    setTimeout(() => aiInputEl.value?.focus(), 220)
  })
})

watch(searchActive, (active) => {
  if (active) isAiOpen.value = false
})

function buildInitials(value) {
  const parts = String(value || '').split(' ').filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
  return String(value || '').slice(0, 2).toUpperCase()
}

function filterEntitiesBySchool(items, activeSchoolId) {
  if (!Array.isArray(items)) return []
  if (!Number.isFinite(activeSchoolId)) return items
  return items.filter((item) => Number(item?.school_id) === activeSchoolId)
}

function isStudentUser(user) {
  const roles = Array.isArray(user?.roles)
    ? user.roles.map((role) => String(role?.role?.name || role?.name || '').toLowerCase())
    : []
  return Boolean(user?.student_profile) || roles.includes('student')
}

function openSearchResult(result) {
  searchQuery.value = ''
  result.action?.()
}

function openDepartment(department) {
  router.push({ name: settingsRouteName.value, query: { department: department.id } })
}

function openCouncilManagement() {
  router.push({ name: councilRouteName.value })
}

function handleOverviewAction(card) {
  if (!card?.route) return
  router.push(card.route)
}

function toggleAiPanel() {
  isAiOpen.value = !isAiOpen.value
}

function onAiPanelBeforeEnter(element) {
  element.style.height = '0px'
  element.style.opacity = '0'
  element.style.transform = 'translateY(-8px)'
  element.style.willChange = 'height, opacity, transform'
}

function onAiPanelEnter(element) {
  const height = element.scrollHeight
  element.style.transition = 'height 520ms cubic-bezier(0.22, 1, 0.36, 1), opacity 320ms ease, transform 420ms cubic-bezier(0.22, 1, 0.36, 1)'
  nextFrame(() => {
    element.style.height = `${height}px`
    element.style.opacity = '1'
    element.style.transform = 'translateY(0)'
  })
}

function onAiPanelAfterEnter(element) {
  element.style.height = 'auto'
  element.style.transition = ''
  element.style.willChange = ''
}

function onAiPanelBeforeLeave(element) {
  element.style.height = `${element.scrollHeight}px`
  element.style.opacity = '1'
  element.style.transform = 'translateY(0)'
  element.style.willChange = 'height, opacity, transform'
}

function onAiPanelLeave(element) {
  element.style.transition = 'height 420ms cubic-bezier(0.4, 0, 0.2, 1), opacity 240ms ease, transform 300ms ease'
  nextFrame(() => {
    element.style.height = '0px'
    element.style.opacity = '0'
    element.style.transform = 'translateY(-6px)'
  })
}

function onAiPanelAfterLeave(element) {
  element.style.transition = ''
  element.style.height = ''
  element.style.opacity = ''
  element.style.transform = ''
  element.style.willChange = ''
}

async function handleLogout() {
  await logout()
}
</script>

<style scoped>
.school-it-users{min-height:100vh;padding:30px 28px 120px;font-family:'Manrope',sans-serif}
.school-it-users__shell{width:100%;max-width:1120px;margin:0 auto}
.school-it-users__header{display:flex;align-items:center;justify-content:space-between;gap:18px}
.school-it-users__profile{display:inline-flex;align-items:center;min-height:56px;padding:8px 14px 8px 8px;border:none;border-radius:999px;background:var(--color-surface);color:var(--color-text-always-dark);transition:all .3s ease;cursor:pointer}
.school-it-users__profile-main{display:inline-flex;align-items:center;gap:12px;min-width:0}
.school-it-users__avatar-wrap{position:relative;display:inline-flex;flex-shrink:0}
.school-it-users__avatar{width:42px;height:42px;border-radius:999px;object-fit:cover;flex-shrink:0}
.school-it-users__avatar--fallback{display:inline-flex;align-items:center;justify-content:center;background:var(--color-nav);color:var(--color-nav-text);font-size:14px;font-weight:700}
.school-it-users__status-dot{position:absolute;right:0;bottom:0;width:10px;height:10px;border-radius:999px;background:var(--color-primary);border:2px solid var(--color-surface)}
.school-it-users__profile-copy{display:flex;flex-direction:column;align-items:flex-start;min-width:0;line-height:1}
.school-it-users__eyebrow{font-size:10px;font-weight:500;color:var(--color-text-muted)}
.school-it-users__name{margin-top:2px;font-size:14px;font-weight:700;line-height:1.08;color:var(--color-text-always-dark)}
.school-it-users__signout{display:inline-flex;align-items:center;overflow:hidden;max-width:0;opacity:0;margin-left:0;white-space:nowrap;transition:all .3s ease-in-out;color:#D92D20;cursor:pointer}
.school-it-users__signout-label{margin-left:8px;font-size:14px;font-weight:500;letter-spacing:-.02em}
.school-it-users__profile:hover .school-it-users__signout,.school-it-users__profile--expanded .school-it-users__signout{max-width:150px;opacity:1;margin-left:24px;margin-right:4px}
.school-it-users__notify{width:44px;height:44px;border:none;border-radius:999px;background:var(--color-surface);color:var(--color-text-always-dark);display:inline-flex;align-items:center;justify-content:center;transition:transform .16s ease;flex-shrink:0}
.school-it-users__notify:active{transform:scale(.95)}
.school-it-users__body{display:flex;flex-direction:column;gap:18px;margin-top:24px}
.school-it-users__title{margin:0;font-size:22px;font-weight:800;line-height:1;letter-spacing:-.05em;color:var(--color-text-primary)}
.school-it-users__search{display:flex;flex-direction:column;gap:10px}
.school-it-users__search-row{display:flex;align-items:stretch;gap:clamp(8px,3vw,12px)}
.school-it-users__search-wrap{flex:1;min-width:0}
.school-it-users__search-shell{display:grid;grid-template-rows:auto 0fr;padding:11px clamp(12px,4vw,16px);border-radius:30px;background:var(--color-surface);transition:grid-template-rows .32s cubic-bezier(.22,1,.36,1),border-radius .32s cubic-bezier(.22,1,.36,1)}
.school-it-users__search-shell--open{grid-template-rows:auto 1fr;border-radius:28px}
.school-it-users__search-input-row{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:clamp(8px,2.5vw,10px);min-height:clamp(38px,10vw,40px)}
.school-it-users__search-input{flex:1;min-width:0;border:none;background:transparent;outline:none;color:var(--color-text-always-dark);font-size:clamp(13px,3.8vw,14px);font-weight:500}
.school-it-users__search-input::placeholder{color:var(--color-text-muted)}
.school-it-users__search-icon{width:clamp(30px,8vw,32px);height:clamp(30px,8vw,32px);padding:0;border:1px solid var(--color-surface-border);border-radius:999px;background:transparent;color:var(--color-primary);display:inline-flex;align-items:center;justify-content:center;line-height:0;appearance:none;flex-shrink:0;place-self:center}
.school-it-users__search-icon :deep(svg){display:block;width:clamp(15px,4.5vw,18px);height:clamp(15px,4.5vw,18px)}
.school-it-users__search-results{overflow:hidden;min-height:0}
.school-it-users__search-results-inner{display:flex;flex-direction:column;gap:10px;padding:14px 0 6px}
.school-it-users__search-result{width:100%;padding:14px 16px;border:none;border-radius:22px;background:color-mix(in srgb,var(--color-surface) 90%,var(--color-bg));display:flex;flex-direction:column;gap:8px;text-align:left}
.school-it-users__search-result-top{display:flex;align-items:center;justify-content:space-between;gap:12px}
.school-it-users__search-result-name{font-size:14px;font-weight:700;color:var(--color-text-always-dark)}
.school-it-users__search-result-type{min-height:28px;padding:0 12px;border-radius:999px;background:color-mix(in srgb,var(--color-primary) 18%,white);color:var(--color-text-always-dark);display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;letter-spacing:.02em;flex-shrink:0}
.school-it-users__search-result-meta,.school-it-users__empty{font-size:12px;color:var(--color-text-muted)}
.school-it-users__ai-pill{width:clamp(108px,30vw,122px);min-height:clamp(56px,15vw,60px);padding:0 clamp(12px,4vw,14px);border:none;border-radius:999px;background:var(--color-primary);color:var(--color-banner-text);display:inline-flex;align-items:center;justify-content:center;gap:clamp(8px,2.6vw,10px);flex-shrink:0;transition:opacity .2s ease,transform .2s ease,box-shadow .25s ease,filter .22s ease}
.school-it-users__ai-pill:hover{filter:brightness(1.08);transform:scale(1.04)}
.school-it-users__ai-pill:active{transform:scale(.96)}
.school-it-users__ai-pill--open{box-shadow:0 12px 24px rgba(0,0,0,.14);transform:translateY(1px) scale(.98)}
.school-it-users__ai-logo{width:clamp(28px,8vw,32px);height:clamp(28px,8vw,32px);object-fit:contain}
.school-it-users__ai-copy{font-size:clamp(12px,3.4vw,13px);font-weight:700;line-height:.98;text-align:left}
.school-it-users__ai-panel{overflow:hidden;transform-origin:top center}
.school-it-users__ai-panel-inner{overflow:hidden}
.school-it-users__ai-shell{position:relative;display:flex;flex-direction:column;gap:10px;padding:14px;background:var(--color-ai-surface);border-radius:28px;box-shadow:0 18px 40px rgba(0,0,0,.14);overflow:hidden}
.school-it-users__ai-messages{position:relative;z-index:1;display:flex;flex-direction:column;gap:10px;min-height:clamp(110px,22vh,180px);max-height:min(46vh,320px);overflow-y:auto;padding:6px 6px 0;scrollbar-width:none}
.school-it-users__ai-messages::-webkit-scrollbar{display:none}
.school-it-users__ai-messages-inner{display:flex;flex-direction:column;gap:10px}
.school-it-users__bubble{max-width:88%;padding:12px 16px;border-radius:24px;font-size:13px;font-weight:600;line-height:1.6;font-family:'Manrope',sans-serif;word-break:break-word}
.school-it-users__bubble--ai{align-self:flex-start;background:#FFFFFF;color:#0A0A0A;box-shadow:0 8px 18px rgba(0,0,0,.08)}
.school-it-users__bubble--user{align-self:flex-end;background:var(--color-ai-user-bubble-bg);color:var(--color-ai-user-bubble-text);border:1px solid var(--color-ai-input-border)}
.school-it-users__bubble--typing{display:flex;align-items:center;gap:6px;padding:12px 16px}
.school-it-users__typing-dot{width:6px;height:6px;border-radius:999px;background:color-mix(in srgb,var(--color-ai-surface-text) 50%, transparent);animation:schoolItUsersDotBounce 1s infinite ease-in-out}
.school-it-users__ai-input{position:relative;z-index:1}
.school-it-users__ai-input-row{display:flex;align-items:center;gap:8px;height:44px;padding:0 8px 0 16px;border:1.4px solid var(--color-ai-input-border);border-radius:999px;background:var(--color-ai-input-bg);transition:border-color .2s ease,background .2s ease}
.school-it-users__ai-input-row:focus-within{background:var(--color-ai-input-bg-focus);border-color:color-mix(in srgb,var(--color-ai-surface-text) 22%, var(--color-ai-surface))}
.school-it-users__ai-input-field{flex:1;min-width:0;border:none;outline:none;background:transparent;color:var(--color-ai-surface-text);font-size:12.5px;font-weight:600}
.school-it-users__ai-input-field::placeholder{color:var(--color-ai-surface-text);opacity:.55}
.school-it-users__ai-send{display:flex;align-items:center;justify-content:center;width:34px;height:34px;border:none;border-radius:999px;background:var(--color-ai-send-bg);color:var(--color-ai-surface-text);cursor:pointer;flex-shrink:0;transition:background .18s ease,transform .15s ease,opacity .18s ease}
.school-it-users__ai-send:hover:not(:disabled){background:var(--color-ai-send-bg-hover);transform:scale(1.08)}
.school-it-users__ai-send:disabled{opacity:.45;cursor:not-allowed}
.school-it-users__overview{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.school-it-users__hero-card{position:relative;display:flex;flex-direction:column;justify-content:space-between;gap:18px;min-height:188px;padding:26px 22px 20px;border-radius:32px;overflow:hidden}
.school-it-users__hero-card--primary{background:var(--color-primary);color:var(--color-banner-text)}
.school-it-users__hero-card--surface{background:var(--color-surface);color:var(--color-text-always-dark)}
.school-it-users__hero-card-copy{display:flex;flex-direction:column;gap:10px;min-width:0}
.school-it-users__overview-title{margin:0;font-size:clamp(24px,8vw,44px);line-height:.92;letter-spacing:-.06em;font-weight:700}
.school-it-users__overview-meta{font-size:12px;font-weight:700;line-height:1;color:var(--color-primary)}
.school-it-users__hero-card-pill{width:fit-content;min-height:52px;padding:0 18px 0 6px;border:none;border-radius:999px;background:var(--color-primary);color:var(--color-banner-text);display:inline-flex;align-items:center;gap:12px;font-size:12px;font-weight:700;letter-spacing:-.02em;white-space:nowrap}
.school-it-users__hero-card-pill--surface{background:var(--color-surface);color:var(--color-text-always-dark)}
.school-it-users__hero-card-pill-icon{width:40px;height:40px;border-radius:999px;background:var(--color-nav);color:var(--color-nav-text);display:inline-flex;align-items:center;justify-content:center;flex-shrink:0}
.school-it-users__alert{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:22px 20px;border-radius:28px;background:var(--color-surface)}
.school-it-users__alert--management{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;padding:24px 22px;gap:20px;min-height:124px}
.school-it-users__alert-copy{display:flex;flex-direction:column;gap:4px;min-width:0}
.school-it-users__alert-copy--management{gap:0;max-width:none;align-items:center;justify-self:stretch;text-align:center}
.school-it-users__alert-org-name{margin:0;font-size:clamp(24px,7.2vw,40px);line-height:.94;letter-spacing:-.06em;font-weight:700;color:var(--color-text-always-dark);text-align:center}
.school-it-users__alert-kicker{margin:0;font-size:clamp(18px,5vw,28px);line-height:1;font-weight:800;letter-spacing:-.05em;color:#FF2D20}
.school-it-users__alert-message{margin:0;max-width:16ch;font-size:15px;line-height:1.05;color:var(--color-text-always-dark)}
.school-it-users__action-pill{width:fit-content;min-height:52px;padding:0 18px 0 6px;border:none;border-radius:999px;background:var(--color-primary);color:var(--color-banner-text);display:inline-flex;align-items:center;gap:12px;font-size:12px;font-weight:700;letter-spacing:-.02em;white-space:nowrap;flex-shrink:0}
.school-it-users__action-pill--inline{min-height:54px;padding-right:18px;font-size:13px}
.school-it-users__action-pill-icon{width:40px;height:40px;border-radius:999px;background:var(--color-nav);color:var(--color-nav-text);display:inline-flex;align-items:center;justify-content:center;flex-shrink:0}
.school-it-users__department-list{display:flex;flex-direction:column;gap:18px}
.school-it-users__department-card{display:grid;grid-template-columns:minmax(0,1fr) minmax(138px,.9fr);gap:8px;padding:8px;border-radius:32px;background:var(--color-surface)}
.school-it-users__department-main{display:flex;flex-direction:column;justify-content:space-between;min-height:194px;padding:20px 14px 14px}
.school-it-users__department-title{margin:0;max-width:7ch;font-size:clamp(28px,8vw,52px);line-height:.92;letter-spacing:-.07em;font-weight:700;color:var(--color-text-always-dark)}
.school-it-users__department-panel{display:flex;flex-direction:column;gap:10px;padding:22px 16px;border-radius:24px;background:color-mix(in srgb,var(--color-surface) 88%,var(--color-bg))}
.school-it-users__department-label{margin:0;font-size:12px;font-weight:700;line-height:1.1;color:var(--color-primary)}
.school-it-users__program-list{display:flex;flex-direction:column;gap:4px;margin:0;padding:0;list-style:none}
.school-it-users__program-item{font-size:14px;line-height:1.15;color:var(--color-text-always-dark)}
.school-it-users-bubble-enter-active{animation:schoolItUsersBubblePop .45s cubic-bezier(.34,1.56,.64,1) both}
.school-it-users__bubble--ai.school-it-users-bubble-enter-active{transform-origin:bottom left}
.school-it-users__bubble--user.school-it-users-bubble-enter-active{transform-origin:bottom right}

@media (min-width:768px){
  .school-it-users{padding:40px 36px 56px}
  .school-it-users__body{margin-top:30px;gap:22px}
  .school-it-users__title{font-size:28px}
  .school-it-users__search-row,.school-it-users__ai-panel{max-width:780px}
  .school-it-users__overview{max-width:780px}
  .school-it-users__alert{max-width:780px}
  .school-it-users__alert--management{padding:28px 26px}
  .school-it-users__department-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}
}

@media (prefers-reduced-motion:reduce){
  .school-it-users__ai-pill,.school-it-users__ai-send,.school-it-users-bubble-enter-active{transition:none;animation:none}
}

@keyframes schoolItUsersDotBounce{
  0%,100%{transform:translateY(0)}
  40%{transform:translateY(-4px)}
}

@keyframes schoolItUsersBubblePop{
  0%{opacity:0;transform:scale(.55)}
  65%{opacity:1;transform:scale(1.04)}
  82%{transform:scale(.97)}
  100%{transform:scale(1)}
}
</style>
