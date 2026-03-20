<template>
  <!-- Mobile Bottom Navigation -->
  <nav
    class="bottom-nav fixed bottom-5 left-1/2 -translate-x-1/2 z-50 md:hidden"
    aria-label="Mobile navigation"
  >
    <div class="bottom-nav__shell" :style="bottomNavStyle">
      <button
        v-for="item in navItems"
        :key="item.name"
        @click="navigate(item.route)"
        :aria-label="item.name"
        class="bottom-nav__button"
        :class="isActive(item) ? 'bottom-nav__button--active' : 'bottom-nav__button--idle'"
      >
        <!-- Active glowing background -->
        <span
          v-if="isActive(item)"
          class="bottom-nav__glow"
          style="background: radial-gradient(circle, var(--color-primary) 0%, transparent 60%); opacity: 0.15;"
        />
        
        <component
          :is="item.icon"
          :size="20"
          :stroke-width="isActive(item) ? 2.5 : 2"
          :color="isActive(item) ? 'var(--color-primary)' : 'var(--color-nav-text)'"
          class="bottom-nav__icon"
          :class="{ 'bottom-nav__icon--active': isActive(item) }"
        />

        <!-- Active Dot Indicator -->
        <span
          v-if="isActive(item)"
          class="bottom-nav__dot"
          style="background: var(--color-primary);"
        />
      </button>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getNavigationItemsForPath } from '@/components/navigation/navigationItems.js'

const router = useRouter()
const route = useRoute()
const navItems = computed(() => getNavigationItemsForPath(route.path))
const bottomNavStyle = computed(() => ({
  '--nav-count': String(navItems.value.length),
}))

function isActive(item) {
  const path = item?.route
  if (path === '/dashboard' || path === '/exposed/dashboard' || path === '/workspace' || path === '/exposed/workspace') {
    return route.path === path || route.path === `${path}/`
  }

  const matchPrefixes = Array.isArray(item?.matchPrefixes) ? item.matchPrefixes : []
  return route.path.startsWith(path) || matchPrefixes.some((prefix) => route.path.startsWith(prefix))
}

function navigate(path) {
  if (route.path === path) return
  router.push(path)
}
</script>

<style scoped>
.bottom-nav__shell {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 12px 16px;
  border-radius: 999px;
  background: var(--color-nav-glass-bg);
  border: 1px solid var(--color-nav-glass-border);
  box-shadow: var(--color-nav-glass-shadow);
}

.bottom-nav__shell::before,
.bottom-nav__shell::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
}

.bottom-nav__shell::before {
  z-index: -2;
  background: var(--color-nav-glass-layer);
  box-shadow: inset 0 1px 0 var(--color-nav-glass-inset);
}

.bottom-nav__shell::after {
  z-index: -1;
  background:
    var(--color-nav-glass-light),
    linear-gradient(90deg, rgba(255, 255, 255, 0.04) 0%, rgba(255, 255, 255, 0) 42%, rgba(255, 255, 255, 0.06) 100%);
}

.bottom-nav__button {
  position: relative;
  width: 52px;
  height: 48px;
  border-radius: 999px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: opacity 200ms ease, transform 220ms ease;
}

.bottom-nav__button--idle {
  opacity: 0.4;
}

.bottom-nav__button--idle:active {
  transform: scale(0.96);
}

.bottom-nav__glow {
  position: absolute;
  inset: 0;
  border-radius: 999px;
}

.bottom-nav__icon {
  position: relative;
  z-index: 10;
  transition: transform 220ms ease, opacity 200ms ease;
}

.bottom-nav__icon--active {
  margin-bottom: 8px;
  transform: scale(1.04);
}

.bottom-nav__dot {
  position: absolute;
  bottom: 8px;
  width: 6px;
  height: 6px;
  border-radius: 999px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
}

@supports ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .bottom-nav__shell {
    -webkit-backdrop-filter: blur(var(--nav-glass-blur)) saturate(135%);
    backdrop-filter: blur(var(--nav-glass-blur)) saturate(135%);
  }
}

@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .bottom-nav__shell {
    background: var(--color-nav-glass-bg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .bottom-nav__button,
  .bottom-nav__icon {
    transition: none;
  }
}
</style>
