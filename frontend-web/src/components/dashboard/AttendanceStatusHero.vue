<template>
  <div class="attendance-hero">
    <div class="attendance-hero__chart-wrap">
      <!-- SVG Donut Ring -->
      <svg
        class="attendance-hero__svg"
        viewBox="0 0 200 200"
        role="img"
        aria-label="Attendance donut chart"
      >
        <!-- Track ring -->
        <circle
          class="attendance-hero__track"
          cx="100"
          cy="100"
          :r="radius"
          fill="none"
          :stroke-width="strokeWidth"
        />
        <!-- Excused segment -->
        <circle
          v-if="excusedDash > 0"
          class="attendance-hero__segment attendance-hero__segment--excused"
          cx="100"
          cy="100"
          :r="radius"
          fill="none"
          :stroke-width="strokeWidth"
          :stroke-dasharray="`${excusedDash} ${circumference - excusedDash}`"
          :stroke-dashoffset="excusedOffset"
          stroke-linecap="round"
        />
        <!-- Missed segment -->
        <circle
          v-if="missedDash > 0"
          class="attendance-hero__segment attendance-hero__segment--missed"
          cx="100"
          cy="100"
          :r="radius"
          fill="none"
          :stroke-width="strokeWidth"
          :stroke-dasharray="`${missedDash} ${circumference - missedDash}`"
          :stroke-dashoffset="missedOffset"
          stroke-linecap="round"
        />
        <!-- Attended segment (on top) -->
        <circle
          v-if="attendedDash > 0"
          class="attendance-hero__segment attendance-hero__segment--attended"
          cx="100"
          cy="100"
          :r="radius"
          fill="none"
          :stroke-width="strokeWidth"
          :stroke-dasharray="`${attendedDash} ${circumference - attendedDash}`"
          :stroke-dashoffset="attendedOffset"
          stroke-linecap="round"
        />
      </svg>

      <!-- Center content -->
      <div class="attendance-hero__center">
        <span class="attendance-hero__percent">{{ attendanceRate }}</span>
        <span class="attendance-hero__percent-sign">%</span>
      </div>
    </div>

    <!-- Compliance badge + legend -->
    <div class="attendance-hero__info">
      <div
        class="attendance-hero__badge"
        :class="`attendance-hero__badge--${complianceKey}`"
      >
        <span class="attendance-hero__badge-dot" />
        {{ complianceLabel }}
      </div>

      <p class="attendance-hero__subtitle">
        Attendance compliance standing
      </p>

      <!-- Legend -->
      <div class="attendance-hero__legend">
        <div class="attendance-hero__legend-item">
          <span class="attendance-hero__legend-dot attendance-hero__legend-dot--attended" />
          <span>Attended <strong>{{ attended }}</strong></span>
        </div>
        <div class="attendance-hero__legend-item">
          <span class="attendance-hero__legend-dot attendance-hero__legend-dot--missed" />
          <span>Missed <strong>{{ missed }}</strong></span>
        </div>
        <div class="attendance-hero__legend-item">
          <span class="attendance-hero__legend-dot attendance-hero__legend-dot--excused" />
          <span>Excused <strong>{{ excused }}</strong></span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  attended: { type: Number, default: 0 },
  missed: { type: Number, default: 0 },
  excused: { type: Number, default: 0 },
})

const radius = 78
const strokeWidth = 18
const circumference = 2 * Math.PI * radius
const gapSize = 4

const total = computed(() => props.attended + props.missed + props.excused)
const attendanceRate = computed(() => {
  const denominator = props.attended + props.missed
  if (denominator <= 0) return 0
  return Math.round((props.attended / denominator) * 100)
})

const complianceKey = computed(() => {
  const rate = attendanceRate.value
  if (rate >= 80) return 'compliant'
  if (rate >= 60) return 'at-risk'
  return 'non-compliant'
})

const complianceLabel = computed(() => {
  const map = { compliant: 'Compliant', 'at-risk': 'At Risk', 'non-compliant': 'Non-Compliant' }
  return map[complianceKey.value]
})

// Segment calculations — each segment is a fraction of circumference
const attendedFraction = computed(() => (total.value > 0 ? props.attended / total.value : 0))
const missedFraction = computed(() => (total.value > 0 ? props.missed / total.value : 0))
const excusedFraction = computed(() => (total.value > 0 ? props.excused / total.value : 0))

const segmentGap = computed(() => {
  const activeSegments = [attendedFraction.value, missedFraction.value, excusedFraction.value].filter((f) => f > 0).length
  return activeSegments > 1 ? gapSize : 0
})

const attendedDash = computed(() => Math.max(0, attendedFraction.value * circumference - segmentGap.value))
const missedDash = computed(() => Math.max(0, missedFraction.value * circumference - segmentGap.value))
const excusedDash = computed(() => Math.max(0, excusedFraction.value * circumference - segmentGap.value))

// Offsets — rotate each segment to start where the previous one ends
// Start from top (-90 degrees = circumference / 4 offset)
const baseOffset = circumference / 4
const attendedOffset = computed(() => baseOffset)
const missedOffset = computed(() => baseOffset - (attendedFraction.value * circumference))
const excusedOffset = computed(() => baseOffset - ((attendedFraction.value + missedFraction.value) * circumference))
</script>

<style scoped>
.attendance-hero {
  display: flex;
  align-items: center;
  gap: clamp(24px, 6vw, 40px);
  padding: clamp(24px, 5vw, 36px);
  border-radius: 28px;
  background: var(--color-surface);
  border: 1px solid rgba(10, 10, 10, 0.05);
}

.attendance-hero__chart-wrap {
  position: relative;
  width: clamp(150px, 38vw, 200px);
  height: clamp(150px, 38vw, 200px);
  flex-shrink: 0;
}

.attendance-hero__svg {
  width: 100%;
  height: 100%;
  transform: rotate(0deg);
  overflow: visible;
}

.attendance-hero__track {
  stroke: rgba(10, 10, 10, 0.06);
}

.attendance-hero__segment {
  transition: stroke-dasharray 1s cubic-bezier(0.22, 1, 0.36, 1),
              stroke-dashoffset 1s cubic-bezier(0.22, 1, 0.36, 1);
  animation: hero-ring-draw 1.2s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.attendance-hero__segment--attended {
  stroke: var(--color-status-compliant);
}

.attendance-hero__segment--missed {
  stroke: var(--color-status-non-compliant);
}

.attendance-hero__segment--excused {
  stroke: var(--color-status-excused);
}

@keyframes hero-ring-draw {
  0% {
    stroke-dashoffset: 490;
    opacity: 0;
  }
  30% {
    opacity: 1;
  }
  100% {
    opacity: 1;
  }
}

.attendance-hero__center {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

.attendance-hero__percent {
  font-size: clamp(36px, 10vw, 52px);
  font-weight: 800;
  letter-spacing: -0.06em;
  line-height: 1;
  color: var(--color-surface-text);
}

.attendance-hero__percent-sign {
  font-size: clamp(18px, 5vw, 24px);
  font-weight: 700;
  color: var(--color-surface-text-muted);
  align-self: flex-start;
  margin-top: clamp(8px, 2vw, 14px);
}

.attendance-hero__info {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

.attendance-hero__badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 800;
  letter-spacing: -0.01em;
  align-self: flex-start;
}

.attendance-hero__badge--compliant {
  background: rgba(34, 197, 94, 0.12);
  color: #15803D;
}

.attendance-hero__badge--at-risk {
  background: rgba(245, 158, 11, 0.14);
  color: #92400E;
}

.attendance-hero__badge--non-compliant {
  background: rgba(239, 68, 68, 0.12);
  color: #B91C1C;
}

.attendance-hero__badge-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  animation: badge-pulse 2s ease-in-out infinite;
}

@keyframes badge-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(0.85); }
}

.attendance-hero__subtitle {
  margin: 0;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-surface-text-muted);
}

.attendance-hero__legend {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 4px;
}

.attendance-hero__legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-surface-text-secondary);
}

.attendance-hero__legend-item strong {
  font-weight: 800;
  color: var(--color-surface-text);
}

.attendance-hero__legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.attendance-hero__legend-dot--attended {
  background: var(--color-status-compliant);
}

.attendance-hero__legend-dot--missed {
  background: var(--color-status-non-compliant);
}

.attendance-hero__legend-dot--excused {
  background: var(--color-status-excused);
}

/* Mobile: stack vertically */
@media (max-width: 520px) {
  .attendance-hero {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .attendance-hero__info {
    align-items: center;
  }

  .attendance-hero__legend {
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: center;
    gap: 12px;
  }
}
</style>
