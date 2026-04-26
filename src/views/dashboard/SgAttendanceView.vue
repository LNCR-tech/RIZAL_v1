<template>
  <section class="sg-sub-page">
    <header class="sg-sub-header dashboard-enter dashboard-enter--1">
      <button class="sg-sub-back" type="button" @click="goBack">
        <ArrowLeft :size="20" />
      </button>
      <h1 class="sg-sub-title">Manage Attendance</h1>
    </header>

    <div v-if="isLoading" class="sg-sub-loading dashboard-enter dashboard-enter--2">
      <p>Loading attendance data...</p>
    </div>

    <div v-else-if="loadError" class="sg-sub-error dashboard-enter dashboard-enter--2">
      <p>{{ loadError }}</p>
      <button class="sg-sub-action" type="button" @click="reload">Try Again</button>
    </div>

    <template v-else>
      <div class="sg-sub-card sg-att-summary dashboard-enter dashboard-enter--2">
        <h2 class="sg-sub-card-title">Attendance Summary</h2>
        <div v-if="summary" class="sg-att-stats">
          <div class="sg-att-stat">
            <span class="sg-att-stat-value">{{ summary.total_events ?? '—' }}</span>
            <span class="sg-att-stat-label">Events</span>
          </div>
          <div class="sg-att-stat">
            <span class="sg-att-stat-value">{{ summary.total_present ?? '—' }}</span>
            <span class="sg-att-stat-label">Present</span>
          </div>
          <div class="sg-att-stat">
            <span class="sg-att-stat-value">{{ summary.total_absent ?? '—' }}</span>
            <span class="sg-att-stat-label">Absent</span>
          </div>
          <div class="sg-att-stat">
            <span class="sg-att-stat-value">{{ summary.total_late ?? '—' }}</span>
            <span class="sg-att-stat-label">Late</span>
          </div>
        </div>
        <p v-else class="sg-sub-empty">Summary data unavailable.</p>
      </div>

      <div class="sg-sub-card dashboard-enter dashboard-enter--3">
        <h2 class="sg-sub-card-title">Recent Records</h2>
        <div v-if="records.length" class="sg-att-list">
          <article v-for="record in records" :key="record.id || record.event_id" class="sg-att-row">
            <div class="sg-att-info">
              <span class="sg-att-event">{{ record.event_title || record.event_name || 'Event' }}</span>
              <span class="sg-att-date">{{ formatDate(record.event_date || record.created_at) }}</span>
            </div>
            <span class="sg-att-status-badge" :class="`sg-att-status-badge--${(record.status || '').toLowerCase()}`">
              {{ record.status || '—' }}
            </span>
          </article>
        </div>
        <p v-else class="sg-sub-empty">No attendance records yet.</p>
      </div>
    </template>
  </section>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from 'lucide-vue-next'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useSgPreviewBundle } from '@/composables/useSgPreviewBundle.js'
import { useSgDashboard } from '@/composables/useSgDashboard.js'
import { getAttendanceSummary, getMyAttendance } from '@/services/backendApi.js'
import { withPreservedGovernancePreviewQuery } from '@/services/routeWorkspace.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const route = useRoute()
const router = useRouter()
const { apiBaseUrl } = useDashboardSession()
const { previewBundle } = useSgPreviewBundle(() => props.preview)
const { isLoading: sgLoading } = useSgDashboard(props.preview)

const isLoading = ref(true)
const loadError = ref('')
const summary = ref(null)
const records = ref([])

function formatDate(d) {
  if (!d) return ''
  try { return new Date(d).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) }
  catch { return d }
}

function goBack() {
  router.push(
    props.preview
      ? withPreservedGovernancePreviewQuery(route, '/exposed/governance')
      : '/governance'
  )
}

watch(
  [apiBaseUrl, () => sgLoading.value, () => route.query?.variant],
  async ([url]) => {
    if (!url || sgLoading.value) return
    await loadAttendance(url)
  },
  { immediate: true }
)

async function loadAttendance(url) {
  isLoading.value = true
  loadError.value = ''
  try {
    if (props.preview) {
      summary.value = previewBundle.value?.attendance?.summary || null
      records.value = Array.isArray(previewBundle.value?.attendance?.records)
        ? previewBundle.value.attendance.records.map((record) => ({ ...record }))
        : []
      return
    }

    const token = localStorage.getItem('aura_token') || ''
    const [summaryData, attendanceRecords] = await Promise.allSettled([
      getAttendanceSummary(url, token),
      getMyAttendance(url, token),
    ])
    summary.value = summaryData.status === 'fulfilled' ? summaryData.value : null
    records.value = attendanceRecords.status === 'fulfilled' ? attendanceRecords.value : []
  } catch (e) {
    loadError.value = e?.message || 'Unable to load attendance data.'
  } finally { isLoading.value = false }
}

async function reload() { if (apiBaseUrl.value) await loadAttendance(apiBaseUrl.value) }
</script>

<style scoped>
@import '@/assets/css/sg-sub-views.css';

.sg-att-summary { margin-bottom: 4px; }
.sg-att-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.sg-att-stat { display: flex; flex-direction: column; align-items: center; padding: 12px 8px; border-radius: 14px; background: var(--color-surface-border); }
.sg-att-stat-value { font-size: 22px; font-weight: 800; color: var(--color-primary); }
.sg-att-stat-label { font-size: 11px; font-weight: 600; color: var(--color-text-muted); margin-top: 2px; }

.sg-att-list { display: flex; flex-direction: column; gap: 6px; }
.sg-att-row { display: flex; align-items: center; justify-content: space-between; padding: 12px 14px; border-radius: 12px; background: var(--color-surface-border); }
.sg-att-info { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.sg-att-event { font-size: 14px; font-weight: 600; color: var(--color-text-primary); }
.sg-att-date { font-size: 12px; color: var(--color-text-muted); }
.sg-att-status-badge { font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 10px; text-transform: capitalize; }
.sg-att-status-badge--present { background: #27ae6033; color: #27ae60; }
.sg-att-status-badge--absent { background: #e74c3c33; color: #e74c3c; }
.sg-att-status-badge--late { background: #f0ad4e33; color: #f0ad4e; }
.sg-att-status-badge--excused { background: #3498db33; color: #3498db; }
</style>
