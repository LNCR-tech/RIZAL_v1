<template>
  <!--
    University Banner Card
    The school logo is clipped by the card's overflow-hidden + border-radius,
    creating the "half-masked into the corner" effect from the designer reference.
    Backend-ready: schoolName + schoolLogo come from /school-settings/me response.
  -->
  <div
    class="relative rounded-3xl overflow-hidden w-full"
    style="background: var(--color-primary); min-height: 200px;"
  >
    <!-- Text content -->
    <div class="relative z-10 p-5 flex flex-col justify-between" style="min-height: 200px;">
      <div>
        <p class="text-[13px] font-semibold opacity-80" style="color: var(--color-banner-text);">Welcome to</p>
        <h2
          class="text-[28px] font-extrabold leading-tight mt-0.5"
          style="color: var(--color-banner-text); max-width: 55%;"
        >
          {{ schoolName }}
        </h2>
      </div>

      <!-- Announcement Button -->
        <button
          @click="$emit('announcement-click')"
          class="mt-4 flex items-center gap-3 rounded-full pl-3 pr-5 py-2.5 self-start transition-all duration-150 hover:scale-105 active:scale-95 group"
          style="background: var(--color-nav);"
        >
          <span class="flex items-center justify-center w-7 h-7 rounded-full bg-white/10 group-hover:bg-white/20 transition-colors">
            <ArrowRight :size="14" color="var(--color-nav-text)" :stroke-width="2.5" />
          </span>
        <span class="text-[12px] font-semibold" style="color: var(--color-nav-text);">Latest Announcement</span>
        </button>
    </div>

    <!--
      University Logo — absolutely positioned inside the card.
      right: -20px pushes ~15% of the logo beyond the card's right edge.
      The card's overflow:hidden + border-radius clips it naturally,
      creating the rounded mask effect seen in the designer reference.
      Adjust right offset (--logo-offset) to control how much is clipped.
    -->
    <div
      v-if="resolvedLogoSrc && !logoUnavailable"
      class="logo-wrap"
    >
      <img
        :src="resolvedLogoSrc"
        :alt="schoolName + ' logo'"
        class="logo-img object-contain drop-shadow-xl opacity-95"
        @error="onLogoError"
      />
    </div>
    <div v-else class="logo-fallback" aria-hidden="true">
      {{ schoolInitials }}
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { ArrowRight } from 'lucide-vue-next'
import { resolveBackendMediaCandidates, resolveLoadableMediaUrl } from '@/services/backendMedia.js'

const props = defineProps({
  schoolName: {
    type: String,
    default: 'University Name',
  },
  schoolLogo: {
    type: String,
    default: '',
  },
  schoolLogoCandidates: {
    type: Array,
    default: () => [],
  },
  apiBaseUrl: {
    type: String,
    default: '',
  },
})

defineEmits(['announcement-click'])

const logoUnavailable = ref(false)
const resolvedLogoSrc = ref('')
const schoolInitials = computed(() => buildInitials(props.schoolName))
const resolvedLogoCandidates = computed(() => {
  const candidates = props.schoolLogoCandidates.length
    ? props.schoolLogoCandidates
    : [props.schoolLogo]

  return resolveBackendMediaCandidates(candidates, props.apiBaseUrl)
})
let logoRequestId = 0

function onLogoError() {
  logoUnavailable.value = true
}

watch(
  () => [props.apiBaseUrl, resolvedLogoCandidates.value.join('|')],
  async () => {
    const requestId = ++logoRequestId
    logoUnavailable.value = false
    resolvedLogoSrc.value = ''

    if (!resolvedLogoCandidates.value.length) {
      logoUnavailable.value = true
      return
    }

    const nextLogoSrc = await resolveLoadableMediaUrl(
      resolvedLogoCandidates.value,
      props.apiBaseUrl
    )

    if (requestId !== logoRequestId) return

    resolvedLogoSrc.value = nextLogoSrc || ''
    logoUnavailable.value = !nextLogoSrc
  },
  { immediate: true }
)

function buildInitials(value) {
  const parts = String(value || '').split(' ').filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
  return String(value || '').slice(0, 2).toUpperCase()
}
</script>

<style scoped>
/*
  Logo wrapper — absolute, vertically centred, pushed right so
  the card's overflow:hidden + rounded-3xl clips the right portion.
  Change right value to control how much of the logo is clipped:
    0px   = fully inside, touching the right edge
   -20px  = ~15% clipped  (current — matches designer)
   -40px  = ~30% clipped
*/
.logo-wrap {
  position: absolute;
  right: -20px;
  top: 68%;
  transform: translateY(-50%);
  pointer-events: none;
  z-index: 1;
}

.logo-img {
  width: 140px;
  height: 140px;
}

.logo-fallback {
  position: absolute;
  right: -20px;
  top: 68%;
  transform: translateY(-50%);
  width: 140px;
  height: 140px;
  border-radius: 32px;
  background: rgba(255, 255, 255, 0.14);
  color: var(--color-banner-text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 800;
  letter-spacing: 0.08em;
  pointer-events: none;
  z-index: 1;
}

@media (min-width: 768px) {
  .logo-wrap {
    right: -24px;
  }
  .logo-img {
    width: 165px;
    height: 165px;
  }
  .logo-fallback {
    right: -24px;
    width: 165px;
    height: 165px;
  }
}
</style>
