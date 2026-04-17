<template>
  <section class="aura-chat-page">
    <div class="aura-chat-shell" role="region" aria-label="Aura AI Chat">
      <header class="chat-header">
        <div class="chat-header-left">
          <button
            class="chat-icon-btn"
            aria-label="Back"
            title="Back"
            type="button"
            @click="goBack"
          >
            <ArrowLeft :size="16" />
          </button>
          <img :src="activeAuraLogo" alt="Aura" class="chat-logo" />
          <div class="chat-header-title">
            <span class="chat-title">Aura AI</span>
            <span class="chat-subtitle">{{ getActiveConversationLabel() }}</span>
          </div>
        </div>

        <div class="chat-header-actions">
          <button
            class="chat-icon-btn"
            aria-label="Copy conversation"
            title="Copy conversation"
            type="button"
            @click="copyConversation"
          >
            <Copy :size="15" />
          </button>
          <button
            class="chat-icon-btn"
            aria-label="Start new chat"
            title="New chat"
            type="button"
            @click="startNewConversation"
          >
            <Plus :size="15" />
          </button>
        </div>
      </header>

      <div class="chat-body">
        <aside class="chat-sidebar" aria-label="Conversation list">
          <div class="chat-sidebar-header">
            <div class="chat-sidebar-title">Chats</div>
          </div>

          <div v-if="isLoadingConversations" class="chat-sidebar-meta">Loading...</div>
          <div v-else-if="conversationsError" class="chat-sidebar-meta chat-sidebar-meta--error">
            {{ conversationsError }}
          </div>
          <div v-else-if="!conversations?.length" class="chat-sidebar-meta">No conversations yet.</div>

          <div v-if="conversations?.length" class="chat-sidebar-list">
            <div
              v-for="conversation in conversations"
              :key="conversation.conversation_id"
              role="button"
              tabindex="0"
              class="chat-sidebar-item"
              :class="String(conversation.conversation_id) === String(conversationId || '') ? 'chat-sidebar-item--active' : ''"
              @click="selectConversation(conversation.conversation_id)"
              @keydown.enter="selectConversation(conversation.conversation_id)"
              @keydown.space.prevent="selectConversation(conversation.conversation_id)"
            >
              <div class="chat-sidebar-item-title">
                {{ conversation.title || conversation.last_message || 'New chat' }}
              </div>
              <button
                type="button"
                class="chat-sidebar-item-delete"
                aria-label="Delete conversation"
                title="Delete conversation"
                @click.stop="removeConversation(conversation.conversation_id)"
              >
                <Trash2 :size="14" />
              </button>
            </div>
          </div>
        </aside>

        <div class="chat-main">
          <div class="chat-messages" ref="scrollEl">
            <TransitionGroup name="bubble" tag="div" class="chat-messages-inner">
              <div
                v-for="message in messages"
                :key="message.id"
                :class="['bubble', message.sender === 'ai' ? 'bubble--ai' : 'bubble--user']"
              >
                <ChatMarkdownMessage :text="message.text" />
              </div>

              <div v-if="isTyping && typingConversationId === conversationId" key="typing" class="bubble bubble--ai bubble--typing">
                <span class="dot" style="animation-delay: 0ms" />
                <span class="dot" style="animation-delay: 150ms" />
                <span class="dot" style="animation-delay: 300ms" />
              </div>
            </TransitionGroup>
          </div>

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
                type="button"
                @click="sendMessage"
              >
                <Send :size="16" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Copy, Send, Plus, Trash2 } from 'lucide-vue-next'
import ChatMarkdownMessage from '@/components/ui/ChatMarkdownMessage.vue'
import { activeAuraLogo } from '@/config/theme.js'
import { useChat } from '@/composables/useChat.js'
import {
  hasNavigableHistory,
  resolveWorkspaceHomeLocation,
  withPreservedGovernancePreviewQuery,
} from '@/services/routeWorkspace.js'

const route = useRoute()
const router = useRouter()
const inputEl = ref(null)

const {
  messages,
  inputText,
  isTyping,
  conversationId,
  conversations,
  isLoadingConversations,
  conversationsError,
  scrollEl,
  sendMessage,
  copyConversation,
  refreshConversations,
  startNewConversation,
  selectConversation,
  removeConversation,
  getActiveConversationLabel,
  typingConversationId,
  closeAll,
} = useChat()

function goBack() {
  if (hasNavigableHistory(route)) {
    router.back()
    return
  }

  const fallback = withPreservedGovernancePreviewQuery(route, resolveWorkspaceHomeLocation(route))
  router.push(fallback)
}

onMounted(async () => {
  document.body.classList.add('no-scroll') // Lock the page
  closeAll()
  await refreshConversations()

  if (conversationId.value && messages.value.length <= 1) {
    try {
      await selectConversation(conversationId.value)
    } catch {
      // Keep the default greeting if conversation history fails to load.
    }
  }

  setTimeout(() => inputEl.value?.focus(), 220)
})

onUnmounted(() => {
  document.body.classList.remove('no-scroll') // Unlock when leaving
})
</script>

<style scoped>
.aura-chat-page {
  height: 100dvh;
  padding: 22px 18px 26px;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* Prevent page scroll */
}

.aura-chat-shell {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--color-primary);
  border-radius: 30px;
  overflow: hidden;
  box-shadow: 0 28px 68px rgba(12, 18, 33, 0.18);
}

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
  min-width: 0;
}

.chat-logo {
  width: 36px;
  height: 36px;
  object-fit: contain;
  flex-shrink: 0;
}

.chat-header-title {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
  min-width: 0;
}

.chat-title {
  font-size: 15px;
  font-weight: 800;
  color: var(--color-banner-text);
  letter-spacing: -0.3px;
}

.chat-subtitle {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-banner-text);
  opacity: 0.68;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.12);
  color: var(--color-banner-text);
  cursor: pointer;
  transition: background 0.18s ease, transform 0.15s ease;
}

.chat-icon-btn:hover {
  background: rgba(0, 0, 0, 0.22);
  transform: scale(1.06);
}

.chat-body {
  display: flex;
  flex: 1;
  min-height: 0;
}

.chat-sidebar {
  width: 260px;
  flex: 0 0 auto;
  border-right: 1px solid rgba(0, 0, 0, 0.12);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 0;
}

.chat-sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.chat-sidebar-title {
  font-family: 'Manrope', sans-serif;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(0, 0, 0, 0.55);
}

.chat-sidebar-meta {
  font-family: 'Manrope', sans-serif;
  font-size: 12px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.55);
}

.chat-sidebar-meta--error {
  color: rgba(160, 0, 0, 0.72);
}

.chat-sidebar-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-right: 4px;
  scrollbar-width: none;
}

.chat-sidebar-list::-webkit-scrollbar {
  display: none;
}

.chat-sidebar-item {
  width: 100%;
  text-align: left;
  border: 1px solid rgba(0, 0, 0, 0.12);
  background: rgba(255, 255, 255, 0.55);
  border-radius: 14px;
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  cursor: pointer;
  transition: background 0.18s ease, transform 0.15s ease, border-color 0.18s ease;
}

.chat-sidebar-item:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateY(-1px);
}

.chat-sidebar-item--active {
  border-color: rgba(0, 0, 0, 0.28);
  background: rgba(255, 255, 255, 0.95);
}

.chat-sidebar-item-title {
  font-family: 'Manrope', sans-serif;
  font-size: 12px;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.8);
  line-height: 1.3;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.chat-sidebar-item-delete {
  flex: 0 0 auto;
  border: none;
  background: transparent;
  color: rgba(0, 0, 0, 0.52);
  border-radius: 10px;
  padding: 6px;
  cursor: pointer;
}

.chat-sidebar-item-delete:hover {
  background: rgba(0, 0, 0, 0.06);
  color: rgba(0, 0, 0, 0.72);
}

.chat-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

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

.chat-messages-inner {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bubble {
  max-width: min(86%, 760px);
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
  background: var(--color-surface);
  color: var(--color-text-always-dark);
}

.bubble--user {
  align-self: flex-end;
  background: rgba(0, 0, 0, 0.14);
  color: var(--color-banner-text);
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.bubble--typing {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 16px 20px;
}

.dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.35);
  animation: bounce 1s infinite ease-in-out;
}

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

.bubble-enter-active {
  animation: bubble-pop 0.42s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

.bubble--ai.bubble-enter-active {
  transform-origin: bottom left;
}

.bubble--user.bubble-enter-active {
  transform-origin: bottom right;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  40% { transform: translateY(-5px); }
}

@keyframes bubble-pop {
  0% { opacity: 0; transform: scale(0.55); }
  65% { opacity: 1; transform: scale(1.04); }
  82% { transform: scale(0.97); }
  100% { transform: scale(1); }
}

@media (max-width: 900px) {
  .aura-chat-page {
    padding: 14px 12px 16px;
  }

  .aura-chat-shell {
    height: calc(100vh - 30px);
    border-radius: 24px;
  }

  .chat-body {
    flex-direction: column;
  }

  .chat-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid rgba(0, 0, 0, 0.12);
    max-height: 168px;
  }

  .chat-messages {
    padding: 8px 12px 12px;
  }

  .chat-input-wrap {
    padding: 10px 10px 12px;
  }
}
</style>
