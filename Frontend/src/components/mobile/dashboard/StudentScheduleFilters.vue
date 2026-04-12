<template>
  <div class="student-schedule-filters" aria-label="Event status filters">
    <button
      v-for="filter in filters"
      :key="filter.id"
      type="button"
      class="student-schedule-filters__button"
      :class="{ 'student-schedule-filters__button--active': modelValue === filter.id }"
      :aria-pressed="modelValue === filter.id ? 'true' : 'false'"
      @click="$emit('update:modelValue', filter.id)"
    >
      {{ filter.label }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  filters: {
    type: Array,
    default: () => [],
  },
  modelValue: {
    type: String,
    default: 'all',
  },
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.student-schedule-filters {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  width: 100%;
  padding: 0 2px 2px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.student-schedule-filters::-webkit-scrollbar {
  display: none;
}

.student-schedule-filters__button {
  flex: 0 0 auto;
  padding: 0 24px;
  min-height: 50px;
  border: 1px solid transparent;
  border-radius: 999px;
  background: var(--color-surface);
  color: var(--color-text-always-dark);
  font-family: 'Manrope', sans-serif;
  font-size: 14px;
  font-weight: 500;
  line-height: 1;
  white-space: nowrap;
  transition: transform 180ms ease, background-color 180ms ease, color 180ms ease;
}

.student-schedule-filters__button:active {
  transform: scale(0.97);
}

.student-schedule-filters__button--active {
  background: var(--color-pill-row-active-bg, var(--color-secondary));
  color: var(--color-pill-row-active-text, var(--color-secondary-text));
  font-weight: 500;
}
</style>
