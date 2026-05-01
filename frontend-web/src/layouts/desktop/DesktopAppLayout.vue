<template>
  <div class="desktop-app-layout">
    <ObsidianBackground />
    <DesktopSideNav />
    <main class="desktop-app-layout__main">
      <div class="desktop-app-layout__content">
        <AppLayoutOutlet />
      </div>
    </main>
  </div>
</template>

<script setup>
import DesktopSideNav from '@/components/desktop/navigation/DesktopSideNav.vue'
import ObsidianBackground from '@/components/ui/ObsidianBackground.vue'
import AppLayoutOutlet from '@/layouts/shared/AppLayoutOutlet.vue'
import { useProtectedShellSession } from '@/layouts/shared/useProtectedShellSession.js'

useProtectedShellSession()
</script>

<style scoped>
.desktop-app-layout {
  min-height: 100vh;
  background: transparent;
  font-family: 'Manrope', sans-serif;
  color: #ffffff;
}

.desktop-app-layout__main {
  min-height: 100vh;
  margin-left: 80px;
  padding-bottom: 32px;
}

.desktop-app-layout__content {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 32px;
}
</style>

