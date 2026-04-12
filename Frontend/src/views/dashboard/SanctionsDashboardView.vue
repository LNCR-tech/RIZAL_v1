<template>
  <section class="sg-sub-page">
    <header class="sg-sub-header dashboard-enter dashboard-enter--1">
      <button class="sg-sub-back" type="button" @click="goBack">
        <ArrowLeft :size="20" />
      </button>
      <h1 class="sg-sub-title">Sanctions Dashboard</h1>
    </header>

    <div v-if="isLoading" class="sg-sub-loading dashboard-enter dashboard-enter--2">
      <p>Loading sanctions dashboard...</p>
    </div>

    <div v-else-if="loadError" class="sg-sub-error dashboard-enter dashboard-enter--2">
      <p>{{ loadError }}</p>
      <button class="sg-sub-action" type="button" @click="reload">Try Again</button>
    </div>

    <template v-else>
      <div class="sg-summary-grid dashboard-enter dashboard-enter--2">
        <article class="sg-summary-card">
          <span class="sg-summary-val">{{ dashboard.total_events }}</span>
          <span class="sg-summary-lbl">Events</span>
        </article>
        <article class="sg-summary-card">
          <span class="sg-summary-val">{{ dashboard.total_participants }}</span>
          <span class="sg-summary-lbl">Participants</span>
        </article>
        <article class="sg-summary-card">
          <span class="sg-summary-val" style="color:#e67e22;">{{ dashboard.total_absent }}</span>
          <span class="sg-summary-lbl">Absent</span>
        </article>
        <article class="sg-summary-card">
          <span class="sg-summary-val">{{ formatPercent(dashboard.overall_absence_rate_percent) }}</span>
          <span class="sg-summary-lbl">Absence Rate</span>
        </article>
      </div>

      <div class="sg-sub-toolbar dashboard-enter dashboard-enter--3">
        <div class="sg-sub-search-shell">
          <input
            v-model="searchQuery"
            type="text"
            class="sg-sub-search-input"
            placeholder="Search events"
          >
          <Search :size="14" style="color: var(--color-text-muted);" />
        </div>
      </div>

      <div class="sg-sub-card dashboard-enter dashboard-enter--4">
        <h2 class="sg-sub-card-title">Governance Events</h2>

        <div v-if="filteredEvents.length" class="sanctions-table-wrap">
          <table class="sanctions-table">
            <thead>
              <tr>
                <th>Event</th>
                <th>Participants</th>
                <th>Absent</th>
                <th>Absence Rate</th>
                <th>Pending</th>
                <th>Complied</th>
                <th />
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in filteredEvents" :key="item.event_id">
                <td>
                  <div class="sanctions-table__event">
                    <strong>{{ item.event_name }}</strong>
                    <span>{{ item.owner_level }}</span>
                  </div>
                </td>
                <td>{{ item.participant_count }}</td>
                <td>{{ item.absent_count }}</td>
                <td>{{ formatPercent(item.absence_rate_percent) }}</td>
                <td>{{ item.pending_sanctions }}</td>
                <td>{{ item.complied_sanctions }}</td>
                <td class="sanctions-table__actions">
                  <button class="sg-sub-action" type="button" @click="openStudents(item.event_id)">
                    Open
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <p v-else class="sg-sub-empty">No sanctioned events found.</p>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Search } from 'lucide-vue-next'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useSgDashboard } from '@/composables/useSgDashboard.js'
import { useSgPreviewBundle } from '@/composables/useSgPreviewBundle.js'
import { getSanctionsDashboard } from '@/services/backendApi.js'
import { withPreservedGovernancePreviewQuery } from '@/services/routeWorkspace.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const route = useRoute()
const router = useRouter()
const { apiBaseUrl, token } = useDashboardSession()
const { isLoading: sgLoading } = useSgDashboard(props.preview)
const { previewBundle } = useSgPreviewBundle(() => props.preview)

const isLoading = ref(true)
const loadError = ref('')
const searchQuery = ref('')
const dashboard = ref({
  total_events: 0,
  total_participants: 0,
  total_absent: 0,
  total_pending_sanctions: 0,
  total_complied_sanctions: 0,
  overall_absence_rate_percent: 0,
  events: [],
})

const filteredEvents = computed(() => {
  const query = String(searchQuery.value || '').trim().toLowerCase()
  if (!query) return dashboard.value.events || []

  return (dashboard.value.events || []).filter((eventSummary) => (
    String(eventSummary.event_name || '').toLowerCase().includes(query)
    || String(eventSummary.owner_level || '').toLowerCase().includes(query)
  ))
})

watch(
  [apiBaseUrl, () => sgLoading.value, () => route.query?.variant],
  async ([url]) => {
    if (!url || sgLoading.value) return
    await loadDashboard(url)
  },
  { immediate: true }
)

function goBack() {
  if (props.preview) {
    router.push(withPreservedGovernancePreviewQuery(route, '/exposed/governance/events'))
    return
  }
  router.push('/governance/events')
}

function openStudents(eventId) {
  if (props.preview) {
    router.push(withPreservedGovernancePreviewQuery(route, {
      name: 'PreviewSgSanctionedStudents',
      params: { eventId: String(eventId) },
    }))
    return
  }

  router.push({
    name: 'SgSanctionedStudents',
    params: { eventId: String(eventId) },
  })
}

function formatPercent(value) {
  const normalized = Number(value)
  if (!Number.isFinite(normalized)) return '0%'
  return `${Math.round(normalized * 10) / 10}%`
}

function buildPreviewDashboard(bundle = null) {
  const sourceEvents = Array.isArray(bundle?.events) ? bundle.events : []
  const events = sourceEvents.map((event, index) => {
    const participantCount = 160 + (index * 32)
    const absentCount = Math.max(6, Math.round(participantCount * (0.08 + (index * 0.02))))
    const pending = Math.max(0, absentCount - (4 + index))
    const complied = Math.max(0, absentCount - pending)
    return {
      event_id: Number(event.id),
      event_name: event.name || 'Untitled Event',
      owner_level: String(event.scope_label || 'SG').includes('Campus') ? 'SSG' : 'SG',
      participant_count: participantCount,
      absent_count: absentCount,
      pending_sanctions: pending,
      complied_sanctions: complied,
      absence_rate_percent: participantCount > 0 ? (absentCount / participantCount) * 100 : 0,
    }
  })

  const totalParticipants = events.reduce((sum, item) => sum + item.participant_count, 0)
  const totalAbsent = events.reduce((sum, item) => sum + item.absent_count, 0)
  const totalPending = events.reduce((sum, item) => sum + item.pending_sanctions, 0)
  const totalComplied = events.reduce((sum, item) => sum + item.complied_sanctions, 0)

  return {
    total_events: events.length,
    total_participants: totalParticipants,
    total_absent: totalAbsent,
    total_pending_sanctions: totalPending,
    total_complied_sanctions: totalComplied,
    overall_absence_rate_percent: totalParticipants > 0
      ? (totalAbsent / totalParticipants) * 100
      : 0,
    events,
  }
}

async function loadDashboard(url) {
  isLoading.value = true
  loadError.value = ''

  try {
    if (props.preview) {
      dashboard.value = buildPreviewDashboard(previewBundle.value)
      return
    }

    dashboard.value = await getSanctionsDashboard(url, token.value)
  } catch (error) {
    loadError.value = error?.message || 'Unable to load sanctions dashboard.'
  } finally {
    isLoading.value = false
  }
}

async function reload() {
  if (!apiBaseUrl.value) return
  await loadDashboard(apiBaseUrl.value)
}
</script>

<style scoped>
@import '@/assets/css/sg-sub-views.css';

.sg-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.sg-summary-card {
  border-radius: 16px;
  background: var(--color-surface);
  padding: 14px 12px;
  display: grid;
  gap: 6px;
}

.sg-summary-val {
  font-size: 24px;
  font-weight: 800;
  color: var(--color-text-primary);
  line-height: 1;
}

.sg-summary-lbl {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.sanctions-table-wrap {
  overflow-x: auto;
}

.sanctions-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 760px;
}

.sanctions-table thead th {
  text-align: left;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  padding: 0 10px 10px;
}

.sanctions-table tbody td {
  padding: 12px 10px;
  border-top: 1px solid color-mix(in srgb, var(--color-text-muted) 18%, transparent);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.sanctions-table__event {
  display: grid;
  gap: 2px;
}

.sanctions-table__event strong {
  font-size: 13px;
  line-height: 1.35;
}

.sanctions-table__event span {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-muted);
}

.sanctions-table__actions {
  text-align: right;
}

.sanctions-table__actions .sg-sub-action {
  min-height: 34px;
  padding: 0 12px;
  font-size: 12px;
}

@media (max-width: 768px) {
  .sg-summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
