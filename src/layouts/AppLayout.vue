<template>
  <!-- Shared layout for all student dashboard pages -->
  <div class="min-h-screen" style="background: var(--color-bg); font-family: 'Manrope', sans-serif;">
    <!-- Desktop Sidebar (left) -->
    <SideNav />

    <!-- Main content area -->
    <main
      class="min-h-screen"
      :class="[
        'md:ml-[80px]',   // sidebar width offset on desktop
        'pb-28 md:pb-8',  // bottom padding for mobile nav
      ]"
    >
      <RouterView v-slot="{ Component, route }">
        <Transition name="page-fade" mode="out-in">
          <component :is="Component" :key="route.path" />
        </Transition>
      </RouterView>
    </main>

    <!-- Mobile Bottom Nav -->
    <BottomNav />
  </div>
</template>

<script setup>
import { RouterView } from 'vue-router'
import SideNav from '@/components/navigation/SideNav.vue'
import BottomNav from '@/components/navigation/BottomNav.vue'
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
</style>
