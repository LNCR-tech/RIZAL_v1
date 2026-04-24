<template>
  <!-- Teleport to body so it's never clipped by sidebar overflow -->
  <Teleport to="body">
    <!-- Transparent backdrop: click outside = close -->
    <Transition name="chat-backdrop">
      <div
        v-if="isFullOpen"
        class="aura-chat-backdrop"
        @click="closeFull"
      />
    </Transition>

    <Transition name="chat-window">
      <div
        v-if="isFullOpen"
        ref="windowEl"
        class="aura-chat-window"
        role="dialog"
        aria-label="Aura AI Chat"
        @click.stop
      >
        <!-- ── Header ─────────────────────────────────────────────── -->
        <div class="chat-header">
          <div class="chat-header-left">
            <img :src="activeAuraLogo" alt="Aura" class="chat-logo" />
            <div class="chat-header-title">
              <span class="chat-title">Aura AI</span>
              <span class="chat-subtitle">Your campus assistant</span>
            </div>
          </div>

          <div class="chat-header-actions">
            <!-- Minimize → return to mini pill -->
            <button
              class="chat-icon-btn"
              aria-label="Minimize chat"
              @click="minimizeToMini"
            >
              <Minus :size="15" />
            </button>
            <!-- Close entirely -->
            <button
              class="chat-icon-btn chat-icon-btn--close"
              aria-label="Close chat"
              @click="closeFull"
            >
              <X :size="15" />
            </button>
          </div>
        </div>

        <!-- ── Messages area ──────────────────────────────────────── -->
        <div class="chat-messages" ref="scrollEl">
          <TransitionGroup name="bubble" tag="div" class="chat-messages-inner">
            <div
              v-for="msg in messages"
              :key="msg.id"
              :class="['bubble', msg.sender === 'ai' ? 'bubble--ai' : 'bubble--user']"
            >
              <div v-if="msg.html" v-html="msg.html" class="chat-html-content" />
              <template v-else>{{ msg.text }}</template>

              <div v-if="msg.actions && msg.actions.length" class="chat-actions">
                <button
                  v-for="(action, i) in msg.actions"
                  :key="i"
                  class="chat-action-btn"
                  @click="handleAction(action)"
                >
                  <component v-if="action.icon" :is="action.icon" :size="14" class="action-icon" />
                  <span>{{ action.label }}</span>
                </button>
              </div>
            </div>

            <!-- Typing indicator -->
            <div v-if="isTyping" key="typing" class="bubble bubble--ai bubble--typing">
              <span class="dot" style="animation-delay: 0ms"   />
              <span class="dot" style="animation-delay: 150ms" />
              <span class="dot" style="animation-delay: 300ms" />
            </div>
          </TransitionGroup>
        </div>

        <!-- ── Input bar ──────────────────────────────────────────── -->
        <div class="chat-input-wrap">
          <div class="chat-input-row">
            <input
              ref="inputEl"
              v-model="inputText"
              class="chat-input"
              type="text"
              placeholder="Ask Aura anything..."
              :disabled="isTyping"
              @keyup.enter="sendMessage"
            />
            <button
              class="chat-send-btn"
              :disabled="!inputText.trim() || isTyping"
              aria-label="Send message"
              @click="sendMessage"
            >
              <Send :size="16" />
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Minus, X, Send, Download, ExternalLink } from 'lucide-vue-next'
import { activeAuraLogo } from '@/config/theme.js'
import { useChat } from '@/composables/useChat.js'
import { downloadDemoReport } from '@/services/demoReportDownload.js'
import { useRouter } from 'vue-router'

const windowEl = ref(null)

const {
  messages,
  inputText,
  isTyping,
  isFullOpen,
  scrollEl,
  sendMessage,
  closeFull,
  minimizeToMini,
} = useChat()

const router = useRouter()

async function handleAction(action) {
  if (action.route) {
    router.push(action.route)
  }
  if (action.actionId === 'download-pdf' || action.actionId === 'download-csv') {
    await downloadDemoReport(action.actionId.split('-')[1])
  }
}

const inputEl = ref(null)

// Auto-focus input when window opens
watch(isFullOpen, (val) => {
  if (val) {
    setTimeout(() => inputEl.value?.focus(), 350)
  }
})
</script>

<style scoped>
/* ── Backdrop (transparent, catches outside clicks) ────── */
.aura-chat-backdrop {
  position: fixed;
  inset: 0;
  z-index: 9998;
  background: transparent;
  cursor: default;
}

.chat-backdrop-enter-active,
.chat-backdrop-leave-active {
  transition: opacity 0.22s ease;
}
.chat-backdrop-enter-from,
.chat-backdrop-leave-to {
  opacity: 0;
}

/* ── Floating window shell ─────────────────────────────── */
.aura-chat-window {
  position: fixed;
  left: 72px;         /* just to the right of the sidebar pill */
  bottom: 64px;       /* float above the bottom of the screen  */
  z-index: 9999;

  width: 360px;
  height: 520px;
  display: flex;
  flex-direction: column;

  background: var(--color-primary);
  border-radius: 28px;
  overflow: hidden;
}

/* ── Open / close animation ────────────────────────────── */
.chat-window-enter-active {
  transition: opacity 0.35s ease, transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.chat-window-leave-active {
  transition: opacity 0.22s ease, transform 0.22s cubic-bezier(0.4, 0, 1, 1);
}
.chat-window-enter-from,
.chat-window-leave-to {
  opacity: 0;
  transform: scale(0.88) translateY(12px);
}
.chat-window-enter-to,
.chat-window-leave-from {
  opacity: 1;
  transform: scale(1) translateY(0);
}

/* ── Header ────────────────────────────────────────────── */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 16px 12px;
  flex-shrink: 0;
}

.chat-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.chat-logo {
  width: 36px;
  height: 36px;
  object-fit: contain;
}

.chat-header-title {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.chat-title {
  font-size: 15px;
  font-weight: 800;
  color: var(--color-banner-text);
  letter-spacing: -0.3px;
}

.chat-subtitle {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-banner-text);
  opacity: 0.6;
}

.chat-header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.chat-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.1);
  color: var(--color-banner-text);
  cursor: pointer;
  transition: background 0.18s ease, transform 0.15s ease;
}

.chat-icon-btn:hover {
  background: rgba(0, 0, 0, 0.2);
  transform: scale(1.08);
}

.chat-icon-btn--close:hover {
  background: rgba(0, 0, 0, 0.25);
}

/* ── Messages ──────────────────────────────────────────── */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 4px 16px 16px;
  scrollbar-width: none;
}

.chat-messages::-webkit-scrollbar {
  display: none;
}

/* TransitionGroup wrapper — must be flex col for align-self to work */
.chat-messages-inner {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ── Bubbles ───────────────────────────────────────────── */
.bubble {
  max-width: 86%;
  padding: 14px 18px;
  border-radius: 25px;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.65;
  font-family: 'Manrope', sans-serif;
  word-break: break-word;
}

.bubble--ai {
  align-self: flex-start;
  background: #ffffff;
  color: #0a0a0a;
}

.bubble--user {
  align-self: flex-end;
  background: rgba(0, 0, 0, 0.14);
  color: var(--color-banner-text);
  border: 1px solid rgba(255, 255, 255, 0.15);
}

/* ── Typing indicator ──────────────────────────────────── */
.bubble--typing {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 16px 20px;
  border-radius: 25px;
}

.dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.35);
  animation: bounce 1s infinite ease-in-out;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0);    }
  40%       { transform: translateY(-5px); }
}

/* ── iMessage-style bubble pop animation ───────────────── */
.bubble-enter-active {
  animation: bubble-pop 0.42s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

/* AI bubbles pop from bottom-left, user from bottom-right */
.bubble--ai.bubble-enter-active  { transform-origin: bottom left;  }
.bubble--user.bubble-enter-active { transform-origin: bottom right; }

@keyframes bubble-pop {
  0%   { opacity: 0; transform: scale(0.55); }
  65%  { opacity: 1; transform: scale(1.04); }
  82%  { transform: scale(0.97);             }
  100% { transform: scale(1);                }
}

/* ── Input bar ─────────────────────────────────────────── */
.chat-input-wrap {
  padding: 10px 14px 16px;
  flex-shrink: 0;
}

.chat-input-row {
  display: flex;
  align-items: center;
  background: rgba(0, 0, 0, 0.08);
  border: 1.5px solid rgba(0, 0, 0, 0.2);
  border-radius: 999px;
  padding: 0 8px 0 18px;
  height: 48px;
  gap: 6px;
  transition: border-color 0.18s ease, background 0.18s ease;
}

.chat-input-row:focus-within {
  background: rgba(0, 0, 0, 0.12);
  border-color: rgba(0, 0, 0, 0.35);
}

.chat-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 13px;
  font-weight: 500;
  font-family: 'Manrope', sans-serif;
  color: var(--color-banner-text);
  min-width: 0;
}

.chat-input::placeholder {
  color: var(--color-banner-text);
  opacity: 0.45;
}

.chat-send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.15);
  color: var(--color-banner-text);
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.18s ease, transform 0.15s ease, opacity 0.18s ease;
}

.chat-send-btn:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.25);
  transform: scale(1.08);
}

.chat-send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ── Rich Content Styles ───────────────────────────────── */
::v-deep(.chat-html-content p) {
  margin: 0 0 10px;
}
::v-deep(.chat-html-content p:last-child) {
  margin: 0;
}
::v-deep(.chat-html-content .mock-graph) {
  margin-top: 12px;
  display: flex;
  align-items: flex-end;
  gap: 8px;
  height: 100px;
  padding: 10px 0;
  border-bottom: 2px solid rgba(0,0,0,0.1);
}
::v-deep(.chat-html-content .mock-graph-bar) {
  flex: 1;
  background: var(--color-primary);
  border-radius: 4px 4px 0 0;
  position: relative;
  min-height: 10px;
}
::v-deep(.chat-html-content .mock-graph-bar span) {
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 11px;
  font-weight: 700;
  color: rgba(0,0,0,0.6);
}
::v-deep(.chat-html-content .mock-graph-label) {
  text-align: center;
  font-size: 10px;
  font-weight: 700;
  margin-top: 6px;
  color: rgba(0,0,0,0.5);
  text-transform: uppercase;
  display: flex;
  justify-content: space-around;
}
::v-deep(.chat-html-content .mock-graph-label span) {
  flex: 1;
}

.chat-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.chat-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid rgba(0,0,0,0.1);
  background: rgba(0,0,0,0.05);
  color: #0A0A0A;
  font-size: 13px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s ease;
}
.chat-action-btn:hover {
  background: rgba(0,0,0,0.08);
}
.action-icon {
  opacity: 0.7;
}
</style>
