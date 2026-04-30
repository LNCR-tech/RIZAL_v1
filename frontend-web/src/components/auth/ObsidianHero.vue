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

    <!-- Base Halftone Mesh (The "Floor") -->
    <div class="obsidian-hero__mesh obsidian-hero__mesh--base"></div>

    <!-- Floating Halftone Mesh (The "Lifted" Layer) -->
    <div 
      class="obsidian-hero__mesh obsidian-hero__mesh--active"
      :style="{
        '-webkit-mask-image': `radial-gradient(circle 100px at ${renderedX}px ${renderedY}px, black 0%, transparent 100%)`,
        'mask-image': `radial-gradient(circle 100px at ${renderedX}px ${renderedY}px, black 0%, transparent 100%)`,
        'opacity': renderedOpacity,
        'transform': `translate3d(0, ${renderedOpacity * -10}px, 0)`
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
 * Implements "Physical Lift" using translateY and downward shadow offsets.
 */

const heroContainer = ref(null)

// Physics state
const targetX = ref(null)
const targetY = ref(null)
const targetOpacity = ref(0)

const renderedX = ref(0)
const renderedY = ref(0)
const renderedOpacity = ref(0)

let rafId = null

const lerp = (start, end, factor) => start + (end - start) * factor

function updatePhysics() {
  if (targetX.value !== null) {
    renderedX.value = lerp(renderedX.value, targetX.value, 0.1)
    renderedY.value = lerp(renderedY.value, targetY.value, 0.1)
  }
  
  // Smoothly fade/lift in and out
  renderedOpacity.value = lerp(renderedOpacity.value, targetOpacity.value, 0.08)
  
  rafId = requestAnimationFrame(updatePhysics)
}

function handleMouseMove(e) {
  if (!heroContainer.value) return
  const rect = heroContainer.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  
  if (targetOpacity.value === 0) {
    renderedX.value = x
    renderedY.value = y
  }
  
  targetX.value = x
  targetY.value = y
  targetOpacity.value = 1
}

function handleMouseLeave() {
  targetOpacity.value = 0
}

onMounted(() => {
  updatePhysics()
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

/* Mesh Base: The normal dots (The "Floor") */
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

/* Mesh Active: The "Lifted" Layer */
.obsidian-hero__mesh--active {
  background-image: radial-gradient(rgba(255, 255, 255, 0.95) 1.5px, transparent 0);
  z-index: 2;
  
  /* Drop-shadow is offset DOWNWARD (10px) to simulate height from the floor */
  filter: drop-shadow(0 10px 5px rgba(255, 255, 255, 0.25));
  
  will-change: mask-image, -webkit-mask-image, transform, opacity;
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
