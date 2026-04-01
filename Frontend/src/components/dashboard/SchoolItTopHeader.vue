<template>
  <header ref="headerEl" class="school-it-top-header">
    <button
      ref="profileEl"
      class="school-it-top-header__profile"
      :class="{ 'school-it-top-header__profile--expanded': isExpanded }"
      type="button"
      aria-label="Account actions"
      @click="toggleExpanded"
    >
      <span class="school-it-top-header__profile-main">
        <span class="school-it-top-header__avatar-wrap">
          <img
            v-if="avatarUrl"
            :src="avatarUrl"
            :alt="avatarAlt"
            class="school-it-top-header__avatar"
          >
          <span
            v-else
            class="school-it-top-header__avatar school-it-top-header__avatar--fallback"
          >
            {{ initials }}
          </span>
          <span class="school-it-top-header__status-dot" aria-hidden="true" />
        </span>

        <span class="school-it-top-header__profile-copy">
          <span class="school-it-top-header__eyebrow">Welcome Back</span>
          <span class="school-it-top-header__name">{{ schoolLabel }}</span>
        </span>
      </span>

      <span class="school-it-top-header__signout" @click.stop="emit('logout')">
        <LogOut :size="18" color="#D92D20" :stroke-width="2.4" />
        <span class="school-it-top-header__signout-label">Sign Out</span>
      </span>
    </button>

    <button
      class="school-it-top-header__notify"
      type="button"
      aria-label="Notifications"
      @click="emit('toggle-notifications')"
    >
      <Bell :size="18" :stroke-width="2" />
    </button>
  </header>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Bell, LogOut } from 'lucide-vue-next'

const props = defineProps({
  avatarUrl: {
    type: String,
    default: '',
  },
  schoolName: {
    type: String,
    default: '',
  },
  displayName: {
    type: String,
    default: 'School IT',
  },
  initials: {
    type: String,
    default: 'SI',
  },
})

const emit = defineEmits(['logout', 'toggle-notifications'])

const isExpanded = ref(false)
const headerEl = ref(null)
const profileEl = ref(null)

const schoolLabel = computed(() => abbreviateSchoolName(props.schoolName || props.displayName))
const avatarAlt = computed(() => props.displayName || schoolLabel.value)

function toggleExpanded() {
  isExpanded.value = !isExpanded.value
}

function collapseExpanded(event) {
  if (!isExpanded.value) return
  const profile = profileEl.value
  if (profile instanceof HTMLElement && event.target instanceof Node && !profile.contains(event.target)) {
    isExpanded.value = false
  }
}

function abbreviateSchoolName(value) {
  const input = String(value || '').trim()
  if (!input) return 'School IT'

  const words = input.match(/[A-Za-z0-9]+/g) || []
  if (!words.length) return input

  const firstWord = words[0] || ''
  if (/^[A-Z]{2,10}$/.test(firstWord)) {
    return `${firstWord.split('').join('.')}.`
  }

  const stopwords = new Set(['of', 'the', 'and', 'for', 'at', 'in', 'on', 'de', 'la'])
  const significantWords = words.filter((word) => !stopwords.has(word.toLowerCase()))
  const sourceWords = significantWords.length >= 2 ? significantWords : words

  if (sourceWords.length === 1) {
    return sourceWords[0]
  }

  return `${sourceWords.map((word) => word[0].toUpperCase()).join('.')}.`
}

onMounted(() => {
  window.addEventListener('pointerdown', collapseExpanded, true)
})

onBeforeUnmount(() => {
  window.removeEventListener('pointerdown', collapseExpanded, true)
})
</script>

<style scoped>
.school-it-top-header{width:100%;display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:clamp(10px,3.6vw,16px)}
.school-it-top-header__profile{display:flex;align-items:center;min-width:0;max-width:min(100%,clamp(162px,56vw,228px));min-height:52px;padding:7px clamp(10px,2.8vw,12px) 7px 7px;border:none;border-radius:999px;background:var(--color-surface);color:var(--color-text-always-dark);transition:max-width .3s ease,padding .3s ease,box-shadow .24s ease,transform .18s ease;cursor:pointer;overflow:hidden;justify-self:start;box-shadow:0 10px 22px rgba(15,23,42,.04)}
.school-it-top-header__profile--expanded{max-width:min(100%,clamp(220px,76vw,292px))}
.school-it-top-header__profile-main{display:flex;align-items:center;gap:10px;min-width:0;flex:1}
.school-it-top-header__avatar-wrap{position:relative;display:inline-flex;flex-shrink:0}
.school-it-top-header__avatar{width:38px;height:38px;border-radius:999px;object-fit:cover;flex-shrink:0}
.school-it-top-header__avatar--fallback{display:inline-flex;align-items:center;justify-content:center;background:var(--color-nav);color:var(--color-nav-text);font-size:13px;font-weight:700}
.school-it-top-header__status-dot{position:absolute;right:0;bottom:0;width:10px;height:10px;border-radius:999px;background:var(--color-primary);border:2px solid var(--color-surface)}
.school-it-top-header__profile-copy{display:flex;flex-direction:column;align-items:flex-start;min-width:0;line-height:1;text-align:left}
.school-it-top-header__eyebrow{font-size:10px;font-weight:500;color:var(--color-text-muted);white-space:nowrap}
.school-it-top-header__name{margin-top:2px;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px;font-weight:700;line-height:1.08;color:var(--color-text-always-dark);letter-spacing:-.02em}
.school-it-top-header__signout{display:inline-flex;align-items:center;overflow:hidden;max-width:0;min-width:0;opacity:0;margin-left:0;white-space:nowrap;transition:max-width .3s ease,opacity .25s ease,margin .3s ease;color:#D92D20;cursor:pointer;flex-shrink:1}
.school-it-top-header__signout-label{margin-left:8px;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px;font-weight:500;letter-spacing:-.02em}
.school-it-top-header__profile--expanded .school-it-top-header__signout{max-width:min(36vw,118px);opacity:1;margin-left:clamp(8px,2.4vw,16px)}
.school-it-top-header__notify{width:42px;height:42px;border:none;border-radius:999px;background:var(--color-surface);color:var(--color-text-always-dark);display:inline-grid;place-items:center;transition:transform .16s ease;flex-shrink:0;line-height:0;box-shadow:0 10px 22px rgba(15,23,42,.04);justify-self:end}
.school-it-top-header__notify:active{transform:scale(.95)}
.school-it-top-header__notify :deep(svg){display:block}

@media (max-width: 420px){
  .school-it-top-header{gap:10px}
  .school-it-top-header__profile{max-width:min(100%,clamp(150px,58vw,204px))}
  .school-it-top-header__profile--expanded{max-width:min(100%,clamp(204px,74vw,252px))}
}

@media (max-width: 360px){
  .school-it-top-header__profile{padding-right:8px;min-height:50px;max-width:min(100%,clamp(142px,60vw,188px))}
  .school-it-top-header__profile--expanded{max-width:min(100%,clamp(188px,76vw,234px))}
  .school-it-top-header__profile-main{gap:8px}
  .school-it-top-header__avatar{width:36px;height:36px}
  .school-it-top-header__avatar--fallback{font-size:12px}
  .school-it-top-header__name{font-size:11px}
  .school-it-top-header__profile--expanded .school-it-top-header__signout{max-width:32px;margin-left:6px}
  .school-it-top-header__signout-label{display:none}
  .school-it-top-header__notify{width:40px;height:40px}
}
</style>
