<template>
  <main class="not-found-view">
    <section class="not-found-view__panel">
      <p class="not-found-view__eyebrow">Not found</p>
      <h1 class="not-found-view__title">This page does not exist.</h1>
      <p class="not-found-view__message">
        The route may have changed, or the link may be incomplete.
      </p>
      <div class="not-found-view__actions">
        <button class="not-found-view__button not-found-view__button--primary" type="button" @click="goBack">
          Go back
        </button>
        <button class="not-found-view__button" type="button" @click="goHome">
          Go home
        </button>
      </div>
    </section>
  </main>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { hasNavigableHistory } from '@/services/routeWorkspace.js'

const route = useRoute()
const router = useRouter()

function goBack() {
  if (hasNavigableHistory(route)) {
    router.back()
    return
  }

  goHome()
}

function resolveHomePath() {
  if (route.path.startsWith('/exposed/governance')) return '/exposed/governance'
  if (route.path.startsWith('/exposed/workspace')) return '/exposed/workspace'
  if (route.path.startsWith('/exposed/dashboard')) return '/exposed/dashboard'
  if (route.path.startsWith('/governance')) return '/governance'
  if (route.path.startsWith('/workspace')) return '/workspace'
  if (route.path.startsWith('/admin')) return '/admin'
  return '/dashboard'
}

function goHome() {
  router.push(resolveHomePath()).catch(() => null)
}
</script>

<style scoped>
.not-found-view {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: var(--color-bg);
  color: var(--color-text-primary);
  font-family: 'Manrope', sans-serif;
}

.not-found-view__panel {
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

.not-found-view__eyebrow {
  margin: 0;
  color: var(--color-surface-text-muted);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.not-found-view__title {
  margin: 0;
  color: var(--color-surface-text);
  font-size: 24px;
  line-height: 1.12;
  font-weight: 800;
}

.not-found-view__message {
  margin: 0;
  color: var(--color-surface-text-secondary);
  font-size: 14px;
  line-height: 1.55;
}

.not-found-view__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 6px;
}

.not-found-view__button {
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

.not-found-view__button--primary {
  background: var(--color-primary);
  color: var(--color-banner-text);
}
</style>
