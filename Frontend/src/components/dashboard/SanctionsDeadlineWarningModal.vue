<template>
  <Transition name="sanctions-warning">
    <div v-if="open" class="sanctions-warning" role="dialog" aria-modal="true" aria-labelledby="sanctions-warning-title">
      <div class="sanctions-warning__backdrop" @click="emit('dismiss')" />
      <div class="sanctions-warning__card">
        <p class="sanctions-warning__eyebrow">Clearance Notice</p>
        <h2 id="sanctions-warning-title" class="sanctions-warning__title">Active Clearance Deadline</h2>
        <p class="sanctions-warning__copy">
          You currently have
          <strong>{{ pendingCount }}</strong>
          pending sanction{{ pendingCount === 1 ? '' : 's' }}.
          Deadline:
          <strong>{{ formatDeadline(deadline?.deadline_at) }}</strong>.
        </p>
        <button class="sanctions-warning__action" type="button" @click="emit('dismiss')">
          View My Sanctions
        </button>
      </div>
    </div>
  </Transition>
</template>

<script setup>
const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  pendingCount: {
    type: Number,
    default: 0,
  },
  deadline: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['dismiss'])

function formatDeadline(value) {
  const parsed = new Date(value || '')
  if (Number.isNaN(parsed.getTime())) return 'TBA'
  return parsed.toLocaleString('en-PH', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}
</script>

<style scoped>
.sanctions-warning {
  position: fixed;
  inset: 0;
  z-index: 10950;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.sanctions-warning__backdrop {
  position: absolute;
  inset: 0;
  background: rgba(10, 10, 10, 0.48);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.sanctions-warning__card {
  position: relative;
  width: min(100%, 420px);
  border-radius: 22px;
  padding: 22px 20px;
  background: var(--color-surface, #ffffff);
  box-shadow: 0 22px 48px rgba(0, 0, 0, 0.24);
  display: grid;
  gap: 10px;
  font-family: 'Manrope', sans-serif;
}

.sanctions-warning__eyebrow {
  margin: 0;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #b45309;
}

.sanctions-warning__title {
  margin: 0;
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--color-text-primary, #0a0a0a);
}

.sanctions-warning__copy {
  margin: 0;
  font-size: 14px;
  line-height: 1.55;
  color: var(--color-text-secondary, #4b5563);
}

.sanctions-warning__copy strong {
  color: var(--color-text-primary, #111827);
}

.sanctions-warning__action {
  margin-top: 4px;
  min-height: 44px;
  border: none;
  border-radius: 999px;
  background: var(--color-primary, #0a0a0a);
  color: var(--color-banner-text, #ffffff);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.sanctions-warning-enter-active,
.sanctions-warning-leave-active {
  transition: opacity 0.2s ease;
}

.sanctions-warning-enter-from,
.sanctions-warning-leave-to {
  opacity: 0;
}
</style>
