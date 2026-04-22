<template>
  <RouterView v-slot="{ Component, route }">
    <Suspense timeout="0">
      <template #default>
        <Transition name="page-fade" mode="out-in">
          <component :is="Component" :key="route.name" />
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
  transition: opacity 0.1s ease;
  will-change: opacity;
}

.page-fade-enter-from {
  opacity: 0;
}

.page-fade-leave-to {
  opacity: 0;
}

.app-layout-outlet__boot-wrapper {
  display: flex;
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: var(--color-surface, #ffffff);
}
</style>

