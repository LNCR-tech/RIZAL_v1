<template>
  <div
    class="gather-welcome"
    @touchstart.passive="handleTouchStart"
    @touchend.passive="handleTouchEnd"
  >
    <div class="gather-welcome__shell">
      <div class="gather-welcome__topbar">
        <button
          v-if="showSkipButton"
          class="gather-welcome__skip"
          type="button"
          @click="skipToEnd"
        >
          Skip
        </button>
      </div>

      <div class="gather-welcome__viewport">
        <Transition :name="transitionName" mode="out-in">
          <article :key="currentSlide.id" class="gather-welcome__slide" :style="currentSlideArtStyle">
            <div class="gather-welcome__hero">
              <div class="gather-welcome__art-card">
                <DotLottieVue
                  v-if="currentSlide.animationSrc"
                  class="gather-welcome__animation"
                  autoplay
                  loop
                  :src="currentSlide.animationSrc"
                />

                <div v-else class="gather-welcome__placeholder">
                  <div class="gather-welcome__placeholder-orb" />
                  <div class="gather-welcome__placeholder-icon">
                    <component :is="currentSlide.fallbackIcon" :size="36" :stroke-width="2.1" />
                  </div>
                  <p class="gather-welcome__placeholder-label">{{ currentSlide.fallbackLabel }}</p>
                  <p class="gather-welcome__placeholder-note">Drop in the dotLottie source later and this slide will use it automatically.</p>
                </div>
              </div>
            </div>

            <div class="gather-welcome__content">
              <h1
                v-if="currentSlide.titleGradient?.text && currentSlide.titlePrefix"
                class="gather-welcome__title gather-welcome__title--gradient"
              >
                <span>{{ currentSlide.titlePrefix }}</span>
                <GradientText
                  class="gather-welcome__title-gradient"
                  :colors="currentSlide.titleGradient.colors"
                  :animation-speed="currentSlide.titleGradient.animationSpeed"
                  :show-border="currentSlide.titleGradient.showBorder"
                  :direction="currentSlide.titleGradient.direction"
                >
                  {{ currentSlide.titleGradient.text }}
                </GradientText>
              </h1>
              <h1 v-else class="gather-welcome__title">{{ currentSlide.title }}</h1>
              <p class="gather-welcome__description">{{ currentSlide.description }}</p>
            </div>
          </article>
        </Transition>
      </div>

      <footer class="gather-welcome__footer">
        <div class="gather-welcome__indicators" role="tablist" aria-label="Gather tutorial slides">
          <button
            v-for="(slide, index) in slides"
            :key="slide.id"
            type="button"
            class="gather-welcome__indicator"
            :class="{ 'gather-welcome__indicator--active': index === currentIndex }"
            :aria-label="`Go to slide ${index + 1}`"
            :aria-current="index === currentIndex ? 'true' : 'false'"
            @click="goToSlide(index)"
          />
        </div>

        <button class="gather-welcome__primary" type="button" @click="handlePrimaryAction">
          <span>{{ primaryActionLabel }}</span>
          <component :is="primaryActionIcon" :size="16" :stroke-width="2.2" />
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DotLottieVue } from '@lottiefiles/dotlottie-vue'
import { ArrowRight, CircleCheckBig } from 'lucide-vue-next'
import GradientText from '@/components/ui/GradientText.vue'
import { gatherTutorialSlides } from '@/data/gatherTutorialSlides.js'
import { isNativeApp, primeLocationAccess, requestLocationPermission } from '@/services/devicePermissions.js'
import { hasSeenGatherOnboarding, markGatherOnboardingSeen } from '@/services/gatherOnboarding.js'
import { resolveGatherAttendanceLocation } from '@/services/routeWorkspace.js'

defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const router = useRouter()
const route = useRoute()
const slides = gatherTutorialSlides
const currentIndex = ref(0)
const transitionDirection = ref('forward')
const touchStartX = ref(null)
const locationPermissionRequested = ref(false)

const currentSlide = computed(() => slides[currentIndex.value] || slides[0])
const currentSlideArtStyle = computed(() => {
  const artSize = Number(currentSlide.value?.artSize) || 198
  return {
    '--gather-art-size': `${artSize}px`,
  }
})
const isLastSlide = computed(() => currentIndex.value === slides.length - 1)
const showSkipButton = computed(() => slides.length > 1 && !isLastSlide.value)
const primaryActionLabel = computed(() => {
  if (!isLastSlide.value) return 'Next'
  return 'Gather and attendance now'
})
const primaryActionIcon = computed(() => (
  isLastSlide.value ? CircleCheckBig : ArrowRight
))
const transitionName = computed(() => (
  transitionDirection.value === 'forward' ? 'gather-slide-forward' : 'gather-slide-backward'
))

function goToSlide(index) {
  const normalizedIndex = Number(index)
  if (!Number.isInteger(normalizedIndex)) return
  if (normalizedIndex < 0 || normalizedIndex >= slides.length || normalizedIndex === currentIndex.value) return

  transitionDirection.value = normalizedIndex > currentIndex.value ? 'forward' : 'backward'
  currentIndex.value = normalizedIndex
}

function nextSlide() {
  if (isLastSlide.value) return
  goToSlide(currentIndex.value + 1)
}

function skipToEnd() {
  openGatherExperience()
}

function openGatherExperience() {
  markGatherOnboardingSeen()
  router.replace(resolveGatherAttendanceLocation(route))
}

function handlePrimaryAction() {
  if (!isLastSlide.value) {
    nextSlide()
    return
  }

  openGatherExperience()
}

function handleTouchStart(event) {
  touchStartX.value = event.changedTouches?.[0]?.clientX ?? null
}

function handleTouchEnd(event) {
  if (touchStartX.value == null) return

  const touchEndX = event.changedTouches?.[0]?.clientX ?? touchStartX.value
  const deltaX = touchEndX - touchStartX.value
  touchStartX.value = null

  if (Math.abs(deltaX) < 48) return
  if (deltaX < 0) {
    nextSlide()
    return
  }

  goToSlide(currentIndex.value - 1)
}

watch(
  () => currentSlide.value?.id,
  async (slideId) => {
    if (!isNativeApp()) return
    if (slideId !== 'share-location' || locationPermissionRequested.value) return

    locationPermissionRequested.value = true

    try {
      const permission = await requestLocationPermission()
      if (permission.granted) {
        void primeLocationAccess()
      }
    } catch {
      // Leave the slide interactive even if the native prompt fails.
    }
  },
  { immediate: true },
)

onMounted(() => {
  if (hasSeenGatherOnboarding()) {
    router.replace(resolveGatherAttendanceLocation(route))
    return
  }

  markGatherOnboardingSeen()
})
</script>

<style scoped>
.gather-welcome {
  --gather-accent: var(--color-nav-active);
  --gather-button-bg: var(--color-nav);
  --gather-button-text: var(--color-nav-active);
  --gather-shadow: color-mix(in srgb, var(--color-nav) 18%, transparent);
  --gather-soft-stroke: color-mix(in srgb, var(--color-surface-text) 12%, transparent);
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--gather-accent) 12%, var(--color-bg)) 0%, transparent 34%),
    radial-gradient(circle at 82% 16%, color-mix(in srgb, var(--color-text-primary) 6%, transparent) 0%, transparent 24%),
    linear-gradient(180deg, color-mix(in srgb, var(--color-surface) 74%, var(--color-bg)) 0%, var(--color-bg) 100%);
  color: var(--color-text-primary);
  padding:
    max(24px, calc(env(safe-area-inset-top, 0px) + 12px))
    18px
    max(30px, calc(env(safe-area-inset-bottom, 0px) + 14px));
  font-family: 'Manrope', sans-serif;
}

.gather-welcome__shell {
  width: min(100%, 420px);
  min-height: calc(100vh - 54px);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 16px;
}

.gather-welcome__topbar {
  min-height: 22px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.gather-welcome__viewport {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
}

.gather-welcome__skip {
  appearance: none;
  border: none;
  background: transparent;
  padding: 0;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: color-mix(in srgb, var(--color-text-primary) 38%, transparent);
  cursor: pointer;
  transition: color 180ms ease, opacity 180ms ease;
}

.gather-welcome__skip:hover {
  color: color-mix(in srgb, var(--color-text-primary) 52%, transparent);
}

.gather-welcome__slide {
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 14px;
  text-align: center;
}

.gather-welcome__hero {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
}

.gather-welcome__art-card {
  position: relative;
  width: 100%;
  overflow: visible;
  min-height: calc(var(--gather-art-size, 198px) + 16px);
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.gather-welcome__art-card::before {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  width: calc(var(--gather-art-size, 198px) + 38px);
  height: calc(var(--gather-art-size, 198px) + 38px);
  border-radius: 999px;
  transform: translate(-50%, -50%);
  background:
    radial-gradient(circle, color-mix(in srgb, var(--gather-accent) 16%, var(--color-surface)) 0%, color-mix(in srgb, var(--color-surface) 72%, transparent) 38%, transparent 74%);
  filter: blur(12px);
  opacity: 0.96;
  pointer-events: none;
}

.gather-welcome__animation {
  width: min(100%, var(--gather-art-size, 198px));
  height: min(100%, var(--gather-art-size, 198px));
  position: relative;
  z-index: 1;
}

.gather-welcome__placeholder {
  position: relative;
  z-index: 1;
  width: min(100%, var(--gather-art-size, 198px));
  min-height: var(--gather-art-size, 198px);
  border-radius: 26px;
  background: transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 22px;
  text-align: center;
}

.gather-welcome__placeholder-orb {
  position: absolute;
  inset: 12px 12px auto;
  height: 92px;
  border-radius: 999px;
  background: radial-gradient(circle, color-mix(in srgb, var(--gather-accent) 24%, transparent) 0%, transparent 68%);
  filter: blur(18px);
}

.gather-welcome__placeholder-icon {
  position: relative;
  z-index: 1;
  width: 64px;
  height: 64px;
  border-radius: 22px;
  background: var(--gather-button-bg);
  color: var(--gather-button-text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 18px 30px var(--gather-shadow),
    inset 0 1px 0 color-mix(in srgb, var(--color-nav-text) 8%, transparent);
}

.gather-welcome__placeholder-label,
.gather-welcome__placeholder-note,
.gather-welcome__description {
  margin: 0;
}

.gather-welcome__placeholder-label {
  position: relative;
  z-index: 1;
  font-size: 15px;
  font-weight: 800;
  color: var(--color-text-primary);
  letter-spacing: -0.03em;
}

.gather-welcome__placeholder-note {
  position: relative;
  z-index: 1;
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-text-muted);
}

.gather-welcome__content {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 0;
  align-items: center;
  text-align: center;
}

.gather-welcome__title {
  margin: 0;
  max-width: 12ch;
  font-size: clamp(36px, 10vw, 48px);
  font-weight: 800;
  line-height: 0.94;
  letter-spacing: -0.06em;
  color: var(--color-text-primary);
  white-space: pre-line;
}

.gather-welcome__title--gradient {
  white-space: normal;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: baseline;
  gap: 0 0.18em;
}

.gather-welcome__title-gradient {
  line-height: inherit;
  letter-spacing: inherit;
}

.gather-welcome__description {
  max-width: 28ch;
  font-size: 15px;
  line-height: 1.76;
  color: var(--color-text-secondary);
  margin-inline: auto;
}

.gather-welcome__footer {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 18px;
}

.gather-welcome__indicators {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.gather-welcome__indicator {
  appearance: none;
  border: none;
  font: inherit;
  width: 9px;
  height: 9px;
  border-radius: 999px;
  padding: 0;
  background: color-mix(in srgb, var(--color-text-primary) 14%, transparent);
  cursor: pointer;
  transition: width 220ms ease, background-color 220ms ease, transform 180ms ease;
}

.gather-welcome__indicator--active {
  width: 30px;
  background: var(--gather-accent);
}

.gather-welcome__primary {
  appearance: none;
  border: none;
  font: inherit;
  width: fit-content;
  max-width: min(100%, 280px);
  min-height: 52px;
  margin: 0 auto;
  padding: 0 18px;
  border-radius: 999px;
  background: var(--gather-button-bg);
  color: var(--gather-button-text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-shadow:
    0 16px 30px var(--gather-shadow),
    inset 0 1px 0 color-mix(in srgb, var(--color-nav-text) 8%, transparent);
  font-size: 14px;
  font-weight: 800;
  letter-spacing: -0.02em;
  white-space: nowrap;
  cursor: pointer;
}

.gather-slide-forward-enter-active,
.gather-slide-forward-leave-active,
.gather-slide-backward-enter-active,
.gather-slide-backward-leave-active {
  transition: opacity 220ms ease, transform 300ms cubic-bezier(0.22, 1, 0.36, 1);
}

.gather-slide-forward-enter-from,
.gather-slide-backward-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

.gather-slide-forward-leave-to,
.gather-slide-backward-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

@media (max-width: 380px) {
  .gather-welcome {
    padding-inline: 12px;
  }

  .gather-welcome__shell {
    min-height: calc(100vh - 48px);
  }

  .gather-welcome__art-card {
    min-height: calc(var(--gather-art-size, 198px) + 8px);
  }

  .gather-welcome__title {
    font-size: clamp(32px, 9.8vw, 42px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .gather-welcome__indicator,
  .gather-slide-forward-enter-active,
  .gather-slide-forward-leave-active,
  .gather-slide-backward-enter-active,
  .gather-slide-backward-leave-active {
    transition: none;
  }
}
</style>
