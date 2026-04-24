<template>
  <section class="student-status">
    <article class="student-status__summary-card">
      <div class="student-status__summary-head">
        <div class="student-status__summary-copy">
          <p class="student-status__eyebrow">Attendance</p>
          <h2 class="student-status__title">Status Summary</h2>
        </div>

        <div class="student-status__summary-actions">
          <div class="student-status__toggle" role="tablist" aria-label="Status summary display mode">
            <button
              type="button"
              class="student-status__toggle-button"
              :class="{ 'student-status__toggle-button--active': displayMode === 'chart' }"
              :aria-selected="displayMode === 'chart' ? 'true' : 'false'"
              @click="displayMode = 'chart'"
            >
              Chart
            </button>
            <button
              type="button"
              class="student-status__toggle-button"
              :class="{ 'student-status__toggle-button--active': displayMode === 'table' }"
              :aria-selected="displayMode === 'table' ? 'true' : 'false'"
              @click="displayMode = 'table'"
            >
              Table
            </button>
          </div>

          <button
            type="button"
            class="student-status__download"
            :disabled="!hasData"
            @click="downloadReport"
          >
            <Download :size="16" :stroke-width="2" />
            <span>Report</span>
          </button>
        </div>
      </div>

      <template v-if="hasData">
        <div v-if="displayMode === 'chart'" class="student-status__chart">
          <div
            v-for="item in chartItems"
            :key="item.key"
            class="student-status__chart-column"
          >
            <span class="student-status__value-pill" :class="`student-status__value-pill--${item.key}`">
              {{ item.valueLabel }}
            </span>

            <div class="student-status__bar-track">
              <span
                class="student-status__bar-fill"
                :class="`student-status__bar-fill--${item.key}`"
                :style="{ height: `${item.height}%` }"
              />
            </div>

            <div class="student-status__chart-labels">
              <strong>{{ item.label }}</strong>
              <span>{{ item.shareLabel }}</span>
            </div>
          </div>
        </div>

        <div v-else class="student-status__table">
          <article
            v-for="item in summaryModel.items"
            :key="item.key"
            class="student-status__table-row"
          >
            <div class="student-status__table-status">
              <span class="student-status__status-dot" :class="`student-status__status-dot--${item.key}`" />
              <strong>{{ item.label }}</strong>
            </div>

            <span class="student-status__table-value">{{ item.valueLabel }}</span>
            <span class="student-status__table-share">{{ item.shareLabel }}</span>
          </article>
        </div>
      </template>

      <article v-else class="student-status__empty">
        <ChartNoAxesColumn :size="18" :stroke-width="2" />
        <div>
          <strong>No attendance status data yet.</strong>
          <p>Status summary will appear after the backend returns attendance records.</p>
        </div>
      </article>
    </article>

    <section class="student-status__stats-grid">
      <article
        v-for="card in statCards"
        :key="card.key"
        class="student-status__stat-card"
        :class="`student-status__stat-card--${card.tone}`"
      >
        <div class="student-status__stat-top">
          <div class="student-status__stat-eyebrow">
            <span class="student-status__stat-icon">
              <component :is="card.icon" :size="18" :stroke-width="2" />
            </span>
            <span>{{ card.label }}</span>
          </div>
        </div>

        <div class="student-status__stat-copy">
          <strong>{{ card.value }}</strong>
        </div>
      </article>
    </section>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import {
  CalendarDays,
  ChartNoAxesColumn,
  CircleCheckBig,
  CircleX,
  Download,
  ShieldCheck,
} from 'lucide-vue-next'
import {
  buildStudentStatusSummary,
  downloadStudentStatusSummaryCsv,
} from '@/services/studentStatusSummary.js'

const props = defineProps({
  records: {
    type: Array,
    default: () => [],
  },
  events: {
    type: Array,
    default: () => [],
  },
  user: {
    type: Object,
    default: null,
  },
})

const displayMode = ref('chart')

const summaryModel = computed(() => buildStudentStatusSummary({
  attendanceRecords: props.records,
  events: props.events,
}))

const hasData = computed(() => summaryModel.value.totalMarked > 0)

const chartItems = computed(() => {
  const maxValue = Math.max(...summaryModel.value.items.map((item) => item.value), 1)
  return summaryModel.value.items.map((item) => ({
    ...item,
    height: Math.max(18, Math.round((item.value / maxValue) * 100)),
  }))
})

const statCards = computed(() => [
  {
    key: 'total',
    label: 'Total Events',
    value: summaryModel.value.totalMarkedLabel,
    icon: CalendarDays,
    tone: 'accent',
  },
  {
    key: 'attended',
    label: 'Attended',
    value: summaryModel.value.attendedCountLabel,
    icon: CircleCheckBig,
    tone: 'surface',
  },
  {
    key: 'missed',
    label: 'Missed',
    value: summaryModel.value.missedCountLabel,
    icon: CircleX,
    tone: 'surface',
  },
  {
    key: 'excused',
    label: 'Excused',
    value: summaryModel.value.excusedCountLabel,
    icon: ShieldCheck,
    tone: 'accent',
  },
])

async function downloadReport() {
  if (!hasData.value) return
  await downloadStudentStatusSummaryCsv({
    user: props.user,
    summary: summaryModel.value,
  })
}
</script>

<style scoped>
.student-status {
  display: grid;
  gap: 16px;
}

.student-status__summary-card,
.student-status__stat-card {
  border-radius: 30px;
  background: color-mix(in srgb, var(--color-bg) 46%, var(--color-surface));
  box-shadow: 0 18px 48px color-mix(in srgb, var(--color-nav) 8%, transparent);
}

.student-status__summary-card {
  padding: 18px;
  display: grid;
  gap: 16px;
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--color-primary) 16%, transparent), transparent 42%),
    linear-gradient(180deg, color-mix(in srgb, var(--color-surface) 98%, transparent), color-mix(in srgb, var(--color-bg) 38%, var(--color-surface)));
}

.student-status__summary-head,
.student-status__summary-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.student-status__summary-head {
  align-items: flex-start;
}

.student-status__summary-copy {
  display: grid;
  gap: 6px;
}

.student-status__eyebrow {
  margin: 0;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-primary);
}

.student-status__title {
  margin: 0;
  font-size: clamp(22px, 4.8vw, 30px);
  line-height: 1;
  letter-spacing: -0.05em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.student-status__summary-actions {
  flex-wrap: wrap;
  justify-content: flex-end;
}

.student-status__toggle {
  padding: 4px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: color-mix(in srgb, var(--color-bg) 56%, var(--color-surface));
}

.student-status__toggle-button,
.student-status__download {
  min-height: 38px;
  border: none;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 800;
  font-family: inherit;
  cursor: pointer;
}

.student-status__toggle-button {
  padding: 0 14px;
  background: transparent;
  color: var(--color-text-muted);
}

.student-status__toggle-button--active {
  background: var(--color-nav);
  color: var(--color-nav-text);
}

.student-status__download {
  padding: 0 16px;
  background: var(--color-nav);
  color: var(--color-nav-text);
}

.student-status__download:disabled {
  opacity: 0.48;
  cursor: not-allowed;
}

.student-status__chart {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.student-status__chart-column {
  min-width: 0;
  display: grid;
  grid-template-rows: auto minmax(0, 176px) auto;
  gap: 10px;
  justify-items: center;
}

.student-status__value-pill {
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
  color: var(--color-text-primary);
  background: color-mix(in srgb, var(--color-surface) 90%, transparent);
}

.student-status__value-pill--present {
  color: var(--color-status-compliant);
}

.student-status__value-pill--late {
  color: var(--color-status-late);
}

.student-status__value-pill--absent {
  color: var(--color-status-non-compliant);
}

.student-status__value-pill--excused {
  color: var(--color-status-excused);
}

.student-status__bar-track {
  width: 100%;
  min-width: 0;
  height: 176px;
  padding: 8px;
  border-radius: 999px;
  display: flex;
  align-items: flex-end;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--color-surface) 72%, transparent), color-mix(in srgb, var(--color-bg) 32%, var(--color-surface)));
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--color-surface-border) 84%, transparent);
}

.student-status__bar-fill {
  width: 100%;
  border-radius: 999px;
  transition: height 220ms ease;
}

.student-status__bar-fill--present {
  background: linear-gradient(180deg, color-mix(in srgb, var(--color-status-compliant) 76%, white), color-mix(in srgb, var(--color-status-compliant) 54%, white));
}

.student-status__bar-fill--late {
  background: linear-gradient(180deg, color-mix(in srgb, var(--color-status-late) 76%, white), color-mix(in srgb, var(--color-status-late) 56%, white));
}

.student-status__bar-fill--absent {
  background: linear-gradient(180deg, color-mix(in srgb, var(--color-status-non-compliant) 70%, white), color-mix(in srgb, var(--color-status-non-compliant) 54%, white));
}

.student-status__bar-fill--excused {
  background: linear-gradient(180deg, color-mix(in srgb, var(--color-status-excused) 74%, white), color-mix(in srgb, var(--color-status-excused) 54%, white));
}

.student-status__chart-labels {
  display: grid;
  gap: 2px;
  justify-items: center;
  text-align: center;
}

.student-status__chart-labels strong {
  font-size: 12px;
  line-height: 1.15;
  font-weight: 800;
  color: var(--color-text-primary);
}

.student-status__chart-labels span {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-muted);
}

.student-status__table {
  display: grid;
  gap: 10px;
}

.student-status__table-row {
  padding: 14px 16px;
  border-radius: 22px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 12px;
  background: color-mix(in srgb, var(--color-bg) 54%, var(--color-surface));
}

.student-status__table-status {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.student-status__status-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  flex-shrink: 0;
}

.student-status__status-dot--present {
  background: var(--color-status-compliant);
}

.student-status__status-dot--late {
  background: var(--color-status-late);
}

.student-status__status-dot--absent {
  background: var(--color-status-non-compliant);
}

.student-status__status-dot--excused {
  background: var(--color-status-excused);
}

.student-status__table-status strong,
.student-status__table-value {
  font-size: 14px;
  font-weight: 800;
  color: var(--color-text-primary);
}

.student-status__table-share {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-muted);
}

.student-status__empty {
  padding: 18px;
  border-radius: 24px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: color-mix(in srgb, var(--color-bg) 54%, var(--color-surface));
  color: var(--color-text-muted);
}

.student-status__empty strong {
  display: block;
  margin-bottom: 4px;
  color: var(--color-text-primary);
}

.student-status__empty p {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
}

.student-status__stats-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.student-status__stat-card {
  min-height: 148px;
  padding: 16px;
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 16px;
  overflow: hidden;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--color-surface) 98%, transparent), color-mix(in srgb, var(--color-bg) 32%, var(--color-surface)));
  box-shadow:
    inset 0 1px 0 color-mix(in srgb, var(--color-surface-border-strong) 72%, transparent),
    0 12px 28px color-mix(in srgb, var(--color-nav) 6%, transparent);
}

.student-status__stat-card--accent {
  background:
    linear-gradient(
      180deg,
      color-mix(in srgb, var(--color-primary) 76%, white),
      color-mix(in srgb, var(--color-primary) 62%, white)
    );
  box-shadow:
    0 22px 44px color-mix(in srgb, var(--color-primary) 18%, transparent),
    inset 0 1px 0 color-mix(in srgb, white 56%, transparent);
}

.student-status__stat-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.student-status__stat-eyebrow {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.student-status__stat-eyebrow span:last-child {
  min-width: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-size: 12px;
  line-height: 1.12;
  letter-spacing: -0.02em;
  font-weight: 700;
  color: color-mix(in srgb, var(--color-text-primary) 78%, var(--color-text-muted));
}

.student-status__stat-card--accent .student-status__stat-eyebrow span:last-child {
  color: color-mix(in srgb, var(--color-banner-text) 90%, transparent);
}

.student-status__stat-icon {
  width: 42px;
  height: 42px;
  border-radius: 15px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--color-primary) 14%, transparent);
  color: var(--color-primary);
  flex-shrink: 0;
}

.student-status__stat-card--accent .student-status__stat-icon {
  background: color-mix(in srgb, var(--color-banner-text) 12%, transparent);
  color: var(--color-banner-text);
}

.student-status__stat-copy {
  display: grid;
  align-content: end;
}

.student-status__stat-copy strong {
  font-size: clamp(30px, 5.6vw, 40px);
  line-height: 0.92;
  letter-spacing: -0.06em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.student-status__stat-card--accent .student-status__stat-copy strong {
  color: var(--color-banner-text);
}

@media (min-width: 960px) {
  .student-status {
    grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.9fr);
    align-items: start;
  }
}

@media (max-width: 767px) {
  .student-status__summary-head,
  .student-status__summary-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .student-status__summary-actions {
    justify-content: flex-start;
  }

  .student-status__toggle {
    justify-content: space-between;
  }

  .student-status__toggle-button {
    flex: 1 1 0;
  }

  .student-status__download {
    width: 100%;
  }

  .student-status__chart {
    gap: 10px;
  }

  .student-status__chart-column {
    grid-template-rows: auto minmax(0, 152px) auto;
  }

  .student-status__bar-track {
    height: 152px;
  }
}
</style>
