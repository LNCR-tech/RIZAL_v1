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

    <!-- The Interactive Physics Mesh (Canvas) -->
    <canvas ref="meshCanvas" class="obsidian-hero__canvas"></canvas>

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
 * ObsidianHero.vue - 3D Pin-Mesh Edition
 * Implements "Pillar" connections for a tactical 3D depth effect.
 */

const heroContainer = ref(null)
const meshCanvas = ref(null)

// Mouse tracking
const mouseX = ref(-1000)
const mouseY = ref(-1000)
const isHovering = ref(false)

// Grid Settings
const GRID_SIZE = 20
const DOT_SIZE = 1.5
const HOVER_RADIUS = 120
const MAX_LIFT = 12 // Increased lift for better pillar visibility

let ctx = null
let width = 0
let height = 0
let rafId = null

// Dot object structure
class Dot {
  constructor(x, y) {
    this.baseX = x
    this.baseY = y
    this.currentY = y
    this.opacity = 0.16
    this.targetOpacity = 0.16
  }

  update(mX, mY, hovering) {
    const dx = mX - this.baseX
    const dy = mY - this.baseY
    const dist = Math.sqrt(dx * dx + dy * dy)

    if (hovering && dist < HOVER_RADIUS) {
      const factor = 1 - (dist / HOVER_RADIUS)
      const targetY = this.baseY - (factor * MAX_LIFT)
      
      this.currentY += (targetY - this.currentY) * 0.1
      this.targetOpacity = 0.16 + (factor * 0.8)
    } else {
      this.currentY += (this.baseY - this.currentY) * 0.08
      this.targetOpacity = 0.16
    }

    this.opacity += (this.targetOpacity - this.opacity) * 0.1
  }

  draw(context) {
    // 1. Draw the "Pillar" (Stem) if lifted
    if (Math.abs(this.currentY - this.baseY) > 0.5) {
      context.strokeStyle = `rgba(255, 255, 255, ${this.opacity * 0.25})`
      context.lineWidth = 0.5
      context.beginPath()
      context.moveTo(this.baseX, this.baseY)
      context.lineTo(this.baseX, this.currentY)
      context.stroke()
    }

    // 2. Draw the "Cap" (The Dot)
    context.fillStyle = `rgba(255, 255, 255, ${this.opacity})`
    context.beginPath()
    context.arc(this.baseX, this.currentY, DOT_SIZE / 2, 0, Math.PI * 2)
    context.fill()
  }
}

let dots = []

function initGrid() {
  dots = []
  for (let x = GRID_SIZE / 2; x < width; x += GRID_SIZE) {
    for (let y = GRID_SIZE / 2; y < height; y += GRID_SIZE) {
      dots.push(new Dot(x, y))
    }
  }
}

function resize() {
  if (!heroContainer.value || !meshCanvas.value) return
  const rect = heroContainer.value.getBoundingClientRect()
  width = rect.width
  height = rect.height
  meshCanvas.value.width = width * window.devicePixelRatio
  meshCanvas.value.height = height * window.devicePixelRatio
  ctx = meshCanvas.value.getContext('2d')
  ctx.scale(window.devicePixelRatio, window.devicePixelRatio)
  initGrid()
}

function animate() {
  if (!ctx) return
  ctx.clearRect(0, 0, width, height)

  for (let i = 0; i < dots.length; i++) {
    dots[i].update(mouseX.value, mouseY.value, isHovering.value)
    dots[i].draw(ctx)
  }

  rafId = requestAnimationFrame(animate)
}

function handleMouseMove(e) {
  if (!heroContainer.value) return
  const rect = heroContainer.value.getBoundingClientRect()
  mouseX.value = e.clientX - rect.left
  mouseX.value = e.clientX - rect.left
  mouseY.value = e.clientY - rect.top
  isHovering.value = true
}

function handleMouseLeave() {
  isHovering.value = false
}

onMounted(() => {
  window.addEventListener('resize', resize)
  resize()
  animate()
})

onUnmounted(() => {
  window.removeEventListener('resize', resize)
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

.obsidian-hero__canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.obsidian-hero__glint {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  pointer-events: none;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.08) 0%, transparent 70%);
  will-change: transform, opacity;
}

.obsidian-hero__glint--1 {
  width: 80%; height: 60%; top: -20%; left: -10%;
  animation: obsidian-shimmer 15s infinite alternate ease-in-out;
}

.obsidian-hero__glint--2 {
  width: 60%; height: 40%; bottom: 0%; right: -5%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.05) 0%, transparent 70%);
  animation: obsidian-shimmer 20s infinite alternate-reverse ease-in-out;
  animation-delay: -4s;
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
  0% { transform: translate3d(-15%, -10%, 0) scale(1) rotate(0deg); opacity: 0.4; }
  50% { opacity: 0.8; }
  100% { transform: translate3d(15%, 10%, 0) scale(1.2) rotate(10deg); opacity: 0.4; }
}
</style>
