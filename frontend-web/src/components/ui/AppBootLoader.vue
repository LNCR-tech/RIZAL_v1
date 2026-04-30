<template>
  <div
    class="app-boot-loader"
    role="status"
    aria-live="polite"
    aria-label="Loading Aura"
  >
    <div class="app-boot-loader__viewport">
      <DotLottieVue
        ref="playerRef"
        class="app-boot-loader__animation"
        animation-id="Main Scene"
        autoplay
        loop
        :src="splashAnimationUrl"
      />
    </div>

    <span class="app-boot-loader__sr-only">Loading Aura</span>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { DotLottieVue } from '@lottiefiles/dotlottie-vue'
import splashAnimationUrl from '@/assets/animations/splash.lottie?url'
import { markBootSplashPlaybackReady } from '@/services/bootSplash.js'

const playerRef = ref(null)

let dotLottieInstance = null
let attachAttempts = 0
let attachTimer = null
let playbackReadyNotified = false

function notifyPlaybackReady() {
  if (playbackReadyNotified) {
    return
  }

  playbackReadyNotified = true
  markBootSplashPlaybackReady()
}

function handlePlayerReady() {
  if (!dotLottieInstance) {
    return
  }

  dotLottieInstance.setLoop(true)
  dotLottieInstance.play()
  notifyPlaybackReady()
}

function attachPlayerListeners() {
  dotLottieInstance = playerRef.value?.getDotLottieInstance?.() ?? null

  if (!dotLottieInstance) {
    attachAttempts += 1
    if (attachAttempts <= 20) {
      attachTimer = window.setTimeout(attachPlayerListeners, 50)
    }
    return
  }

  dotLottieInstance.addEventListener('ready', handlePlayerReady)
  dotLottieInstance.addEventListener('load', handlePlayerReady)
  dotLottieInstance.addEventListener('play', notifyPlaybackReady)

  if (dotLottieInstance.isLoaded) {
    handlePlayerReady()
  }
}

onMounted(() => {
  nextTick(() => {
    attachPlayerListeners()
  })
})

onBeforeUnmount(() => {
  if (attachTimer) {
    window.clearTimeout(attachTimer)
    attachTimer = null
  }

  if (!dotLottieInstance) {
    return
  }

  dotLottieInstance.removeEventListener('ready', handlePlayerReady)
  dotLottieInstance.removeEventListener('load', handlePlayerReady)
  dotLottieInstance.removeEventListener('play', notifyPlaybackReady)
})
</script>

<style scoped>
.app-boot-loader {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  background: #050505;
}

.app-boot-loader__viewport {
  width: min(100vw, 430px);
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.app-boot-loader__animation {
  width: 100%;
  height: 100%;
  min-height: 100dvh;
}

.app-boot-loader__sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
