/**
 * useChat — AI Chat Composable
 *
 * Owns all chat state and message logic.
 * Shared as a singleton (module-level refs) so SideNav mini-chat
 * and the floating AuraChatWindow stay perfectly in sync.
 */

import { ref, nextTick } from 'vue'
import { getStoredAuthMeta } from '@/services/localAuth.js'
import { resolveAssistantBaseUrl } from '@/services/assistantBaseUrl.js'
import { streamAssistantReply } from '@/services/assistantApi.js'

// ─── Shared singleton state ───────────────────────────────────────────────────
const messages   = ref([
  { id: 1, sender: 'ai', text: 'Hi! I am Aura AI. How can I help you today?' }
])
const inputText  = ref('')
const isTyping   = ref(false)
const isMiniOpen = ref(false)
const isFullOpen = ref(false)
const conversationId = ref(loadStoredConversationId())

// Holds a ref to the messages scroll container (set by the active chat view)
const scrollEl   = ref(null)

function getAssistantErrorMessage(error) {
  const status = Number(error?.status || 0)
  const message = String(error?.message || '').trim()

  if (status === 401) {
    return 'Your session expired. Log in again so Aura can use your account scope.'
  }

  if (status === 403 && message) {
    return message
  }

  if (message) {
    return message
  }

  return 'Something went wrong while contacting Aura Assistant. Please try again.'
}

function loadStoredConversationId() {
  try {
    const raw = localStorage.getItem('aura_assistant_conversation_id')
    const trimmed = String(raw || '').trim()
    return trimmed || null
  } catch {
    return null
  }
}

function storeConversationId(value) {
  const normalized = String(value || '').trim()
  conversationId.value = normalized || null

  try {
    if (conversationId.value) {
      localStorage.setItem('aura_assistant_conversation_id', conversationId.value)
    } else {
      localStorage.removeItem('aura_assistant_conversation_id')
    }
  } catch {
    // Ignore storage errors and keep the in-memory value.
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function scrollToBottom() {
  nextTick(() => {
    if (scrollEl.value) {
      scrollEl.value.scrollTop = scrollEl.value.scrollHeight
    }
  })
}

async function streamAiResponse(userMessage, { token, userMeta } = {}) {
  const aiMessage = { id: Date.now() + 1, sender: 'ai', text: '' }
  messages.value.push(aiMessage)

  await streamAssistantReply({
    baseUrl: resolveAssistantBaseUrl(),
    token,
    message: userMessage,
    conversationId: conversationId.value,
    userMeta,
    onMessageChunk: (chunk, meta) => {
      aiMessage.text += chunk
      if (meta?.conversationId) {
        storeConversationId(meta.conversationId)
      }
      scrollToBottom()
    },
  })
}

// ─── Public actions ───────────────────────────────────────────────────────────
async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isTyping.value) return

  messages.value.push({ id: Date.now(), sender: 'user', text })
  inputText.value = ''
  isTyping.value  = true
  scrollToBottom()

  try {
    const token = String(localStorage.getItem('aura_token') || '').trim()
    const userMeta = getStoredAuthMeta()

    if (!token) {
      messages.value.push({
        id: Date.now() + 1,
        sender: 'ai',
        text: 'Please log in first so I can access your campus account scope.',
      })
      return
    }

    await streamAiResponse(text, { token, userMeta })
  } catch (error) {
    messages.value.push({
      id: Date.now() + 1,
      sender: 'ai',
      text: getAssistantErrorMessage(error)
    })
  } finally {
    isTyping.value = false
    scrollToBottom()
  }
}

function openMini()  { isMiniOpen.value = true  }
function closeMini() { isMiniOpen.value = false }

function openFull()  {
  isFullOpen.value = true
  // Mini stays open in background; full window takes focus
}

function closeFull() { isFullOpen.value = false }

function openPill()  {
  // Called when user clicks the collapsed lime pill
  isMiniOpen.value = true
}

function expandToFull() {
  // Called from mini chat's Maximize button
  isMiniOpen.value = false   // hide the mini pill — full window takes over
  isFullOpen.value = true
}

function minimizeToMini() {
  // Called from full chat's Minimize button
  isFullOpen.value = false
  isMiniOpen.value = true
}

function closeAll() {
  isFullOpen.value = false
  isMiniOpen.value = false
}

// ─── Composable export ────────────────────────────────────────────────────────
export function useChat() {
  return {
    messages,
    inputText,
    isTyping,
    isMiniOpen,
    isFullOpen,
    conversationId,
    scrollEl,
    sendMessage,
    openMini,
    closeMini,
    openFull,
    closeFull,
    openPill,
    expandToFull,
    minimizeToMini,
    closeAll,
  }
}
