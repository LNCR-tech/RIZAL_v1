<template>
  <component :is="activeNavComponent" :nav-items="navItems" />
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import MobileBrandedBottomNav from '@/components/mobile/navigation/MobileBrandedBottomNav.vue'
import MobileGlassIconNav from '@/components/mobile/navigation/MobileGlassIconNav.vue'
import {
  getNavigationItemsForContext,
  resolveNavigationContext,
} from '@/components/navigation/navigationItems.js'

const BRANDED_CONTEXTS = new Set([
  'dashboard',
  'dashboard_preview',
  'governance',
  'governance_preview',
])

const route = useRoute()
const navigationContext = computed(() => resolveNavigationContext(route))
const navItems = computed(() => getNavigationItemsForContext(navigationContext.value))
const activeNavComponent = computed(() => (
  BRANDED_CONTEXTS.has(navigationContext.value)
    ? MobileBrandedBottomNav
    : MobileGlassIconNav
))
</script>
