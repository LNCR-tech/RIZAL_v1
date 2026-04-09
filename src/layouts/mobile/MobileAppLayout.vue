<template>
  <div class="mobile-app-layout">
    <main class="mobile-app-layout__main">
      <AppLayoutOutlet />
    </main>
    <MobileBottomNav />
  </div>
</template>

<script setup>
import MobileBottomNav from '@/components/mobile/navigation/MobileBottomNav.vue'
import AppLayoutOutlet from '@/layouts/shared/AppLayoutOutlet.vue'
import { useProtectedShellSession } from '@/layouts/shared/useProtectedShellSession.js'

useProtectedShellSession()
</script>

<style scoped>
.mobile-app-layout {
  min-height: 100vh;
  background: var(--color-bg);
  font-family: 'Manrope', sans-serif;
}

.mobile-app-layout__main {
  min-height: 100vh;
  padding-bottom: 112px;
}
</style>

