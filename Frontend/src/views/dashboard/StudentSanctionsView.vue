<template>
  <section class="student-sanctions-page">
    <TopBar
      class="dashboard-enter dashboard-enter--1"
      :user="activeUser"
      :unread-count="activeUnreadAnnouncements"
      @toggle-notifications="showNotifications = !showNotifications"
    />

    <header class="student-sanctions-page__header dashboard-enter dashboard-enter--2">
      <div>
        <p class="student-sanctions-page__eyebrow">Student Compliance</p>
        <h1 class="student-sanctions-page__title">Sanctions</h1>
      </div>
      <button class="student-sanctions-page__refresh" type="button" @click="reload">
        Refresh
      </button>
    </header>

    <div v-if="isLoading" class="student-sanctions-page__state dashboard-enter dashboard-enter--3">
      <p>Loading your sanctions...</p>
    </div>

    <div v-else-if="loadError" class="student-sanctions-page__state student-sanctions-page__state--error dashboard-enter dashboard-enter--3">
      <p>{{ loadError }}</p>
      <button class="student-sanctions-page__retry" type="button" @click="reload">Try Again</button>
    </div>

    <template v-else>
      <section class="student-sanctions-summary dashboard-enter dashboard-enter--3">
        <article class="student-sanctions-summary__card">
          <span>Total Records</span>
          <strong>{{ sanctions.length }}</strong>
        </article>
        <article class="student-sanctions-summary__card">
          <span>Pending</span>
          <strong>{{ pendingRecords.length }}</strong>
        </article>
        <article class="student-sanctions-summary__card">
          <span>Complied</span>
          <strong>{{ compliedRecords.length }}</strong>
        </article>
      </section>

      <section class="student-sanctions-section dashboard-enter dashboard-enter--4">
        <header class="student-sanctions-section__header">
          <h2>Sanctions List</h2>
          <p>All sanctioned events and item-level compliance status.</p>
        </header>

        <div v-if="sanctionRecords.length" class="student-sanctions-records">
          <article
            v-for="record in sanctionRecords"
            :key="record.id || `${record.event_id}-${record.created_at || record.updated_at || 'record'}`"
            class="student-sanctions-record"
          >
            <header class="student-sanctions-record__header">
              <div class="student-sanctions-record__event">
                <strong>{{ resolveEventName(record) }}</strong>
                <span>{{ formatRecordMeta(record) }}</span>
              </div>
              <span class="student-sanctions-record__status" :class="`student-sanctions-record__status--${resolveRecordStatus(record)}`">
                {{ formatStatusLabel(resolveRecordStatus(record)) }}
              </span>
            </header>

            <ul v-if="Array.isArray(record.items) && record.items.length" class="student-sanctions-record__items">
              <li
                v-for="item in record.items"
                :key="item.id || item.item_code || item.item_name"
                class="student-sanctions-record__item"
              >
                <div class="student-sanctions-record__item-main">
                  <strong>{{ item.item_name }}</strong>
                  <p v-if="item.item_description">{{ item.item_description }}</p>
                </div>
                <span class="student-sanctions-record__item-status" :class="`student-sanctions-record__item-status--${normalizeStatus(item.status)}`">
                  {{ formatStatusLabel(normalizeStatus(item.status)) }}
                </span>
              </li>
            </ul>
            <p v-else class="student-sanctions-record__empty">No sanction items were listed for this event.</p>
          </article>
        </div>
        <p v-else class="student-sanctions-section__empty">You do not have sanction records right now.</p>
      </section>

      <section class="student-sanctions-section dashboard-enter dashboard-enter--5">
        <header class="student-sanctions-section__header">
          <h2>Compliance History</h2>
          <p>Complied sanctions with completion date, school year, and semester.</p>
        </header>

        <div v-if="complianceHistory.length" class="student-sanctions-history">
          <article
            v-for="entry in complianceHistory"
            :key="entry.key"
            class="student-sanctions-history__row"
          >
            <div>
              <span>Date</span>
              <strong>{{ entry.dateLabel }}</strong>
            </div>
            <div>
              <span>School Year</span>
              <strong>{{ entry.schoolYear }}</strong>
            </div>
            <div>
              <span>Semester</span>
              <strong>{{ entry.semester }}</strong>
            </div>
            <div>
              <span>Event</span>
              <strong>{{ entry.eventName }}</strong>
            </div>
          </article>
        </div>
        <p v-else class="student-sanctions-section__empty">No complied sanctions yet.</p>
      </section>
    </template>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import TopBar from '@/components/dashboard/TopBar.vue'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { usePreviewTheme } from '@/composables/usePreviewTheme.js'
import { studentDashboardPreviewData } from '@/data/studentDashboardPreview.js'
import { getMySanctions } from '@/services/backendApi.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const route = useRoute()
const showNotifications = ref(false)

const {
  apiBaseUrl,
  token,
  currentUser,
  events,
  unreadAnnouncements,
} = useDashboardSession()

const activeUser = computed(() => (props.preview ? studentDashboardPreviewData.user : currentUser.value))
const activeEvents = computed(() => (props.preview ? studentDashboardPreviewData.events : events.value))
const activeSchoolSettings = computed(() => (props.preview ? studentDashboardPreviewData.schoolSettings : null))
const activeUnreadAnnouncements = computed(() => (props.preview ? 0 : unreadAnnouncements.value))

usePreviewTheme(() => props.preview, activeSchoolSettings)

const sanctions = ref([])
const isLoading = ref(true)
const loadError = ref('')

const eventNameLookup = computed(() => {
  const lookup = new Map()
  for (const event of activeEvents.value) {
    const eventId = Number(event?.id)
    if (Number.isFinite(eventId)) {
      lookup.set(eventId, event?.name || `Event #${eventId}`)
    }
  }
  return lookup
})

const sanctionRecords = computed(() => {
  const records = Array.isArray(sanctions.value) ? sanctions.value : []
  return [...records].sort((left, right) => {
    const leftPending = hasPendingItems(left)
    const rightPending = hasPendingItems(right)
    if (leftPending !== rightPending) return leftPending ? -1 : 1

    const leftTimestamp = toTimestamp(
      left?.updated_at || left?.created_at || left?.complied_at
    )
    const rightTimestamp = toTimestamp(
      right?.updated_at || right?.created_at || right?.complied_at
    )
    return rightTimestamp - leftTimestamp
  })
})

const pendingRecords = computed(() => sanctionRecords.value.filter((record) => hasPendingItems(record)))
const compliedRecords = computed(() => sanctionRecords.value.filter((record) => !hasPendingItems(record)))

const complianceHistory = computed(() => {
  return compliedRecords.value
    .map((record, index) => {
      const period = resolveAcademicPeriod(record)
      const compliedAt = record?.complied_at || record?.updated_at || record?.created_at || null
      const eventName = resolveEventName(record)
      return {
        key: `${record?.id || record?.event_id || index}-${compliedAt || 'na'}`,
        eventName,
        dateLabel: formatDate(compliedAt),
        schoolYear: period.schoolYear,
        semester: period.semester,
        timestamp: toTimestamp(compliedAt),
      }
    })
    .sort((left, right) => right.timestamp - left.timestamp)
})

watch(
  [apiBaseUrl, token, () => currentUser.value?.id, () => props.preview, () => route.query?.variant],
  async ([url, authToken, userId, previewMode]) => {
    if (previewMode) {
      await loadSanctions(url, authToken)
      return
    }
    if (!url || !authToken || !Number.isFinite(Number(userId))) return
    await loadSanctions(url, authToken)
  },
  { immediate: true }
)

function toTimestamp(value) {
  const parsed = new Date(value || 0).getTime()
  return Number.isFinite(parsed) ? parsed : 0
}

function normalizeStatus(value) {
  const normalized = String(value || '').trim().toLowerCase()
  if (!normalized) return 'pending'
  return normalized
}

function hasPendingItems(record = null) {
  const overallStatus = normalizeStatus(record?.status)
  if (overallStatus === 'pending') return true

  const items = Array.isArray(record?.items) ? record.items : []
  return items.some((item) => normalizeStatus(item?.status) === 'pending')
}

function resolveRecordStatus(record = null) {
  return hasPendingItems(record) ? 'pending' : 'complied'
}

function resolveEventName(record = null) {
  const directName = String(record?.event_name || '').trim()
  if (directName) return directName

  const eventId = Number(record?.event_id)
  if (Number.isFinite(eventId)) {
    return eventNameLookup.value.get(eventId) || `Event #${eventId}`
  }
  return 'Event'
}

function formatStatusLabel(status = '') {
  const normalized = normalizeStatus(status)
  if (normalized === 'pending') return 'Pending'
  if (normalized === 'complied') return 'Complied'
  return normalized.charAt(0).toUpperCase() + normalized.slice(1)
}

function formatDate(value) {
  if (!value) return 'N/A'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return 'N/A'
  return parsed.toLocaleDateString('en-PH', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function formatRecordMeta(record = null) {
  if (resolveRecordStatus(record) === 'pending') {
    const createdAt = formatDate(record?.created_at || record?.updated_at)
    return createdAt === 'N/A' ? 'Pending compliance' : `Pending since ${createdAt}`
  }

  const compliedDate = formatDate(record?.complied_at || record?.updated_at || record?.created_at)
  return compliedDate === 'N/A' ? 'Complied' : `Complied on ${compliedDate}`
}

function resolveAcademicPeriod(record = null) {
  const schoolYear = String(record?.school_year || '').trim()
  const semester = String(record?.semester || '').trim()

  if (schoolYear || semester) {
    return {
      schoolYear: schoolYear || 'N/A',
      semester: semester || 'N/A',
    }
  }

  const baseDate = new Date(record?.complied_at || record?.updated_at || record?.created_at || '')
  if (Number.isNaN(baseDate.getTime())) {
    return {
      schoolYear: 'N/A',
      semester: 'N/A',
    }
  }

  const year = baseDate.getFullYear()
  const month = baseDate.getMonth() + 1
  const schoolYearStart = month >= 8 ? year : year - 1
  const computedSchoolYear = `${schoolYearStart}-${schoolYearStart + 1}`

  let computedSemester = 'Midyear'
  if (month >= 8) computedSemester = '1st Semester'
  else if (month <= 5) computedSemester = '2nd Semester'

  return {
    schoolYear: computedSchoolYear,
    semester: computedSemester,
  }
}

function buildPreviewSanctions() {
  return [
    {
      id: 9101,
      event_id: 8,
      event_name: 'Department Meeting',
      status: 'pending',
      created_at: new Date().toISOString(),
      items: [
        {
          id: 811,
          item_name: 'Community Service',
          item_description: 'Complete 3 hours of service assigned by your program council.',
          status: 'pending',
        },
        {
          id: 812,
          item_name: 'Reflection Letter',
          item_description: 'Submit a reflection letter about the event absence.',
          status: 'pending',
        },
      ],
    },
    {
      id: 9102,
      event_id: 10,
      event_name: 'College Sportsfest',
      status: 'complied',
      complied_at: new Date(Date.now() - 18 * 24 * 60 * 60 * 1000).toISOString(),
      school_year: '2025-2026',
      semester: '2nd Semester',
      items: [
        {
          id: 821,
          item_name: 'Attendance Make-Up Duty',
          item_description: 'Joined approved make-up duty by student governance.',
          status: 'complied',
        },
      ],
    },
  ]
}

async function loadSanctions(url, authToken) {
  isLoading.value = true
  loadError.value = ''

  try {
    if (props.preview) {
      sanctions.value = buildPreviewSanctions()
      return
    }

    sanctions.value = await getMySanctions(url, authToken)
  } catch (error) {
    loadError.value = error?.message || 'Unable to load your sanctions.'
  } finally {
    isLoading.value = false
  }
}

async function reload() {
  await loadSanctions(apiBaseUrl.value, token.value)
}
</script>

<style scoped>
.student-sanctions-page {
  min-height: 100vh;
  padding: 28px 22px 110px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.student-sanctions-page__header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.student-sanctions-page__eyebrow {
  margin: 0 0 4px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
}

.student-sanctions-page__title {
  margin: 0;
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: var(--color-text-primary);
}

.student-sanctions-page__refresh,
.student-sanctions-page__retry {
  min-height: 40px;
  padding: 0 16px;
  border-radius: 999px;
  border: none;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.student-sanctions-page__refresh {
  background: var(--color-primary);
  color: var(--color-banner-text);
}

.student-sanctions-page__retry {
  margin-top: 8px;
  background: rgba(220, 38, 38, 0.12);
  color: #b91c1c;
}

.student-sanctions-page__state {
  border-radius: 20px;
  padding: 18px;
  background: var(--color-surface);
  color: var(--color-text-muted);
  font-size: 14px;
  font-weight: 600;
}

.student-sanctions-page__state--error {
  color: #b91c1c;
}

.student-sanctions-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.student-sanctions-summary__card {
  border-radius: 18px;
  padding: 14px;
  background: var(--color-surface);
  display: grid;
  gap: 6px;
}

.student-sanctions-summary__card span {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-text-muted);
}

.student-sanctions-summary__card strong {
  font-size: 24px;
  line-height: 1;
  letter-spacing: -0.03em;
  color: var(--color-text-primary);
}

.student-sanctions-section {
  border-radius: 24px;
  padding: 16px;
  background: var(--color-surface);
  display: grid;
  gap: 12px;
}

.student-sanctions-section__header {
  display: grid;
  gap: 3px;
}

.student-sanctions-section__header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--color-text-primary);
}

.student-sanctions-section__header p {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-muted);
}

.student-sanctions-section__empty {
  margin: 0;
  padding: 16px;
  border-radius: 14px;
  background: color-mix(in srgb, var(--color-bg) 62%, var(--color-surface));
  font-size: 13px;
  color: var(--color-text-muted);
}

.student-sanctions-records {
  display: grid;
  gap: 10px;
}

.student-sanctions-record {
  border-radius: 16px;
  padding: 14px;
  background: color-mix(in srgb, var(--color-bg) 62%, var(--color-surface));
  display: grid;
  gap: 10px;
}

.student-sanctions-record__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.student-sanctions-record__event {
  display: grid;
  gap: 3px;
}

.student-sanctions-record__event strong {
  font-size: 14px;
  line-height: 1.4;
  color: var(--color-text-primary);
}

.student-sanctions-record__event span {
  font-size: 12px;
  color: var(--color-text-muted);
}

.student-sanctions-record__status {
  min-height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.student-sanctions-record__status--pending {
  color: #b45309;
  background: rgba(245, 158, 11, 0.14);
}

.student-sanctions-record__status--complied {
  color: #166534;
  background: rgba(34, 197, 94, 0.16);
}

.student-sanctions-record__items {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 8px;
}

.student-sanctions-record__item {
  border-radius: 12px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.58);
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.student-sanctions-record__item-main {
  display: grid;
  gap: 2px;
}

.student-sanctions-record__item-main strong {
  font-size: 13px;
  color: var(--color-text-primary);
}

.student-sanctions-record__item-main p {
  margin: 0;
  font-size: 12px;
  line-height: 1.45;
  color: var(--color-text-muted);
}

.student-sanctions-record__item-status {
  min-height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.student-sanctions-record__item-status--pending {
  color: #b45309;
  background: rgba(245, 158, 11, 0.14);
}

.student-sanctions-record__item-status--complied {
  color: #166534;
  background: rgba(34, 197, 94, 0.16);
}

.student-sanctions-record__empty {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-muted);
}

.student-sanctions-history {
  display: grid;
  gap: 8px;
}

.student-sanctions-history__row {
  border-radius: 14px;
  padding: 12px;
  background: color-mix(in srgb, var(--color-bg) 62%, var(--color-surface));
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.student-sanctions-history__row span {
  display: block;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.student-sanctions-history__row strong {
  display: block;
  margin-top: 3px;
  font-size: 12px;
  line-height: 1.35;
  color: var(--color-text-primary);
}

@media (max-width: 900px) {
  .student-sanctions-summary {
    grid-template-columns: 1fr;
  }

  .student-sanctions-history__row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 768px) {
  .student-sanctions-page {
    padding: 36px 36px 40px;
    gap: 20px;
  }
}
</style>
