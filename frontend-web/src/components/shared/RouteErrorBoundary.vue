<template>
  <slot v-if="!errorMessage" />

  <section v-else class="route-error-boundary" role="alert" aria-live="assertive">
    <div class="route-error-boundary__panel">
      <p class="route-error-boundary__eyebrow">Screen error</p>
      <h1 class="route-error-boundary__title">This page could not render.</h1>
      <p class="route-error-boundary__message">{{ errorMessage }}</p>
      <div class="route-error-boundary__actions">
        <button class="route-error-boundary__button route-error-boundary__button--primary" type="button" @click="retry">
          Try again
        </button>
        <button class="route-error-boundary__button" type="button" @click="goHome">
          Go back
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onErrorCaptured, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { isChunkLoadError, attemptChunkRecovery } from '@/services/appBootstrap.js'

const route = useRoute()
const router = useRouter()
const errorMessage = ref('')

function normalizeErrorMessage(error) {
  return String(error?.message || error || 'Unexpected render error.').trim() || 'Unexpected render error.'
}

onErrorCaptured((error, instance, info) => {
  if (isChunkLoadError(error)) {
    attemptChunkRecovery(route.fullPath)
    return false
  }

  const componentName = instance?.type?.__name || instance?.type?.name || 'unknown component'
  const message = normalizeErrorMessage(error)
  console.error('Aura route render error', {
    component: componentName,
    message,
    info: String(info || ''),
    route: route.fullPath,
  })
  errorMessage.value = message
  return false
})

watch(
  () => route.fullPath,
  () => {
    errorMessage.value = ''
  }
)

function retry() {
  errorMessage.value = ''
}

function resolveFallbackPath() {
  if (route.path.startsWith('/governance')) return '/governance'
  if (route.path.startsWith('/workspace')) return '/workspace'
  if (route.path.startsWith('/admin')) return '/admin'
  if (route.path.startsWith('/exposed/governance')) return '/exposed/governance'
  if (route.path.startsWith('/exposed/workspace')) return '/exposed/workspace'
  if (route.path.startsWith('/exposed/dashboard')) return '/exposed/dashboard'
  return '/dashboard'
}

function goHome() {
  router.push(resolveFallbackPath()).catch(() => null)
}
</script>

<style scoped>
.route-error-boundary {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: var(--color-bg);
  color: var(--color-text-primary);
}

.route-error-boundary__panel {
  width: min(100%, 420px);
  display: grid;
  gap: 12px;
  padding: 24px;
  border-radius: 8px;
  border: 1px solid color-mix(in srgb, var(--color-surface-border) 88%, transparent);
  background: var(--color-surface);
  color: var(--color-surface-text);
  box-shadow: 0 18px 42px color-mix(in srgb, var(--color-nav) 10%, transparent);
}

.route-error-boundary__eyebrow {
  margin: 0;
  color: var(--color-surface-text-muted);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.route-error-boundary__title {
  margin: 0;
  color: var(--color-surface-text);
  font-size: 24px;
  line-height: 1.12;
  font-weight: 800;
}

.route-error-boundary__message {
  margin: 0;
  color: var(--color-surface-text-secondary);
  font-size: 14px;
  line-height: 1.55;
}

.route-error-boundary__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 6px;
}

.route-error-boundary__button {
  min-height: 42px;
  padding: 0 16px;
  border: none;
  border-radius: 8px;
  background: color-mix(in srgb, var(--color-bg) 48%, var(--color-surface));
  color: var(--color-surface-text);
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
}

.route-error-boundary__button--primary {
  background: var(--color-primary);
  color: var(--color-banner-text);
}
</style>
