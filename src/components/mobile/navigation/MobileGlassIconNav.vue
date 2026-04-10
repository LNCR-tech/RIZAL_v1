<template>
  <nav class="mobile-glass-nav" aria-label="Mobile navigation">
    <div class="mobile-glass-nav__shell">
      <button
        v-for="item in navItems"
        :key="item.name"
        type="button"
        class="mobile-glass-nav__button"
        :class="isActive(item) ? 'mobile-glass-nav__button--active' : 'mobile-glass-nav__button--idle'"
        :aria-label="item.name"
        @click="navigate(item.route)"
      >
        <span
          v-if="isActive(item)"
          class="mobile-glass-nav__glow"
          aria-hidden="true"
        />

        <component
          :is="item.icon"
          :size="20"
          :stroke-width="isActive(item) ? 2.5 : 2"
          :color="isActive(item) ? 'var(--color-primary)' : '#ffffff'"
          class="mobile-glass-nav__icon"
          :class="{ 'mobile-glass-nav__icon--active': isActive(item) }"
        />

        <span
          v-if="isActive(item)"
          class="mobile-glass-nav__dot"
          aria-hidden="true"
        />
      </button>
    </div>
  </nav>
</template>

<script setup>
import { useMobileBottomNav } from '@/components/mobile/navigation/useMobileBottomNav.js'

defineProps({
  navItems: {
    type: Array,
    default: () => [],
  },
})

const { isActive, navigate } = useMobileBottomNav()
</script>

<style scoped>
.mobile-glass-nav {
  position: fixed;
  left: 50%;
  bottom: max(20px, calc(env(safe-area-inset-bottom, 0px) + 10px));
  transform: translateX(-50%);
  z-index: 50;
}

.mobile-glass-nav__shell {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  display: flex;
  align-items: center;
  height: 60px;
  padding: 0 12px;
  gap: 4px;
  border-radius: 999px;
  background:
    linear-gradient(180deg, rgba(18, 18, 18, 0.72) 0%, rgba(9, 9, 9, 0.58) 100%),
    color-mix(in srgb, var(--color-nav-glass-bg) 86%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-nav-glass-border) 76%, rgba(255, 255, 255, 0.14));
  box-shadow:
    0 16px 32px rgba(0, 0, 0, 0.26),
    0 8px 18px rgba(0, 0, 0, 0.14),
    inset 0 1px 0 rgba(255, 255, 255, 0.16),
    inset 0 -1px 0 rgba(255, 255, 255, 0.03);
}

.mobile-glass-nav__shell::before,
.mobile-glass-nav__shell::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
}

.mobile-glass-nav__shell::before {
  z-index: -2;
  background:
    radial-gradient(circle at 16% 14%, rgba(255, 255, 255, 0.2) 0%, rgba(255, 255, 255, 0.06) 15%, transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.03) 42%, rgba(255, 255, 255, 0.05) 100%),
    var(--color-nav-glass-layer);
  box-shadow:
    inset 0 1px 0 color-mix(in srgb, var(--color-nav-glass-inset) 92%, rgba(255, 255, 255, 0.18)),
    inset 0 -8px 14px rgba(255, 255, 255, 0.02);
}

.mobile-glass-nav__shell::after {
  z-index: -1;
  background:
    radial-gradient(circle at 86% 22%, rgba(255, 255, 255, 0.1) 0%, transparent 20%),
    linear-gradient(104deg, rgba(255, 255, 255, 0.18) 0%, rgba(255, 255, 255, 0.06) 18%, rgba(255, 255, 255, 0) 42%, rgba(255, 255, 255, 0.08) 82%, rgba(255, 255, 255, 0.14) 100%),
    var(--color-nav-glass-light);
  opacity: 0.9;
}

.mobile-glass-nav__button {
  position: relative;
  width: 52px;
  height: 60px;
  border-radius: 999px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: opacity 200ms ease, transform 220ms ease;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  cursor: pointer;
  user-select: none;
}

.mobile-glass-nav__button--idle {
  opacity: 0.4;
}

.mobile-glass-nav__button--idle:active {
  transform: scale(0.96);
}

.mobile-glass-nav__glow {
  position: absolute;
  inset: 0;
  border-radius: 999px;
  background: radial-gradient(circle, var(--color-primary) 0%, transparent 60%);
  opacity: 0.15;
}

.mobile-glass-nav__icon {
  position: relative;
  z-index: 1;
  transition: transform 220ms ease, opacity 200ms ease;
}

.mobile-glass-nav__icon--active {
  margin-bottom: 8px;
  transform: scale(1.04);
}

.mobile-glass-nav__dot {
  position: absolute;
  bottom: 8px;
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: var(--color-primary);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
}

@supports ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .mobile-glass-nav__shell {
    -webkit-backdrop-filter: blur(calc(var(--nav-glass-blur) + 4px)) saturate(160%) brightness(1.06);
    backdrop-filter: blur(calc(var(--nav-glass-blur) + 4px)) saturate(160%) brightness(1.06);
  }
}

@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .mobile-glass-nav__shell {
    background: var(--color-nav-glass-bg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .mobile-glass-nav__button,
  .mobile-glass-nav__icon {
    transition: none;
  }
}
</style>
