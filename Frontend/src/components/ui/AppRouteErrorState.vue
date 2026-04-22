<template>
  <section class="app-route-error-state" role="alert" aria-live="assertive">
    <div class="app-route-error-state__card">
      <p class="app-route-error-state__eyebrow">Screen unavailable</p>
      <h2 class="app-route-error-state__title">This view could not be loaded.</h2>
      <p class="app-route-error-state__message">
        {{ resolvedMessage }}
      </p>
      <div class="app-route-error-state__actions">
        <button type="button" class="app-route-error-state__button app-route-error-state__button--primary" @click="reloadApp">
          Reload app
        </button>
        <button type="button" class="app-route-error-state__button" @click="goBack">
          Go back
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  error: {
    type: Object,
    default: null,
  },
  viewLabel: {
    type: String,
    default: 'screen',
  },
})

const resolvedMessage = computed(() => {
  const rawMessage = String(props.error?.message || '').trim()
  if (rawMessage) {
    return rawMessage
  }

  return `Aura could not finish loading the ${props.viewLabel}.`
})

function reloadApp() {
  window.location.reload()
}

function goBack() {
  if (window.history.length > 1) {
    window.history.back()
    return
  }

  window.location.assign('/')
}
</script>

<style scoped>
.app-route-error-state {
  min-height: 100dvh;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at top, rgba(10, 10, 10, 0.08), transparent 45%),
    linear-gradient(180deg, #f7f7f5 0%, #ffffff 100%);
}

.app-route-error-state__card {
  width: min(100%, 420px);
  border-radius: 28px;
  padding: 28px 24px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(10, 10, 10, 0.08);
  box-shadow: 0 22px 60px rgba(10, 10, 10, 0.08);
  text-align: center;
  font-family: 'Manrope', sans-serif;
}

.app-route-error-state__eyebrow {
  margin: 0;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(10, 10, 10, 0.48);
}

.app-route-error-state__title {
  margin: 12px 0 0;
  font-size: 26px;
  line-height: 1.1;
  font-weight: 800;
  color: #0a0a0a;
}

.app-route-error-state__message {
  margin: 12px 0 0;
  font-size: 14px;
  line-height: 1.6;
  color: rgba(10, 10, 10, 0.68);
}

.app-route-error-state__actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 22px;
}

.app-route-error-state__button {
  min-width: 132px;
  border: none;
  border-radius: 999px;
  padding: 12px 18px;
  background: rgba(10, 10, 10, 0.08);
  color: #0a0a0a;
  font-family: 'Manrope', sans-serif;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.app-route-error-state__button--primary {
  background: var(--color-primary, #0a0a0a);
  color: var(--color-primary-text, #ffffff);
}
</style>
