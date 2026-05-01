<template>
  <div class="obsidian-bg" aria-hidden="true">
    <div class="obsidian-bg__base"></div>
    <div class="obsidian-bg__glint obsidian-bg__glint--1"></div>
    <div class="obsidian-bg__glint obsidian-bg__glint--2"></div>
    <canvas ref="bgCanvas" class="obsidian-bg__canvas"></canvas>
    <div class="obsidian-bg__texture"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

/**
 * ObsidianBackground.vue - The persistent global "Sleek Obsidian" floor.
 * Optimized for dashboard background performance.
 */

const bgCanvas = ref(null)
const mouseX = ref(-1000)
const mouseY = ref(-1000)

const GRID_SIZE = 24 // Slightly larger for dashboard performance
const DOT_SIZE = 1.2
const HOVER_RADIUS = 150
const MAX_LIFT = 12

let ctx = null
let width = 0
let height = 0
let rafId = null

class Dot {
  constructor(x, y) {
    this.baseX = x
    this.baseY = y
    this.currentY = y
    this.opacity = 0.12
  }

  update(mX, mY) {
    const dx = mX - this.baseX
    const dy = mY - this.baseY
    const dist = Math.sqrt(dx * dx + dy * dy)

    if (dist < HOVER_RADIUS) {
      const factor = 1 - (dist / HOVER_RADIUS)
      const targetY = this.baseY - (factor * MAX_LIFT)
      this.currentY += (targetY - this.currentY) * 0.08
      this.opacity = 0.12 + (factor * 0.4)
    } else {
      this.currentY += (this.baseY - this.currentY) * 0.05
      this.opacity = 0.12
    }
  }

  draw(context) {
    context.fillStyle = `rgba(0, 0, 0, ${this.opacity})`
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
  if (!bgCanvas.value) return
  width = window.innerWidth
  height = window.innerHeight
  bgCanvas.value.width = width * window.devicePixelRatio
  bgCanvas.value.height = height * window.devicePixelRatio
  ctx = bgCanvas.value.getContext('2d')
  ctx.scale(window.devicePixelRatio, window.devicePixelRatio)
  initGrid()
}

function animate() {
  if (!ctx) return
  ctx.clearRect(0, 0, width, height)
  for (let i = 0; i < dots.length; i++) {
    dots[i].update(mouseX.value, mouseY.value)
    dots[i].draw(ctx)
  }
  rafId = requestAnimationFrame(animate)
}

function handleMouseMove(e) {
  mouseX.value = e.clientX
  mouseY.value = e.clientY
}

onMounted(() => {
  window.addEventListener('resize', resize)
  window.addEventListener('mousemove', handleMouseMove)
  resize()
  animate()
})

onUnmounted(() => {
  window.removeEventListener('resize', resize)
  window.removeEventListener('mousemove', handleMouseMove)
  if (rafId) cancelAnimationFrame(rafId)
})
</script>

<style scoped>
.obsidian-bg {
  position: fixed;
  inset: 0;
  background-color: var(--color-bg);
  z-index: -1;
  pointer-events: none;
}

.obsidian-bg__base {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 50% 0%, rgba(0, 0, 0, 0.02) 0%, transparent 70%);
}

.obsidian-bg__canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.obsidian-bg__glint {
  position: absolute;
  border-radius: 50%;
  filter: blur(140px);
  background: radial-gradient(circle, var(--color-primary-glint, rgba(0, 0, 0, 0.03)) 0%, transparent 70%);
  animation: bg-shimmer 20s infinite alternate ease-in-out;
}

.obsidian-bg__glint--1 { width: 100%; height: 80%; top: -10%; left: -20%; }
.obsidian-bg__glint--2 { width: 80%; height: 60%; bottom: -10%; right: -10%; animation-delay: -5s; }

.obsidian-bg__texture {
  position: absolute;
  inset: 0;
  opacity: 0.03;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
}

@keyframes bg-shimmer {
  0% { transform: translate3d(-10%, -5%, 0) scale(1); opacity: 0.4; }
  100% { transform: translate3d(10%, 5%, 0) scale(1.1); opacity: 0.6; }
}
</style>
