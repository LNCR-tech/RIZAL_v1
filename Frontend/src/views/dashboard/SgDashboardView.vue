<template>
  <div class="sg-page">
    <!-- TopBar (reused) -->
    <TopBar
      class="dashboard-enter dashboard-enter--1"
      :user="currentUser"
      :unread-count="0"
    />

    <!-- Page Title -->
    <div class="mt-1 px-1 dashboard-enter dashboard-enter--2">
      <h1 class="sg-page-title">Home</h1>
    </div>

    <!-- Search bar + Talk to Aura AI row -->
    <div class="search-area dashboard-enter dashboard-enter--3">
      <div class="search-row">
        <!-- Search bar -->
        <div class="search-wrap" :class="{ 'search-wrap--active': searchActive }">
          <div class="search-shell" :class="{ 'search-shell--open': searchActive }">
            <div class="search-input-row">
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Search modules..."
                class="search-input"
              />
              <span class="search-icon-wrap" aria-hidden="true">
                <Search
                  :size="14"
                  class="search-icon"
                  style="color: var(--color-primary);"
                />
              </span>
            </div>
          </div>
        </div>

        <!-- Talk to Aura AI (mobile only) -->
        <button
          v-show="!searchActive"
          class="ai-pill md:hidden"
          :class="{ 'ai-pill--open': isMobileAiOpen }"
          aria-label="Talk to Aura AI"
          :aria-expanded="isMobileAiOpen ? 'true' : 'false'"
          aria-controls="mobile-ai-panel"
          type="button"
          @click="toggleMobileAi"
        >
          <img
            :src="secondaryAuraLogo"
            alt="Aura"
            class="w-4 h-4 object-contain opacity-90"
          />
          <span
            class="text-[9px] font-extrabold text-left leading-[1.1]"
            style="color: var(--color-search-pill-text);"
          >
            Talk to<br>Aura Ai
          </span>
        </button>
      </div>

      <!-- Mobile AI panel -->
      <Transition
        name="mobile-ai-panel"
        @before-enter="onMobilePanelBeforeEnter"
        @enter="onMobilePanelEnter"
        @after-enter="onMobilePanelAfterEnter"
        @before-leave="onMobilePanelBeforeLeave"
        @leave="onMobilePanelLeave"
        @after-leave="onMobilePanelAfterLeave"
      >
        <div
          v-if="isMobileAiOpen && !searchActive"
          id="mobile-ai-panel"
          class="mobile-ai-panel md:hidden"
          role="region"
          aria-label="Aura AI chat"
        >
          <div class="mobile-ai-panel-inner">
            <div class="mobile-ai-shell">
              <div class="mobile-ai-messages" ref="scrollEl">
                <TransitionGroup name="mobile-bubble" tag="div" class="mobile-ai-messages-inner">
                  <div
                    v-for="msg in messages"
                    :key="msg.id"
                    :class="['mobile-bubble', msg.sender === 'ai' ? 'mobile-bubble--ai' : 'mobile-bubble--user']"
                  >
                    {{ msg.text }}
                  </div>

                  <div v-if="isTyping" key="typing" class="mobile-bubble mobile-bubble--ai mobile-bubble--typing">
                    <span class="mobile-dot" style="animation-delay: 0ms"   />
                    <span class="mobile-dot" style="animation-delay: 150ms" />
                    <span class="mobile-dot" style="animation-delay: 300ms" />
                  </div>
                </TransitionGroup>
              </div>

              <div class="mobile-ai-input">
                <div class="mobile-ai-input-row">
                  <input
                    ref="mobileInputEl"
                    v-model="inputText"
                    class="mobile-ai-input-field"
                    type="text"
                    placeholder="Ask Aura..."
                    :disabled="isTyping"
                    @keyup.enter="sendMessage"
                  />
                  <button
                    class="mobile-ai-send-btn"
                    :disabled="!inputText.trim() || isTyping"
                    aria-label="Send message"
                    type="button"
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
    </div>

    <!-- Error state -->
    <div v-if="error && !isLoading" class="sg-state-card dashboard-enter dashboard-enter--4">
      <AlertCircle :size="32" style="color: var(--color-primary);" />
      <p class="sg-state-title">Unable to load SG Dashboard</p>
      <p class="sg-state-message">{{ error }}</p>
    </div>

    <!-- Dashboard content -->
    <template v-else>
      <!-- Hero banner -->
      <div class="sg-hero dashboard-enter dashboard-enter--4">
        <div class="sg-hero-content">
          <p class="sg-hero-subtitle">Welcome to</p>
          <h2 class="sg-hero-title">{{ acronym }} Dashboard</h2>
          <p class="sg-hero-officer">
            <template v-if="officerPosition">{{ officerPosition }} </template>
            {{ officerName }}
          </p>
        </div>
        <div v-if="resolvedSchoolLogo && !heroLogoUnavailable" class="sg-hero-logo-wrap">
          <img
            :src="resolvedSchoolLogo"
            :alt="schoolName + ' logo'"
            class="sg-hero-logo"
            @error="onHeroLogoError"
          />
        </div>
        <div v-else class="sg-hero-logo-fallback" aria-hidden="true">
          {{ schoolInitials }}
        </div>
      </div>

      <section class="sg-reports dashboard-enter dashboard-enter--5">
        <article class="sg-report-card sg-report-card--summary">
          <div class="sg-report-head">
            <div>
              <p class="sg-report-kicker">Governance Snapshot</p>
              <h2 class="sg-report-title">{{ unitName }}</h2>
            </div>
            <span class="sg-report-badge">{{ overviewLoading ? 'Syncing' : 'Live' }}</span>
          </div>

          <p v-if="overviewError" class="sg-report-note">{{ overviewError }}</p>

          <div class="sg-report-stats">
            <article v-for="card in overviewCards" :key="card.id" class="sg-report-stat">
              <span>{{ card.label }}</span>
              <strong>{{ card.value }}</strong>
              <small>{{ card.meta }}</small>
            </article>
          </div>
        </article>

        <article class="sg-report-card">
          <div class="sg-report-head">
            <div>
              <p class="sg-report-kicker">Child Units</p>
              <h2 class="sg-report-title">Member Load</h2>
            </div>
          </div>

          <div v-if="childUnitChartData.labels.length" class="sg-report-chart">
            <ReportsBarChart :data="childUnitChartData" :options="chartOptions.bar" />
          </div>
          <p v-else class="sg-report-empty">No child units are assigned to this governance scope yet.</p>
        </article>

        <article class="sg-report-card">
          <div class="sg-report-head">
            <div>
              <p class="sg-report-kicker">Announcements</p>
              <h2 class="sg-report-title">Publishing Mix</h2>
            </div>
          </div>

          <div v-if="announcementStatusChartData.labels.length" class="sg-report-chart">
            <ReportsPieChart :data="announcementStatusChartData" :options="chartOptions.pie" />
          </div>
          <p v-else class="sg-report-empty">No announcement activity is available yet.</p>
        </article>

        <article class="sg-report-card sg-report-card--feed">
          <div class="sg-report-head">
            <div>
              <p class="sg-report-kicker">Recent Announcements</p>
              <h2 class="sg-report-title">What Changed</h2>
            </div>
          </div>

          <div v-if="recentAnnouncementRows.length" class="sg-report-feed">
            <article v-for="item in recentAnnouncementRows" :key="item.id" class="sg-report-feed-row">
              <div>
                <h3>{{ item.title }}</h3>
                <p>{{ item.meta }}</p>
              </div>
              <span class="sg-report-feed-badge">{{ item.badge }}</span>
            </article>
          </div>
          <p v-else class="sg-report-empty">No recent announcements to show.</p>
        </article>
      </section>

      <!-- Anti-Gravity Module Sections -->
      <div
        v-for="(section, sIndex) in filteredSections"
        :key="section.id"
        class="ag-section dashboard-enter"
        :class="`dashboard-enter--${6 + sIndex}`"
      >
        <h2 class="ag-section-title">{{ section.title }}</h2>

        <div class="ag-modules-list">
          <button
            v-for="mod in section.modules"
            :key="mod.id"
            class="ag-module-row"
            :class="{
              'ag-module-row--restricted': !hasPermission(mod.permissionCode) && mod.id !== 'view-students',
              'ag-module-row--high': mod.id === 'create-sg' || mod.id === 'create-org',
            }"
            type="button"
            @click="handleModuleClick(mod)"
          >
            <!-- Icon container -->
            <div
              class="ag-module-icon"
              :class="{
                'ag-module-icon--restricted': !hasPermission(mod.permissionCode) && mod.id !== 'view-students',
              }"
            >
              <component :is="mod.icon" :size="20" :stroke-width="1.8" />
            </div>

            <!-- Text content -->
            <div class="ag-module-text">
              <span class="ag-module-label">{{ mod.label }}</span>
              <span class="ag-module-desc">{{ mod.description }}</span>
            </div>

            <!-- Arrow or Lock -->
            <div class="ag-module-action">
              <template v-if="hasPermission(mod.permissionCode) || mod.id === 'view-students'">
                <div class="ag-module-arrow">
                  <ArrowRight :size="18" :stroke-width="2" />
                </div>
              </template>
              <template v-else>
                <div class="ag-module-lock">
                  <Lock :size="16" :stroke-width="2" />
                </div>
              </template>
            </div>
          </button>
        </div>
      </div>
    </template>

    <!-- Floating toast notification -->
    <Transition name="sg-toast">
      <div
        v-if="toastVisible"
        class="sg-toast"
        @click="toastVisible = false"
      >
        <Lock :size="16" :stroke-width="2.2" />
        <span>{{ toastMessage }}</span>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search, ArrowRight, AlertCircle, Send, Lock } from 'lucide-vue-next'
import TopBar from '@/components/dashboard/TopBar.vue'
import ReportsBarChart from '@/components/reports/ReportsBarChart.vue'
import ReportsPieChart from '@/components/reports/ReportsPieChart.vue'
import { secondaryAuraLogo, applyTheme, loadTheme, defaultTheme } from '@/config/theme.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useSgDashboard } from '@/composables/useSgDashboard.js'
import { useSgPreviewBundle } from '@/composables/useSgPreviewBundle.js'
import { useChat } from '@/composables/useChat.js'
import { getAllSections, filterSectionsBySearch } from '@/data/sgModules.js'
import { getGovernanceDashboardOverview } from '@/services/backendApi.js'
import { resolveBackendMediaCandidates, withMediaCacheKey } from '@/services/backendMedia.js'
import { buildBarChartData, buildPieChartData, toCount } from '@/services/dashboardReportCharts.js'
import { useStoredAuthMeta } from '@/composables/useStoredAuthMeta.js'
import { withPreservedGovernancePreviewQuery } from '@/services/routeWorkspace.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const route = useRoute()
const router = useRouter()
const searchQuery = ref('')
const heroLogoUnavailable = ref(false)
const heroLogoIndex = ref(0)
const heroLogoRetryKey = ref(0)
const toastVisible = ref(false)
const toastMessage = ref('')
const isMobileAiOpen = ref(false)
const mobileInputEl = ref(null)
const overviewLoading = ref(false)
const overviewError = ref('')
const governanceOverview = ref(null)
let toastTimer = null

const authMeta = useStoredAuthMeta()
const { apiBaseUrl, token } = useDashboardSession()
const { previewBundle } = useSgPreviewBundle(() => props.preview)

const {
  isLoading,
  error,
  permissionCodes,
  officerPosition,
  officerName,
  acronym,
  unitName,
  activeUnitId,
  currentUser,
  schoolSettings,
  schoolName,
  schoolLogo,
} = useSgDashboard(props.preview)

const resolvedSchoolLogoCandidates = computed(() =>
  resolveBackendMediaCandidates([
    schoolLogo.value,
    schoolSettings.value?.logo_url,
    authMeta.value?.logoUrl,
    defaultTheme.schoolLogo
  ])
)

const resolvedSchoolLogo = computed(() => {
  if (heroLogoUnavailable.value || !resolvedSchoolLogoCandidates.value.length) return null
  return withMediaCacheKey(
    resolvedSchoolLogoCandidates.value[heroLogoIndex.value] || null,
    heroLogoRetryKey.value || ''
  )
})

function onHeroLogoError() {
  if (heroLogoIndex.value < resolvedSchoolLogoCandidates.value.length - 1) {
    heroLogoIndex.value += 1
    return
  }
  
  if (!heroLogoRetryKey.value) {
    heroLogoRetryKey.value = Date.now()
    return
  }

  heroLogoUnavailable.value = true
}

watch(
  () => resolvedSchoolLogoCandidates.value.join('|'),
  () => {
    heroLogoUnavailable.value = false
    heroLogoIndex.value = 0
    heroLogoRetryKey.value = 0
  }
)

const schoolInitials = computed(() => {
  const parts = String(schoolName.value || '').split(' ').filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
  return String(schoolName.value || '').slice(0, 2).toUpperCase()
})

const searchActive = computed(() => searchQuery.value.trim().length > 0)

/**
 * Anti-Gravity approach: Show ALL modules always.
 * Restricted ones are visually dimmed with a lock icon.
 */
const permissionSet = computed(() => new Set(permissionCodes.value))

function hasPermission(code) {
  return permissionSet.value.has(code)
}

const allSections = computed(() => getAllSections())
const filteredSections = computed(() =>
  filterSectionsBySearch(allSections.value, searchQuery.value)
)

const resolvedGovernanceOverview = computed(() => props.preview
  ? buildPreviewGovernanceOverview(previewBundle.value)
  : governanceOverview.value
)

const overviewCards = computed(() => {
  const overview = resolvedGovernanceOverview.value
  return [
    {
      id: 'students',
      label: 'Students in Scope',
      value: toCount(overview?.total_students),
      meta: 'Students you can currently reach',
    },
    {
      id: 'published',
      label: 'Published Announcements',
      value: toCount(overview?.published_announcement_count),
      meta: `${toCount(overview?.recent_announcements?.length)} recent updates`,
    },
    {
      id: 'children',
      label: 'Child Units',
      value: toCount(overview?.child_units?.length),
      meta: 'Directly under this governance scope',
    },
    {
      id: 'permissions',
      label: 'Active Permissions',
      value: toCount(permissionCodes.value.length),
      meta: 'Granted to this officer session',
    },
  ]
})

const childUnitChartData = computed(() => buildBarChartData(
  (Array.isArray(resolvedGovernanceOverview.value?.child_units) ? resolvedGovernanceOverview.value.child_units : []).map((item) => ({
    label: item.unit_code || item.unit_name,
    value: item.member_count,
  })),
  {
    label: 'Members',
    backgroundColor: 'rgba(0,87,184,0.82)',
  }
))

const announcementStatusChartData = computed(() => {
  const grouped = new Map()
  for (const item of Array.isArray(resolvedGovernanceOverview.value?.recent_announcements) ? resolvedGovernanceOverview.value.recent_announcements : []) {
    const status = String(item?.status || 'draft').trim().toLowerCase() || 'draft'
    grouped.set(status, (grouped.get(status) || 0) + 1)
  }

  return buildPieChartData(Array.from(grouped.entries()).map(([label, value]) => ({
    label: prettify(label),
    value,
  })))
})

const recentAnnouncementRows = computed(() => (Array.isArray(resolvedGovernanceOverview.value?.recent_announcements)
  ? resolvedGovernanceOverview.value.recent_announcements
      .slice(0, 5)
      .map((item) => ({
        id: item.id,
        title: item.title || 'Untitled Announcement',
        meta: `${item.author_name || officerName.value || 'Governance'} • ${formatRelativeDate(item.updated_at)}`,
        badge: prettify(item.status),
      }))
  : []
))

const chartOptions = {
  bar: {
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          precision: 0,
        },
      },
    },
  },
  pie: {
    plugins: {
      legend: {
        position: 'bottom',
      },
    },
  },
}

watch(
  [() => props.preview, schoolSettings],
  ([preview, settings]) => {
    if (!preview || !settings) return
    applyTheme(loadTheme(settings))
  },
  { immediate: true }
)

watch(
  [() => props.preview, apiBaseUrl, token, activeUnitId],
  async ([preview, url, authToken, unitId]) => {
    if (preview) {
      governanceOverview.value = null
      overviewLoading.value = false
      overviewError.value = ''
      return
    }

    if (!url || !authToken || !unitId) return
    await loadGovernanceOverview(url, authToken, Number(unitId))
  },
  { immediate: true }
)

function handleModuleClick(mod) {
  const isPermitted = hasPermission(mod.permissionCode) || mod.id === 'view-students'

  if (!isPermitted) {
    showToast("You currently don't have permission to do this.")
    return
  }

  if (mod.route) {
    const target = props.preview
      ? withPreservedGovernancePreviewQuery(route, mod.route.replace(/^\/governance/, '/exposed/governance'))
      : mod.route
    router.push(target)
  }
}

function showToast(message) {
  if (toastTimer) clearTimeout(toastTimer)
  toastMessage.value = message
  toastVisible.value = true
  toastTimer = setTimeout(() => {
    toastVisible.value = false
  }, 3200)
}

async function loadGovernanceOverview(url, authToken, unitId) {
  overviewLoading.value = true
  overviewError.value = ''

  try {
    governanceOverview.value = await getGovernanceDashboardOverview(url, authToken, unitId)
  } catch (error) {
    governanceOverview.value = null
    overviewError.value = error?.message || 'Governance dashboard data is unavailable right now.'
  } finally {
    overviewLoading.value = false
  }
}

function buildPreviewGovernanceOverview(bundle = null) {
  const announcements = Array.isArray(bundle?.announcements) ? bundle.announcements : []
  const scopeOptions = Array.isArray(bundle?.createUnit?.scopeOptions) ? bundle.createUnit.scopeOptions.slice(0, 4) : []
  const childUnitType = bundle?.createUnit?.childType || 'ORG'

  return {
    governance_unit_id: bundle?.activeUnit?.id || null,
    unit_type: bundle?.activeUnit?.unit_type || null,
    published_announcement_count: announcements.filter((item) => String(item?.status || '').toLowerCase() === 'published').length,
    total_students: Array.isArray(bundle?.students) ? bundle.students.length : 0,
    recent_announcements: announcements.map((item) => ({
      id: item.id,
      title: item.title,
      status: item.status,
      author_name: officerName.value,
      updated_at: item.updated_at || item.created_at || null,
    })),
    child_units: scopeOptions.map((option, index) => ({
      id: index + 1,
      unit_code: `${childUnitType}-${index + 1}`,
      unit_name: option.label,
      description: null,
      unit_type: childUnitType,
      member_count: Math.max(4, 14 - (index * 2)),
    })),
  }
}

function prettify(value) {
  return String(value || '').replace(/_/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase())
}

function formatRelativeDate(value) {
  if (!value) return 'Unknown update'
  try {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    }).format(new Date(value))
  } catch {
    return String(value)
  }
}

// --- Chat & Panel Logic ---
const {
  messages,
  inputText,
  isTyping,
  scrollEl,
  sendMessage,
  closeAll,
} = useChat()

const nextFrame = (cb) => requestAnimationFrame(() => requestAnimationFrame(cb))

function onMobilePanelBeforeEnter(el) {
  el.style.height = '0px'
  el.style.opacity = '0'
  el.style.transform = 'translateY(-8px)'
  el.style.willChange = 'height, opacity, transform'
}

function onMobilePanelEnter(el) {
  const height = el.scrollHeight
  el.style.transition = 'height 520ms cubic-bezier(0.22, 1, 0.36, 1), opacity 320ms ease, transform 420ms cubic-bezier(0.22, 1, 0.36, 1)'
  nextFrame(() => {
    el.style.height = `${height}px`
    el.style.opacity = '1'
    el.style.transform = 'translateY(0)'
  })
}

function onMobilePanelAfterEnter(el) {
  el.style.height = 'auto'
  el.style.transition = ''
  el.style.willChange = ''
}

function onMobilePanelBeforeLeave(el) {
  el.style.height = `${el.scrollHeight}px`
  el.style.opacity = '1'
  el.style.transform = 'translateY(0)'
  el.style.willChange = 'height, opacity, transform'
}

function onMobilePanelLeave(el) {
  el.style.transition = 'height 420ms cubic-bezier(0.4, 0, 0.2, 1), opacity 240ms ease, transform 300ms ease'
  nextFrame(() => {
    el.style.height = '0px'
    el.style.opacity = '0'
    el.style.transform = 'translateY(-6px)'
  })
}

function onMobilePanelAfterLeave(el) {
  el.style.transition = ''
  el.style.height = ''
  el.style.opacity = ''
  el.style.transform = ''
  el.style.willChange = ''
}

function toggleMobileAi() {
  isMobileAiOpen.value = !isMobileAiOpen.value
}

watch(isMobileAiOpen, (open) => {
  if (open) {
    closeAll()
    nextTick(() => {
      setTimeout(() => mobileInputEl.value?.focus(), 220)
    })
  }
})

watch(searchActive, (active) => {
  if (active) isMobileAiOpen.value = false
})
</script>

<style scoped>
.sg-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 100vh;
  padding: 28px 22px 100px;
}

.sg-page-title {
  font-size: 26px;
  font-weight: 800;
  color: var(--color-text-primary);
}

/* ── Search row shell ─────────────────────────────────── */
.search-area {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.search-row {
  display: flex;
  align-items: stretch;
  gap: clamp(8px, 2.8vw, 10px);
}

.search-wrap {
  flex: 1;
  min-width: 0;
  transition: flex 0.3s ease;
}

.search-wrap--active {
  flex: 1 1 100%;
}

.ai-pill {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  flex-shrink: 0;
  width: clamp(70px, 21vw, 76px);
  height: clamp(50px, 14vw, 52px);
  border-radius: 26px;
  border: none;
  background: var(--color-search-pill-bg);
  color: var(--color-search-pill-text);
  cursor: pointer;
  transition: opacity 0.2s ease, transform 0.2s ease, box-shadow 0.25s ease;
}

.ai-pill:hover {
  filter: brightness(1.08);
  transform: scale(1.04);
}

.ai-pill:active {
  transform: scale(0.95);
}

.ai-pill--open {
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.14);
  transform: translateY(1px) scale(0.98);
}

/* ── Mobile AI panel ─────────────────────────────────── */
.mobile-ai-panel {
  overflow: hidden;
  transform-origin: top center;
}

.mobile-ai-panel-inner {
  overflow: hidden;
}

.mobile-ai-shell {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  background: var(--color-primary);
  border-radius: 28px;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.14);
  overflow: hidden;
}

.mobile-ai-shell::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(120% 120% at 18% 0%, rgba(255, 255, 255, 0.28), transparent 55%);
  opacity: 0.5;
  pointer-events: none;
}

.mobile-ai-messages {
  position: relative;
  flex: 1;
  min-height: clamp(110px, 22vh, 180px);
  max-height: min(46vh, 320px);
  overflow-y: auto;
  padding: 6px 6px 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  scrollbar-width: none;
  z-index: 1;
}

.mobile-ai-messages::-webkit-scrollbar {
  display: none;
}

.mobile-ai-messages-inner {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.mobile-bubble {
  max-width: 88%;
  padding: 12px 16px;
  border-radius: 24px;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.6;
  font-family: 'Manrope', sans-serif;
  word-break: break-word;
}

.mobile-bubble--ai {
  align-self: flex-start;
  background: #ffffff;
  color: #0a0a0a;
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.08);
}

.mobile-bubble--user {
  align-self: flex-end;
  background: rgba(0, 0, 0, 0.12);
  color: var(--color-banner-text);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.mobile-bubble--typing {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 16px;
}

.mobile-dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.35);
  animation: mobile-dot-bounce 1s infinite ease-in-out;
}

@keyframes mobile-dot-bounce {
  0%, 100% { transform: translateY(0); }
  40% { transform: translateY(-4px); }
}

.mobile-bubble-enter-active {
  animation: mobile-bubble-pop 0.45s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

.mobile-bubble--ai.mobile-bubble-enter-active { transform-origin: bottom left; }
.mobile-bubble--user.mobile-bubble-enter-active { transform-origin: bottom right; }

@keyframes mobile-bubble-pop {
  0%   { opacity: 0; transform: scale(0.55); }
  65%  { opacity: 1; transform: scale(1.04); }
  82%  { transform: scale(0.97); }
  100% { transform: scale(1); }
}

.mobile-ai-input {
  position: relative;
  z-index: 1;
}

.mobile-ai-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.08);
  border: 1.4px solid rgba(0, 0, 0, 0.2);
  border-radius: 999px;
  padding: 0 8px 0 16px;
  height: 44px;
  transition: border-color 0.2s ease, background 0.2s ease;
}

.mobile-ai-input-row:focus-within {
  background: rgba(0, 0, 0, 0.12);
  border-color: rgba(0, 0, 0, 0.35);
}

.mobile-ai-input-field {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--color-banner-text);
  min-width: 0;
}

.mobile-ai-input-field::placeholder {
  color: var(--color-banner-text);
  opacity: 0.55;
}

.mobile-ai-send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.18);
  color: var(--color-banner-text);
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.18s ease, transform 0.15s ease, opacity 0.18s ease;
}

.mobile-ai-send-btn:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.28);
  transform: scale(1.08);
}

.mobile-ai-send-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* ── Search shell card ────────────────────────────────── */
.search-shell {
  display: grid;
  grid-template-rows: auto 0fr;
  background: var(--color-surface);
  border-radius: 30px;
  padding: 12px clamp(12px, 4vw, 16px);
  box-shadow: 0 10px 26px rgba(0, 0, 0, 0.06);
  transition: grid-template-rows 0.28s ease, box-shadow 0.28s ease, border-radius 0.28s ease;
}

.search-shell--open {
  grid-template-rows: auto 1fr;
  border-radius: 28px;
  box-shadow: 0 12px 34px rgba(0, 0, 0, 0.09);
}

.search-input-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: clamp(8px, 2.5vw, 10px);
  min-height: clamp(30px, 8.5vw, 34px);
}

.search-input {
  width: 100%;
  min-width: 0;
  border: none;
  background: transparent;
  font-size: 13px;
  font-weight: 600;
  outline: none;
  color: var(--color-text-always-dark);
}

.search-input::placeholder {
  color: var(--color-text-muted);
  font-weight: 500;
}

.search-icon { display: block; }

.search-icon-wrap {
  width: clamp(28px, 8vw, 30px);
  height: clamp(28px, 8vw, 30px);
  border-radius: 50%;
  border: 1.5px solid rgba(0, 0, 0, 0.08);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  place-self: center;
}

/* ── Hero Banner ──────── */
.sg-hero {
  position: relative;
  border-radius: 28px;
  overflow: hidden;
  background: var(--color-primary);
  min-height: 160px;
  padding: 28px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.sg-hero-content {
  position: relative;
  z-index: 2;
  max-width: 65%;
}

.sg-hero-subtitle {
  font-size: 13px;
  font-weight: 500;
  opacity: 0.85;
  color: var(--color-banner-text);
}

.sg-hero-title {
  font-size: 32px;
  font-weight: 800;
  letter-spacing: -0.5px;
  line-height: 1.1;
  margin-top: 4px;
  color: var(--color-banner-text);
}

.sg-hero-officer {
  font-size: 13px;
  font-weight: 500;
  margin-top: 8px;
  opacity: 0.9;
  color: var(--color-banner-text);
}

.sg-hero-logo-wrap {
  position: absolute;
  right: -20px;
  top: 68%;
  transform: translateY(-50%);
  pointer-events: none;
  z-index: 1;
}

.sg-hero-logo {
  width: 155px;
  height: 155px;
  object-fit: contain;
  filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.12));
  opacity: 0.95;
}

.sg-hero-logo-fallback {
  position: absolute;
  right: -20px;
  top: 68%;
  transform: translateY(-50%);
  width: 140px;
  height: 140px;
  border-radius: 32px;
  background: rgba(255, 255, 255, 0.14);
  color: var(--color-banner-text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 800;
  letter-spacing: 0.08em;
  pointer-events: none;
  z-index: 1;
}

.sg-reports {
  display: grid;
  gap: 16px;
}

.sg-report-card {
  padding: 18px;
  border-radius: 24px;
  background: var(--color-surface);
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.05);
}

.sg-report-card--summary {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.sg-report-card--feed {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.sg-report-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.sg-report-kicker {
  margin: 0;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.sg-report-title {
  margin: 4px 0 0;
  font-size: 24px;
  line-height: 1.04;
  letter-spacing: -0.05em;
  color: var(--color-text-primary);
}

.sg-report-badge {
  min-height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 16%, white);
  color: var(--color-text-always-dark);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

.sg-report-note,
.sg-report-empty {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: var(--color-text-muted);
}

.sg-report-stats {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.sg-report-stat {
  padding: 14px;
  border-radius: 18px;
  background: var(--color-bg);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sg-report-stat span {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.sg-report-stat strong {
  font-size: 28px;
  line-height: 1;
  letter-spacing: -0.05em;
  color: var(--color-primary);
}

.sg-report-stat small {
  font-size: 12px;
  line-height: 1.45;
  color: var(--color-text-muted);
}

.sg-report-chart {
  min-height: 250px;
}

.sg-report-feed {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sg-report-feed-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px;
  border-radius: 18px;
  background: var(--color-bg);
}

.sg-report-feed-row h3 {
  margin: 0;
  font-size: 15px;
  color: var(--color-text-primary);
}

.sg-report-feed-row p {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--color-text-muted);
}

.sg-report-feed-badge {
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  background: var(--color-field-surface);
  color: var(--color-text-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}

/* ═══════════════════════════════════════════════════════
   ANTI-GRAVITY MODULE SECTIONS
   ═══════════════════════════════════════════════════════ */

.ag-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.ag-section-title {
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.01em;
  color: var(--color-text-primary);
  padding: 0 4px;
  opacity: 0.65;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

/* ── Anti-Gravity Module Row ──────────────────────────── */
.ag-modules-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ag-module-row {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
  padding: 20px 20px 20px 18px;
  background: var(--color-surface);
  border: none;
  border-radius: 24px;
  cursor: pointer;
  text-align: left;
  position: relative;
  box-shadow:
    0 2px 8px rgba(0, 0, 0, 0.04),
    0 8px 32px rgba(0, 0, 0, 0.03);
  transition:
    transform 0.28s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.28s cubic-bezier(0.22, 1, 0.36, 1);
  will-change: transform;
}

.ag-module-row:hover {
  transform: translateY(-3px);
  box-shadow:
    0 4px 12px rgba(0, 0, 0, 0.06),
    0 16px 48px rgba(0, 0, 0, 0.08);
}

.ag-module-row:active {
  transform: translateY(-1px) scale(0.995);
  box-shadow:
    0 2px 8px rgba(0, 0, 0, 0.05),
    0 8px 24px rgba(0, 0, 0, 0.05);
}

/* High prominence modules */
.ag-module-row--high {
  border-left: 3px solid var(--color-primary);
  padding-left: 15px;
}

/* Restricted / locked module */
.ag-module-row--restricted {
  background: var(--color-bg);
  opacity: 0.55;
  cursor: not-allowed;
  box-shadow:
    0 1px 4px rgba(0, 0, 0, 0.02),
    0 4px 16px rgba(0, 0, 0, 0.015);
}

.ag-module-row--restricted:hover {
  transform: none;
  box-shadow:
    0 1px 4px rgba(0, 0, 0, 0.02),
    0 4px 16px rgba(0, 0, 0, 0.015);
}

.ag-module-row--restricted:active {
  transform: scale(0.995);
}

/* ── Module Icon ──────────────────────────────────── */
.ag-module-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: var(--color-primary);
  color: var(--color-banner-text);
  flex-shrink: 0;
  transition: background 0.2s ease, opacity 0.2s ease;
}

.ag-module-icon--restricted {
  background: var(--color-surface-border);
  color: var(--color-surface-text-muted);
}

/* ── Module Text ──────────────────────────────────── */
.ag-module-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.ag-module-label {
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text-always-dark);
  line-height: 1.25;
}

.ag-module-desc {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-surface-text-muted);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── Module Action (arrow / lock) ─────────────────── */
.ag-module-action {
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

.ag-module-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--color-nav);
  color: var(--color-nav-text);
  transition: transform 0.2s ease;
}

.ag-module-row:not(.ag-module-row--restricted):hover .ag-module-arrow {
  transform: translateX(3px);
}

.ag-module-lock {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: transparent;
  color: var(--color-surface-text-muted);
  border: 1.5px dashed var(--color-surface-border);
}

/* ── State cards ──────────────────── */
.sg-state-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 40px 24px;
  border-radius: 24px;
  background: var(--color-surface);
  text-align: center;
}

.sg-state-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.sg-state-message {
  font-size: 13px;
  color: var(--color-text-muted);
  max-width: 280px;
  line-height: 1.5;
}

/* ── Toast ─────────────────────────── */
.sg-toast {
  position: fixed;
  bottom: 100px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 22px;
  border-radius: 20px;
  background: var(--color-nav);
  color: var(--color-nav-text);
  font-size: 13px;
  font-weight: 600;
  box-shadow:
    0 8px 24px rgba(0, 0, 0, 0.18),
    0 20px 60px rgba(0, 0, 0, 0.12);
  z-index: 9999;
  max-width: calc(100vw - 48px);
  cursor: pointer;
  backdrop-filter: blur(8px);
}

.sg-toast-enter-active {
  transition: opacity 0.3s ease, transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.sg-toast-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.sg-toast-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(24px) scale(0.9);
}

.sg-toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(10px) scale(0.95);
}

/* ── Dashboard enter animation ────── */
.dashboard-enter {
  opacity: 1;
  transform: translateY(0);
  animation: sg-fade-up 0.5s ease both;
}

.dashboard-enter--1 { animation-delay: 0ms; }
.dashboard-enter--2 { animation-delay: 60ms; }
.dashboard-enter--3 { animation-delay: 120ms; }
.dashboard-enter--4 { animation-delay: 180ms; }
.dashboard-enter--5 { animation-delay: 240ms; }
.dashboard-enter--6 { animation-delay: 300ms; }
.dashboard-enter--7 { animation-delay: 360ms; }
.dashboard-enter--8 { animation-delay: 420ms; }
.dashboard-enter--9 { animation-delay: 480ms; }
.dashboard-enter--10 { animation-delay: 540ms; }

@keyframes sg-fade-up {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .dashboard-enter {
    animation: none;
    opacity: 1;
    transform: none;
  }
}

@media (min-width: 768px) {
  .sg-page {
    padding: 36px 36px 40px;
  }

  .ai-pill,
  .mobile-ai-panel {
    display: none !important;
  }

  .sg-hero-logo-wrap { right: -24px; }
  .sg-hero-logo { width: 165px; height: 165px; }
  .sg-hero-logo-fallback { right: -24px; width: 165px; height: 165px; }

  .sg-reports {
    grid-template-columns: minmax(0, 1.05fr) minmax(260px, 0.95fr) minmax(260px, 0.95fr);
  }

  .sg-report-card--feed {
    grid-column: 1 / -1;
  }

  .ag-module-row {
    padding: 22px 24px 22px 20px;
    gap: 20px;
    border-radius: 28px;
  }

  .ag-module-label {
    font-size: 16px;
  }

  .ag-module-desc {
    font-size: 13px;
  }
}
</style>
