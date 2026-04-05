<template>
  <RouterView v-slot="{ Component, route }">
    <Suspense timeout="0">
      <template #default>
        <Transition name="page-fade" mode="out-in">
          <component :is="Component" :key="route.fullPath" />
        </Transition>
      </template>

      <template #fallback>
        <div class="app-layout-outlet__boot-wrapper">
          <AppBootLoader />
        </div>
      </template>
    </Suspense>
  </RouterView>
</template>

<script setup>
import { RouterView } from 'vue-router'
import AppBootLoader from '@/components/ui/AppBootLoader.vue'
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

.app-layout-outlet__boot-wrapper {
  display: flex;
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: var(--color-surface, #ffffff);
}
</style>

