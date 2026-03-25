<template>
  <section class="face-scan-section">
    <Transition name="caption-fade" mode="out-in">
      <p v-if="props.caption" :key="props.caption" class="step-caption">{{ props.caption }}</p>
    </Transition>

    <div class="face-scan">
      <div class="scan-ring">
        <svg class="scan-ring-svg" viewBox="0 0 100 100" aria-hidden="true">
          <circle
            class="scan-ring-base"
            cx="50"
            cy="50"
            :r="circleRadius"
            :stroke-width="props.strokeWidth"
          />
          <g class="scan-ring-arc" :class="{ 'scan-ring-arc--orbit': isSweepAnimating }">
            <circle
              class="scan-ring-progress"
              cx="50"
              cy="50"
              :r="circleRadius"
              :stroke-width="props.strokeWidth"
              pathLength="100"
              :style="progressStyle"
            />
            <circle
              class="scan-ring-dot"
              :cx="startPoint.x"
              :cy="startPoint.y"
              :r="props.dotRadius"
              :fill="props.dotColor"
            />
            <circle
              class="scan-ring-dot"
              :cx="endPoint.x"
              :cy="endPoint.y"
              :r="props.dotRadius"
              :fill="props.dotColor"
              :style="{ opacity: normalizedProgress <= 0 ? 0 : 1 }"
            />
          </g>
        </svg>

        <div class="scan-media">
          <video
            v-show="props.isCameraReady"
            :ref="props.videoRef"
            class="scan-video"
            autoplay
            playsinline
            webkit-playsinline
            disablePictureInPicture
            disableRemotePlayback
            controlslist="nodownload noplaybackrate noremoteplayback"
            muted
          />
          <img
            v-if="!props.isCameraReady && props.faceImageUrl"
            :src="props.faceImageUrl"
            alt="Face scan preview"
            class="scan-photo"
          />
          <div v-else-if="!props.isCameraReady" class="scan-photo scan-photo--placeholder" aria-hidden="true">
            <UserRound :size="46" />
          </div>
        </div>
      </div>
    </div>

    <div v-if="props.showError" class="face-error-block">
      <p class="face-error">{{ props.errorText }}</p>
      <button class="face-retry-btn" type="button" @click="$emit('retry')">{{ props.retryText }}</button>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { UserRound } from 'lucide-vue-next'

const props = defineProps({
  caption: {
    type: String,
    default: "Just a moment, verifying it's you...",
  },
  progress: {
    type: Number,
    default: 0,
  },
  isCameraReady: {
    type: Boolean,
    default: false,
  },
  faceImageUrl: {
    type: String,
    default: '',
  },
  showError: {
    type: Boolean,
    default: false,
  },
  errorText: {
    type: String,
    default: 'No face detected',
  },
  retryText: {
    type: String,
    default: 'Try Again',
  },
  videoRef: {
    type: Function,
    default: undefined,
  },
  visualState: {
    type: String,
    default: '',
  },
  startAngle: {
    type: Number,
    default: -90,
  },
  sweepLength: {
    type: Number,
    default: 78,
  },
  strokeWidth: {
    type: Number,
    default: 9,
  },
  ringRadius: {
    type: Number,
    default: undefined,
  },
  dotRadius: {
    type: Number,
    default: 2.2,
  },
  dotColor: {
    type: String,
    default: '#0a0a0a',
  },
})

defineEmits(['retry'])

const normalizedProgress = computed(() => Math.min(100, Math.max(0, props.progress)))
const animatedStates = new Set(['starting', 'detecting', 'capturing', 'submitting'])
const isSweepAnimating = computed(() => animatedStates.has(props.visualState))
const displayProgress = computed(() => (
  isSweepAnimating.value
    ? Math.max(Math.min(100, Math.max(0, props.sweepLength)), normalizedProgress.value)
    : normalizedProgress.value
))
const circleRadius = computed(() => {
  if (typeof props.ringRadius === 'number') return props.ringRadius
  return 50 - props.strokeWidth / 2
})

const progressStyle = computed(() => ({
  strokeDasharray: `${displayProgress.value} 100`,
  opacity: displayProgress.value <= 0 ? 0 : 1,
  transform: `rotate(${props.startAngle}deg)`,
}))

const startPoint = computed(() =>
  polarToCartesian(50, 50, circleRadius.value, props.startAngle)
)

const endPoint = computed(() => {
  const angle = props.startAngle + (displayProgress.value / 100) * 360
  return polarToCartesian(50, 50, circleRadius.value, angle)
})

function polarToCartesian(cx, cy, r, angleDeg) {
  const rad = (angleDeg * Math.PI) / 180
  return {
    x: cx + r * Math.cos(rad),
    y: cy + r * Math.sin(rad),
  }
}
</script>

<style scoped>
.face-scan-section {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
  text-align: center;
}

.step-caption {
  font-size: 13px;
  font-weight: 600;
  color: #5f5f5f;
  margin: 0;
}

.face-error {
  font-size: 11px;
  font-weight: 700;
  color: #d24848;
  margin: 0;
}

.face-error-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-top: 6px;
}

.face-retry-btn {
  border: none;
  background: #ffffff;
  color: #222222;
  font-size: 11px;
  font-weight: 600;
  padding: 8px 24px;
  border-radius: 999px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: transform 0.15s ease;
}

.face-retry-btn:active {
  transform: scale(0.97);
}

.face-scan {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 6px;
}

.scan-ring {
  position: relative;
  width: var(--scan-size);
  height: var(--scan-size);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.scan-ring-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.scan-ring-base {
  fill: none;
  stroke: #f0efe8;
}

.scan-ring-arc {
  transform-origin: 50px 50px;
}

.scan-ring-arc--orbit {
  animation: scan-ring-orbit 3s linear infinite;
}

.scan-ring-progress {
  fill: none;
  stroke: var(--color-primary);
  stroke-linecap: round;
  stroke-dashoffset: 0;
  transform-origin: 50% 50%;
  transition: stroke-dasharray 600ms cubic-bezier(0.22, 1, 0.36, 1), opacity 200ms ease;
}

.scan-ring-dot {
  transition: opacity 0.2s ease;
}

.scan-media {
  width: var(--scan-media);
  height: var(--scan-media);
  border-radius: 50%;
  overflow: hidden;
  background: #f0efe8;
  box-shadow: inset 0 0 0 6px rgba(255, 255, 255, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
}

.scan-video,
.scan-photo {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.scan-video {
  background: #000000;
}

.scan-video::-webkit-media-controls,
.scan-video::-webkit-media-controls-enclosure,
.scan-video::-webkit-media-controls-panel,
.scan-video::-webkit-media-controls-play-button,
.scan-video::-webkit-media-controls-start-playback-button,
.scan-video::-webkit-media-controls-overlay-play-button {
  display: none !important;
  opacity: 0 !important;
}

.scan-photo {
  background: #f2f2f2;
}

.scan-photo--placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8b8b8b;
}

@keyframes scan-ring-orbit {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.caption-fade-enter-active,
.caption-fade-leave-active {
  transition: opacity 0.25s ease;
}

.caption-fade-enter-from,
.caption-fade-leave-to {
  opacity: 0;
}
</style>
