<template>
  <nav class="mobile-branded-nav" aria-label="Mobile navigation">
    <div class="mobile-branded-nav__shell">
      <button
        type="button"
        class="mobile-branded-nav__brand"
        :class="{ 'mobile-branded-nav__brand--active': isGatherActive }"
        aria-label="Open Gather"
        @click="openGather"
      >
        <GatherBrandMark />
        <span class="mobile-branded-nav__brand-label">Gather</span>
      </button>

      <div class="mobile-branded-nav__actions">
        <button
          v-for="item in navItems"
          :key="item.name"
          type="button"
          class="mobile-branded-nav__button"
          :class="{ 'mobile-branded-nav__button--active': isActive(item) }"
          :aria-label="item.name"
          @click="navigate(item.route)"
        >
          <span
            v-if="isActive(item)"
            class="mobile-branded-nav__glow"
            aria-hidden="true"
          />

          <component
            :is="item.icon"
            :size="20"
            :stroke-width="isActive(item) ? 2.45 : 2"
            :color="isActive(item) ? 'var(--color-primary)' : 'var(--mobile-branded-nav-icon-idle)'"
            class="mobile-branded-nav__icon"
          />

          <span
            v-if="isActive(item)"
            class="mobile-branded-nav__dot"
            aria-hidden="true"
          />
        </button>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import GatherBrandMark from '@/components/mobile/navigation/GatherBrandMark.vue'
import { useMobileBottomNav } from '@/components/mobile/navigation/useMobileBottomNav.js'
import {
  isGatherWelcomePath,
  resolveGatherEntryLocation,
} from '@/services/routeWorkspace.js'

defineProps({
  navItems: {
    type: Array,
    default: () => [],
  },
})

const { route, isActive, navigate } = useMobileBottomNav()
const isGatherActive = computed(() => isGatherWelcomePath(route))

function openGather() {
  navigate(resolveGatherEntryLocation(route))
}
</script>

<style scoped>
.mobile-branded-nav {
  position: fixed;
  left: 50%;
  bottom: max(18px, calc(env(safe-area-inset-bottom, 0px) + 8px));
  transform: translateX(-50%);
  z-index: 50;
  width: min(calc(100vw - 24px), 390px);
}

.mobile-branded-nav__shell {
  --mobile-branded-nav-icon-idle: color-mix(in srgb, var(--color-primary) 84%, #f7ffb2 16%);
  position: relative;
  isolation: isolate;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 84px;
  padding: 8px 12px 8px 8px;
  border-radius: 999px;
  background:
    linear-gradient(180deg, rgba(20, 20, 20, 0.7) 0%, rgba(8, 8, 8, 0.56) 100%),
    color-mix(in srgb, var(--color-nav-glass-bg) 86%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-nav-glass-border) 76%, rgba(255, 255, 255, 0.14));
  box-shadow:
    0 18px 38px rgba(0, 0, 0, 0.28),
    0 8px 20px rgba(0, 0, 0, 0.16),
    inset 0 1px 0 rgba(255, 255, 255, 0.18),
    inset 0 -1px 0 rgba(255, 255, 255, 0.04);
}

.mobile-branded-nav__shell::before,
.mobile-branded-nav__shell::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
}

.mobile-branded-nav__shell::before {
  z-index: -2;
  background:
    radial-gradient(circle at 14% 14%, rgba(255, 255, 255, 0.24) 0%, rgba(255, 255, 255, 0.08) 16%, transparent 30%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.14) 0%, rgba(255, 255, 255, 0.03) 42%, rgba(255, 255, 255, 0.06) 100%),
    var(--color-nav-glass-layer);
  box-shadow:
    inset 0 1px 0 color-mix(in srgb, var(--color-nav-glass-inset) 92%, rgba(255, 255, 255, 0.18)),
    inset 0 -10px 18px rgba(255, 255, 255, 0.02);
}

.mobile-branded-nav__shell::after {
  z-index: -1;
  background:
    radial-gradient(circle at 88% 22%, rgba(255, 255, 255, 0.12) 0%, transparent 22%),
    linear-gradient(102deg, rgba(255, 255, 255, 0.2) 0%, rgba(255, 255, 255, 0.06) 18%, rgba(255, 255, 255, 0) 40%, rgba(255, 255, 255, 0.08) 78%, rgba(255, 255, 255, 0.16) 100%),
    var(--color-nav-glass-light);
  opacity: 0.88;
}

.mobile-branded-nav__brand {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  min-width: 142px;
  max-width: 160px;
  height: 68px;
  padding: 0 18px 0 16px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92) 0%, rgba(247, 247, 247, 0.76) 100%),
    rgba(255, 255, 255, 0.58);
  border: 1px solid rgba(255, 255, 255, 0.56);
  color: #121212;
  box-shadow:
    0 12px 24px rgba(9, 9, 11, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.82),
    inset 0 -10px 18px rgba(255, 255, 255, 0.14);
  flex-shrink: 0;
  cursor: pointer;
  appearance: none;
  transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
}

.mobile-branded-nav__brand::before,
.mobile-branded-nav__brand::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
}

.mobile-branded-nav__brand::before {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.46) 0%, rgba(255, 255, 255, 0.08) 48%, transparent 100%);
}

.mobile-branded-nav__brand::after {
  background: radial-gradient(circle at 18% 20%, rgba(255, 255, 255, 0.34) 0%, transparent 28%);
}

.mobile-branded-nav__brand-label {
  font-size: 1.02rem;
  font-weight: 500;
  letter-spacing: -0.03em;
  color: #121212;
  white-space: nowrap;
}

.mobile-branded-nav__brand:active {
  transform: scale(0.985);
}

.mobile-branded-nav__brand--active {
  border-color: color-mix(in srgb, var(--color-primary) 28%, rgba(255, 255, 255, 0.56));
  box-shadow:
    0 16px 30px rgba(9, 9, 11, 0.14),
    inset 0 1px 0 rgba(255, 255, 255, 0.84),
    inset 0 -10px 18px rgba(255, 255, 255, 0.16);
}

.mobile-branded-nav__actions {
  min-width: 0;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
}

.mobile-branded-nav__button {
  position: relative;
  width: 44px;
  height: 68px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: transform 180ms ease, opacity 180ms ease, filter 180ms ease;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  cursor: pointer;
  opacity: 0.94;
}

.mobile-branded-nav__button:active {
  transform: scale(0.96);
}

.mobile-branded-nav__button--active {
  opacity: 1;
}

.mobile-branded-nav__glow {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 52px;
  height: 52px;
  border-radius: 999px;
  transform: translate(-50%, -52%);
  background: radial-gradient(circle, color-mix(in srgb, var(--color-primary) 44%, transparent) 0%, transparent 72%);
  filter: blur(5px);
}

.mobile-branded-nav__icon {
  position: relative;
  z-index: 1;
  transition: transform 180ms ease;
}

.mobile-branded-nav__button--active .mobile-branded-nav__icon {
  transform: translateY(-4px) scale(1.02);
}

.mobile-branded-nav__dot {
  position: absolute;
  left: 50%;
  bottom: 13px;
  width: 7px;
  height: 7px;
  border-radius: 999px;
  transform: translateX(-50%);
  background: var(--color-primary);
  box-shadow: 0 0 14px color-mix(in srgb, var(--color-primary) 48%, transparent);
}

@supports ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .mobile-branded-nav__shell {
    -webkit-backdrop-filter: blur(calc(var(--nav-glass-blur) + 6px)) saturate(170%) brightness(1.08);
    backdrop-filter: blur(calc(var(--nav-glass-blur) + 6px)) saturate(170%) brightness(1.08);
  }

  .mobile-branded-nav__brand {
    -webkit-backdrop-filter: blur(calc(var(--nav-glass-blur) * 0.7)) saturate(145%);
    backdrop-filter: blur(calc(var(--nav-glass-blur) * 0.7)) saturate(145%);
  }
}

@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .mobile-branded-nav__shell {
    background: var(--color-nav-glass-bg);
  }
}

@media (max-width: 360px) {
  .mobile-branded-nav {
    width: min(calc(100vw - 20px), 372px);
  }

  .mobile-branded-nav__shell {
    gap: 8px;
    min-height: 80px;
    padding-right: 10px;
  }

  .mobile-branded-nav__brand {
    min-width: 132px;
    max-width: 146px;
    height: 64px;
    padding: 0 14px 0 14px;
    gap: 10px;
  }

  .mobile-branded-nav__brand-label {
    font-size: 0.97rem;
  }

  .mobile-branded-nav__button {
    width: 40px;
    height: 64px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .mobile-branded-nav__button,
  .mobile-branded-nav__icon {
    transition: none;
  }
}
</style>
