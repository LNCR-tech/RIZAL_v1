<template>
  <section
    class="mobile-attendance-stage"
    :class="{
      'mobile-attendance-stage--ready': cameraReady,
      'mobile-attendance-stage--face-ready': faceDetected,
      'mobile-attendance-stage--busy': busy,
    }"
    aria-label="Attendance scanner"
  >
    <!-- Layer 1: Blurred background video -->
    <video
      v-show="cameraReady"
      :ref="backgroundVideoRef"
      class="mobile-attendance-stage__video mobile-attendance-stage__video--bg"
      autoplay
      playsinline
      webkit-playsinline
      disablePictureInPicture
      disableRemotePlayback
      controlslist="nodownload noplaybackrate noremoteplayback"
      muted
    />

    <!-- Layer 2: Clear sharp focus video -->
    <div class="mobile-attendance-stage__focus-mask">
      <video
        v-show="cameraReady"
        :ref="focusVideoRef"
        class="mobile-attendance-stage__video mobile-attendance-stage__video--focus"
        autoplay
        playsinline
        webkit-playsinline
        disablePictureInPicture
        disableRemotePlayback
        controlslist="nodownload noplaybackrate noremoteplayback"
        muted
      />

      <img
        v-if="!cameraReady && faceImageUrl"
        :src="faceImageUrl"
        alt="Attendance preview"
        class="mobile-attendance-stage__fallback"
      >
      <div v-else-if="!cameraReady" class="mobile-attendance-stage__fallback-placeholder">
        <UserRound :size="56" :stroke-width="1.8" />
      </div>
    </div>

    <!-- Ambient dimming overlay -->
    <div class="mobile-attendance-stage__ambient"></div>

    <!-- Layer 3: Corner brackets using SVG for rounded ends -->
    <div class="mobile-attendance-stage__frame" aria-hidden="true">
      <svg class="mobile-attendance-stage__brackets" viewBox="0 0 270 308" fill="none" xmlns="http://www.w3.org/2000/svg">
        <!-- Top Left -->
        <path d="M 64 3 L 24 3 C 12.4 3 3 12.4 3 24 L 3 64" stroke="currentColor" stroke-width="4.5" stroke-linecap="round"/>
        <!-- Top Right -->
        <path d="M 206 3 L 246 3 C 257.6 3 267 12.4 267 24 L 267 64" stroke="currentColor" stroke-width="4.5" stroke-linecap="round"/>
        <!-- Bottom Left -->
        <path d="M 64 305 L 24 305 C 12.4 305 3 295.6 3 284 L 3 244" stroke="currentColor" stroke-width="4.5" stroke-linecap="round"/>
        <!-- Bottom Right -->
        <path d="M 206 305 L 246 305 C 257.6 305 267 295.6 267 284 L 267 244" stroke="currentColor" stroke-width="4.5" stroke-linecap="round"/>
      </svg>
    </div>
  </section>
</template>

<script setup>
import { UserRound } from 'lucide-vue-next'

defineProps({
  backgroundVideoRef: {
    type: Function,
    default: undefined,
  },
  focusVideoRef: {
    type: Function,
    default: undefined,
  },
  cameraReady: {
    type: Boolean,
    default: false,
  },
  faceDetected: {
    type: Boolean,
    default: false,
  },
  busy: {
    type: Boolean,
    default: false,
  },
  faceImageUrl: {
    type: String,
    default: '',
  },
})
</script>

<style scoped>
/* ── Root ── */
.mobile-attendance-stage {
  position: absolute;
  inset: 0;
}

/* ── Shared video base ── */
.mobile-attendance-stage__video {
  /* Using absolute layout. Parent will contain. */
  object-fit: cover;
  transform: scaleX(-1);
  background: #0a0a0a;
}

.mobile-attendance-stage__video::-webkit-media-controls,
.mobile-attendance-stage__video::-webkit-media-controls-enclosure,
.mobile-attendance-stage__video::-webkit-media-controls-panel,
.mobile-attendance-stage__video::-webkit-media-controls-play-button,
.mobile-attendance-stage__video::-webkit-media-controls-start-playback-button,
.mobile-attendance-stage__video::-webkit-media-controls-overlay-play-button {
  display: none !important;
  opacity: 0 !important;
}

/* ── Layer 1: Blurred background video ── */
.mobile-attendance-stage__video--bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  filter: blur(12px) saturate(1.05) brightness(0.94);
  transform: scale(1.08) scaleX(-1);
}

/* ── Layer 2: Clear sharp focus video ── */
.mobile-attendance-stage__focus-mask {
  position: absolute;
  top: 46%;
  left: 50%;
  width: min(68vw, 270px);
  height: calc(min(68vw, 270px) * 1.14);
  transform: translate(-50%, -50%);
  border-radius: 24px;
  overflow: hidden;
  z-index: 2;
  /* Dual gradients exact mask with a 15px soft feather fade */
  -webkit-mask-image: 
    linear-gradient(to right, transparent 0, black 15px, black calc(100% - 15px), transparent 100%),
    linear-gradient(to bottom, transparent 0, black 15px, black calc(100% - 15px), transparent 100%);
  -webkit-mask-composite: source-in;
  mask-image: 
    linear-gradient(to right, transparent 0, black 15px, black calc(100% - 15px), transparent 100%),
    linear-gradient(to bottom, transparent 0, black 15px, black calc(100% - 15px), transparent 100%);
  mask-composite: intersect;
}

.mobile-attendance-stage__video--focus {
  position: absolute;
  /* Align perfectly with screen center */
  /* Focus mask is centered at 46% height. To place focus video at 50% height, push down 4vh from mask center */
  top: calc(50% + 4vh);
  left: 50%;
  width: 100vw;
  height: 100vh;
  /* Negative translate aligns it perfectly back to the viewport bounds */
  transform: translate(-50%, -50%) scaleX(-1);
  margin: 0;
}

/* ── Fallback states ── */
.mobile-attendance-stage__fallback {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.mobile-attendance-stage__fallback-placeholder {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.85);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0.06)),
    rgba(10, 10, 10, 0.28);
  backdrop-filter: blur(10px);
}

/* ── Ambient dimming overlay ── */
.mobile-attendance-stage__ambient {
  position: absolute;
  inset: 0;
  z-index: 3;
  background:
    radial-gradient(
      ellipse 52% 30% at 50% 46%,
      transparent 0%,
      rgba(0, 0, 0, 0.18) 100%
    );
  pointer-events: none;
}

/* ── Layer 3: Corner brackets ── */
.mobile-attendance-stage__frame {
  position: absolute;
  z-index: 4;
  top: 46%;
  left: 50%;
  width: min(68vw, 270px);
  height: calc(min(68vw, 270px) * 1.14);
  transform: translate(-50%, -50%);
  pointer-events: none;
}

.mobile-attendance-stage__brackets {
  width: 100%;
  height: 100%;
  color: rgba(255, 255, 255, 0.88);
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.12));
  transition:
    color 220ms ease,
    opacity 220ms ease,
    transform 220ms cubic-bezier(0.2, 0, 0, 1);
}

.mobile-attendance-stage--face-ready .mobile-attendance-stage__brackets {
  color: rgba(255, 255, 255, 0.98);
  animation: mobile-attendance-stage-pulse 1.8s ease-in-out infinite;
}

.mobile-attendance-stage--busy .mobile-attendance-stage__brackets {
  transform: scale(1.02);
}

@keyframes mobile-attendance-stage-pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }

  50% {
    opacity: 0.74;
    transform: scale(1.03);
  }
}

@media (prefers-reduced-motion: reduce) {
  .mobile-attendance-stage__brackets {
    transition: none;
    animation: none;
  }
}
</style>
