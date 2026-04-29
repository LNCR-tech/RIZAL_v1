<template>
  <section class="student-analytics" aria-label="Student attendance analytics">
    <article class="student-analytics__hero">
      <div class="student-analytics__hero-head">
        <div>
          <p class="student-analytics__eyebrow">Attendance</p>
          <h2 class="student-analytics__title">{{ summaryModel.attendanceRateLabel }}</h2>
        </div>

        <span
          class="student-analytics__health-pill"
          :class="`student-analytics__health-pill--${heroState.tone}`"
        >
          {{ heroState.label }}
        </span>
      </div>

      <div class="student-analytics__progress-track" aria-hidden="true">
        <span :style="{ width: `${summaryModel.attendanceRate}%` }" />
      </div>

      <div class="student-analytics__hero-bottom">
        <p class="student-analytics__lead">{{ insightCopy }}</p>

        <div class="student-analytics__hero-actions">
          <button
            type="button"
            class="student-analytics__primary-action"
            :disabled="!hasData"
            @click="downloadReport"
          >
            <Download :size="16" :stroke-width="2.2" />
            <span>Report</span>
          </button>
        </div>
      </div>
    </article>

    <p class="student-analytics__sr-only" aria-live="polite">{{ liveSummary }}</p>

    <section class="student-analytics__control-bar" aria-label="Attendance analytics controls">
      <div class="student-analytics__control-copy">
        <p class="student-analytics__panel-kicker">Range</p>
        <strong>{{ rangeSummaryLabel }}</strong>
      </div>

      <div class="student-analytics__range" role="group" aria-label="Attendance analytics date range">
        <button
          v-for="range in rangeOptions"
          :key="range.key"
          type="button"
          class="student-analytics__range-button"
          :class="{ 'student-analytics__range-button--active': activeRange === range.key }"
          :aria-pressed="activeRange === range.key ? 'true' : 'false'"
          @click="activeRange = range.key"
        >
          {{ range.label }}
        </button>
      </div>
    </section>

    <section class="student-analytics__metrics" aria-label="Attendance summary metrics">
      <article
        v-for="metric in metricCards"
        :key="metric.key"
        class="student-analytics__metric"
        :class="`student-analytics__metric--${metric.tone}`"
      >
        <span class="student-analytics__metric-icon">
          <component :is="metric.icon" :size="18" :stroke-width="2.2" />
        </span>
        <span class="student-analytics__metric-label">{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
        <small>{{ metric.help }}</small>
      </article>
    </section>

    <section class="student-analytics__graph-grid">
      <article class="student-analytics__panel student-analytics__panel--trend">
        <div class="student-analytics__panel-head">
          <div>
            <p class="student-analytics__panel-kicker">{{ trendKicker }}</p>
            <h3>Trend</h3>
          </div>
          <TrendingUp :size="20" :stroke-width="2.2" />
        </div>

        <div class="student-analytics__trend" :class="{ 'student-analytics__trend--empty': !hasData }">
          <svg
            class="student-analytics__trend-svg"
            viewBox="0 0 360 190"
            role="img"
            :aria-label="trendChart.ariaLabel"
            preserveAspectRatio="none"
          >
            <line
              v-for="line in trendChart.gridLines"
              :key="line"
              class="student-analytics__trend-grid"
              x1="18"
              x2="342"
              :y1="line"
              :y2="line"
            />
            <path class="student-analytics__trend-area" :d="trendChart.areaPath" />
            <path class="student-analytics__trend-line" :d="trendChart.linePath" />
            <circle
              v-for="point in trendChart.points"
              :key="point.key"
              class="student-analytics__trend-point"
              :class="{ 'student-analytics__trend-point--empty': !point.marked }"
              :cx="point.x"
              :cy="point.y"
              r="4.5"
            />
          </svg>

          <div class="student-analytics__trend-legend">
            <div
              v-for="bar in trendBars"
              :key="bar.key"
              class="student-analytics__trend-chip"
            >
              <span>{{ bar.label }}</span>
              <strong>{{ bar.rateLabel }}</strong>
              <small>{{ bar.markedLabel }}</small>
            </div>
          </div>

          <div class="student-analytics__table-wrap" aria-label="Weekly attendance trend table">
            <table class="student-analytics__data-table">
              <caption>Weekly attendance trend for {{ activeRangeLabel }}</caption>
              <thead>
                <tr>
                  <th scope="col">Week</th>
                  <th scope="col">Rate</th>
                  <th scope="col">Marked</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="bar in trendBars" :key="`${bar.key}-table`">
                  <td>{{ bar.label }}</td>
                  <td>{{ bar.rateLabel }}</td>
                  <td>{{ bar.markedLabel }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </article>

      <article class="student-analytics__panel student-analytics__panel--mix">
        <div class="student-analytics__panel-head">
          <div>
            <p class="student-analytics__panel-kicker">Status Mix</p>
            <h3>Breakdown</h3>
          </div>
          <ChartNoAxesColumn :size="20" :stroke-width="2.2" />
        </div>

        <div class="student-analytics__mix-bar" :aria-label="statusDistributionLabel">
          <span
            v-for="item in statusBarItems"
            :key="item.key"
            class="student-analytics__mix-segment"
            :class="`student-analytics__mix-segment--${item.key}`"
            :style="{ width: `${item.share}%` }"
          />
        </div>

        <div class="student-analytics__status-list">
          <div
            v-for="item in statusItems"
            :key="item.key"
            class="student-analytics__status-row"
          >
            <span class="student-analytics__status-name">
              <i :class="`student-analytics__status-dot student-analytics__status-dot--${item.key}`" />
              {{ item.label }}
            </span>
            <strong>{{ item.valueLabel }}</strong>
            <small>{{ item.shareLabel }}</small>
          </div>
        </div>
      </article>
    </section>

    <section class="student-analytics__lower-grid">
      <article class="student-analytics__panel">
        <div class="student-analytics__panel-head">
          <div>
            <p class="student-analytics__panel-kicker">Next</p>
            <h3>To Do</h3>
          </div>
          <CalendarDays :size="20" :stroke-width="2.2" />
        </div>

        <div v-if="nextActions.length" class="student-analytics__action-list">
          <button
            v-for="item in nextActions"
            :key="item.key"
            type="button"
            class="student-analytics__action-row"
            :class="`student-analytics__action-row--${item.tone}`"
            @click="$emit('open-event', item.event)"
          >
            <span class="student-analytics__action-date">
              <strong>{{ item.day }}</strong>
              <small>{{ item.month }}</small>
            </span>
            <span class="student-analytics__action-copy">
              <strong>{{ item.event.name }}</strong>
              <small>{{ item.meta }}</small>
            </span>
            <span class="student-analytics__action-pill">{{ item.actionLabel }}</span>
            <ArrowUpRight :size="16" :stroke-width="2.2" />
          </button>
        </div>

        <article v-else class="student-analytics__empty">
          <CircleCheckBig :size="18" :stroke-width="2.2" />
          <div>
            <strong>Nothing due.</strong>
            <p>Open check-ins will appear here.</p>
          </div>
        </article>
      </article>

      <article class="student-analytics__panel">
        <div class="student-analytics__panel-head">
          <div>
            <p class="student-analytics__panel-kicker">History</p>
            <h3>Recent</h3>
          </div>
          <Clock3 :size="20" :stroke-width="2.2" />
        </div>

        <div v-if="recentRows.length" class="student-analytics__record-list">
          <article
            v-for="row in recentRows"
            :key="row.key"
            class="student-analytics__record-row"
          >
            <span class="student-analytics__record-status" :class="`student-analytics__record-status--${row.statusKey}`">
              {{ row.statusLabel }}
            </span>
            <span class="student-analytics__record-copy">
              <strong>{{ row.eventName }}</strong>
              <small>{{ row.scheduleLabel }}</small>
            </span>
            <span class="student-analytics__record-time">{{ row.timeInLabel }}</span>
          </article>
        </div>

        <article v-else class="student-analytics__empty">
          <ChartNoAxesColumn :size="18" :stroke-width="2.2" />
          <div>
            <strong>No records yet.</strong>
            <p>Your scans will show here.</p>
          </div>
        </article>
      </article>
    </section>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import {
  ArrowUpRight,
  CalendarDays,
  ChartNoAxesColumn,
  CircleCheckBig,
  CircleX,
  Clock3,
  Download,
  TimerReset,
  TrendingUp,
} from 'lucide-vue-next'
import {
  getAttendanceRecordTimestamp,
  getLatestAttendanceRecordsByEvent,
  isOpenAttendanceRecord,
  normalizeEventStatus,
  parseEventDateTime,
  resolveAttendanceDisplayStatus,
} from '@/services/attendanceFlow.js'
import {
  buildStudentStatusSummary,
  downloadStudentStatusSummaryCsv,
  resolveStudentSummaryStatus,
} from '@/services/studentStatusSummary.js'

const props = defineProps({
  user: {
    type: Object,
    default: null,
  },
  events: {
    type: Array,
    default: () => [],
  },
  records: {
    type: Array,
    default: () => [],
  },
  schoolName: {
    type: String,
    default: 'University Name',
  },
  schoolLogoCandidates: {
    type: Array,
    default: () => [],
  },
  apiBaseUrl: {
    type: String,
    default: '',
  },
})

defineEmits(['open-event', 'announcement-click'])

const DAY_MS = 24 * 60 * 60 * 1000
const rangeOptions = Object.freeze([
  { key: 'all', label: 'All', summary: 'All records' },
  { key: '30d', label: '30D', summary: 'Last 30 days' },
  { key: '90d', label: '90D', summary: 'Last 90 days' },
  { key: 'year', label: 'Year', summary: 'This year' },
])

const activeRange = ref('all')

const safeEvents = computed(() => Array.isArray(props.events) ? props.events.filter(Boolean) : [])
const safeRecords = computed(() => Array.isArray(props.records) ? props.records.filter(Boolean) : [])
const filteredRecords = computed(() => filterRecordsByRange(safeRecords.value, activeRange.value))
const allLatestRecords = computed(() => getLatestAttendanceRecordsByEvent(safeRecords.value))
const latestRecords = computed(() => getLatestAttendanceRecordsByEvent(filteredRecords.value))
const summaryModel = computed(() => buildStudentStatusSummary({
  attendanceRecords: filteredRecords.value,
  events: safeEvents.value,
}))
const hasData = computed(() => summaryModel.value.totalMarked > 0)
const activeRangeOption = computed(() => (
  rangeOptions.find((range) => range.key === activeRange.value) || rangeOptions[0]
))
const activeRangeLabel = computed(() => activeRangeOption.value.label)
const rangeSummaryLabel = computed(() => activeRangeOption.value.summary)
const trendKicker = computed(() => activeRange.value === 'all' ? '6 weeks' : rangeSummaryLabel.value)
const liveSummary = computed(() => (
  `${rangeSummaryLabel.value}: ${summaryModel.value.attendanceRateLabel} attendance rate, ${summaryModel.value.totalMarkedLabel} marked records.`
))
const statusDistributionLabel = computed(() => (
  `Attendance status distribution for ${rangeSummaryLabel.value}. ${summaryModel.value.totalMarkedLabel} marked records.`
))

const latestRecordByEventId = computed(() => {
  const map = new Map()
  allLatestRecords.value.forEach((record) => {
    const eventId = Number(record?.event_id)
    if (Number.isFinite(eventId)) map.set(eventId, record)
  })
  return map
})

const metricCards = computed(() => [
  {
    key: 'attended',
    label: 'Attended',
    value: summaryModel.value.attendedCountLabel,
    help: 'Present + late',
    icon: CircleCheckBig,
    tone: 'good',
  },
  {
    key: 'missed',
    label: 'Missed',
    value: summaryModel.value.missedCountLabel,
    help: 'Absent',
    icon: CircleX,
    tone: 'risk',
  },
  {
    key: 'late',
    label: 'Late',
    value: summaryModel.value.lateCountLabel,
    help: 'After window',
    icon: TimerReset,
    tone: 'warn',
  },
  {
    key: 'excused',
    label: 'Excused',
    value: summaryModel.value.excusedCountLabel,
    help: 'Approved',
    icon: TrendingUp,
    tone: 'brand',
  },
])

const statusItems = computed(() => {
  const fallbackWidth = summaryModel.value.totalMarked > 0 ? 0 : 25
  return summaryModel.value.items.map((item) => ({
    ...item,
    share: item.share || fallbackWidth,
  }))
})

const statusBarItems = computed(() => statusItems.value.filter((item) => item.share > 0))
const trendBars = computed(() => buildTrendBars(latestRecords.value))
const trendChart = computed(() => buildTrendChart(trendBars.value))
const recentRows = computed(() => summaryModel.value.rows.slice(0, 5))
const nextActions = computed(() => buildNextActions(safeEvents.value, latestRecordByEventId.value))

const heroState = computed(() => {
  if (!hasData.value) return { label: 'No data', tone: 'neutral' }
  const rate = summaryModel.value.attendanceRate
  if (rate >= 90) return { label: 'On track', tone: 'good' }
  if (rate >= 75) return { label: 'Steady', tone: 'warn' }
  return { label: 'Needs attention', tone: 'risk' }
})

const insightCopy = computed(() => {
  if (!hasData.value) {
    return 'Scan an event to start tracking.'
  }

  const countLabel = `${summaryModel.value.attendedCountLabel} of ${summaryModel.value.totalMarkedLabel} attended`
  const rate = summaryModel.value.attendanceRate
  if (rate >= 90) {
    return `${countLabel}. Keep it consistent.`
  }
  if (rate >= 75) {
    return `${countLabel}. Watch late or missed events.`
  }
  return `${countLabel}. Prioritize the next open event.`
})

async function downloadReport() {
  if (!hasData.value) return
  await downloadStudentStatusSummaryCsv({
    user: props.user,
    summary: summaryModel.value,
  })
}

function filterRecordsByRange(records = [], rangeKey = 'all') {
  const list = Array.isArray(records) ? records : []
  if (rangeKey === 'all') return list

  const now = Date.now()
  let startMs = 0

  if (rangeKey === '30d') {
    startMs = now - (30 * DAY_MS)
  } else if (rangeKey === '90d') {
    startMs = now - (90 * DAY_MS)
  } else if (rangeKey === 'year') {
    const today = new Date(now)
    startMs = new Date(today.getFullYear(), 0, 1).getTime()
  }

  if (!startMs) return list

  return list.filter((record) => {
    const timestamp = getAttendanceRecordTimestamp(record)
    return Number.isFinite(timestamp) && timestamp >= startMs && timestamp <= now
  })
}

function buildTrendBars(records = []) {
  const validDates = records
    .map((record) => getAttendanceRecordTimestamp(record))
    .filter((time) => Number.isFinite(time) && time > 0)

  const reference = new Date(Math.max(Date.now(), ...validDates))
  const currentWeekStart = startOfWeek(reference)
  const bars = []

  for (let offset = 5; offset >= 0; offset -= 1) {
    const start = new Date(currentWeekStart)
    start.setDate(currentWeekStart.getDate() - (offset * 7))
    const end = new Date(start)
    end.setDate(start.getDate() + 6)
    end.setHours(23, 59, 59, 999)

    const weekRecords = records.filter((record) => {
      const timestamp = getAttendanceRecordTimestamp(record)
      return timestamp >= start.getTime() && timestamp <= end.getTime()
    })
    const marked = weekRecords.length
    const attended = weekRecords.filter((record) => {
      const status = resolveStudentSummaryStatus(record)
      return status === 'present' || status === 'late'
    }).length
    const rate = marked > 0 ? Math.round((attended / marked) * 100) : 0

    bars.push({
      key: start.toISOString(),
      label: formatShortDate(start),
      marked,
      markedLabel: marked > 0 ? `${marked} marked` : 'No records',
      rate,
      rateLabel: marked > 0 ? `${rate}%` : '--',
    })
  }

  return bars
}

function buildTrendChart(bars = []) {
  const width = 360
  const height = 190
  const paddingX = 18
  const paddingY = 20
  const bottom = height - paddingY
  const availableWidth = width - (paddingX * 2)
  const availableHeight = height - (paddingY * 2)
  const step = bars.length > 1 ? availableWidth / (bars.length - 1) : availableWidth

  const points = bars.map((bar, index) => {
    const x = paddingX + (index * step)
    const y = bottom - ((Number(bar.rate) || 0) / 100) * availableHeight
    return {
      ...bar,
      x: Number(x.toFixed(2)),
      y: Number(y.toFixed(2)),
    }
  })

  const safePoints = points.length
    ? points
    : [{ key: 'empty', x: paddingX, y: bottom, rate: 0, marked: 0 }]
  const linePath = safePoints
    .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`)
    .join(' ')
  const firstPoint = safePoints[0]
  const lastPoint = safePoints[safePoints.length - 1]
  const areaPath = `${linePath} L ${lastPoint.x} ${bottom} L ${firstPoint.x} ${bottom} Z`
  const markedWeeks = bars.filter((bar) => bar.marked > 0)
  const averageRate = markedWeeks.length
    ? Math.round(markedWeeks.reduce((total, bar) => total + bar.rate, 0) / markedWeeks.length)
    : 0

  return {
    points: safePoints,
    linePath,
    areaPath,
    gridLines: [paddingY, paddingY + (availableHeight / 2), bottom],
    ariaLabel: markedWeeks.length
      ? `Attendance trend over six weeks. Average rate ${averageRate} percent.`
      : 'Attendance trend over six weeks. No attendance records yet.',
  }
}

function buildNextActions(events = [], recordByEventId = new Map()) {
  return [...events]
    .filter((event) => ['ongoing', 'upcoming'].includes(normalizeEventStatus(event?.status)))
    .sort((left, right) => {
      const leftRank = normalizeEventStatus(left?.status) === 'ongoing' ? 0 : 1
      const rightRank = normalizeEventStatus(right?.status) === 'ongoing' ? 0 : 1
      if (leftRank !== rightRank) return leftRank - rightRank
      return parseEventDateTime(left?.start_datetime).getTime() - parseEventDateTime(right?.start_datetime).getTime()
    })
    .slice(0, 5)
    .map((event) => {
      const eventId = Number(event?.id)
      const record = recordByEventId.get(eventId)
      const status = normalizeEventStatus(event?.status)
      const openRecord = isOpenAttendanceRecord(record)
      const displayStatus = resolveAttendanceDisplayStatus(record)
      const schedule = parseEventDateTime(event?.start_datetime)

      let actionLabel = 'View'
      let tone = 'neutral'
      if (openRecord) {
        actionLabel = 'Sign out'
        tone = 'urgent'
      } else if (status === 'ongoing' && !displayStatus) {
        actionLabel = 'Check in'
        tone = 'urgent'
      } else if (status === 'ongoing') {
        actionLabel = 'Live'
        tone = 'active'
      } else if (status === 'upcoming') {
        actionLabel = 'Upcoming'
      }

      return {
        key: `${eventId}-${event?.start_datetime || ''}`,
        event,
        actionLabel,
        tone,
        day: Number.isFinite(schedule.getTime())
          ? new Intl.DateTimeFormat('en-PH', { day: '2-digit' }).format(schedule)
          : '--',
        month: Number.isFinite(schedule.getTime())
          ? new Intl.DateTimeFormat('en-PH', { month: 'short' }).format(schedule).toUpperCase()
          : 'TBD',
        meta: formatEventMeta(event),
      }
    })
}

function formatEventMeta(event = {}) {
  const pieces = []
  if (event.location) pieces.push(event.location)

  const start = parseEventDateTime(event.start_datetime)
  if (Number.isFinite(start.getTime())) {
    pieces.push(new Intl.DateTimeFormat('en-PH', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    }).format(start))
  }

  return pieces.join(' • ') || 'Schedule pending'
}

function formatShortDate(date) {
  return new Intl.DateTimeFormat('en-PH', {
    month: 'short',
    day: 'numeric',
  }).format(date)
}

function startOfWeek(date) {
  const next = new Date(date)
  const day = next.getDay()
  const diff = day === 0 ? -6 : 1 - day
  next.setDate(next.getDate() + diff)
  next.setHours(0, 0, 0, 0)
  return next
}
</script>

<style scoped>
.student-analytics {
  display: grid;
  gap: clamp(16px, 3vw, 24px);
}

.student-analytics__sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.student-analytics :is(button, [href], [tabindex]):focus-visible {
  outline: 3px solid color-mix(in srgb, var(--color-primary) 64%, var(--color-banner-text));
  outline-offset: 3px;
}

.student-analytics__hero,
.student-analytics__panel,
.student-analytics__metric,
.student-analytics__control-bar {
  border: 1px solid color-mix(in srgb, var(--color-surface-border) 74%, transparent);
  box-shadow: 0 20px 48px color-mix(in srgb, var(--color-nav) 8%, transparent);
}

.student-analytics__hero {
  position: relative;
  min-height: 0;
  border-radius: clamp(28px, 5vw, 42px);
  padding: clamp(22px, 4vw, 34px);
  display: flex;
  flex-direction: column;
  gap: clamp(18px, 3vw, 24px);
  overflow: hidden;
  background:
    radial-gradient(circle at 8% 0%, color-mix(in srgb, var(--color-banner-text) 24%, transparent), transparent 34%),
    radial-gradient(circle at 84% 92%, color-mix(in srgb, var(--color-primary-dark) 34%, transparent), transparent 42%),
    linear-gradient(135deg, var(--color-primary), color-mix(in srgb, var(--color-primary-dark) 82%, var(--color-primary)));
  color: var(--color-banner-text);
}

.student-analytics__hero::after {
  content: '';
  position: absolute;
  inset: auto -8% -28% 28%;
  height: 58%;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-banner-text) 12%, transparent);
  transform: rotate(-8deg);
  pointer-events: none;
}

.student-analytics__hero-head,
.student-analytics__hero-bottom,
.student-analytics__progress-track {
  position: relative;
  z-index: 1;
}

.student-analytics__hero-head,
.student-analytics__hero-bottom {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.student-analytics__hero-head {
  align-items: flex-start;
}

.student-analytics__hero-bottom {
  align-items: flex-end;
}

.student-analytics__eyebrow,
.student-analytics__panel-kicker {
  margin: 0;
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.student-analytics__eyebrow {
  color: color-mix(in srgb, var(--color-banner-text) 72%, transparent);
}

.student-analytics__title {
  margin: 8px 0 0;
  font-size: clamp(66px, 14vw, 112px);
  line-height: 0.78;
  letter-spacing: -0.09em;
  font-weight: 900;
}

.student-analytics__health-pill {
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
  background: color-mix(in srgb, var(--color-banner-text) 14%, transparent);
  color: var(--color-banner-text);
  font-size: 11px;
  font-weight: 900;
}

.student-analytics__health-pill--good {
  background: color-mix(in srgb, var(--color-status-compliant) 20%, transparent);
}

.student-analytics__health-pill--warn {
  background: color-mix(in srgb, var(--color-status-late) 24%, transparent);
}

.student-analytics__health-pill--risk {
  background: color-mix(in srgb, var(--color-status-non-compliant) 20%, transparent);
}

.student-analytics__progress-track {
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
  background: color-mix(in srgb, var(--color-banner-text) 18%, transparent);
}

.student-analytics__progress-track span {
  display: block;
  height: 100%;
  min-width: 2px;
  max-width: 100%;
  border-radius: inherit;
  background: var(--color-banner-text);
}

.student-analytics__lead {
  max-width: 460px;
  margin: 0;
  font-size: clamp(13px, 2vw, 16px);
  line-height: 1.45;
  font-weight: 800;
  color: color-mix(in srgb, var(--color-banner-text) 78%, transparent);
}

.student-analytics__hero-actions {
  display: flex;
  flex-shrink: 0;
}

.student-analytics__primary-action {
  min-height: 46px;
  padding: 0 18px;
  border: none;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  font: inherit;
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
}

.student-analytics__primary-action {
  background: var(--color-nav);
  color: var(--color-nav-text);
}

.student-analytics__primary-action:disabled {
  opacity: 0.46;
  cursor: not-allowed;
}

.student-analytics__primary-action {
  transition: transform 180ms ease, background 180ms ease, opacity 180ms ease;
}

.student-analytics__primary-action:hover:not(:disabled) {
  transform: translateY(-1px);
}

.student-analytics__control-bar {
  border-radius: 28px;
  padding: clamp(14px, 2.6vw, 18px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--color-surface) 94%, transparent), color-mix(in srgb, var(--color-primary) 8%, var(--color-surface))),
    var(--color-surface);
}

.student-analytics__control-copy {
  min-width: 0;
}

.student-analytics__control-copy strong {
  display: block;
  margin-top: 4px;
  font-size: clamp(18px, 3vw, 26px);
  line-height: 1;
  letter-spacing: -0.05em;
  color: var(--color-surface-text);
}

.student-analytics__range {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.student-analytics__range-button {
  min-height: 40px;
  padding: 0 14px;
  border: 1px solid color-mix(in srgb, var(--color-surface-border) 80%, transparent);
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-bg) 52%, var(--color-surface));
  color: var(--color-surface-text-secondary);
  font: inherit;
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  transition: background 180ms ease, color 180ms ease, border-color 180ms ease, transform 180ms ease;
}

.student-analytics__range-button:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--color-primary) 44%, var(--color-surface-border));
  color: var(--color-surface-text);
}

.student-analytics__range-button--active {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: var(--color-banner-text);
}

.student-analytics__metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.student-analytics__metric {
  min-height: 166px;
  border-radius: 30px;
  padding: 18px;
  display: grid;
  gap: 8px;
  align-content: space-between;
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--color-primary) 12%, transparent), transparent 46%),
    var(--color-surface);
}

.student-analytics__metric-icon {
  width: 42px;
  height: 42px;
  border-radius: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 12%, transparent);
}

.student-analytics__metric-label {
  font-size: 12px;
  font-weight: 900;
  color: var(--color-surface-text-secondary);
}

.student-analytics__metric strong {
  font-size: clamp(34px, 5vw, 52px);
  line-height: 0.9;
  letter-spacing: -0.07em;
  font-weight: 900;
  color: var(--color-surface-text);
}

.student-analytics__metric small {
  font-size: 12px;
  line-height: 1.35;
  font-weight: 700;
  color: var(--color-surface-text-muted);
}

.student-analytics__metric--brand {
  background:
    radial-gradient(circle at 80% 12%, color-mix(in srgb, var(--color-banner-text) 16%, transparent), transparent 44%),
    var(--color-primary);
}

.student-analytics__metric--brand,
.student-analytics__metric--brand .student-analytics__metric-label,
.student-analytics__metric--brand strong,
.student-analytics__metric--brand small,
.student-analytics__metric--brand .student-analytics__metric-icon {
  color: var(--color-banner-text);
}

.student-analytics__metric--brand .student-analytics__metric-icon {
  background: color-mix(in srgb, var(--color-banner-text) 14%, transparent);
}

.student-analytics__metric--good .student-analytics__metric-icon {
  color: var(--color-status-compliant);
  background: color-mix(in srgb, var(--color-status-compliant) 12%, transparent);
}

.student-analytics__metric--risk .student-analytics__metric-icon {
  color: var(--color-status-non-compliant);
  background: color-mix(in srgb, var(--color-status-non-compliant) 12%, transparent);
}

.student-analytics__metric--warn .student-analytics__metric-icon {
  color: var(--color-status-late);
  background: color-mix(in srgb, var(--color-status-late) 14%, transparent);
}

.student-analytics__graph-grid,
.student-analytics__lower-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(320px, 0.75fr);
  gap: 16px;
  align-items: stretch;
}

.student-analytics__panel {
  border-radius: 34px;
  padding: clamp(18px, 3vw, 24px);
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--color-surface) 96%, transparent), color-mix(in srgb, var(--color-bg) 36%, var(--color-surface)));
}

.student-analytics__panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  color: var(--color-surface-text);
}

.student-analytics__panel-kicker {
  color: var(--color-primary);
}

.student-analytics__panel h3 {
  margin: 5px 0 0;
  font-size: clamp(20px, 3vw, 28px);
  line-height: 1;
  letter-spacing: -0.055em;
  font-weight: 900;
  color: var(--color-surface-text);
}

.student-analytics__trend {
  margin-top: 22px;
  display: grid;
  gap: 14px;
}

.student-analytics__trend-svg {
  width: 100%;
  height: clamp(210px, 28vw, 270px);
  display: block;
  overflow: visible;
}

.student-analytics__trend-grid {
  stroke: color-mix(in srgb, var(--color-surface-border) 74%, transparent);
  stroke-width: 1;
}

.student-analytics__trend-area {
  fill: color-mix(in srgb, var(--color-primary) 18%, transparent);
}

.student-analytics__trend-line {
  fill: none;
  stroke: var(--color-primary);
  stroke-width: 4;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.student-analytics__trend-point {
  fill: var(--color-surface);
  stroke: var(--color-primary);
  stroke-width: 3;
}

.student-analytics__trend-point--empty {
  fill: color-mix(in srgb, var(--color-bg) 72%, var(--color-surface));
  stroke: color-mix(in srgb, var(--color-surface-text-muted) 46%, transparent);
}

.student-analytics__trend-legend {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 8px;
}

.student-analytics__trend-chip {
  min-width: 0;
  padding: 10px;
  border-radius: 16px;
  display: grid;
  gap: 3px;
  background: color-mix(in srgb, var(--color-bg) 42%, var(--color-surface));
}

.student-analytics__trend-chip span,
.student-analytics__trend-chip strong,
.student-analytics__trend-chip small {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.student-analytics__trend-chip span {
  font-size: 10px;
  font-weight: 900;
  color: var(--color-surface-text-muted);
}

.student-analytics__trend-chip strong {
  font-size: 14px;
  font-weight: 900;
  color: var(--color-surface-text);
}

.student-analytics__trend-chip small {
  font-size: 10px;
  font-weight: 800;
  color: var(--color-surface-text-muted);
}

.student-analytics__table-wrap {
  max-width: 100%;
  overflow-x: auto;
  border-radius: 20px;
  background: color-mix(in srgb, var(--color-bg) 38%, var(--color-surface));
}

.student-analytics__data-table {
  width: 100%;
  min-width: 420px;
  border-collapse: collapse;
  color: var(--color-surface-text);
}

.student-analytics__data-table caption {
  padding: 12px 14px 4px;
  text-align: left;
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-surface-text-muted);
}

.student-analytics__data-table th,
.student-analytics__data-table td {
  padding: 10px 14px;
  border-top: 1px solid color-mix(in srgb, var(--color-surface-border) 62%, transparent);
  text-align: left;
  font-size: 12px;
  font-weight: 800;
}

.student-analytics__data-table th {
  color: var(--color-surface-text-secondary);
}

.student-analytics__data-table td {
  color: var(--color-surface-text);
}

.student-analytics__mix-bar {
  height: 24px;
  margin-top: 26px;
  border-radius: 999px;
  display: flex;
  overflow: hidden;
  background: color-mix(in srgb, var(--color-bg) 54%, var(--color-surface));
}

.student-analytics__mix-segment {
  min-width: 4px;
}

.student-analytics__mix-segment--present,
.student-analytics__status-dot--present {
  background: var(--color-status-compliant);
}

.student-analytics__mix-segment--late,
.student-analytics__status-dot--late {
  background: var(--color-status-late);
}

.student-analytics__mix-segment--absent,
.student-analytics__status-dot--absent {
  background: var(--color-status-non-compliant);
}

.student-analytics__mix-segment--excused,
.student-analytics__status-dot--excused {
  background: var(--color-status-excused);
}

.student-analytics__status-list {
  margin-top: 18px;
  display: grid;
  gap: 10px;
}

.student-analytics__status-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 12px;
  align-items: center;
  padding: 13px 14px;
  border-radius: 20px;
  background: color-mix(in srgb, var(--color-bg) 42%, var(--color-surface));
}

.student-analytics__status-name {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  font-weight: 900;
  color: var(--color-surface-text);
}

.student-analytics__status-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  flex-shrink: 0;
}

.student-analytics__status-row strong {
  font-size: 15px;
  color: var(--color-surface-text);
}

.student-analytics__status-row small {
  font-size: 12px;
  font-weight: 800;
  color: var(--color-surface-text-muted);
}

.student-analytics__action-list,
.student-analytics__record-list {
  margin-top: 18px;
  display: grid;
  gap: 10px;
}

.student-analytics__action-row {
  width: 100%;
  min-height: 78px;
  border: none;
  border-radius: 24px;
  padding: 12px;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto;
  gap: 12px;
  align-items: center;
  text-align: left;
  font: inherit;
  background: color-mix(in srgb, var(--color-bg) 46%, var(--color-surface));
  color: var(--color-surface-text);
  cursor: pointer;
  transition: transform 180ms ease, background 180ms ease;
}

.student-analytics__action-row:hover {
  transform: translateY(-2px);
  background: color-mix(in srgb, var(--color-primary) 10%, var(--color-surface));
}

.student-analytics__action-date {
  width: 52px;
  height: 54px;
  border-radius: 18px;
  display: grid;
  place-items: center;
  align-content: center;
  background: var(--color-primary);
  color: var(--color-banner-text);
}

.student-analytics__action-date strong {
  font-size: 18px;
  line-height: 1;
  font-weight: 900;
}

.student-analytics__action-date small,
.student-analytics__action-copy small {
  font-size: 10px;
  font-weight: 900;
}

.student-analytics__action-copy {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.student-analytics__action-copy strong,
.student-analytics__record-copy strong {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  font-weight: 900;
  color: var(--color-surface-text);
}

.student-analytics__action-copy small,
.student-analytics__record-copy small,
.student-analytics__record-time {
  color: var(--color-surface-text-muted);
}

.student-analytics__action-pill {
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 900;
  background: color-mix(in srgb, var(--color-nav) 8%, transparent);
}

.student-analytics__action-row--urgent .student-analytics__action-pill {
  background: var(--color-nav);
  color: var(--color-nav-text);
}

.student-analytics__action-row--active .student-analytics__action-pill {
  background: color-mix(in srgb, var(--color-status-compliant) 16%, transparent);
  color: var(--color-status-compliant);
}

.student-analytics__record-row {
  min-height: 72px;
  padding: 12px;
  border-radius: 22px;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  background: color-mix(in srgb, var(--color-bg) 46%, var(--color-surface));
}

.student-analytics__record-status {
  min-width: 72px;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 900;
}

.student-analytics__record-status--present {
  background: color-mix(in srgb, var(--color-status-compliant) 14%, transparent);
  color: var(--color-status-compliant);
}

.student-analytics__record-status--late {
  background: color-mix(in srgb, var(--color-status-late) 16%, transparent);
  color: var(--color-status-late);
}

.student-analytics__record-status--absent {
  background: color-mix(in srgb, var(--color-status-non-compliant) 14%, transparent);
  color: var(--color-status-non-compliant);
}

.student-analytics__record-status--excused {
  background: color-mix(in srgb, var(--color-status-excused) 14%, transparent);
  color: var(--color-status-excused);
}

.student-analytics__record-copy {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.student-analytics__record-time {
  max-width: 128px;
  font-size: 11px;
  font-weight: 800;
  text-align: right;
}

.student-analytics__empty {
  margin-top: 18px;
  min-height: 126px;
  padding: 18px;
  border-radius: 24px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: color-mix(in srgb, var(--color-bg) 46%, var(--color-surface));
  color: var(--color-surface-text-muted);
}

.student-analytics__empty strong {
  display: block;
  margin-bottom: 5px;
  color: var(--color-surface-text);
}

.student-analytics__empty p {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
}

@media (max-width: 1100px) {
  .student-analytics__metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .student-analytics__graph-grid,
  .student-analytics__lower-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 767px) {
  .student-analytics {
    gap: 10px;
  }

  .student-analytics__hero {
    border-radius: 28px;
    padding: 18px 18px 16px;
    gap: 14px;
  }

  .student-analytics__hero::after {
    inset: auto -18% -36% 18%;
    height: 62%;
  }

  .student-analytics__hero-head {
    align-items: flex-start;
    gap: 12px;
  }

  .student-analytics__hero-bottom {
    align-items: stretch;
    flex-direction: column;
    gap: 12px;
  }

  .student-analytics__eyebrow,
  .student-analytics__panel-kicker {
    font-size: 10px;
    letter-spacing: 0.11em;
  }

  .student-analytics__title {
    margin-top: 6px;
    font-size: clamp(64px, 22vw, 82px);
    letter-spacing: -0.095em;
  }

  .student-analytics__health-pill {
    min-height: 30px;
    padding: 0 10px;
    font-size: 10px;
  }

  .student-analytics__progress-track {
    height: 8px;
  }

  .student-analytics__lead {
    font-size: 12px;
    line-height: 1.4;
  }

  .student-analytics__hero-actions {
    display: flex;
  }

  .student-analytics__primary-action {
    width: 100%;
    min-height: 40px;
    padding: 0 14px;
    font-size: 11px;
  }

  .student-analytics__control-bar {
    align-items: stretch;
    flex-direction: column;
    border-radius: 999px;
    padding: 7px;
    gap: 0;
  }

  .student-analytics__control-copy {
    display: none;
  }

  .student-analytics__range {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    justify-content: stretch;
    gap: 6px;
  }

  .student-analytics__range-button {
    min-height: 34px;
    padding: 0 6px;
    border: none;
    font-size: 10px;
  }

  .student-analytics__metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .student-analytics__metric {
    min-height: 94px;
    border-radius: 20px;
    padding: 12px;
  }

  .student-analytics__metric-icon {
    width: 30px;
    height: 30px;
    border-radius: 12px;
  }

  .student-analytics__metric-label {
    font-size: 10px;
  }

  .student-analytics__metric strong {
    font-size: clamp(27px, 9vw, 36px);
  }

  .student-analytics__metric small {
    display: none;
  }

  .student-analytics__graph-grid,
  .student-analytics__lower-grid {
    gap: 12px;
  }

  .student-analytics__panel {
    border-radius: 24px;
    padding: 16px;
  }

  .student-analytics__panel h3 {
    font-size: 20px;
  }

  .student-analytics__trend-svg {
    height: 148px;
  }

  .student-analytics__trend-legend,
  .student-analytics__table-wrap {
    display: none;
  }

  .student-analytics__mix-bar {
    height: 18px;
    margin-top: 20px;
  }

  .student-analytics__status-list,
  .student-analytics__action-list,
  .student-analytics__record-list {
    margin-top: 14px;
    gap: 8px;
  }

  .student-analytics__status-row {
    grid-template-columns: minmax(0, 1fr) auto;
    padding: 11px 12px;
    border-radius: 16px;
  }

  .student-analytics__status-row small {
    display: none;
  }

  .student-analytics__action-row {
    min-height: 66px;
    grid-template-columns: auto minmax(0, 1fr) auto;
    gap: 10px;
    padding: 10px;
    border-radius: 20px;
  }

  .student-analytics__action-row > svg {
    display: none;
  }

  .student-analytics__action-date {
    width: 46px;
    height: 48px;
    border-radius: 16px;
  }

  .student-analytics__action-pill {
    min-height: 28px;
    padding: 0 10px;
    font-size: 10px;
  }

  .student-analytics__record-row {
    min-height: 64px;
    grid-template-columns: auto minmax(0, 1fr);
    gap: 10px;
    padding: 10px;
    border-radius: 18px;
  }

  .student-analytics__record-status {
    min-width: 66px;
    min-height: 30px;
    padding: 0 10px;
    font-size: 10px;
  }

  .student-analytics__record-time {
    grid-column: 2;
    max-width: none;
    font-size: 10px;
    text-align: left;
  }

  .student-analytics__empty {
    min-height: 104px;
    margin-top: 14px;
    padding: 14px;
    border-radius: 18px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .student-analytics__action-row,
  .student-analytics__trend-line,
  .student-analytics__primary-action,
  .student-analytics__range-button {
    transition: none;
  }
}
</style>
