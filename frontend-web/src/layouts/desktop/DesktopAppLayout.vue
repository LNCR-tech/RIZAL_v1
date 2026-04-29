<template>
  <div class="desktop-app-layout">
    <DesktopSideNav />
    <main class="desktop-app-layout__main">
      <AppLayoutOutlet />
    </main>
  </div>
</template>

<script setup>
import DesktopSideNav from '@/components/desktop/navigation/DesktopSideNav.vue'
import AppLayoutOutlet from '@/layouts/shared/AppLayoutOutlet.vue'
import { useProtectedShellSession } from '@/layouts/shared/useProtectedShellSession.js'

useProtectedShellSession()
</script>

<style scoped>
.desktop-app-layout {
  min-height: 100dvh;
  background: var(--color-bg);
  font-family: 'Manrope', sans-serif;
}

.desktop-app-layout__main {
  min-height: 100dvh;
  margin-left: 80px;
  padding-bottom: 32px;
  background: var(--color-bg);
}
</style>
