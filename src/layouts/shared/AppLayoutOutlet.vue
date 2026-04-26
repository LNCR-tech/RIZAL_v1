<template>
  <RouterView v-slot="{ Component, route }">
    <Suspense timeout="0">
      <template #default>
        <Transition name="page-fade" mode="out-in">
          <component :is="Component" :key="resolveRouteViewKey(route, Component)" />
        </Transition>
      </template>

      <template #fallback>
        <div class="app-layout-outlet__fallback" aria-live="polite" aria-busy="true">
          <div class="app-layout-outlet__fallback-card">
            <span class="app-layout-outlet__fallback-pulse" aria-hidden="true" />

            <div class="app-layout-outlet__fallback-copy">
              <strong class="app-layout-outlet__fallback-title">Loading workspace</strong>
              <span class="app-layout-outlet__fallback-subtitle">Preparing the next screen.</span>
            </div>
          </div>
        </div>
      </template>
    </Suspense>
  </RouterView>
</template>

<script setup>
import { RouterView } from 'vue-router'

function resolveRouteViewKey(route, component) {
  const matchedRecords = Array.isArray(route?.matched) ? route.matched : []
  const contextKey = [...matchedRecords]
    .reverse()
    .map((record) => record?.meta?.workspaceContext || record?.meta?.primaryNavContext || '')
    .find(Boolean)

  const matchedComponent = matchedRecords[matchedRecords.length - 1]?.components?.default
  const componentKey = (
    matchedComponent?.name
    || matchedComponent?.__name
    || component?.name
    || component?.__name
    || route?.name
    || route?.path
    || 'route-view'
  )

  return [contextKey, componentKey].filter(Boolean).join(':')
}
</script>

<style scoped>
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.26s cubic-bezier(0.22, 1, 0.36, 1);
  will-change: opacity, transform;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(12px) scale(0.985);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.995);
}

.app-layout-outlet__fallback {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background:
    radial-gradient(circle at top, rgba(170, 255, 0, 0.12), transparent 30%),
    rgba(5, 5, 5, 0.78);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}

.app-layout-outlet__fallback-card {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  min-width: min(100%, 272px);
  padding: 16px 18px;
  border-radius: 999px;
  background: rgba(20, 20, 20, 0.82);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.28);
  color: rgba(255, 255, 255, 0.96);
}

.app-layout-outlet__fallback-pulse {
  width: 12px;
  height: 12px;
  flex: 0 0 12px;
  border-radius: 999px;
  background: #aaff00;
  box-shadow: 0 0 0 0 rgba(170, 255, 0, 0.42);
  animation: app-layout-outlet-pulse 1.4s ease-out infinite;
}

.app-layout-outlet__fallback-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.app-layout-outlet__fallback-title {
  font-size: 14px;
  font-weight: 700;
  line-height: 1.2;
}

.app-layout-outlet__fallback-subtitle {
  font-size: 12px;
  line-height: 1.35;
  color: rgba(255, 255, 255, 0.64);
}

@keyframes app-layout-outlet-pulse {
  0% {
    transform: scale(0.92);
    box-shadow: 0 0 0 0 rgba(170, 255, 0, 0.42);
  }

  70% {
    transform: scale(1);
    box-shadow: 0 0 0 14px rgba(170, 255, 0, 0);
  }

  100% {
    transform: scale(0.92);
    box-shadow: 0 0 0 0 rgba(170, 255, 0, 0);
  }
}
</style>
