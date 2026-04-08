<template>
  <div class="quick-stats">
    <article
      v-for="stat in stats"
      :key="stat.label"
      class="quick-stat"
    >
      <div class="quick-stat__icon-wrap" :style="{ background: stat.iconBg }">
        <component :is="stat.icon" :size="18" :stroke-width="2.2" :color="stat.iconColor" />
      </div>
      <div class="quick-stat__content">
        <span class="quick-stat__value">{{ stat.value }}</span>
        <span class="quick-stat__label">{{ stat.label }}</span>
      </div>
    </article>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { CalendarDays, CheckCircle2, XCircle, ShieldCheck } from 'lucide-vue-next'

const props = defineProps({
  totalEvents: { type: Number, default: 0 },
  attended: { type: Number, default: 0 },
  missed: { type: Number, default: 0 },
  excused: { type: Number, default: 0 },
})

const stats = computed(() => [
  {
    label: 'Total Events',
    value: props.totalEvents,
    icon: CalendarDays,
    iconBg: 'rgba(99, 102, 241, 0.10)',
    iconColor: '#6366F1',
  },
  {
    label: 'Attended',
    value: props.attended,
    icon: CheckCircle2,
    iconBg: 'rgba(34, 197, 94, 0.10)',
    iconColor: '#22C55E',
  },
  {
    label: 'Missed',
    value: props.missed,
    icon: XCircle,
    iconBg: 'rgba(239, 68, 68, 0.10)',
    iconColor: '#EF4444',
  },
  {
    label: 'Excused',
    value: props.excused,
    icon: ShieldCheck,
    iconBg: 'rgba(249, 115, 22, 0.10)',
    iconColor: '#F97316',
  },
])
</script>

<style scoped>
.quick-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: clamp(10px, 2.5vw, 16px);
}

.quick-stat {
  display: flex;
  align-items: center;
  gap: clamp(10px, 3vw, 14px);
  padding: clamp(14px, 4vw, 20px);
  border-radius: 22px;
  background: var(--color-surface);
  border: 1px solid rgba(10, 10, 10, 0.05);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.quick-stat:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
}

.quick-stat__icon-wrap {
  width: clamp(36px, 10vw, 44px);
  height: clamp(36px, 10vw, 44px);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.quick-stat__content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.quick-stat__value {
  font-size: clamp(22px, 6vw, 28px);
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1;
  color: var(--color-surface-text);
}

.quick-stat__label {
  font-size: clamp(11px, 3vw, 13px);
  font-weight: 500;
  color: var(--color-surface-text-muted);
  white-space: nowrap;
}

@media (max-width: 767px) {
  .quick-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
