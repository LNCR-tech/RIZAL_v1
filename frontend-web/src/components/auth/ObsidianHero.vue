<template>
  <div class="obsidian-hero" aria-hidden="true">
    <!-- Base dark layer -->
    <div class="obsidian-hero__base"></div>

    <!-- Animated light shimmers -->
    <div class="obsidian-hero__shimmer obsidian-hero__shimmer--1"></div>
    <div class="obsidian-hero__shimmer obsidian-hero__shimmer--2"></div>
    <div class="obsidian-hero__shimmer obsidian-hero__shimmer--3"></div>

    <!-- Halftone Mesh Overlay -->
    <div class="obsidian-hero__mesh"></div>

    <!-- Atmospheric grain/noise -->
    <div class="obsidian-hero__grain"></div>

    <!-- Branding Layer -->
    <div class="obsidian-hero__branding">
      <slot />
    </div>
  </div>
</template>

<script setup>
/**
 * ObsidianHero.vue
 * A high-performance, dynamic replacement for static hero images.
 * Implements the "Sleek Obsidian" aesthetic using CSS-only animations and SVG masks.
 */
</script>

<style scoped>
.obsidian-hero {
  position: absolute;
  inset: 0;
  background-color: #050505;
  overflow: hidden;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  z-index: 0;
}

.obsidian-hero__base {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 20% 30%, rgba(255, 255, 255, 0.03) 0%, transparent 50%);
}

/* Light shimmers that slowly move to create depth */
.obsidian-hero__shimmer {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  pointer-events: none;
  will-change: transform, opacity;
}

.obsidian-hero__shimmer--1 {
  width: 60%;
  height: 50%;
  top: -10%;
  left: -5%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.06) 0%, transparent 70%);
  animation: obsidian-float 25s infinite alternate ease-in-out;
}

.obsidian-hero__shimmer--2 {
  width: 50%;
  height: 40%;
  bottom: 10%;
  right: -10%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.04) 0%, transparent 70%);
  animation: obsidian-float 35s infinite alternate-reverse ease-in-out;
  animation-delay: -5s;
}

.obsidian-hero__shimmer--3 {
  width: 40%;
  height: 30%;
  top: 40%;
  left: 30%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.02) 0%, transparent 70%);
  animation: obsidian-float 45s infinite alternate ease-in-out;
  animation-delay: -12s;
}

/* The Halftone Mesh Layer */
.obsidian-hero__mesh {
  position: absolute;
  inset: 0;
  /* Using a tiny SVG dot pattern as a mask */
  background-image: radial-gradient(rgba(255, 255, 255, 0.12) 1px, transparent 0);
  background-size: 14px 14px;
  background-position: center;
  mask-image: radial-gradient(circle at 30% 30%, black 0%, transparent 85%);
  -webkit-mask-image: radial-gradient(circle at 30% 30%, black 0%, transparent 85%);
  opacity: 0.6;
}

/* Fine grain for a premium texture */
.obsidian-hero__grain {
  position: absolute;
  inset: 0;
  opacity: 0.18;
  pointer-events: none;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
}

.obsidian-hero__branding {
  position: relative;
  z-index: 10;
  padding: 52px 40px;
}

@keyframes obsidian-float {
  0% {
    transform: translate3d(0, 0, 0) scale(1) rotate(0deg);
    opacity: 0.4;
  }
  50% {
    transform: translate3d(5%, 10%, 0) scale(1.1) rotate(5deg);
    opacity: 0.7;
  }
  100% {
    transform: translate3d(-5%, 5%, 0) scale(1) rotate(-3deg);
    opacity: 0.4;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .obsidian-hero__shimmer {
    animation: none;
  }
}
</style>
