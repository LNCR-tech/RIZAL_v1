<template>
  <div class="obsidian-hero" aria-hidden="true">
    <!-- Base Layer: Deep Obsidian -->
    <div class="obsidian-hero__base"></div>

    <!-- Dynamic Glints: Bright, sharp light hits -->
    <div class="obsidian-hero__glint obsidian-hero__glint--1"></div>
    <div class="obsidian-hero__glint obsidian-hero__glint--2"></div>

    <!-- Halftone Mesh: Large, crisp dots with lighting gradient -->
    <div class="obsidian-hero__mesh"></div>

    <!-- Subtle Premium Texture: Very low opacity noise -->
    <div class="obsidian-hero__texture"></div>

    <!-- Branding Layer -->
    <div class="obsidian-hero__branding">
      <slot />
    </div>
  </div>
</template>

<script setup>
/**
 * Refined ObsidianHero.vue
 * Focused on high contrast, crisp halftone dots, and hardware-inspired lighting.
 */
</script>

<style scoped>
.obsidian-hero {
  position: absolute;
  inset: 0;
  background-color: #030303;
  overflow: hidden;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  z-index: 0;
}

.obsidian-hero__base {
  position: absolute;
  inset: 0;
  /* Top-down environmental lighting */
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.05) 0%, transparent 100%);
}

/* Sharp, bright light glints */
.obsidian-hero__glint {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  pointer-events: none;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.12) 0%, transparent 70%);
  will-change: transform, opacity;
}

.obsidian-hero__glint--1 {
  width: 80%;
  height: 60%;
  top: -20%;
  left: -10%;
  animation: obsidian-shimmer 15s infinite alternate ease-in-out;
}

.obsidian-hero__glint--2 {
  width: 60%;
  height: 40%;
  bottom: 0%;
  right: -5%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.08) 0%, transparent 70%);
  animation: obsidian-shimmer 20s infinite alternate-reverse ease-in-out;
  animation-delay: -4s;
}

/* The Halftone Mesh: Large dots with depth-based opacity */
.obsidian-hero__mesh {
  position: absolute;
  inset: 0;
  /* 2px dots with 20px grid spacing */
  background-image: radial-gradient(rgba(255, 255, 255, 0.18) 1.5px, transparent 0);
  background-size: 20px 20px;
  background-position: center;
  
  /* Create the 'lighting' effect on the dots */
  mask-image: linear-gradient(180deg, black 0%, rgba(0, 0, 0, 0.4) 60%, transparent 100%);
  -webkit-mask-image: linear-gradient(180deg, black 0%, rgba(0, 0, 0, 0.4) 60%, transparent 100%);
  
  mix-blend-mode: screen;
  opacity: 0.8;
}

/* High-frequency, low-opacity noise for tactile feel */
.obsidian-hero__texture {
  position: absolute;
  inset: 0;
  opacity: 0.04; /* Extremely subtle */
  pointer-events: none;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
}

.obsidian-hero__branding {
  position: relative;
  z-index: 10;
  padding: 52px 40px;
}

@keyframes obsidian-shimmer {
  0% {
    transform: translate3d(0, 0, 0) scale(1);
    opacity: 0.6;
  }
  100% {
    transform: translate3d(10%, 5%, 0) scale(1.15);
    opacity: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .obsidian-hero__glint {
    animation: none;
  }
}
</style>
