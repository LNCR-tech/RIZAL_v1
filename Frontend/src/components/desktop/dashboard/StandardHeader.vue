<template>
  <header ref="headerEl" class="standard-header">
    <button
      ref="profileEl"
      class="standard-header__profile"
      :class="{ 'standard-header__profile--expanded': isExpanded }"
      type="button"
      aria-label="Account actions"
      @click="toggleExpanded"
    >
      <span class="standard-header__profile-main">
        <span class="standard-header__avatar-wrap">
          <img
            v-if="avatarUrl"
            :src="avatarUrl"
            :alt="avatarAlt"
            class="standard-header__avatar"
          >
          <span
            v-else
            class="standard-header__avatar standard-header__avatar--fallback"
          >
            {{ initials }}
          </span>
          <span class="standard-header__status-dot" aria-hidden="true" />
        </span>

        <span class="standard-header__profile-copy">
          <span class="standard-header__eyebrow">Welcome Back</span>
          <span class="standard-header__name">{{ schoolLabel }}</span>
        </span>
      </span>

      <span class="standard-header__signout" @click.stop="emit('logout')">
        <LogOut :size="18" color="#D92D20" :stroke-width="2.4" />
        <span class="standard-header__signout-label">Sign Out</span>
      </span>
    </button>

    <div class="standard-header__actions">
      <button
        class="standard-header__action-btn"
        type="button"
        aria-label="Toggle Theme"
        @click="toggleDarkMode"
      >
        <Moon :size="18" :stroke-width="2" :color="isDarkMode ? 'var(--color-primary)' : 'currentColor'" />
      </button>

      <button
        class="standard-header__action-btn"
        type="button"
        aria-label="Notifications"
        @click="emit('toggle-notifications')"
      >
        <Bell :size="18" :stroke-width="2" />
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Bell, LogOut, Moon } from 'lucide-vue-next'
import { isDarkMode, toggleDarkMode } from '@/config/theme.js'

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
.standard-header{width:100%;display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:clamp(10px,3.6vw,16px)}
.standard-header__profile{display:flex;align-items:center;min-width:0;max-width:min(100%,clamp(162px,56vw,228px));min-height:52px;padding:7px clamp(10px,2.8vw,12px) 7px 7px;border:1px solid var(--aura-glass-border);border-radius:999px;background:var(--color-surface);color:var(--color-text-always-dark);transition:max-width .3s ease,padding .3s ease,box-shadow .24s ease,transform .18s ease;cursor:pointer;overflow:hidden;justify-self:start;box-shadow:var(--aura-shadow-soft)}
.standard-header__profile--expanded{max-width:min(100%,clamp(220px,76vw,292px))}
.standard-header__profile-main{display:flex;align-items:center;gap:10px;min-width:0;flex:1}
.standard-header__avatar-wrap{position:relative;display:inline-flex;flex-shrink:0}
.standard-header__avatar{width:38px;height:38px;border-radius:999px;object-fit:cover;flex-shrink:0}
.standard-header__avatar--fallback{display:inline-flex;align-items:center;justify-content:center;background:var(--color-nav);color:var(--color-nav-text);font-size:13px;font-weight:700}
.standard-header__status-dot{position:absolute;right:0;bottom:0;width:10px;height:10px;border-radius:999px;background:var(--color-primary);border:2px solid var(--color-surface)}
.standard-header__profile-copy{display:flex;flex-direction:column;align-items:flex-start;min-width:0;line-height:1;text-align:left}
.standard-header__eyebrow{font-size:10px;font-weight:500;color:var(--color-text-muted);white-space:nowrap}
.standard-header__name{margin-top:2px;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px;font-weight:700;line-height:1.08;color:var(--color-text-always-dark);letter-spacing:-.02em}
.standard-header__signout{display:inline-flex;align-items:center;overflow:hidden;max-width:0;min-width:0;opacity:0;margin-left:0;white-space:nowrap;transition:max-width .3s ease,opacity .25s ease,margin .3s ease;color:#D92D20;cursor:pointer;flex-shrink:1}
.standard-header__signout-label{margin-left:8px;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px;font-weight:500;letter-spacing:-.02em}
.standard-header__profile--expanded .standard-header__signout{max-width:min(36vw,118px);opacity:1;margin-left:clamp(8px,2.4vw,16px)}
.standard-header__actions{display:flex;align-items:center;gap:8px;justify-self:end}
.standard-header__action-btn{width:42px;height:42px;border:1px solid var(--aura-glass-border);border-radius:999px;background:var(--color-surface);color:var(--color-text-always-dark);display:inline-grid;place-items:center;transition:transform .16s ease;flex-shrink:0;line-height:0;box-shadow:var(--aura-shadow-soft)}
.standard-header__action-btn:active{transform:scale(.95)}
.standard-header__action-btn :deep(svg){display:block}

@media (max-width: 420px){
  .standard-header{gap:10px}
  .standard-header__profile{max-width:min(100%,clamp(150px,58vw,204px))}
  .standard-header__profile--expanded{max-width:min(100%,clamp(204px,74vw,252px))}
}

@media (max-width: 360px){
  .standard-header__profile{padding-right:8px;min-height:50px;max-width:min(100%,clamp(142px,60vw,188px))}
  .standard-header__profile--expanded{max-width:min(100%,clamp(188px,76vw,234px))}
  .standard-header__profile-main{gap:8px}
  .standard-header__avatar{width:36px;height:36px}
  .standard-header__avatar--fallback{font-size:12px}
  .standard-header__name{font-size:11px}
  .standard-header__profile--expanded .standard-header__signout{max-width:32px;margin-left:6px}
  .standard-header__signout-label{display:none}
  .standard-header__action-btn{width:40px;height:40px}
  .standard-header__actions{gap:6px}
}
</style>
