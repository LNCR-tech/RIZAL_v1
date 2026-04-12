<template>
  <component
    :is="tag"
    class="relative inline-flex max-w-fit items-center justify-center overflow-hidden rounded-[1.25rem] transition-shadow duration-500 ease-out"
    :class="{ 'px-3 py-[0.35rem] backdrop-blur-[10px]': showBorder }"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
    <span
      v-if="showBorder"
      aria-hidden="true"
      class="pointer-events-none absolute inset-0 rounded-[inherit]"
      :style="gradientStyle"
    >
      <span class="absolute inset-[1px] rounded-[inherit] bg-[var(--color-bg)]" />
    </span>

    <span
      class="relative z-[1] inline-block bg-clip-text text-transparent"
      :style="gradientStyle"
    >
      <slot />
    </span>
  </component>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  tag: {
    type: String,
    default: 'span',
  },
  colors: {
    type: Array,
    default: () => ['#5227FF', '#FF9FFC', '#B19EEF'],
  },
  animationSpeed: {
    type: Number,
    default: 8,
  },
  showBorder: {
    type: Boolean,
    default: false,
  },
  direction: {
    type: String,
    default: 'horizontal',
    validator: (value) => ['horizontal', 'vertical', 'diagonal'].includes(value),
  },
  pauseOnHover: {
    type: Boolean,
    default: false,
  },
  yoyo: {
    type: Boolean,
    default: true,
  },
})

const isPaused = ref(false)
const progress = ref(0)

let animationFrameId = 0
let elapsedMs = 0
let lastFrameTime = null

const animationDuration = computed(() => Math.max(0.1, Number(props.animationSpeed) || 0) * 1000)
const resolvedColors = computed(() => {
  const palette = Array.isArray(props.colors) && props.colors.length
    ? props.colors
    : ['#5227FF', '#FF9FFC', '#B19EEF']
  return [...palette, palette[0]]
})
const gradientAngle = computed(() => {
  if (props.direction === 'vertical') return 'to bottom'
  if (props.direction === 'diagonal') return 'to bottom right'
  return 'to right'
})
const backgroundSize = computed(() => {
  if (props.direction === 'vertical') return '100% 300%'
  if (props.direction === 'diagonal') return '300% 300%'
  return '300% 100%'
})
const backgroundPosition = computed(() => {
  const currentProgress = progress.value
  if (props.direction === 'vertical') return `50% ${currentProgress}%`
  if (props.direction === 'diagonal') return `${currentProgress}% 50%`
  return `${currentProgress}% 50%`
})
const gradientStyle = computed(() => ({
  backgroundImage: `linear-gradient(${gradientAngle.value}, ${resolvedColors.value.join(', ')})`,
  backgroundSize: backgroundSize.value,
  backgroundRepeat: 'repeat',
  backgroundPosition: backgroundPosition.value,
}))

function resetAnimation() {
  elapsedMs = 0
  lastFrameTime = null
  progress.value = 0
}

function updateProgress(time) {
  if (isPaused.value) {
    lastFrameTime = null
    animationFrameId = requestAnimationFrame(updateProgress)
    return
  }

  if (lastFrameTime == null) {
    lastFrameTime = time
    animationFrameId = requestAnimationFrame(updateProgress)
    return
  }

  const deltaTime = time - lastFrameTime
  lastFrameTime = time
  elapsedMs += deltaTime

  if (props.yoyo) {
    const fullCycle = animationDuration.value * 2
    const cycleTime = elapsedMs % fullCycle

    if (cycleTime < animationDuration.value) {
      progress.value = (cycleTime / animationDuration.value) * 100
    } else {
      progress.value = 100 - (((cycleTime - animationDuration.value) / animationDuration.value) * 100)
    }
  } else {
    progress.value = ((elapsedMs / animationDuration.value) * 100) % 100
  }

  animationFrameId = requestAnimationFrame(updateProgress)
}

function handleMouseEnter() {
  if (props.pauseOnHover) {
    isPaused.value = true
  }
}

function handleMouseLeave() {
  if (props.pauseOnHover) {
    isPaused.value = false
  }
}

watch(
  () => [props.animationSpeed, props.yoyo, props.direction, props.colors],
  () => {
    resetAnimation()
  },
  { deep: true },
)

onMounted(() => {
  animationFrameId = requestAnimationFrame(updateProgress)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(animationFrameId)
})
</script>
