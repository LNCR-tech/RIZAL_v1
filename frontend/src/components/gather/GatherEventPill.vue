<template>
  <button
    type="button"
    class="gather-event-pill"
    :class="[
      active ? 'gather-event-pill--active' : '',
      `gather-event-pill--${tone}`,
    ]"
    @click="$emit('select')"
  >
    <span
      v-if="active"
      class="gather-event-pill__shine"
      aria-hidden="true"
    />

    <span class="gather-event-pill__header">
      <span class="gather-event-pill__title">{{ title }}</span>
      <span class="gather-event-pill__time">{{ timeLabel }}</span>
    </span>

    <span class="gather-event-pill__footer">
      <span class="gather-event-pill__meta">{{ metaLabel }}</span>
      <span class="gather-event-pill__status">{{ statusLabel }}</span>
    </span>
  </button>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: 'Untitled Event',
  },
  metaLabel: {
    type: String,
    default: 'Location unavailable',
  },
  timeLabel: {
    type: String,
    default: '',
  },
  statusLabel: {
    type: String,
    default: '',
  },
  active: {
    type: Boolean,
    default: false,
  },
  tone: {
    type: String,
    default: 'muted',
  },
})

defineEmits(['select'])
</script>

<style scoped>
.gather-event-pill {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  flex-shrink: 0;
  width: min(78vw, 238px);
  min-height: 76px;
  padding: 14px 18px 13px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--color-nav-glass-border) 78%, transparent);
  background:
    linear-gradient(180deg, rgba(8, 8, 8, 0.58) 0%, rgba(8, 8, 8, 0.4) 100%),
    var(--color-nav-glass-bg);
  color: rgba(255, 255, 255, 0.96);
  display: flex;
  flex-direction: column;
  gap: 6px;
  text-align: left;
  box-shadow:
    0 12px 24px rgba(0, 0, 0, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
  -webkit-backdrop-filter: blur(22px) saturate(155%);
  backdrop-filter: blur(22px) saturate(155%);
  cursor: pointer;
  appearance: none;
  transition:
    transform 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease,
    background-color 180ms ease;
}

.gather-event-pill:active {
  transform: scale(0.98);
}

.gather-event-pill__shine {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(108deg, rgba(255, 255, 255, 0.18) 0%, rgba(255, 255, 255, 0.04) 20%, rgba(255, 255, 255, 0) 42%, rgba(255, 255, 255, 0.12) 82%, rgba(255, 255, 255, 0.22) 100%);
  opacity: 0.88;
  pointer-events: none;
}

.gather-event-pill__header,
.gather-event-pill__footer {
  position: relative;
  z-index: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.gather-event-pill__title,
.gather-event-pill__meta,
.gather-event-pill__status {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.gather-event-pill__title {
  font-size: 14px;
  line-height: 1.1;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.gather-event-pill__time {
  flex-shrink: 0;
  font-size: 11px;
  line-height: 1;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.gather-event-pill__footer {
  color: rgba(255, 255, 255, 0.64);
}

.gather-event-pill__meta {
  font-size: 11px;
  line-height: 1.1;
  font-weight: 600;
}

.gather-event-pill__status {
  flex-shrink: 0;
  font-size: 10px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.gather-event-pill--active {
  border-color: color-mix(in srgb, var(--color-nav-active) 82%, white 18%);
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--color-nav-active) 92%, rgba(0, 0, 0, 0.08)) 0%, color-mix(in srgb, var(--color-nav-active) 84%, rgba(0, 0, 0, 0.18)) 100%);
  color: var(--color-text-always-dark);
  box-shadow:
    0 0 26px color-mix(in srgb, var(--color-nav-active) 34%, transparent),
    0 14px 28px rgba(0, 0, 0, 0.26),
    inset 0 1px 0 rgba(255, 255, 255, 0.24);
}

.gather-event-pill--active .gather-event-pill__footer,
.gather-event-pill--active .gather-event-pill__time {
  color: color-mix(in srgb, var(--color-text-always-dark) 68%, transparent);
}

.gather-event-pill--ready:not(.gather-event-pill--active) .gather-event-pill__time,
.gather-event-pill--ready:not(.gather-event-pill--active) .gather-event-pill__status {
  color: color-mix(in srgb, var(--color-nav-active) 92%, white 8%);
}

.gather-event-pill--pending:not(.gather-event-pill--active) .gather-event-pill__time,
.gather-event-pill--pending:not(.gather-event-pill--active) .gather-event-pill__status {
  color: rgba(255, 255, 255, 0.78);
}

.gather-event-pill--done:not(.gather-event-pill--active) .gather-event-pill__time,
.gather-event-pill--done:not(.gather-event-pill--active) .gather-event-pill__status {
  color: rgba(255, 255, 255, 0.52);
}

.gather-event-pill--error:not(.gather-event-pill--active) .gather-event-pill__time,
.gather-event-pill--error:not(.gather-event-pill--active) .gather-event-pill__status {
  color: #ffb2aa;
}
</style>
