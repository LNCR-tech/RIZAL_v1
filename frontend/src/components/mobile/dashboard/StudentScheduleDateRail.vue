<template>
  <div ref="railRef" class="student-date-rail" aria-label="Event dates">
    <div
      v-for="(page, pageIndex) in weekPages"
      :key="page.key"
      class="student-date-rail__page"
      :class="{ 'student-date-rail__page--current': pageIndex === initialWeekIndex }"
    >
      <button
        v-for="day in page.days"
        :key="day.key"
        type="button"
        class="student-date-rail__day"
        :class="{
          'student-date-rail__day--selected': modelValue === day.key,
          'student-date-rail__day--today': day.isToday && modelValue !== day.key,
        }"
        :aria-pressed="modelValue === day.key ? 'true' : 'false'"
        @click="$emit('update:modelValue', day.key)"
      >
        <span class="student-date-rail__weekday">{{ day.label }}</span>
        <span class="student-date-rail__number">{{ day.dayNumber }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref, watch } from 'vue'

const props = defineProps({
  weekPages: {
    type: Array,
    default: () => [],
  },
  modelValue: {
    type: String,
    default: '',
  },
  initialWeekIndex: {
    type: Number,
    default: 0,
  },
})

defineEmits(['update:modelValue'])

const railRef = ref(null)

async function scrollToInitialWeek() {
  await nextTick()

  const container = railRef.value
  if (!container) return

  const targetPage = container.children[props.initialWeekIndex]
  if (!targetPage) return

  container.scrollLeft = targetPage.offsetLeft
}

onMounted(() => {
  void scrollToInitialWeek()
})

watch(
  () => `${props.weekPages.length}:${props.initialWeekIndex}`,
  () => {
    void scrollToInitialWeek()
  }
)
</script>

<style scoped>
.student-date-rail {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.student-date-rail::-webkit-scrollbar {
  display: none;
}

.student-date-rail__page {
  min-width: 100%;
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 10px;
  scroll-snap-align: start;
}

.student-date-rail__day {
  padding: 0;
  min-height: 88px;
  border: 1px solid transparent;
  border-radius: 24px;
  background: var(--color-surface);
  color: var(--color-text-always-dark);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-family: 'Manrope', sans-serif;
  transition: transform 180ms ease, border-color 180ms ease, background-color 180ms ease;
}

.student-date-rail__day:active {
  transform: scale(0.97);
}

.student-date-rail__day--selected {
  background: var(--color-primary);
  color: var(--color-banner-text);
}

.student-date-rail__day--today {
  border-color: color-mix(in srgb, var(--color-primary) 40%, transparent);
}

.student-date-rail__weekday {
  font-size: 11px;
  line-height: 1.1;
  font-weight: 500;
  letter-spacing: -0.01em;
}

.student-date-rail__number {
  font-size: 31px;
  line-height: 0.95;
  font-weight: 500;
  letter-spacing: -0.04em;
}
</style>
