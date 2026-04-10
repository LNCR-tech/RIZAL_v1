<template>
  <div class="governance-workspace">
    <TopBar class="dashboard-enter dashboard-enter--1" :user="currentUser" :unread-count="0" />

    <div class="governance-top-row dashboard-enter dashboard-enter--2">
      <div class="search-wrap">
        <div class="search-shell" :class="{ 'search-shell--expanded': searchActive }">
          <div class="search-input-row">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search workspaces..."
              class="search-input"
            />
            <span class="search-icon-wrap" aria-hidden="true">
              <Search :size="14" class="search-icon" style="color: var(--color-primary);" />
            </span>
          </div>

          <div class="search-results-panel">
            <div class="search-results-inner">
              <div v-if="searchResults.length" class="search-results-list">
                <button
                  v-for="item in searchResults"
                  :key="item.id"
                  type="button"
                  class="search-result-item"
                  @click="handleSearchResultClick(item)"
                >
                  <div class="search-result-icon">
                    <component :is="item.icon" :size="16" :stroke-width="2" />
                  </div>
                  <div class="search-result-copy">
                    <strong>{{ item.label }}</strong>
                    <span>{{ item.sublabel }}</span>
                  </div>
                </button>
              </div>
              <div v-else class="search-results-empty">
                No results found for "{{ searchQuery }}"
              </div>
            </div>
          </div>
        </div>
      </div>

      <button
        type="button"
        class="governance-create-button"
        aria-label="Open governance create actions"
        @click="handleOpenCreateSheet"
      >
        <Plus :size="18" :stroke-width="2.1" />
        <span>Create</span>
      </button>
    </div>

    <section v-if="isWorkspaceLoading" class="governance-state-card dashboard-enter dashboard-enter--3">
      <LoaderCircle class="governance-state-card__spinner" :size="28" :stroke-width="2.2" />
      <p class="governance-state-card__title">Loading governance workspace</p>
      <p class="governance-state-card__copy">Syncing your unit data.</p>
    </section>

    <section
      v-else-if="workspaceError && !hasRenderableData"
      class="governance-state-card governance-state-card--error dashboard-enter dashboard-enter--3"
    >
      <AlertCircle :size="28" :stroke-width="2.1" />
      <p class="governance-state-card__title">Governance workspace unavailable</p>
      <p class="governance-state-card__copy">{{ workspaceError }}</p>
    </section>

    <template v-else>
      <template v-if="isOverviewSection">
        <template v-if="isSsgOverview">
          <section class="governance-summary-grid governance-summary-grid--ssg dashboard-enter dashboard-enter--3">
            <article
              v-for="card in ssgSummaryCards"
              :key="card.key"
              class="governance-card governance-card--stat governance-card--spotlight governance-card--stat-showcase"
              :class="[
                `governance-card--stat-showcase-${card.tone}`,
                card.position ? `governance-card--stat-showcase-${card.position}` : '',
              ]"
            >
              <div class="governance-stat-showcase__top">
                <div class="governance-stat-showcase__eyebrow">
                  <div class="governance-stat-showcase__icon">
                    <component :is="card.icon" :size="18" :stroke-width="2" />
                  </div>
                  <span>{{ card.label }}</span>
                </div>
              </div>

              <div class="governance-stat-showcase__copy">
                <strong>{{ card.value }}</strong>
              </div>
            </article>
          </section>

          <section class="governance-analytics-shell dashboard-enter dashboard-enter--4">
            <div class="governance-analytics-shell__header">
              <h2 class="governance-analytics-shell__title">Event Analytics</h2>

              <label
                v-if="analyticsEventOptions.length"
                class="governance-analytics-picker"
              >
                <span class="governance-event-select governance-event-select--primary">
                  <select
                    class="governance-event-select__input"
                    :value="selectedAnalyticsEventId || ''"
                    @change="setSelectedAnalyticsEventId($event.target.value)"
                  >
                    <option
                      v-for="option in analyticsEventOptions"
                      :key="option.value"
                      :value="option.value"
                    >
                      {{ option.label }}
                    </option>
                  </select>
                  <ChevronDown :size="16" :stroke-width="2" />
                </span>
              </label>
            </div>

            <div class="governance-analytics-stack">
              <article class="governance-card governance-card--health governance-card--health-showcase">
                <div class="governance-health-card__header">
                  <div class="governance-health-card__header-copy">
                    <p class="governance-health-card__label">Event Health</p>
                    <h2 class="governance-health-card__title">{{ eventHealthInsight.title }}</h2>
                  </div>

                  <div ref="reportMenuRef" class="governance-health-card__menu-wrap">
                    <button
                      type="button"
                      class="governance-health-card__menu"
                      :aria-expanded="isReportMenuOpen ? 'true' : 'false'"
                      aria-label="Open report actions"
                      @click="toggleReportMenu"
                    >
                      <MoreHorizontal :size="18" :stroke-width="2.2" />
                    </button>

                    <div v-if="isReportMenuOpen" class="governance-report-popover">
                      <button
                        type="button"
                        class="governance-report-popover__action governance-report-popover__action--primary"
                        :disabled="!canExportPar || isExportingPar"
                        @click="handleExportPar"
                      >
                        <FileText :size="16" :stroke-width="2" />
                        <span>{{ isExportingPar ? 'Preparing PAR...' : 'Export PAR' }}</span>
                      </button>

                      <button
                        type="button"
                        class="governance-report-popover__action"
                        :disabled="!canExportMasterlist || isExportingMasterlist"
                        @click="handleExportMasterlist"
                      >
                        <FileSpreadsheet :size="16" :stroke-width="2" />
                        <span>{{ isExportingMasterlist ? 'Preparing CSV...' : 'Export CSV' }}</span>
                      </button>
                    </div>
                  </div>
                </div>

                <div class="governance-health-card__meta">
                  <span class="governance-health__state">
                    <span class="governance-health__state-dot" />
                    {{ eventHealthInsight.statusLabel }}
                  </span>
                  <span>{{ eventHealthInsight.eventDateLabel }}</span>
                </div>

                <div
                  class="governance-health-arc"
                  :aria-label="`${eventHealthInsight.title}: ${eventHealthInsight.valueLabel} capacity`"
                  role="img"
                >
                  <div class="governance-health-arc__badge">
                    <span class="governance-health-arc__badge-dot" />
                    <strong>{{ eventHealthInsight.secondaryValueLabel }}</strong>
                    <span>{{ eventHealthInsight.secondaryLabel }}</span>
                  </div>

                  <span
                    v-for="segment in eventHealthGaugeSegments"
                    :key="segment.key"
                    class="governance-health-arc__segment"
                    :class="{ 'is-active': segment.active }"
                    :style="segment.style"
                  />

                  <div class="governance-health-arc__center">
                    <strong class="governance-health-arc__value">{{ eventHealthInsight.valueLabel }}</strong>
                    <span class="governance-health-arc__caption">Capacity</span>
                  </div>
                </div>

                <div class="governance-health-card__tiles">
                  <article class="governance-health-card__tile">
                    <span>Attended</span>
                    <strong>{{ eventHealthInsight.attendedLabel }}</strong>
                  </article>

                  <article class="governance-health-card__tile">
                    <span>Target</span>
                    <strong>{{ eventHealthInsight.totalLabel }}</strong>
                  </article>
                </div>

                <p v-if="exportError" class="governance-report-error governance-report-error--inline">{{ exportError }}</p>
              </article>

              <article class="governance-card governance-card--chart">
                <GovernanceBreakdownBars
                  v-if="demographicInsight.items.length"
                  :title="demographicInsight.title"
                  :items="demographicInsight.items"
                />
                <article v-else class="governance-empty-card governance-empty-card--subtle">
                  <BarChart3 :size="18" :stroke-width="2" />
                  <div>
                    <strong>Waiting for richer attendance rows.</strong>
                  </div>
                </article>
              </article>

              <article class="governance-card governance-card--chart governance-card--arrival">
                <div class="governance-card__header governance-card__header--compact">
                  <div>
                    <h2 class="governance-card__title">Peak Arrival Time</h2>
                  </div>
                </div>

                <GovernanceArrivalBars
                  v-if="arrivalInsight.items.length"
                  :insight="arrivalInsight"
                />
                <article v-else class="governance-empty-card governance-empty-card--subtle">
                  <Clock3 :size="18" :stroke-width="2" />
                  <div>
                    <strong>No sign-in timestamps yet.</strong>
                  </div>
                </article>
              </article>
            </div>
          </section>

          <section class="governance-analytics-shell dashboard-enter dashboard-enter--5">
            <article class="governance-card governance-card--chart governance-card--timeline">
              <div class="governance-card__header">
                <div>
                  <p class="governance-card__eyebrow">Semester Arc</p>
                  <h2 class="governance-card__title">Engagement Over Time</h2>
                </div>
              </div>

              <GovernanceTrendChart
                v-if="engagementTimeline.points.length > 1"
                :points="engagementTimeline.points"
              />
              <article v-else class="governance-empty-card governance-empty-card--subtle">
                <TrendingUp :size="18" :stroke-width="2" />
                <div>
                  <strong>More reported events are needed for a trend line.</strong>
                </div>
              </article>
            </article>
          </section>

        </template>

        <section v-else class="governance-summary-grid dashboard-enter dashboard-enter--3">
          <article class="governance-card governance-card--engagement">
            <div class="governance-card__header">
              <div>
                <p class="governance-card__eyebrow">Analytics</p>
                <h2 class="governance-card__title">Engagement</h2>
              </div>
              <span v-if="reportsLoading" class="governance-card__status">Refreshing</span>
            </div>

            <div class="governance-card__engagement-body">
              <GovernanceProgressRing :percentage="engagementMetric.percentage">
                <strong class="governance-progress-copy__value">{{ engagementMetric.valueLabel }}</strong>
                <span class="governance-progress-copy__label">{{ engagementMetric.centerLabel }}</span>
              </GovernanceProgressRing>
            </div>
          </article>

          <article class="governance-card governance-card--stat">
            <div class="governance-stat-card__icon">
              <UsersRound :size="18" :stroke-width="2" />
            </div>
            <div class="governance-stat-card__copy">
              <strong>{{ activeStudentsMetric.valueLabel }}</strong>
              <p>Students in scope</p>
            </div>
          </article>

          <article class="governance-card governance-card--stat">
            <div class="governance-stat-card__icon">
              <CalendarDays :size="18" :stroke-width="2" />
            </div>
            <div class="governance-stat-card__copy">
              <strong>{{ eventVolumeMetric.valueLabel }}</strong>
              <p>Events this week</p>
            </div>
          </article>

          <article class="governance-card governance-card--stat">
            <div class="governance-stat-card__icon">
              <BellRing :size="18" :stroke-width="2" />
            </div>
            <div class="governance-stat-card__copy">
              <strong>{{ latestAnnouncementReachMetric.valueLabel }}</strong>
              <p>Announcement reach</p>
            </div>
          </article>
        </section>

        <section class="governance-zone dashboard-enter" :class="isSsgOverview ? 'dashboard-enter--7' : 'dashboard-enter--4'">
          <div class="governance-zone__header">
            <div>
              <p class="governance-zone__eyebrow">Needs Attention</p>
              <h2 class="governance-zone__title">Actionable follow-ups</h2>
            </div>
          </div>

          <div v-if="attentionItems.length" class="governance-attention-list">
            <button
              v-for="item in attentionItems"
              :key="item.key"
              type="button"
              class="governance-attention-card"
              :class="`governance-attention-card--${item.tone}`"
              @click="openAttentionItem(item)"
            >
              <div class="governance-attention-card__icon">
                <CircleAlert :size="18" :stroke-width="2.1" />
              </div>

              <div class="governance-attention-card__copy">
                <span class="governance-attention-card__eyebrow">{{ item.eyebrow }}</span>
                <strong>{{ item.title }}</strong>
              </div>

              <span class="governance-attention-card__action">{{ item.actionLabel }}</span>
            </button>
          </div>
          <article v-else class="governance-empty-card">
            <ShieldCheck :size="20" :stroke-width="2" />
            <div>
              <strong>Nothing urgent right now.</strong>
            </div>
          </article>
        </section>

        <section class="governance-zone dashboard-enter" :class="isSsgOverview ? 'dashboard-enter--8' : 'dashboard-enter--5'">
          <div class="governance-zone__header">
            <div>
              <p class="governance-zone__eyebrow">Up Next</p>
              <h2 class="governance-zone__title">Upcoming events</h2>
            </div>

            <button type="button" class="governance-inline-action" @click="openSection('events')">
              Open Events
              <ArrowRight :size="16" :stroke-width="2" />
            </button>
          </div>

          <div v-if="upcomingEvents.length" class="governance-event-carousel">
            <article
              v-for="event in upcomingEvents"
              :key="event.id"
              class="governance-event-card"
              :class="`governance-event-card--${getUpcomingEventTone(event)}`"
            >
              <div class="governance-event-card__top">
                <span class="governance-event-card__status">
                  {{ getUpcomingEventTone(event) === 'live' ? 'Live now' : getStatusLabel(event.status) }}
                </span>
                <span class="governance-event-card__scope">{{ event.scope_label || activeUnitName }}</span>
              </div>

              <strong class="governance-event-card__title">{{ event.name || 'Untitled event' }}</strong>
              <p class="governance-event-card__line">{{ event.location || 'Location pending' }}</p>

              <div class="governance-event-card__footer">
                <span class="governance-event-card__time">
                  <Clock3 :size="14" :stroke-width="2" />
                  {{ formatDateRange(event.start_datetime || event.start_time, event.end_datetime || event.end_time) }}
                </span>

                <button type="button" class="governance-event-card__button" @click.stop="openEvent(event)">
                  {{ getUpcomingEventActionLabel(event) }}
                </button>
              </div>
            </article>
          </div>
          <article v-else class="governance-empty-card">
            <CalendarDays :size="20" :stroke-width="2" />
            <div>
              <strong>No upcoming events.</strong>
            </div>
          </article>
        </section>

        <section class="governance-zone governance-zone--feed dashboard-enter" :class="isSsgOverview ? 'dashboard-enter--9' : 'dashboard-enter--6'">
          <div class="governance-zone__header">
            <div>
              <p class="governance-zone__eyebrow">Recent Announcements</p>
              <h2 class="governance-zone__title">Latest governance updates</h2>
            </div>
          </div>

          <div v-if="recentAnnouncements.length" class="governance-feed-list">
            <article
              v-for="announcement in recentAnnouncements"
              :key="announcement.id"
              class="governance-feed-card"
            >
              <div class="governance-feed-card__top">
                <div class="governance-feed-card__headline">
                  <strong>{{ announcement.title || 'Untitled announcement' }}</strong>
                  <span>{{ formatAnnouncementTime(announcement.created_at || announcement.updated_at) }}</span>
                </div>
                <span class="governance-feed-card__status">{{ getStatusLabel(announcement.status) }}</span>
              </div>

              <div class="governance-feed-card__meta">
                <span>{{ formatAnnouncementAudienceMeta(announcement) }}</span>
              </div>
            </article>
          </div>
          <article v-else class="governance-empty-card">
            <Megaphone :size="20" :stroke-width="2" />
            <div>
              <strong>No announcements yet.</strong>
            </div>
          </article>
        </section>
      </template>

      <section v-else class="governance-section-grid dashboard-enter dashboard-enter--3">
        <article class="governance-panel governance-panel--primary">
          <div class="governance-panel__header">
            <p class="governance-panel__eyebrow">Temporary View</p>
            <h2 class="governance-panel__title">{{ currentSection.placeholderTitle }}</h2>
          </div>

          <div class="governance-placeholder-list">
            <p
              v-for="feature in currentSection.featureList"
              :key="feature"
              class="governance-placeholder-list__item"
            >
              {{ feature }}
            </p>
          </div>
        </article>

        <article class="governance-panel">
          <template v-if="currentSection.key === 'events'">
            <div class="governance-panel__header">
              <p class="governance-panel__eyebrow">Event Snapshot</p>
              <h2 class="governance-panel__title">Scoped events</h2>
            </div>

            <div v-if="events.length" class="governance-list">
              <button
                v-for="event in upcomingEvents"
                :key="event.id"
                type="button"
                class="governance-list__item"
                @click="openEvent(event)"
              >
                <div class="governance-list__copy">
                  <strong>{{ event.name || 'Untitled event' }}</strong>
                  <span>{{ formatEventLine(event) }}</span>
                </div>
                <ArrowRight :size="16" :stroke-width="2" />
              </button>
            </div>
            <p v-else class="governance-panel__empty">No governance events are visible for this unit yet.</p>
          </template>

          <template v-else-if="currentSection.key === 'students'">
            <div class="governance-panel__header">
              <p class="governance-panel__eyebrow">Directory Snapshot</p>
              <h2 class="governance-panel__title">Students in scope</h2>
            </div>

            <div v-if="studentsPreview.length" class="governance-list">
              <article
                v-for="student in studentsPreview"
                :key="student.id || student.user_id || student.user?.id"
                class="governance-list__item governance-list__item--static"
              >
                <div class="governance-list__copy">
                  <strong>{{ formatStudentName(student) }}</strong>
                  <span>{{ formatStudentMeta(student) }}</span>
                </div>
              </article>
            </div>
            <p v-else class="governance-panel__empty">No students are currently exposed in this governance scope.</p>
          </template>

          <template v-else>
            <div class="governance-panel__header">
              <p class="governance-panel__eyebrow">Governance Scope</p>
              <h2 class="governance-panel__title">Active unit details</h2>
            </div>

            <div class="governance-detail-grid">
              <div class="governance-detail-card">
                <span>Unit type</span>
                <strong>{{ activeUnitType || 'Governance' }}</strong>
              </div>
              <div class="governance-detail-card">
                <span>Members</span>
                <strong>{{ formatWholeNumber(membersCount) }}</strong>
              </div>
              <div class="governance-detail-card">
                <span>Permissions</span>
                <strong>{{ formatWholeNumber(permissionCodes.length) }}</strong>
              </div>
              <div class="governance-detail-card">
                <span>Announcements</span>
                <strong>{{ formatWholeNumber(announcements.length) }}</strong>
              </div>
            </div>

            <div v-if="permissionBadgeList.length" class="governance-chip-list">
              <span v-for="permission in permissionBadgeList" :key="permission" class="governance-chip">
                {{ permission }}
              </span>
            </div>
          </template>
        </article>
      </section>
    </template>

    <GovernanceCreateSheet
      :open="isCreateSheetOpen"
      :actions="createActions"
      @close="closeCreateSheet"
      @select="handleCreateAction"
    />

    <Transition name="governance-permission-alert">
      <div
        v-if="isPermissionAlertOpen"
        class="governance-permission-alert__backdrop"
        @click.self="closePermissionAlert"
      >
        <section
          class="governance-permission-alert"
          role="dialog"
          aria-modal="true"
          aria-labelledby="governance-permission-alert-title"
        >
          <div class="governance-permission-alert__icon">
            <AlertCircle :size="20" :stroke-width="2.2" />
          </div>

          <div class="governance-permission-alert__copy">
            <p class="governance-permission-alert__eyebrow">Permission Required</p>
            <h2 id="governance-permission-alert-title" class="governance-permission-alert__title">
              You currently do not have permission for this workspace.
            </h2>
            <p class="governance-permission-alert__description">
              Your account is inside {{ activeUnitName }}, but the backend has not returned any governance
              permission codes yet. Ask your unit administrator to assign access before using management actions.
            </p>
          </div>

          <button
            type="button"
            class="governance-permission-alert__button"
            @click="closePermissionAlert"
          >
            Got it
          </button>
        </section>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  AlertCircle,
  ArrowRight,
  BarChart3,
  BellRing,
  Building2,
  CalendarDays,
  ChevronDown,
  CircleAlert,
  Clock3,
  MoreHorizontal,
  FileSpreadsheet,
  FileText,
  GraduationCap,
  LoaderCircle,
  Megaphone,
  Plus,
  ShieldCheck,
  TrendingUp,
  UsersRound,
  Search,
} from 'lucide-vue-next'
import TopBar from '@/components/dashboard/TopBar.vue'
import GovernanceArrivalBars from '@/components/governance/GovernanceArrivalBars.vue'
import GovernanceBreakdownBars from '@/components/governance/GovernanceBreakdownBars.vue'
import GovernanceCreateSheet from '@/components/governance/GovernanceCreateSheet.vue'
import GovernanceProgressRing from '@/components/governance/GovernanceProgressRing.vue'
import GovernanceTrendChart from '@/components/governance/GovernanceTrendChart.vue'
import { applyTheme, loadTheme } from '@/config/theme.js'
import { useGovernanceWorkspace } from '@/composables/useGovernanceWorkspace.js'

const props = defineProps({
  preview: { type: Boolean, default: false },
  section: { type: String, default: 'overview' },
})

const searchQuery = ref('')

const {
  currentUser,
  schoolSettings,
  permissionCodes,
  acronym,
  activeUnitType,
  activeUnitName,
  workspaceEyebrow,
  officerMeta,
  headerTitle,
  headerDescription,
  membersCount,
  studentsPreview,
  events,
  upcomingEvents,
  announcements,
  recentAnnouncements,
  permissionBadgeList,
  currentSection,
  isOverviewSection,
  hasRenderableData,
  isWorkspaceLoading,
  workspaceError,
  reportsLoading,
  engagementMetric,
  eventHealthInsight,
  demographicInsight,
  engagementTimeline,
  arrivalInsight,
  analyticsEventOptions,
  selectedAnalyticsEventId,
  activeStudentsMetric,
  totalStudentsMetric,
  eventVolumeMetric,
  latestAnnouncementReachMetric,
  attentionItems,
  exportError,
  isExportingPar,
  isExportingMasterlist,
  analyticsFocusEntry,
  canExportPar,
  canExportMasterlist,
  isCreateSheetOpen,
  hasPermission,
  openSection,
  openEvent,
  openAttentionItem,
  openCreateSheet,
  closeCreateSheet,
  handleCreateAction,
  setSelectedAnalyticsEventId,
  exportPostActivityReport,
  exportMasterlist,
  getUpcomingEventActionLabel,
  getUpcomingEventTone,
  formatStudentName,
  formatStudentMeta,
  formatEventLine,
  formatDateRange,
  formatAnnouncementTime,
  formatWholeNumber,
  getStatusLabel,
} = useGovernanceWorkspace({
  preview: props.preview,
  section: () => props.section,
})

const searchActive = computed(() => searchQuery.value.trim().length > 0)
const hasGovernancePermissionCodes = computed(() => permissionCodes.value.length > 0)
const isPermissionAlertOpen = ref(false)
const hasShownPermissionAlert = ref(false)

const searchResults = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return []

  const results = []

  studentsPreview.value.forEach(student => {
    const name = formatStudentName(student)
    const meta = formatStudentMeta(student)
    if (name.toLowerCase().includes(query) || meta.toLowerCase().includes(query)) {
      results.push({
        id: `student-${student.id || student.user_id}`,
        type: 'student',
        label: name,
        sublabel: meta,
        icon: UsersRound,
        data: student
      })
    }
  })

  events.value.forEach(event => {
    const name = event.name || 'Untitled event'
    const loc = event.location || ''
    if (name.toLowerCase().includes(query) || loc.toLowerCase().includes(query)) {
      results.push({
        id: `event-${event.id}`,
        type: 'event',
        label: name,
        sublabel: formatEventLine(event),
        icon: CalendarDays,
        data: event
      })
    }
  })

  announcements.value.forEach(ann => {
    const title = ann.title || 'Untitled announcement'
    if (title.toLowerCase().includes(query)) {
      results.push({
        id: `ann-${ann.id}`,
        type: 'announcement',
        label: title,
        sublabel: formatAnnouncementTime(ann.created_at || ann.updated_at),
        icon: BellRing,
        data: ann
      })
    }
  })

  return results.slice(0, 6)
})

function handleSearchResultClick(item) {
  if (item.type === 'event') {
    openEvent(item.data)
  } else if (item.type === 'student') {
    openSection('students')
  } else if (item.type === 'announcement') {
    openSection('events')
  }
  searchQuery.value = ''
}

function closePermissionAlert() {
  isPermissionAlertOpen.value = false
}

function handleOpenCreateSheet() {
  if (isWorkspaceLoading.value) return

  if (!activeUnitType.value) {
    openCreateSheet()
    return
  }

  if (!hasGovernancePermissionCodes.value) {
    isPermissionAlertOpen.value = true
    hasShownPermissionAlert.value = true
    return
  }

  openCreateSheet()
}

watch(
  [() => props.preview, schoolSettings],
  ([preview, nextSchoolSettings]) => {
    if (!preview || !nextSchoolSettings) return
    applyTheme(loadTheme(nextSchoolSettings))
  },
  { immediate: true }
)

watch(selectedAnalyticsEventId, () => {
  closeReportMenu()
})

watch(
  [isWorkspaceLoading, workspaceError, activeUnitType, permissionCodes],
  ([loading, error, unitType, nextPermissionCodes]) => {
    const nextCodes = Array.isArray(nextPermissionCodes) ? nextPermissionCodes : []
    const shouldShowAlert = !loading && !error && Boolean(unitType) && nextCodes.length === 0

    if (shouldShowAlert && !hasShownPermissionAlert.value) {
      isPermissionAlertOpen.value = true
      hasShownPermissionAlert.value = true
      return
    }

    if (!shouldShowAlert) {
      isPermissionAlertOpen.value = false
      hasShownPermissionAlert.value = false
    }
  },
  { immediate: true }
)

const isSsgOverview = computed(() => isOverviewSection.value && activeUnitType.value === 'SSG')
const isReportMenuOpen = ref(false)
const reportMenuRef = ref(null)
const ssgSummaryCards = computed(() => [
  {
    key: 'total-students',
    label: 'Total Students',
    value: totalStudentsMetric.value.valueLabel,
    icon: GraduationCap,
    tone: 'accent',
    position: 'top-left',
  },
  {
    key: 'students-in-scope',
    label: 'Managed Students',
    value: activeStudentsMetric.value.valueLabel,
    icon: UsersRound,
    tone: 'surface',
    position: 'top-right',
  },
  {
    key: 'events-this-week',
    label: 'Events This Week',
    value: eventVolumeMetric.value.valueLabel,
    icon: CalendarDays,
    tone: 'surface',
    position: 'bottom-left',
  },
  {
    key: 'announcement-reach',
    label: 'Announcement Reach',
    value: latestAnnouncementReachMetric.value.valueLabel,
    icon: BellRing,
    tone: 'accent',
    position: 'bottom-right',
  },
])

const eventHealthGaugeSegments = computed(() => {
  const segmentCount = 15
  const percentage = Number(eventHealthInsight.value?.percentage || 0)
  const activeCount = Math.max(0, Math.min(segmentCount, Math.round((percentage / 100) * segmentCount)))
  const startAngle = 200
  const endAngle = 340
  const radius = 102
  const centerX = 126
  const centerY = 132

  return Array.from({ length: segmentCount }, (_, index) => {
    const ratio = segmentCount > 1 ? index / (segmentCount - 1) : 0
    const angle = startAngle + ((endAngle - startAngle) * ratio)
    const radians = (angle * Math.PI) / 180
    const x = centerX + (Math.cos(radians) * radius)
    const y = centerY + (Math.sin(radians) * radius)

    return {
      key: `event-health-segment-${index}`,
      active: index < activeCount,
      style: {
        left: `${x}px`,
        top: `${y}px`,
        transform: `translate(-50%, -50%) rotate(${angle + 90}deg)`,
        opacity: index < activeCount
          ? `${Math.max(0.45, 1 - (ratio * 0.42))}`
          : '1',
      },
    }
  })
})

function closeReportMenu() {
  isReportMenuOpen.value = false
}

function toggleReportMenu() {
  isReportMenuOpen.value = !isReportMenuOpen.value
}

function handleDocumentPointerDown(event) {
  const menuElement = reportMenuRef.value
  if (!menuElement || menuElement.contains(event.target)) return
  closeReportMenu()
}

function handleExportPar() {
  closeReportMenu()
  exportPostActivityReport()
}

function handleExportMasterlist() {
  closeReportMenu()
  exportMasterlist()
}

onMounted(() => {
  document.addEventListener('pointerdown', handleDocumentPointerDown)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown)
})

const createActions = computed(() => [
  {
    key: 'event',
    label: 'Event',
    description: 'Create and publish a governance-scoped event with attendance controls.',
    icon: CalendarDays,
    sectionKey: 'events',
    disabled: !hasPermission('manage_events'),
    disabledReason: 'Needs event permission',
  },
  {
    key: 'announcement',
    label: 'Announcement',
    description: 'Write a new governance update and manage its audience reach.',
    icon: Megaphone,
    sectionKey: 'events',
    disabled: !hasPermission('manage_announcements'),
    disabledReason: 'Needs announcement permission',
  },
  hasPermission('create_sg')
    ? {
      key: 'college-council',
      label: 'College Council',
      description: 'Create an SG and assign it to a department under your SSG.',
      icon: Building2,
      route: props.preview ? '/exposed/governance/create-unit' : '/governance/create-unit',
      disabled: false,
    }
    : null,
  hasPermission('create_org')
    ? {
      key: 'organization',
      label: 'Organization',
      description: 'Create an ORG inside your SG department and prepare its roster.',
      icon: GraduationCap,
      route: props.preview ? '/exposed/governance/create-unit' : '/governance/create-unit',
      disabled: false,
    }
    : null,
].filter(Boolean))

function formatAnnouncementAudienceMeta(announcement) {
  const seenCount = Number(
    announcement?.seen_count
    ?? announcement?.seen_students
    ?? announcement?.view_count
    ?? announcement?.read_count
  )
  const audienceCount = Number(
    announcement?.audience_count
    ?? announcement?.target_count
    ?? announcement?.recipient_count
    ?? announcement?.total_recipients
  )

  if (Number.isFinite(seenCount) && Number.isFinite(audienceCount) && audienceCount > 0) {
    return `Seen by ${formatWholeNumber(seenCount)} of ${formatWholeNumber(audienceCount)} students.`
  }
  if (Number.isFinite(seenCount)) {
    return `Seen by ${formatWholeNumber(seenCount)} students.`
  }
  return 'Reach analytics will appear here when the backend provides them.'
}
</script>

<style scoped>
.governance-workspace {
  --governance-shadow-soft: 0 18px 48px color-mix(in srgb, var(--color-nav) 8%, transparent);
  --governance-shadow-soft-compact: 0 10px 26px color-mix(in srgb, var(--color-nav) 8%, transparent);
  --governance-shadow-strong: 0 18px 48px color-mix(in srgb, var(--color-nav) 14%, transparent);
  --governance-shadow-float: 0 12px 24px color-mix(in srgb, var(--color-nav) 10%, transparent);
  --governance-shadow-popover: 0 18px 44px color-mix(in srgb, var(--color-nav) 14%, transparent);
  --governance-surface-edge: color-mix(in srgb, var(--color-surface) 74%, transparent);
  --governance-surface-edge-strong: color-mix(in srgb, var(--color-surface) 82%, transparent);
  --governance-accent-soft: color-mix(in srgb, var(--color-secondary) 76%, white);
  --governance-warning: var(--color-status-at-risk);
  --governance-warning-bg: color-mix(in srgb, var(--color-status-at-risk) 14%, transparent);
  --governance-danger: var(--color-status-non-compliant);
  --governance-danger-bg: color-mix(in srgb, var(--color-status-non-compliant) 12%, transparent);
  min-height: 100vh;
  padding: 28px 22px 116px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  font-family: 'Manrope', sans-serif;
}

.governance-state-card,
.governance-card,
.governance-zone,
.governance-panel,
.governance-empty-card {
  border-radius: 30px;
  background: color-mix(in srgb, var(--color-bg) 46%, var(--color-surface));
  box-shadow: var(--governance-shadow-soft);
}

.governance-header__copy {
  gap: 8px;
}

.governance-header__eyebrow,
.governance-card__eyebrow,
.governance-zone__eyebrow,
.governance-panel__eyebrow,
.governance-attention-card__eyebrow {
  margin: 0;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-primary);
}

.governance-header__title,
.governance-zone__title,
.governance-panel__title,
.governance-state-card__title,
.governance-card__title {
  margin: 0;
  font-size: 26px;
  line-height: 1;
  letter-spacing: -0.05em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-header__description,
.governance-zone__copy,
.governance-panel__copy,
.governance-state-card__copy,
.governance-card__copy,
.governance-feed-card__body,
.governance-empty-card p,
.governance-placeholder-list__item,
.governance-list__copy span,
.governance-panel__empty {
  margin: 0;
  font-size: 14px;
  line-height: 1.65;
  color: var(--color-text-muted);
}

.governance-header__actions {
  gap: 12px;
}

.governance-context-card {
  gap: 6px;
  padding: 18px 20px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--color-primary) 18%, transparent), transparent 48%),
    color-mix(in srgb, var(--color-bg) 58%, var(--color-surface));
}

.governance-context-card__acronym {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--color-primary);
}

.governance-context-card__title {
  font-size: 16px;
  line-height: 1.3;
  color: var(--color-text-primary);
}

.governance-context-card__meta {
  font-size: 13px;
  color: var(--color-text-muted);
}

.governance-create-button,
.governance-inline-action,
.governance-event-card__button {
  border: none;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
}

.governance-create-button {
  align-self: center;
  padding: 0 18px;
  height: clamp(52px, 14vw, 56px);
  background: var(--color-primary);
  color: var(--color-banner-text);
  flex-shrink: 0;
  border-radius: 30px;
}

.governance-top-row {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  gap: clamp(8px, 2.8vw, 10px);
  position: relative;
  z-index: 200;
}

.search-wrap {
  flex: 1;
  min-width: 0;
  position: relative;
  z-index: 100;
}

.search-shell {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  display: grid;
  grid-template-rows: auto 0fr;
  background: var(--color-surface);
  border-radius: 30px;
  padding: 12px clamp(12px, 4vw, 16px);
  box-shadow: var(--governance-shadow-soft-compact);
  min-height: 100%;
  transition: grid-template-rows 0.28s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.28s ease, border-radius 0.28s ease;
}

.search-shell--expanded {
  grid-template-rows: auto 1fr;
  border-radius: 28px;
  box-shadow: var(--governance-shadow-strong);
}

.search-input-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: clamp(8px, 2.5vw, 10px);
}

.search-results-panel {
  overflow: hidden;
}

.search-results-inner {
  padding-top: 14px;
}

.search-results-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: clamp(240px, 40vh, 360px);
  overflow-y: auto;
  scrollbar-width: thin;
}

.search-result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 16px;
  border: none;
  background: transparent;
  color: var(--color-text-primary);
  cursor: pointer;
  text-align: left;
  transition: background 0.15s ease;
}

.search-result-item:hover,
.search-result-item:focus {
  background: color-mix(in srgb, var(--color-bg) 50%, var(--color-surface));
  outline: none;
}

.search-result-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--color-primary) 12%, transparent);
  color: var(--color-primary);
  flex-shrink: 0;
}

.search-result-copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.search-result-copy strong {
  font-size: 14px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.search-result-copy span {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.search-results-empty {
  padding: 20px 0 10px;
  text-align: center;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-muted);
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

.search-icon-wrap {
  width: clamp(28px, 8vw, 30px);
  height: clamp(28px, 8vw, 30px);
  border-radius: 50%;
  border: 1.5px solid var(--color-surface-border);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  place-self: center;
}

.governance-state-card {
  padding: 28px;
  align-items: center;
  text-align: center;
  gap: 10px;
}

.governance-state-card--error {
  color: var(--governance-danger);
}

.governance-state-card__spinner {
  color: var(--color-primary);
  animation: governance-spin 1s linear infinite;
}

.governance-summary-grid {
  display: grid;
  gap: 14px;
}

.governance-summary-grid--ssg {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.governance-analytics-shell,
.governance-analytics-grid,
.governance-analytics-stack,
.governance-health__copy,
.governance-health__metrics {
  display: grid;
  gap: 14px;
}

.governance-analytics-shell__header {
  display: grid;
  gap: 10px;
  padding-inline: 4px;
}

.governance-analytics-shell__title {
  margin: 0;
  font-size: 18px;
  line-height: 1;
  letter-spacing: -0.04em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-analytics-picker {
  display: grid;
}

.governance-card {
  padding: 18px;
  gap: 14px;
}

.governance-card--health,
.governance-card--chart {
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--color-primary) 16%, transparent), transparent 45%),
    color-mix(in srgb, var(--color-bg) 46%, var(--color-surface));
}

.governance-card--health-showcase {
  gap: 16px;
  background:
    radial-gradient(circle at 22% 14%, color-mix(in srgb, var(--color-primary) 18%, transparent), transparent 32%),
    linear-gradient(180deg, color-mix(in srgb, var(--color-surface) 96%, transparent), color-mix(in srgb, var(--color-bg) 40%, var(--color-surface)));
}

.governance-card--engagement {
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--color-primary) 18%, transparent), transparent 44%),
    color-mix(in srgb, var(--color-bg) 44%, var(--color-surface));
}

.governance-card__header,
.governance-zone__header,
.governance-panel__header,
.governance-event-card__top,
.governance-event-card__footer,
.governance-feed-card__top,
.governance-attention-card,
.governance-list__item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.governance-card__header--compact {
  align-items: center;
}

.governance-card__status {
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 14%, transparent);
}

.governance-card__engagement-body {
  display: grid;
  gap: 18px;
  place-items: center;
  text-align: center;
}

.governance-health__top,
.governance-health__content,
.governance-health__heading,
.governance-health__stats {
  display: grid;
  gap: 10px;
}

.governance-health__top {
  justify-items: center;
}

.governance-event-select {
  position: relative;
  width: min(100%, 252px);
  justify-self: center;
  display: inline-flex;
  align-items: center;
}

.governance-event-select--primary {
  width: min(100%, 320px);
  justify-self: start;
}

.governance-event-select__input {
  width: 100%;
  min-height: 44px;
  padding: 0 40px 0 16px;
  border: none;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-bg) 56%, var(--color-surface));
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 700;
  font-family: inherit;
  outline: none;
  appearance: none;
}

.governance-event-select svg {
  position: absolute;
  right: 14px;
  color: var(--color-text-muted);
  pointer-events: none;
}

.governance-health-card__header,
.governance-health-card__header-copy,
.governance-health-card__tiles {
  display: grid;
  gap: 12px;
}

.governance-health-card__header {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
}

.governance-health-card__menu-wrap {
  position: relative;
}

.governance-health-card__header-copy {
  gap: 6px;
}

.governance-health-card__label {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.governance-health-card__title {
  margin: 0;
  font-size: clamp(24px, 3vw, 30px);
  line-height: 1.04;
  letter-spacing: -0.05em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-health-card__menu {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--color-surface) 86%, transparent);
  color: var(--color-text-muted);
  cursor: pointer;
}

.governance-health-card__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-muted);
}

.governance-health-arc {
  position: relative;
  width: min(100%, 252px);
  height: 196px;
  margin: 0 auto;
}

.governance-health-arc__segment {
  position: absolute;
  width: 14px;
  height: 42px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 10%, var(--color-surface));
  transform-origin: center center;
}

.governance-health-arc__segment.is-active {
  background: var(--color-primary);
  box-shadow: 0 10px 24px color-mix(in srgb, var(--color-primary) 18%, transparent);
}

.governance-health-arc__center {
  position: absolute;
  left: 50%;
  top: 60%;
  transform: translate(-50%, -50%);
  display: grid;
  justify-items: center;
  gap: 4px;
  text-align: center;
}

.governance-health-arc__value {
  font-size: 24px;
  line-height: 1;
  letter-spacing: -0.05em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-health-arc__caption {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.governance-health-arc__badge {
  position: absolute;
  left: 34px;
  top: 44px;
  z-index: 1;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: color-mix(in srgb, var(--color-surface) 96%, transparent);
  box-shadow: var(--governance-shadow-float);
  color: var(--color-text-primary);
}

.governance-health-arc__badge-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: var(--color-secondary);
}

.governance-health-arc__badge strong,
.governance-health-arc__badge span {
  font-size: 11px;
  line-height: 1;
  font-weight: 700;
}

.governance-health-arc__badge span:last-child {
  color: var(--color-text-muted);
}

.governance-health-card__tiles {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.governance-health-card__tile {
  min-width: 0;
  padding: 16px;
  border-radius: 22px;
  background: color-mix(in srgb, var(--color-bg) 54%, var(--color-surface));
  display: grid;
  gap: 8px;
}

.governance-health-card__tile span {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-muted);
}

.governance-health-card__tile strong {
  font-size: 32px;
  line-height: 1;
  letter-spacing: -0.05em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-report-popover {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  z-index: 10;
  width: min(240px, calc(100vw - 68px));
  padding: 10px;
  border-radius: 22px;
  background: color-mix(in srgb, var(--color-surface) 96%, transparent);
  box-shadow: var(--governance-shadow-popover);
  display: grid;
  gap: 8px;
}

.governance-report-popover__action {
  min-height: 46px;
  padding: 0 14px;
  border: none;
  border-radius: 16px;
  background: color-mix(in srgb, var(--color-bg) 52%, var(--color-surface));
  color: var(--color-text-primary);
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  font-size: 13px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
}

.governance-report-popover__action--primary {
  background: var(--color-nav);
  color: var(--color-nav-text);
}

.governance-report-popover__action:disabled {
  opacity: 0.56;
  cursor: not-allowed;
}

.governance-health__event-title {
  margin: 0;
  font-size: clamp(20px, 2.5vw, 24px);
  line-height: 1.06;
  letter-spacing: -0.05em;
  font-weight: 800;
  color: var(--color-text-primary);
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.governance-health__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-muted);
}

.governance-health__state {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--color-text-primary);
}

.governance-health__state-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--color-primary);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-primary) 18%, transparent);
}

.governance-health__body {
  display: grid;
  gap: 18px;
}

.governance-health__body--compact {
  grid-template-columns: minmax(112px, 132px) minmax(0, 1fr);
  align-items: center;
  gap: 16px;
}

.governance-health__stats {
  gap: 0;
}

.governance-health__stat-row {
  min-width: 0;
  padding: 10px 0;
  border-bottom: 1px solid color-mix(in srgb, var(--color-text-muted) 12%, transparent);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.governance-health__stat-row:last-child {
  border-bottom: none;
}

.governance-health__stat-row span {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.governance-health__stat-row strong {
  font-size: 20px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: -0.05em;
  color: var(--color-text-primary);
}

.governance-progress-copy__value {
  font-size: 28px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: var(--color-text-primary);
}

.governance-progress-copy__label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.governance-card--stat {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 14px;
}

.governance-card--spotlight {
  min-height: 100%;
}

.governance-card--stat-showcase {
  position: relative;
  overflow: hidden;
  min-height: 160px;
  grid-template-columns: 1fr;
  grid-template-rows: auto 1fr;
  gap: 18px;
  padding: 20px;
  border-radius: 28px;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--color-surface) 96%, transparent), color-mix(in srgb, var(--color-bg) 34%, var(--color-surface)));
  box-shadow:
    0 18px 42px color-mix(in srgb, var(--color-nav) 8%, transparent),
    inset 0 1px 0 var(--governance-surface-edge);
}

.governance-card--stat-showcase-accent {
  background:
    linear-gradient(
      180deg,
      color-mix(in srgb, var(--color-primary) 76%, white),
      color-mix(in srgb, var(--color-primary) 62%, white)
    );
  color: var(--color-banner-text);
  box-shadow:
    0 22px 44px color-mix(in srgb, var(--color-primary) 18%, transparent),
    inset 0 1px 0 color-mix(in srgb, white 56%, transparent);
}

.governance-card--stat-showcase-top-left {
  border-radius: 28px;
}

.governance-card--stat-showcase-top-right {
  border-radius: 28px;
}

.governance-card--stat-showcase-bottom-left {
  border-radius: 28px;
}

.governance-card--stat-showcase-bottom-right {
  border-radius: 28px;
}

.governance-card--stat-showcase-surface {
  background:
    linear-gradient(
      180deg,
      color-mix(in srgb, var(--color-surface) 98%, transparent),
      color-mix(in srgb, var(--color-bg) 32%, var(--color-surface))
    );
  box-shadow:
    inset 0 1px 0 var(--governance-surface-edge-strong),
    0 12px 28px color-mix(in srgb, var(--color-nav) 6%, transparent);
}

.governance-card--stat-showcase > * {
  position: relative;
  z-index: 1;
}

.governance-card--stat-showcase-accent::before {
  content: none;
}

.governance-stat-showcase__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.governance-stat-showcase__eyebrow {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.governance-stat-showcase__eyebrow span {
  min-width: 0;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  font-size: 12px;
  line-height: 1.12;
  letter-spacing: -0.02em;
  font-weight: 700;
  color: color-mix(in srgb, var(--color-text-primary) 78%, var(--color-text-muted));
}

.governance-stat-showcase__icon {
  width: 42px;
  height: 42px;
  border-radius: 15px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--color-primary) 14%, transparent);
  color: var(--color-primary);
}

.governance-card--stat-showcase-accent .governance-stat-showcase__icon {
  background: color-mix(in srgb, var(--color-banner-text) 12%, transparent);
  color: var(--color-banner-text);
}

.governance-card--stat-showcase-accent .governance-stat-showcase__eyebrow span {
  color: color-mix(in srgb, var(--color-banner-text) 90%, transparent);
}

.governance-stat-showcase__copy {
  min-width: 0;
  display: grid;
  align-content: end;
  gap: 0;
}

.governance-stat-showcase__copy strong {
  font-size: clamp(30px, 5.6vw, 40px);
  line-height: 0.92;
  letter-spacing: -0.06em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-card--stat-showcase-accent .governance-stat-showcase__copy strong {
  color: var(--color-banner-text);
}

.governance-stat-card__icon {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--color-primary) 14%, transparent);
  color: var(--color-primary);
}

.governance-stat-card__copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.governance-stat-card__copy strong {
  font-size: 28px;
  line-height: 1;
  letter-spacing: -0.05em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-stat-card__copy p {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.governance-feed-card__headline span,
.governance-feed-card__meta,
.governance-event-card__line,
.governance-event-card__time,
.governance-attention-card__copy p {
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-text-muted);
}

.governance-zone,
.governance-panel {
  padding: 18px;
  gap: 14px;
}

.governance-inline-action {
  padding: 0 14px;
  height: 40px;
  background: color-mix(in srgb, var(--color-primary) 12%, transparent);
  color: var(--color-primary);
}

.governance-attention-list,
.governance-feed-list,
.governance-placeholder-list,
.governance-list,
.governance-chip-list {
  display: grid;
  gap: 12px;
}

.governance-attention-card,
.governance-list__item,
.governance-feed-card {
  width: 100%;
  border: none;
  border-radius: 24px;
  padding: 16px;
  text-align: left;
  background: color-mix(in srgb, var(--color-bg) 54%, var(--color-surface));
  color: inherit;
}

.governance-attention-card__icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.governance-attention-card--warning .governance-attention-card__icon {
  background: var(--governance-warning-bg);
  color: var(--governance-warning);
}

.governance-attention-card--critical .governance-attention-card__icon {
  background: var(--governance-danger-bg);
  color: var(--governance-danger);
}

.governance-attention-card--default .governance-attention-card__icon {
  background: color-mix(in srgb, var(--color-primary) 14%, transparent);
  color: var(--color-primary);
}

.governance-attention-card__copy {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.governance-attention-card__copy strong,
.governance-empty-card strong,
.governance-list__copy strong,
.governance-feed-card__headline strong,
.governance-event-card__title {
  font-size: 15px;
  line-height: 1.35;
  color: var(--color-text-primary);
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.governance-attention-card__action {
  align-self: center;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-primary);
  white-space: nowrap;
}

.governance-empty-card {
  padding: 18px;
  gap: 10px;
}

.governance-empty-card--subtle {
  padding: 16px;
  border-radius: 24px;
  background: color-mix(in srgb, var(--color-bg) 58%, var(--color-surface));
  box-shadow: none;
}

.governance-empty-card svg {
  color: var(--color-primary);
}

.governance-report-error {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--governance-danger);
}

.governance-report-error--inline {
  padding-inline: 4px;
}

.governance-event-carousel {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: minmax(264px, 1fr);
  gap: 14px;
  overflow-x: auto;
  padding-bottom: 4px;
  scroll-snap-type: x proximity;
}

.governance-event-card {
  padding: 16px;
  border-radius: 28px;
  background: color-mix(in srgb, var(--color-bg) 52%, var(--color-surface));
  display: flex;
  flex-direction: column;
  gap: 10px;
  scroll-snap-align: start;
  min-width: 0;
}

.governance-event-card--live {
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--color-primary) 24%, transparent), transparent 46%),
    color-mix(in srgb, var(--color-bg) 46%, var(--color-surface));
}

.governance-event-card__status,
.governance-event-card__scope,
.governance-feed-card__status {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.governance-event-card__status,
.governance-feed-card__status {
  color: var(--color-primary);
}

.governance-event-card__scope {
  color: var(--color-text-muted);
}

.governance-event-card__footer {
  align-items: center;
}

.governance-event-card__time {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.governance-event-card__button {
  min-height: 40px;
  padding: 0 14px;
  background: var(--color-nav);
  color: var(--color-nav-text);
}

.governance-feed-card {
  gap: 8px;
}

.governance-feed-card__top {
  align-items: flex-start;
}

.governance-feed-card__headline {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.governance-feed-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.governance-section-grid {
  display: grid;
  gap: 14px;
}

.governance-panel--primary {
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--color-primary) 16%, transparent), transparent 48%),
    color-mix(in srgb, var(--color-bg) 52%, var(--color-surface));
}

.governance-placeholder-list__item {
  padding: 12px 14px;
  border-radius: 20px;
  background: color-mix(in srgb, var(--color-bg) 58%, var(--color-surface));
}

.governance-list__item {
  align-items: center;
}

.governance-list__item--static {
  cursor: default;
}

.governance-list__copy {
  min-width: 0;
  flex: 1;
  gap: 4px;
}

.governance-detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.governance-detail-card {
  padding: 14px;
  border-radius: 20px;
  background: color-mix(in srgb, var(--color-bg) 56%, var(--color-surface));
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.governance-detail-card span {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.governance-detail-card strong {
  font-size: 16px;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-chip-list {
  margin-top: 2px;
}

.governance-chip {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 12%, transparent);
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 700;
}

.governance-permission-alert__backdrop {
  position: fixed;
  inset: 0;
  z-index: 90;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: color-mix(in srgb, var(--color-nav) 22%, transparent);
  backdrop-filter: blur(14px);
}

.governance-permission-alert {
  width: min(100%, 420px);
  padding: 24px;
  border-radius: 30px;
  background: color-mix(in srgb, var(--color-surface) 96%, transparent);
  box-shadow: var(--governance-shadow-strong);
  display: grid;
  gap: 18px;
}

.governance-permission-alert__icon {
  width: 52px;
  height: 52px;
  border-radius: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--governance-danger-bg);
  color: var(--governance-danger);
}

.governance-permission-alert__copy {
  display: grid;
  gap: 8px;
}

.governance-permission-alert__eyebrow {
  margin: 0;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--governance-danger);
}

.governance-permission-alert__title {
  margin: 0;
  font-size: 24px;
  line-height: 1.08;
  letter-spacing: -0.05em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-permission-alert__description {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-muted);
}

.governance-permission-alert__button {
  min-height: 48px;
  padding: 0 18px;
  border: none;
  border-radius: 18px;
  background: var(--color-nav);
  color: var(--color-nav-text);
  font-size: 14px;
  font-weight: 800;
  font-family: inherit;
  cursor: pointer;
}

@media (min-width: 768px) {
  .governance-workspace {
    padding: 32px 32px 44px;
    gap: 22px;
  }

  .governance-header {
    grid-template-columns: minmax(0, 1.3fr) auto;
    align-items: flex-end;
  }

  .governance-header__actions {
    align-items: flex-end;
  }

  .governance-create-button {
    align-self: stretch;
  }

  .governance-summary-grid {
    grid-template-columns: minmax(0, 1.15fr) repeat(3, minmax(0, 1fr));
  }

  .governance-summary-grid--ssg {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .governance-health__body {
    grid-template-columns: auto minmax(0, 1fr);
    align-items: center;
  }

  .governance-analytics-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .governance-zone__header {
    align-items: flex-end;
  }

  .governance-section-grid {
    grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
  }

  .governance-analytics-shell__header {
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: end;
  }
}

@media (max-width: 767px) {
  .governance-workspace {
    padding-bottom: calc(112px + env(safe-area-inset-bottom, 0px));
  }

  .governance-header,
  .governance-state-card,
  .governance-card,
  .governance-zone,
  .governance-panel {
    border-radius: 28px;
  }

  .governance-header__title,
  .governance-zone__title,
  .governance-panel__title,
  .governance-state-card__title {
    font-size: 24px;
  }

  .governance-card--stat {
    grid-template-columns: 1fr;
  }

  .governance-card--stat-showcase {
    min-height: 148px;
    gap: 16px;
    padding: 16px;
  }

  .governance-summary-grid--ssg {
    gap: 12px;
  }

  .governance-card--stat-showcase-top-left {
    border-radius: 28px;
  }

  .governance-card--stat-showcase-top-right {
    border-radius: 28px;
  }

  .governance-card--stat-showcase-bottom-left {
    border-radius: 28px;
  }

  .governance-card--stat-showcase-bottom-right {
    border-radius: 28px;
  }

  .governance-health-card__title {
    font-size: 22px;
  }

  .governance-health-arc {
    width: min(100%, 236px);
    height: 184px;
  }

  .governance-health-arc__badge {
    left: 18px;
    top: 38px;
  }

  .governance-health__body--compact {
    grid-template-columns: minmax(104px, 120px) minmax(0, 1fr);
    align-items: start;
    gap: 14px;
  }

  .governance-health__event-title {
    text-align: left;
  }

  .governance-health__meta {
    justify-content: flex-start;
  }

  .governance-health__content {
    width: 100%;
  }

  .governance-health-card__tiles {
    grid-template-columns: 1fr 1fr;
  }

  .governance-stat-card__icon,
  .governance-stat-showcase__icon {
    width: 42px;
    height: 42px;
  }

  .governance-zone__header,
  .governance-card__header,
  .governance-feed-card__top,
  .governance-attention-card,
  .governance-list__item {
    flex-direction: column;
  }

  .governance-attention-card__action {
    align-self: flex-start;
  }

  .governance-event-card__footer {
    flex-direction: column;
    align-items: flex-start;
  }

  .governance-event-card__button,
  .governance-inline-action {
    width: 100%;
  }

  .governance-permission-alert__backdrop {
    padding: 16px;
  }

  .governance-permission-alert {
    padding: 22px 20px 20px;
    border-radius: 28px;
  }

  .governance-permission-alert__title {
    font-size: 22px;
  }
}

.governance-permission-alert-enter-active,
.governance-permission-alert-leave-active {
  transition: opacity 0.24s ease;
}

.governance-permission-alert-enter-active .governance-permission-alert,
.governance-permission-alert-leave-active .governance-permission-alert {
  transition: transform 0.32s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.24s ease;
}

.governance-permission-alert-enter-from,
.governance-permission-alert-leave-to {
  opacity: 0;
}

.governance-permission-alert-enter-from .governance-permission-alert,
.governance-permission-alert-leave-to .governance-permission-alert {
  transform: translateY(18px) scale(0.98);
  opacity: 0;
}

@keyframes governance-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
