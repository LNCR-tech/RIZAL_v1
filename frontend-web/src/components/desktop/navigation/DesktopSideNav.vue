<template>
  <aside
    class="nav-rail"
    :style="navRailStyle"
    aria-label="Desktop navigation"
  >
    <div class="nav-rail__shell">
      <div class="nav-rail__content">
        <div class="nav-rail__nav">
          <button
            v-for="item in navItems"
            :key="item.name"
            class="nav-rail__button"
            :class="isActive(item) ? 'nav-rail__button--active' : 'nav-rail__button--idle'"
            :aria-label="item.name"
            @click="navigate(item.route)"
          >
            <span
              v-if="isActive(item)"
              class="nav-rail__glow"
              style="background: radial-gradient(circle, var(--color-primary) 0%, transparent 65%); opacity: 0.15; top: 50%; transform: translateY(-50%);"
            />

            <component
              :is="item.icon"
              :size="19"
              :stroke-width="isActive(item) ? 2.2 : 1.6"
              :color="'var(--color-primary)'"
              class="nav-rail__icon"
            />

            <span
              class="nav-rail__dot"
              :style="isActive(item)
                ? 'background: var(--color-primary); opacity: 1;'
                : 'background: transparent; opacity: 0;'"
            />
          </button>
        </div>

        <div ref="pillRef" class="relative w-[40px] h-[74px] mx-2 mb-1.5 z-50">
          <div
            class="absolute top-0 left-0 flex flex-col overflow-hidden transition-all duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)] shadow-lg origin-left w-[40px] h-[74px] rounded-[26px] cursor-pointer hover:brightness-110 hover:scale-105 active:scale-95"
            style="background: var(--color-primary);"
            @click="expandToFull"
          >
            <div class="absolute inset-0 flex flex-col items-center justify-center gap-1">
              <img :src="activeAuraLogo" alt="Aura" class="w-6 h-6 object-contain opacity-90" />
              <span
                class="text-[8px] font-extrabold text-center leading-snug"
                style="color: var(--color-banner-text);"
              >
                Talk to<br>Aura Ai
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </aside>

  <AuraChatWindow />
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { activeAuraLogo } from '@/config/theme.js'
import { useChat } from '@/composables/useChat.js'
import AuraChatWindow from '@/components/ui/AuraChatWindow.vue'
import { getNavigationItemsForRoute } from '@/components/navigation/navigationItems.js'
import { withPreservedGovernancePreviewQuery } from '@/services/routeWorkspace.js'

const {
  expandToFull,
} = useChat()

const router = useRouter()
const route = useRoute()
const navItems = computed(() => getNavigationItemsForRoute(route))
const railHeight = computed(() => Math.max(380, 150 + (navItems.value.length * 58)))
const navRailStyle = computed(() => ({
  '--nav-rail-height': `${railHeight.value}px`,
  height: `${railHeight.value}px`,
  top: `calc(50vh - ${railHeight.value / 2}px)`,
}))

function isActive(item) {
  const path = item?.route
  if (
    path === '/dashboard' ||
    path === '/exposed/dashboard' ||
    path === '/workspace' ||
    path === '/exposed/workspace' ||
    path === '/admin' ||
    path === '/exposed/admin' ||
    path === '/governance' ||
    path === '/exposed/governance' ||
    path === '/sg' ||
    path === '/exposed/sg'
  ) {
    return route.path === path || route.path === `${path}/`
  }

  const matchPrefixes = Array.isArray(item?.matchPrefixes) ? item.matchPrefixes : []
  return route.path.startsWith(path) || matchPrefixes.some((prefix) => route.path.startsWith(prefix))
}

function navigate(path) {
  const target = withPreservedGovernancePreviewQuery(route, path)
  const resolvedTarget = router.resolve(target)
  if (route.fullPath === resolvedTarget.fullPath) return
  router.push(target)
}


</script>

<style scoped>
.nav-rail {
  position: fixed;
  left: 16px;
  width: 52px;
  min-height: 380px;
  z-index: 50;
}

.nav-rail__shell {
  position: relative;
  isolation: isolate;
  overflow: visible;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  height: 100%;
  border-radius: 32px;
  background: var(--color-nav-glass-bg);
  backdrop-filter: blur(var(--nav-glass-blur)) saturate(160%);
  -webkit-backdrop-filter: blur(var(--nav-glass-blur)) saturate(160%);
  border: 1px solid var(--color-nav-glass-border);
  box-shadow: var(--color-nav-glass-shadow);
}

.nav-rail__shell::before,
.nav-rail__shell::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
}

.nav-rail__shell::before {
  z-index: -2;
  background: var(--color-nav-glass-layer);
  box-shadow: inset 0 1px 0 var(--color-nav-glass-inset);
}

.nav-rail__shell::after {
  z-index: -1;
  background:
    var(--color-nav-glass-light),
    linear-gradient(180deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.01) 48%, rgba(255, 255, 255, 0.08) 100%);
}

.nav-rail__content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 100%;
}

.nav-rail__nav {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  padding: 18px 0 12px;
  gap: 2px;
  flex: 1;
}

.nav-rail__button {
  position: relative;
  width: 100%;
  min-height: 54px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: opacity 200ms ease, transform 220ms ease;
}

.nav-rail__button--idle {
  opacity: 0.35;
}

.nav-rail__button--idle:hover {
  opacity: 0.65;
  transform: translateY(-1px);
}

.nav-rail__button--active {
  opacity: 1;
}

.nav-rail__glow {
  position: absolute;
  width: 48px;
  height: 48px;
  border-radius: 999px;
  pointer-events: none;
}

.nav-rail__icon {
  position: relative;
  z-index: 10;
  transition: transform 220ms ease, opacity 200ms ease;
}

.nav-rail__button--active .nav-rail__icon {
  transform: scale(1.04);
}

.nav-rail__dot {
  width: 4px;
  height: 4px;
  border-radius: 999px;
  transition: opacity 200ms ease, background-color 200ms ease, transform 220ms ease;
}

.nav-rail__button--active .nav-rail__dot {
  transform: translateY(1px);
}

@supports ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .nav-rail__shell {
    -webkit-backdrop-filter: blur(var(--nav-glass-blur)) saturate(135%);
    backdrop-filter: blur(var(--nav-glass-blur)) saturate(135%);
  }
}

@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .nav-rail__shell {
    background: var(--color-nav-glass-bg);
  }
}

</style>
