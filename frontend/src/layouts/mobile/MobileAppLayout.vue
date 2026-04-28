<template>
  <div class="mobile-app-layout">
    <main
      class="mobile-app-layout__main"
      :class="{ 'mobile-app-layout__main--immersive': hideMobileNav }"
    >
      <AppLayoutOutlet />
    </main>
    <MobileBottomNav v-if="!hideMobileNav" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import MobileBottomNav from '@/components/mobile/navigation/MobileBottomNav.vue'
import AppLayoutOutlet from '@/layouts/shared/AppLayoutOutlet.vue'
import { useProtectedShellSession } from '@/layouts/shared/useProtectedShellSession.js'

useProtectedShellSession()

const route = useRoute()
const hideMobileNav = computed(() => (
  route.matched.some((record) => record?.meta?.hideMobileNav)
))
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

.mobile-app-layout__main--immersive {
  padding-bottom: 0;
}
</style>
