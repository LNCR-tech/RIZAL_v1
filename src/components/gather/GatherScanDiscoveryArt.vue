<template>
  <div class="gather-scan-art">
    <div class="gather-scan-art__stage" aria-hidden="true">
      <DotLottieVue
        v-if="animationSrc"
        class="gather-scan-art__animation"
        autoplay
        loop
        :src="animationSrc"
      />

      <div v-else class="gather-scan-art__placeholder">
        <span class="gather-scan-art__ring gather-scan-art__ring--outer" />
        <span class="gather-scan-art__ring gather-scan-art__ring--inner" />

        <div class="gather-scan-art__icon-shell">
          <LoaderCircle
            v-if="busy"
            :size="30"
            :stroke-width="2.2"
            class="gather-scan-art__spinner"
          />
          <Search v-else :size="28" :stroke-width="2.2" />
        </div>
      </div>
    </div>

    <div class="gather-scan-art__copy">
      <h3 class="gather-scan-art__title">{{ title }}</h3>
      <p class="gather-scan-art__description">{{ description }}</p>
    </div>
  </div>
</template>

<script setup>
import { DotLottieVue } from '@lottiefiles/dotlottie-vue'
import { LoaderCircle, Search } from 'lucide-vue-next'

defineProps({
  animationSrc: {
    type: String,
    default: '',
  },
  busy: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '',
  },
  description: {
    type: String,
    default: '',
  },
})
</script>

<style scoped>
.gather-scan-art,
.gather-scan-art__copy,
.gather-scan-art__placeholder,
.gather-scan-art__icon-shell {
  display: flex;
}

.gather-scan-art {
  width: 100%;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  text-align: center;
}

.gather-scan-art__stage {
  position: relative;
  width: min(46vw, 168px);
  height: min(46vw, 168px);
  border-radius: 999px;
  background:
    radial-gradient(circle at top, color-mix(in srgb, var(--color-nav-active) 12%, transparent) 0%, transparent 52%),
    color-mix(in srgb, var(--color-surface) 84%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-surface-border) 74%, transparent);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.4),
    0 18px 36px rgba(15, 23, 42, 0.08);
  overflow: hidden;
}

.gather-scan-art__animation,
.gather-scan-art__placeholder {
  width: 100%;
  height: 100%;
}

.gather-scan-art__placeholder {
  position: relative;
  align-items: center;
  justify-content: center;
}

.gather-scan-art__ring {
  position: absolute;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--color-nav-active) 24%, var(--color-surface-border));
}

.gather-scan-art__ring--outer {
  inset: 14px;
}

.gather-scan-art__ring--inner {
  inset: 34px;
}

.gather-scan-art__icon-shell {
  position: relative;
  z-index: 1;
  width: 62px;
  height: 62px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-surface) 92%, white 8%);
  color: var(--color-nav-active);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.72),
    0 12px 24px rgba(15, 23, 42, 0.08);
}

.gather-scan-art__copy {
  max-width: 280px;
  flex-direction: column;
  gap: 8px;
}

.gather-scan-art__title,
.gather-scan-art__description {
  margin: 0;
}

.gather-scan-art__title {
  font-size: 20px;
  line-height: 1.05;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: var(--color-text-primary);
}

.gather-scan-art__description {
  font-size: 13px;
  line-height: 1.55;
  color: var(--color-text-secondary);
}

.gather-scan-art__spinner {
  animation: gather-scan-art-spin 0.9s linear infinite;
}

@keyframes gather-scan-art-spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .gather-scan-art__spinner {
    animation: none;
  }
}
</style>
