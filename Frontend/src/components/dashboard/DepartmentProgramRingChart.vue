<template>
  <div class="department-program-ring">
    <svg
      class="department-program-ring__svg"
      viewBox="0 0 220 220"
      aria-hidden="true"
    >
      <circle
        class="department-program-ring__track"
        cx="110"
        cy="110"
        :r="radius"
      />

      <g :transform="`rotate(${startAngle} 110 110)`">
        <circle
          v-for="segment in renderedSegments"
          :key="segment.id"
          class="department-program-ring__segment"
          :class="{
            'department-program-ring__segment--inactive': segment.id !== displayItem?.id,
          }"
          cx="110"
          cy="110"
          :r="radius"
          :stroke-dasharray="segment.dasharray"
          :stroke-dashoffset="segment.dashoffset"
          :style="{ stroke: segment.color }"
          @click="selectSegment(segment.id)"
        />
      </g>
    </svg>

    <div class="department-program-ring__center">
      <span class="department-program-ring__percentage">{{ percentageLabel }}</span>
      <span class="department-program-ring__label">{{ displayLabel }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [Number, String],
    default: null,
  },
  items: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update:modelValue'])

const radius = 72
const strokeWidth = 24
const startAngle = -58
const gapDegrees = 7
const circumference = 2 * Math.PI * radius

const normalizedItems = computed(() => (
  Array.isArray(props.items)
    ? props.items
      .filter((item) => item && item.id != null)
      .map((item) => ({
        ...item,
        percentage: normalizePercentage(item.percentage),
      }))
    : []
))

const displayItem = computed(() => (
  normalizedItems.value.find((item) => String(item.id) === String(props.modelValue))
  || normalizedItems.value[0]
  || null
))

const percentageLabel = computed(() => `${Math.round(displayItem.value?.percentage || 0)}%`)
const displayLabel = computed(() => displayItem.value?.shortLabel || 'No Data')

const renderedSegments = computed(() => {
  const rankedItems = normalizedItems.value
    .filter((item) => item.percentage > 0)
    .sort((left, right) => left.percentage - right.percentage)

  if (!rankedItems.length) return []

  if (rankedItems.length === 1) {
    const onlyItem = rankedItems[0]
    const segmentLength = circumference * (onlyItem.percentage / 100)
    return [{
      ...onlyItem,
      dasharray: `${segmentLength} ${Math.max(circumference - segmentLength, 0)}`,
      dashoffset: 0,
    }]
  }

  const gapLength = circumference * gapDegrees / 360
  const totalGapLength = rankedItems.length * gapLength
  const availableLength = Math.max(circumference - totalGapLength, 0)

  let offset = 0
  return rankedItems.map((item) => {
    const segmentLength = Math.max(availableLength * (item.percentage / 100), 0)
    const safeLength = Number.isFinite(segmentLength) ? segmentLength : 0
    const segment = {
      ...item,
      dasharray: `${safeLength} ${Math.max(circumference - safeLength, 0)}`,
      dashoffset: -offset,
    }

    offset += safeLength + gapLength
    return segment
  })
})

function normalizePercentage(value) {
  const normalized = Number(value)
  if (!Number.isFinite(normalized)) return 0
  return Math.max(0, Math.min(100, normalized))
}

function selectSegment(segmentId) {
  emit('update:modelValue', segmentId)
}
</script>

<style scoped>
.department-program-ring {
  position: relative;
  width: clamp(132px, 34vw, 170px);
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.department-program-ring__svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}

.department-program-ring__track,
.department-program-ring__segment {
  fill: none;
  stroke-width: 24;
}

.department-program-ring__track {
  stroke: rgba(255, 255, 255, 0.28);
}

.department-program-ring__segment {
  stroke-linecap: round;
  cursor: pointer;
  transition: opacity 220ms ease, transform 220ms ease, filter 240ms ease;
  transform-origin: 110px 110px;
}

.department-program-ring__segment--inactive {
  opacity: 0.74;
}

.department-program-ring__segment:not(.department-program-ring__segment--inactive) {
  filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.08));
}

.department-program-ring__center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  pointer-events: none;
  text-align: center;
}

.department-program-ring__percentage {
  font-size: clamp(22px, 6vw, 40px);
  line-height: 0.92;
  letter-spacing: -0.06em;
  font-weight: 700;
  color: var(--color-text-always-dark);
}

.department-program-ring__label {
  max-width: 72px;
  font-size: clamp(10px, 2.8vw, 12px);
  line-height: 1.05;
  font-weight: 700;
  color: var(--color-text-always-dark);
}

@media (prefers-reduced-motion: reduce) {
  .department-program-ring__segment {
    transition: none;
  }
}
</style>
