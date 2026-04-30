<template>
  <div 
    ref="heroContainer"
    class="obsidian-hero" 
    aria-hidden="true"
    @mousemove="handleMouseMove"
    @mouseleave="handleMouseLeave"
  >
    <!-- Base Layer: Deep Obsidian -->
    <div class="obsidian-hero__base"></div>

    <!-- Dynamic Glints: Bright, sharp light hits -->
    <div class="obsidian-hero__glint obsidian-hero__glint--1"></div>
    <div class="obsidian-hero__glint obsidian-hero__glint--2"></div>

    <!-- Base Halftone Mesh (Static/Subtle) -->
    <div class="obsidian-hero__mesh obsidian-hero__mesh--base"></div>

    <!-- Active Halftone Mesh (The Glow/Pop Layer) -->
    <div 
      class="obsidian-hero__mesh obsidian-hero__mesh--active"
      :style="{
        '-webkit-mask-image': `radial-gradient(circle 100px at ${renderedX}px ${renderedY}px, black 0%, transparent 100%)`,
        'mask-image': `radial-gradient(circle 100px at ${renderedX}px ${renderedY}px, black 0%, transparent 100%)`
      }"
    ></div>

    <!-- Subtle texture -->
    <div class="obsidian-hero__texture"></div>

    <!-- Branding Layer -->
    <div class="obsidian-hero__branding">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

/**
 * ObsidianHero.vue
 * Implements smooth trailing delay (Lerp) and dual-layer mesh for dot-only glow.
 */

const heroContainer = ref(null)

// Target is where the mouse is
const targetX = ref(-500)
const targetY = ref(-500)

// Rendered is where the glow currently is (the trailing effect)
const renderedX = ref(-500)
const renderedY = ref(-500)

let rafId = null

const lerp = (start, end, factor) => start + (end - start) * factor

function updateGlowPosition() {
  // 0.1 factor creates the "smooth trailing" feel
  renderedX.value = lerp(renderedX.value, targetX.value, 0.1)
  renderedY.value = lerp(renderedY.value, targetY.value, 0.1)
  
  rafId = requestAnimationFrame(updateGlowPosition)
}

function handleMouseMove(e) {
  if (!heroContainer.value) return
  const rect = heroContainer.value.getBoundingClientRect()
  targetX.value = e.clientX - rect.left
  targetY.value = e.clientY - rect.top
}

function handleMouseLeave() {
  // Optionally move the glow off-screen when mouse leaves
  targetX.value = -500
  targetY.value = -500
}

onMounted(() => {
  updateGlowPosition()
})

onUnmounted(() => {
  if (rafId) cancelAnimationFrame(rafId)
})
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
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.05) 0%, transparent 100%);
}

.obsidian-hero__glint {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  pointer-events: none;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
  will-change: transform, opacity;
}

.obsidian-hero__glint--1 {
  width: 80%; height: 60%; top: -20%; left: -10%;
  animation: obsidian-shimmer 15s infinite alternate ease-in-out;
}

.obsidian-hero__glint--2 {
  width: 60%; height: 40%; bottom: 0%; right: -5%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.06) 0%, transparent 70%);
  animation: obsidian-shimmer 20s infinite alternate-reverse ease-in-out;
  animation-delay: -4s;
}

/* Mesh Base: The normal dots */
.obsidian-hero__mesh {
  position: absolute;
  inset: 0;
  background-size: 20px 20px;
  background-position: center;
  pointer-events: none;
}

.obsidian-hero__mesh--base {
  background-image: radial-gradient(rgba(255, 255, 255, 0.16) 1.5px, transparent 0);
  mask-image: linear-gradient(180deg, black 0%, rgba(0, 0, 0, 0.4) 60%, transparent 100%);
  -webkit-mask-image: linear-gradient(180deg, black 0%, rgba(0, 0, 0, 0.4) 60%, transparent 100%);
  opacity: 0.8;
  z-index: 1;
}

/* Mesh Active: The "Pop and Glow" dots */
.obsidian-hero__mesh--active {
  /* Larger, brighter dots (2.5px instead of 1.5px) */
  background-image: radial-gradient(rgba(255, 255, 255, 0.9) 2.5px, transparent 0);
  z-index: 2;
  will-change: mask-image, -webkit-mask-image;
}

.obsidian-hero__texture {
  position: absolute;
  inset: 0;
  opacity: 0.04;
  pointer-events: none;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
}

.obsidian-hero__branding {
  position: relative;
  z-index: 10;
  padding: 52px 40px;
}

@keyframes obsidian-shimmer {
  0% { transform: translate3d(0, 0, 0) scale(1); opacity: 0.6; }
  100% { transform: translate3d(10%, 5%, 0) scale(1.15); opacity: 1; }
}
</style>
