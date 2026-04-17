<template>
  <section class="school-it-home">
    <div class="school-it-home__shell">
      <!-- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||| -->
      <!-- FEATURE: Navigation menu and breadcrumbs -->
      <StandardHeader
        class="dashboard-enter dashboard-enter--1"
        :avatar-url="avatarUrl"
        :school-name="schoolName"
        :display-name="displayName"
        :initials="initials"
        @logout="handleLogout"
      />
      <div class="school-it-home__breadcrumbs">
        <Breadcrumbs />
      </div>
      <!-- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||| -->

      <div class="school-it-home__body">
        <h1 class="school-it-home__title dashboard-enter dashboard-enter--2">Home</h1>

        <section class="school-it-home__search dashboard-enter dashboard-enter--3">
          <div class="school-it-home__search-row">
            <div class="school-it-home__search-wrap">
              <div class="school-it-home__search-shell" :class="{ 'school-it-home__search-shell--open': searchActive }">
                <div class="school-it-home__search-input-row">
                  <input v-model="searchQuery" v-bind="schoolSearchInputAttrs" type="text" placeholder="Search school data" class="school-it-home__search-input">
                  <button class="school-it-home__search-icon" type="button" aria-label="Search">
                    <Search :size="18" />
                  </button>
                </div>

                <div class="school-it-home__search-results">
                  <div class="school-it-home__search-results-inner">
                    <template v-if="searchActive">
                      <button
                        v-for="result in searchResults"
                        :key="result.key"
                        class="school-it-home__search-result"
                        type="button"
                        @click="openSearchResult(result)"
                      >
                        <div class="school-it-home__search-result-top">
                          <span class="school-it-home__search-result-name">{{ result.name }}</span>
                          <span class="school-it-home__search-result-type">{{ result.type }}</span>
                        </div>
                        <span class="school-it-home__search-result-meta">{{ result.meta }}</span>
                      </button>
                      <p v-if="!searchResults.length" class="school-it-home__empty">No matching school data found.</p>
                    </template>
                  </div>
                </div>
              </div>
            </div>

            <button
              v-show="!searchActive"
              class="school-it-home__ai-pill"
              :class="{ 'school-it-home__ai-pill--open': isAiOpen }"
              type="button"
              aria-label="Talk to Aura AI"
              :aria-expanded="isAiOpen ? 'true' : 'false'"
              aria-controls="school-it-ai-panel"
              @click="toggleAiPanel"
            >
              <img :src="secondaryAuraLogo" alt="Aura" class="school-it-home__ai-logo">
              <span class="school-it-home__ai-copy">Talk to<br>Aura Ai</span>
            </button>
          </div>

          <Transition
            name="school-it-ai-panel"
            @before-enter="onAiPanelBeforeEnter"
            @enter="onAiPanelEnter"
            @after-enter="onAiPanelAfterEnter"
            @before-leave="onAiPanelBeforeLeave"
            @leave="onAiPanelLeave"
            @after-leave="onAiPanelAfterLeave"
          >
            <div
              v-if="isAiOpen && !searchActive"
              id="school-it-ai-panel"
              class="school-it-home__ai-panel"
              role="region"
              aria-label="Aura AI chat"
            >
              <div class="school-it-home__ai-panel-inner">
                <div class="school-it-home__ai-shell">
                  <div ref="scrollEl" class="school-it-home__ai-messages">
                    <TransitionGroup name="school-it-bubble" tag="div" class="school-it-home__ai-messages-inner">
                      <div
                        v-for="message in messages"
                        :key="message.id"
                        :class="[
                          'school-it-home__bubble',
                          message.sender === 'ai'
                            ? 'school-it-home__bubble--ai'
                            : 'school-it-home__bubble--user',
                        ]"
                      >
                        {{ message.text }}
                      </div>

                      <div
                        v-if="isTyping"
                        key="typing"
                        class="school-it-home__bubble school-it-home__bubble--ai school-it-home__bubble--typing"
                      >
                        <span class="school-it-home__typing-dot" style="animation-delay: 0ms" />
                        <span class="school-it-home__typing-dot" style="animation-delay: 150ms" />
                        <span class="school-it-home__typing-dot" style="animation-delay: 300ms" />
                      </div>
                    </TransitionGroup>
                  </div>

                  <div class="school-it-home__ai-input">
                    <div class="school-it-home__ai-input-row">
                      <input
                        ref="aiInputEl"
                        v-model="inputText"
                        class="school-it-home__ai-input-field"
                        type="text"
                        placeholder="Ask Aura..."
                        :disabled="isTyping"
                        @keyup.enter="sendMessage"
                      >
                      <button
                        class="school-it-home__ai-send"
                        type="button"
                        aria-label="Send message"
                        :disabled="!inputText.trim() || isTyping"
                        @click="sendMessage"
                      >
                        <Send :size="15" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Transition>
        </section>

        <div class="school-it-home__cards">
          <section class="school-it-home__hero dashboard-enter dashboard-enter--4">
            <div class="school-it-home__hero-copy">
              <p class="school-it-home__hero-kicker">Hi School IT of</p>
              <h2 class="school-it-home__hero-title">{{ schoolName }}</h2>
              <button class="school-it-home__pill" type="button" @click="router.push({ name: settingsRouteName })">
                <span class="school-it-home__pill-icon"><ArrowRight :size="18" /></span>
                Edit Details
              </button>
            </div>

            <div class="school-it-home__hero-logo">
              <img
                v-if="heroLogoSrc && !heroLogoUnavailable"
                :src="heroLogoSrc"
                :alt="`${schoolName} logo`"
                class="school-it-home__hero-logo-image"
                @error="handleHeroLogoError"
              >
              <div v-else class="school-it-home__hero-logo-fallback">{{ schoolInitials }}</div>
            </div>
          </section>

          <section class="school-it-home__summary dashboard-enter dashboard-enter--5">
            <div class="school-it-home__summary-content">
              <div class="school-it-home__summary-header">
                <span class="school-it-home__summary-mini">University Structure</span>
                <h3 class="school-it-home__summary-title">Departments</h3>
              </div>
              
              <div class="school-it-home__summary-stats">
                <div class="school-it-home__summary-stat">
                  <strong class="school-it-home__summary-value">{{ departmentCountLabel }}</strong>
                  <span class="school-it-home__summary-caption">Active Depts</span>
                </div>
                <div class="school-it-home__summary-divider" />
                <div class="school-it-home__summary-stat">
                  <strong class="school-it-home__summary-value school-it-home__summary-value--small">{{ programCountLabel }}</strong>
                  <span class="school-it-home__summary-caption">Programs</span>
                </div>
              </div>

              <button class="school-it-home__ghost-pill" type="button" @click="router.push({ name: settingsRouteName })">
                <span>Access Structure</span>
                <ArrowRight :size="14" />
              </button>
            </div>
          </section>

          <!-- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||| -->
          <!-- FEATURE: Show attendance status (Present/Absent) -->
          <section class="school-it-home__rate dashboard-enter dashboard-enter--6">
            <div class="school-it-home__rate-content">
              <div class="school-it-home__rate-info">
                <span class="school-it-home__summary-mini">Today's Performance</span>
                <h3 class="school-it-home__rate-minimal-title">Attendance Rate</h3>
                <p class="school-it-home__rate-minimal-meta">{{ attendanceRateMeta }}</p>
              </div>

              <div class="school-it-home__rate-visual">
                <SchoolItMetricRing :value="presentRateLabel" compact :delay="0.08" />
                <span class="school-it-home__rate-visual-label">Present</span>
              </div>
            </div>
          </section>

              <article class="school-it-home__status-panel">
                <SchoolItMetricRing :value="absentRateLabel" compact :delay="0.24" />
                <span class="school-it-home__metric-label school-it-home__metric-label--compact">Absent</span>
              </article>
            </div>
          </section>
          <!-- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||| -->

          <section class="school-it-home__admins dashboard-enter dashboard-enter--8">
            <div class="school-it-home__admins-content">
              <div class="school-it-home__admins-header">
                <span class="school-it-home__summary-mini">Account Access</span>
                <h3 class="school-it-home__summary-title">Campus Admins</h3>
              </div>
              <p class="school-it-home__admins-description">Manage fellow administrators and reset credentials safely.</p>
              <button class="school-it-home__ghost-pill" type="button" @click="router.push({ name: accountsRouteName })">
                <span>Manage Accounts</span>
                <ArrowRight :size="14" />
              </button>
            </div>
          </section>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ArrowRight, Search, Send } from 'lucide-vue-next'
import StandardHeader from '@/components/desktop/dashboard/StandardHeader.vue'
import Breadcrumbs from '@/components/desktop/dashboard/Breadcrumbs.vue'
import SchoolItMetricRing from '@/components/desktop/dashboard/SchoolItMetricRing.vue'
import { useSchoolItHomeLogic } from '@/composables/useSchoolItHomeLogic.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const {
  router,
  searchQuery,
  schoolSearchInputAttrs,
  isAiOpen,
  aiInputEl,
  scrollEl,
  searchActive,
  schoolName,
  avatarUrl,
  heroLogoSrc,
  heroLogoUnavailable,
  displayName,
  initials,
  schoolInitials,
  settingsRouteName,
  accountsRouteName,
  departmentCountLabel,
  programCountLabel,
  attendanceRateMeta,
  presentRateLabel,
  absentRateLabel,
  searchResults,
  inputText,
  isTyping,
  messages,
  sendMessage,
  secondaryAuraLogo,
  handleHeroLogoError,
  openSearchResult,
  toggleAiPanel,
  handleLogout
} = useSchoolItHomeLogic(props)

const nextFrame = (callback) => requestAnimationFrame(() => requestAnimationFrame(callback))

function onAiPanelBeforeEnter(element) {
  element.style.height = '0px'
  element.style.opacity = '0'
  element.style.transform = 'translateY(-8px)'
  element.style.willChange = 'height, opacity, transform'
}

function onAiPanelEnter(element) {
  const height = element.scrollHeight
  element.style.transition = 'height 520ms cubic-bezier(0.22, 1, 0.36, 1), opacity 320ms ease, transform 420ms cubic-bezier(0.22, 1, 0.36, 1)'
  nextFrame(() => {
    element.style.height = `${height}px`
    element.style.opacity = '1'
    element.style.transform = 'translateY(0)'
  })
}

function onAiPanelAfterEnter(element) {
  element.style.height = 'auto'
  element.style.transition = ''
  element.style.willChange = ''
}

function onAiPanelBeforeLeave(element) {
  element.style.height = `${element.scrollHeight}px`
  element.style.opacity = '1'
  element.style.transform = 'translateY(0)'
  element.style.willChange = 'height, opacity, transform'
}

function onAiPanelLeave(element) {
  element.style.transition = 'height 420ms cubic-bezier(0.4, 0, 0.2, 1), opacity 240ms ease, transform 300ms ease'
  nextFrame(() => {
    element.style.height = '0px'
    element.style.opacity = '0'
    element.style.transform = 'translateY(-6px)'
  })
}

function onAiPanelAfterLeave(element) {
  element.style.transition = ''
  element.style.height = ''
  element.style.opacity = ''
  element.style.transform = ''
  element.style.willChange = ''
}
</script>

<style scoped>
.school-it-home{min-height:100vh;padding:30px 28px 120px;font-family:'Manrope',sans-serif}
.school-it-home__shell{width:100%;max-width:1120px;margin:0 auto}
.school-it-home__body{display:flex;flex-direction:column;gap:18px;margin-top:24px}
.school-it-home__title{margin:0;font-size:22px;font-weight:800;line-height:1;letter-spacing:-.05em;color:var(--color-text-primary)}
.school-it-home__search{display:flex;flex-direction:column;gap:10px}
.school-it-home__search-row{display:flex;align-items:stretch;gap:clamp(8px,3vw,12px)}
.school-it-home__search-wrap{flex:1;min-width:0}
.school-it-home__search-shell{display:grid;grid-template-rows:auto 0fr;padding:11px clamp(12px,4vw,16px);border-radius:30px;background:var(--color-surface);transition:grid-template-rows .32s cubic-bezier(.22,1,.36,1),border-radius .32s cubic-bezier(.22,1,.36,1)}
.school-it-home__search-shell--open{grid-template-rows:auto 1fr;border-radius:28px}
.school-it-home__search-input-row{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:clamp(8px,2.5vw,10px);min-height:clamp(38px,10vw,40px)}
.school-it-home__search-input{flex:1;min-width:0;border:none;background:transparent;outline:none;color:var(--color-text-primary);font-size:clamp(13px,3.8vw,14px);font-weight:500}
.school-it-home__search-input::placeholder{color:var(--color-text-muted)}
.school-it-home__search-icon{width:clamp(30px,8vw,32px);height:clamp(30px,8vw,32px);padding:0;border:1px solid var(--color-surface-border);border-radius:999px;background:transparent;color:var(--color-primary);display:inline-flex;align-items:center;justify-content:center;align-self:center;line-height:0;appearance:none;flex-shrink:0;place-self:center}
.school-it-home__search-icon :deep(svg){display:block;width:clamp(15px,4.5vw,18px);height:clamp(15px,4.5vw,18px);transform:translateY(0)}
.school-it-home__search-results{overflow:hidden;min-height:0}
.school-it-home__search-results-inner{display:flex;flex-direction:column;gap:10px;padding:14px 0 6px}
.school-it-home__search-result{width:100%;padding:14px 16px;border:none;border-radius:22px;background:color-mix(in srgb,var(--color-surface) 90%,var(--color-bg));display:flex;flex-direction:column;gap:8px;text-align:left}
.school-it-home__search-result-top{display:flex;align-items:center;justify-content:space-between;gap:12px}
.school-it-home__search-result-name{font-size:14px;font-weight:700;color:var(--color-text-primary)}
.school-it-home__search-result-type{min-height:28px;padding:0 12px;border-radius:999px;background:var(--color-primary);color:var(--color-banner-text);display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;letter-spacing:.02em;flex-shrink:0}
.school-it-home__search-result-meta,.school-it-home__empty{font-size:12px;color:var(--color-text-muted)}
.school-it-home__ai-pill{width:clamp(108px,30vw,122px);min-height:clamp(56px,15vw,60px);padding:0 clamp(12px,4vw,14px);border:none;border-radius:999px;background:var(--color-search-pill-bg);color:var(--color-search-pill-text);display:inline-flex;align-items:center;justify-content:center;gap:clamp(8px,2.6vw,10px);flex-shrink:0;transition:opacity .2s ease,transform .2s ease,box-shadow .25s ease,filter .22s ease}
.school-it-home__ai-pill:hover{filter:brightness(1.08);transform:scale(1.04)}
.school-it-home__ai-pill:active{transform:scale(.96)}
.school-it-home__ai-pill--open{box-shadow:0 12px 24px rgba(0,0,0,.14);transform:translateY(1px) scale(.98)}
.school-it-home__ai-logo{width:clamp(28px,8vw,32px);height:clamp(28px,8vw,32px);object-fit:contain}
.school-it-home__ai-copy{font-size:clamp(12px,3.4vw,13px);font-weight:700;line-height:.98;text-align:left}
.school-it-home__ai-panel{overflow:hidden;transform-origin:top center}
.school-it-home__ai-panel-inner{overflow:hidden}
.school-it-home__ai-shell{position:relative;display:flex;flex-direction:column;gap:10px;padding:14px;background:var(--color-ai-surface);border-radius:28px;box-shadow:0 18px 40px rgba(0,0,0,.14);overflow:hidden}
.school-it-home__ai-messages{position:relative;z-index:1;display:flex;flex-direction:column;gap:10px;min-height:clamp(110px,22vh,180px);max-height:min(46vh,320px);overflow-y:auto;padding:6px 6px 0;scrollbar-width:none}
.school-it-home__ai-messages::-webkit-scrollbar{display:none}
.school-it-home__ai-messages-inner{display:flex;flex-direction:column;gap:10px}
.school-it-home__bubble{max-width:88%;padding:12px 16px;border-radius:24px;font-size:13px;font-weight:600;line-height:1.6;font-family:'Manrope',sans-serif;word-break:break-word}
.school-it-home__bubble--ai{align-self:flex-start;background:var(--color-surface);color:var(--color-surface-text);border:1px solid var(--aura-glass-border);box-shadow:var(--aura-shadow-soft)}
.school-it-home__bubble--user{align-self:flex-end;background:var(--color-ai-user-bubble-bg);color:var(--color-ai-user-bubble-text);border:1px solid var(--color-ai-input-border)}
.school-it-home__bubble--typing{display:flex;align-items:center;gap:6px;padding:12px 16px}
.school-it-home__typing-dot{width:6px;height:6px;border-radius:999px;background:color-mix(in srgb,var(--color-ai-surface-text) 50%, transparent);animation:school-it-dot-bounce 1s infinite ease-in-out}
.school-it-home__ai-input{position:relative;z-index:1}
.school-it-home__ai-input-row{display:flex;align-items:center;gap:8px;height:44px;padding:0 8px 0 16px;border:1.4px solid var(--color-ai-input-border);border-radius:999px;background:var(--color-ai-input-bg);transition:border-color .2s ease,background .2s ease}
.school-it-home__ai-input-row:focus-within{background:var(--color-ai-input-bg-focus);border-color:color-mix(in srgb,var(--color-ai-surface-text) 22%, var(--color-ai-surface))}
.school-it-home__ai-input-field{flex:1;min-width:0;border:none;outline:none;background:transparent;color:var(--color-ai-surface-text);font-size:12.5px;font-weight:600}
.school-it-home__ai-input-field::placeholder{color:var(--color-ai-surface-text);opacity:.55}
.school-it-home__ai-send{display:flex;align-items:center;justify-content:center;width:34px;height:34px;border:none;border-radius:999px;background:var(--color-ai-send-bg);color:var(--color-ai-surface-text);cursor:pointer;flex-shrink:0;transition:background .18s ease,transform .15s ease,opacity .18s ease}
.school-it-home__ai-send:hover:not(:disabled){background:var(--color-ai-send-bg-hover);transform:scale(1.08)}
.school-it-home__ai-send:disabled{opacity:.45;cursor:not-allowed}
.school-it-bubble-enter-active{animation:school-it-bubble-pop .45s cubic-bezier(.34,1.56,.64,1) both}
.school-it-home__bubble--ai.school-it-bubble-enter-active{transform-origin:bottom left}
.school-it-home__bubble--user.school-it-bubble-enter-active{transform-origin:bottom right}
.school-it-home__cards{display:grid;gap:20px}
.school-it-home__hero,.school-it-home__summary,.school-it-home__rate,.school-it-home__status{border-radius:32px;overflow:hidden}
.school-it-home__hero{position:relative;display:block;min-height:230px;padding:28px 18px 0;background:var(--color-primary);--school-it-hero-logo-size:140px;--school-it-hero-logo-offset:-20px;--school-it-hero-logo-top:68%}
.school-it-home__hero-copy{position:relative;z-index:1;display:flex;flex-direction:column;min-width:0;min-height:202px;max-width:calc(100% - (var(--school-it-hero-logo-size) * 0.68));align-self:stretch}
.school-it-home__hero-kicker{margin:0;font-size:17px;line-height:1.18;font-weight:500;color:var(--color-banner-text)}
.school-it-home__hero-title{margin:8px 0 0;max-width:6ch;font-size:clamp(26px,10vw,58px);line-height:.95;letter-spacing:-.07em;font-weight:800;color:var(--color-banner-text)}
.school-it-home__hero-logo{position:absolute;right:var(--school-it-hero-logo-offset);top:var(--school-it-hero-logo-top);transform:translateY(-50%);display:flex;align-items:flex-end;justify-content:flex-end;pointer-events:none;z-index:0}
.school-it-home__hero-logo-image{width:var(--school-it-hero-logo-size);height:var(--school-it-hero-logo-size);object-fit:contain;object-position:bottom right}
.school-it-home__hero-logo-fallback{width:var(--school-it-hero-logo-size);height:var(--school-it-hero-logo-size);border-radius:32px;background:rgba(10,10,10,.12);color:var(--color-banner-text);display:inline-flex;align-items:center;justify-content:center;font-size:28px;font-weight:800;letter-spacing:.08em}
.school-it-home__pill{width:fit-content;min-height:58px;margin-top:auto;margin-bottom:24px;padding:0 22px 0 8px;border:none;border-radius:999px;background:var(--color-surface);color:var(--color-surface-text);display:inline-flex;align-items:center;gap:14px;font-size:13px;font-weight:700}
.school-it-home__pill--compact{min-height:56px;margin-bottom:0}
.school-it-home__pill-icon{width:42px;height:42px;border-radius:999px;background:var(--color-nav);color:var(--color-nav-text);display:inline-flex;align-items:center;justify-content:center;flex-shrink:0}
.school-it-home__summary{background:var(--color-surface);display:flex;flex-direction:column;border:1px solid var(--aura-glass-border);box-shadow:var(--aura-shadow-soft), var(--aura-glow-primary)}
.school-it-home__summary-content{padding:26px;display:flex;flex-direction:column;gap:22px;flex:1}
.school-it-home__summary-mini{font-size:10px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--color-text-muted);display:block;margin-bottom:6px}
.school-it-home__summary-title{margin:0;font-size:28px;font-weight:800;letter-spacing:-.04em;color:var(--color-text-primary)}
.school-it-home__summary-stats{display:flex;align-items:center;gap:20px}
.school-it-home__summary-stat{display:flex;flex-direction:column;gap:2px}
.school-it-home__summary-value{font-size:42px;line-height:1;font-weight:800;letter-spacing:-.06em;color:var(--color-primary)}
.school-it-home__summary-value--small{color:var(--color-text-primary);opacity:.85}
.school-it-home__summary-caption{font-size:12px;font-weight:600;color:var(--color-text-muted)}
.school-it-home__summary-divider{width:1px;height:30px;background:var(--color-surface-border);opacity:.5}
.school-it-home__ghost-pill{margin-top:auto;display:inline-flex;align-items:center;gap:8px;padding:10px 14px;background:var(--color-field-surface);border:none;border-radius:999px;font-size:12px;font-weight:700;color:var(--color-text-primary);width:fit-content;cursor:pointer;transition:all .2s ease}
.school-it-home__ghost-pill:hover{background:var(--color-surface-border)}

.school-it-home__rate{background:var(--color-surface);display:flex;flex-direction:column;border:1px solid var(--aura-glass-border);box-shadow:var(--aura-shadow-soft), var(--aura-glow-primary)}
.school-it-home__rate-content{padding:26px;display:flex;align-items:center;justify-content:space-between;gap:20px;flex:1}
.school-it-home__rate-info{display:flex;flex-direction:column;min-width:0}
.school-it-home__rate-minimal-title{margin:0;font-size:24px;font-weight:800;letter-spacing:-.04em;color:var(--color-text-primary)}
.school-it-home__rate-minimal-meta{margin:8px 0 0;font-size:13px;line-height:1.5;color:var(--color-text-secondary);max-width:20ch}
.school-it-home__rate-visual{display:flex;flex-direction:column;align-items:center;gap:6px;flex-shrink:0}
.school-it-home__rate-visual-label{font-size:11px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;color:var(--color-text-muted)}

.school-it-home__status{background:var(--color-surface);padding:12px}
.school-it-home__status-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.school-it-home__status-panel{min-height:222px;border-radius:24px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:16px 10px 14px;border:1px solid var(--aura-glass-border);box-shadow:var(--aura-shadow-soft)}
.school-it-home__admins{background:var(--color-surface);display:flex;flex-direction:column;border:1px solid var(--aura-glass-border);box-shadow:var(--aura-shadow-soft)}
.school-it-home__admins-content{padding:26px;display:flex;flex-direction:column;gap:12px;flex:1}
.school-it-home__admins-description{margin:0;font-size:14px;line-height:1.5;color:var(--color-text-secondary);max-width:32ch}
@media (min-width:768px){
  .school-it-home{padding:40px 36px 56px}
  .school-it-home__body{margin-top:30px;gap:22px}
  .school-it-home__title{font-size:28px}
  .school-it-home__search-row{max-width:780px}
  .school-it-home__ai-panel{max-width:780px}
  .school-it-home__cards{grid-template-columns:minmax(0,1.1fr) minmax(320px,.9fr);grid-template-areas:"hero hero" "summary rate" "status status";gap:22px}
  .school-it-home__hero{grid-area:hero;min-height:332px;padding:34px 28px 0;--school-it-hero-logo-size:164px;--school-it-hero-logo-offset:-24px;--school-it-hero-logo-top:69%}
  .school-it-home__hero-copy{min-height:276px;max-width:calc(100% - (var(--school-it-hero-logo-size) * 0.74))}
  .school-it-home__hero-title{max-width:8ch}
  .school-it-home__summary{grid-area:summary;min-height:266px}
  .school-it-home__rate{grid-area:rate;min-height:266px}
  .school-it-home__status{grid-area:status}
  .school-it-home__admins{grid-area:admins}
  .school-it-home__status-panel{min-height:252px}
}
@media (min-width:1100px){
  .school-it-home__cards{grid-template-columns:minmax(0,1.04fr) minmax(360px,.96fr);grid-template-areas:"hero hero" "summary rate" "summary status" "admins status"}
}
@media (prefers-reduced-motion:reduce){
  .school-it-home__ai-pill,.school-it-home__ai-send,.school-it-bubble-enter-active{transition:none;animation:none}
}

@keyframes school-it-dot-bounce{
  0%,100%{transform:translateY(0)}
  40%{transform:translateY(-4px)}
}

@keyframes school-it-bubble-pop{
  0%{opacity:0;transform:scale(.55)}
  65%{opacity:1;transform:scale(1.04)}
  82%{transform:scale(.97)}
  100%{transform:scale(1)}
}
.school-it-home__breadcrumbs {
  margin: 12px 0;
  padding: 0 4px;
}
</style>
