/**
 * useChat — AI Chat Composable
 *
 * Shared as a singleton (module-level refs) so SideNav mini-chat
 * and the floating AuraChatWindow stay perfectly in sync.
 */

import { ref, nextTick } from 'vue'
import { getStoredAuthMeta } from '@/services/localAuth.js'
import { resolveAssistantBaseUrl } from '@/services/assistantBaseUrl.js'
import {
  streamAssistantReply,
  listAssistantConversations,
  getAssistantConversation,
  deleteAssistantConversation,
  AssistantApiError,
} from '@/services/assistantApi.js'

// ─── Shared singleton state ───────────────────────────────────────────────────
const messages   = ref([
  { id: 1, sender: 'ai', text: 'Hi! I am Aura AI. How can I help you today?' }
])
const inputText  = ref('')
const isTyping   = ref(false)
const currentToolCall = ref(null)
const typingConversationId = ref(null)
const isMiniOpen = ref(false)
const isFullOpen = ref(false)
const conversationId = ref(loadStoredConversationId())
const conversations = ref([])
const isLoadingConversations = ref(false)
const conversationsError = ref(null)
const copyStatus = ref('idle')

const scrollEl   = ref(null)
let copyResetTimer = null

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

function getAuthToken() {
  return String(localStorage.getItem('aura_token') || '').trim()
}

function normalizeConversationTitle(convo) {
  const raw = String(convo?.title || '').trim()
  if (raw) return raw
  const fallback = String(convo?.last_message || '').trim()
  return fallback ? fallback.slice(0, 44) : 'New chat'
}

function resetToGreeting() {
  messages.value = [
    { id: 1, sender: 'ai', text: 'Hi! I am Aura AI. How can I help you today?' },
  ]
}

function resetChatState() {
  resetToGreeting()
  storeConversationId(null)
  conversations.value = []
  typingConversationId.value = null
  isTyping.value = false
  isMiniOpen.value = false
  isFullOpen.value = false
  conversationsError.value = null
}

function formatConversationText() {
  return (messages.value || [])
    .map((msg) => {
      const sender = msg?.sender === 'user' ? 'You' : 'Aura'
      const text = String(msg?.text ?? '').trim()
      if (!text) return null
      return `${sender}: ${text}`
    })
    .filter(Boolean)
    .join('\n\n')
}

async function copyConversation() {
  const text = formatConversationText()
  if (!text) return false

  try {
    if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
    } else {
      const el = document.createElement('textarea')
      el.value = text
      el.setAttribute('readonly', '')
      el.style.position = 'fixed'
      el.style.left = '-9999px'
      el.style.top = '0'
      document.body.appendChild(el)
      el.select()
      document.execCommand('copy')
      document.body.removeChild(el)
    }

    copyStatus.value = 'copied'
    if (copyResetTimer) clearTimeout(copyResetTimer)
    copyResetTimer = setTimeout(() => { copyStatus.value = 'idle' }, 1200)
    return true
  } catch {
    copyStatus.value = 'failed'
    if (copyResetTimer) clearTimeout(copyResetTimer)
    copyResetTimer = setTimeout(() => { copyStatus.value = 'idle' }, 1500)
    return false
  }
}

async function streamAiResponse(userMessage, { token, userMeta } = {}) {
  const msgId = Date.now() + 1
  messages.value.push({ id: msgId, sender: 'ai', text: '', visual: null })
  const msgIdx = messages.value.length - 1

  try {
    return await streamAssistantReply({
      baseUrl: resolveAssistantBaseUrl(),
      token,
      message: userMessage,
      conversationId: conversationId.value,
      userMeta,
      onMessageChunk: (chunk, meta) => {
        if (messages.value[msgIdx] !== undefined) {
          messages.value[msgIdx] = {
            ...messages.value[msgIdx],
            text: (messages.value[msgIdx].text || '') + chunk,
          }
        }
        if (meta?.conversationId) {
          storeConversationId(meta.conversationId)
          typingConversationId.value = meta.conversationId
        }
        scrollToBottom()
      },
      onVisualization: (viz, meta) => {
        if (messages.value[msgIdx] !== undefined) {
          messages.value[msgIdx] = {
            ...messages.value[msgIdx],
            visual: viz,
          }
        }
        if (meta?.conversationId) {
          storeConversationId(meta.conversationId)
        }
        scrollToBottom()
      },
      onToolCall: (toolName) => {
        currentToolCall.value = toolName
      },
      onToolDone: () => {
        currentToolCall.value = null
      },
    })
  } catch (err) {
    const idx = messages.value.findIndex((m) => m.id === msgId)
    if (idx >= 0) messages.value.splice(idx, 1)
    throw err
  }
}

async function refreshConversations() {
  const token = getAuthToken()
  conversationsError.value = null

  if (!token) {
    conversations.value = []
    return []
  }

  isLoadingConversations.value = true
  try {
    const data = await listAssistantConversations({ baseUrl: resolveAssistantBaseUrl(), token })
    conversations.value = Array.isArray(data) ? data : []
    return conversations.value
  } catch (err) {
    conversationsError.value = err instanceof AssistantApiError
      ? `${err.message}${err.status ? ` (HTTP ${err.status})` : ''}`
      : (err?.message || 'Failed to load conversations.')
    conversations.value = []
    return []
  } finally {
    isLoadingConversations.value = false
  }
}

async function startNewConversation() {
  storeConversationId(null)
  resetToGreeting()
}

async function selectConversation(targetConversationId) {
  const token = getAuthToken()
  const normalized = String(targetConversationId || '').trim()
  if (!token || !normalized) return false

  try {
    const convo = await getAssistantConversation({
      baseUrl: resolveAssistantBaseUrl(),
      token,
      conversationId: normalized,
    })

    const mapped = (convo?.messages || []).map((m, idx) => ({
      id: idx + 1,
      sender: m?.role === 'user' ? 'user' : 'ai',
      text: String(m?.content ?? ''),
      visual: m?.visual_data?.visual ?? null,
    }))

    messages.value = mapped.length
      ? mapped
      : [{ id: 1, sender: 'ai', text: 'Hi! I am Aura AI. How can I help you today?' }]

    storeConversationId(convo?.conversation_id || normalized)
    scrollToBottom()
    return true
  } catch (err) {
    if (err instanceof AssistantApiError && err.status === 404) {
      await startNewConversation()
      await refreshConversations()
      return false
    }
    throw err
  }
}

async function removeConversation(targetConversationId) {
  const token = getAuthToken()
  const normalized = String(targetConversationId || '').trim()
  if (!token || !normalized) return false

  await deleteAssistantConversation({
    baseUrl: resolveAssistantBaseUrl(),
    token,
    conversationId: normalized,
  })

  if (conversationId.value === normalized) {
    await startNewConversation()
  }
  await refreshConversations()
  return true
}

function getActiveConversationLabel() {
  const current = conversationId.value
  if (!current) return 'New chat'

  const match = (conversations.value || []).find((c) => String(c?.conversation_id || '') === current)
  if (!match) return 'Continuing chat'
  return normalizeConversationTitle(match)
}

// ─── Public actions ───────────────────────────────────────────────────────────
async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isTyping.value) return

  messages.value.push({ id: Date.now(), sender: 'user', text })
  inputText.value = ''
  isTyping.value  = true
  typingConversationId.value = conversationId.value
  scrollToBottom()

  try {
    const token = getAuthToken()
    const userMeta = getStoredAuthMeta()
    if (!token) {
      messages.value.push({
        id: Date.now() + 1,
        sender: 'ai',
        text: 'Please log in first so I can access your campus account scope.',
      })
      return
    }

    try {
      const result = await streamAiResponse(text, { token, userMeta })
      if (result?.conversationId && result.conversationId !== conversationId.value) {
        storeConversationId(result.conversationId)
      }
      refreshConversations()
    } catch (err) {
      const isConversationNotFound = err instanceof AssistantApiError
        && err.status === 404
        && /conversation not found/i.test(String(err.message || ''))

      if (isConversationNotFound && conversationId.value) {
        storeConversationId(null)
        const result = await streamAiResponse(text, { token, userMeta })
        if (result?.conversationId) storeConversationId(result.conversationId)
        refreshConversations()
      } else {
        throw err
      }
    }
  } catch (error) {
    if (typeof console !== 'undefined') {
      console.warn('Aura assistant request failed:', error)
    }

    messages.value.push({
      id: Date.now() + 1,
      sender: 'ai',
      text: getAssistantErrorMessage(error),
    })
  } finally {
    isTyping.value = false
    typingConversationId.value = null
    currentToolCall.value = null
    scrollToBottom()
  }
}

function openMini()  { isMiniOpen.value = true  }
function closeMini() { isMiniOpen.value = false }

function openFull()  {
  isFullOpen.value = true
}

function closeFull() { isFullOpen.value = false }

function openPill()  {
  isMiniOpen.value = true
}

function expandToFull() {
  isMiniOpen.value = false
  isFullOpen.value = true
}

function minimizeToMini() {
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
    currentToolCall,
    typingConversationId,
    isMiniOpen,
    isFullOpen,
    conversationId,
    conversations,
    isLoadingConversations,
    conversationsError,
    scrollEl,
    copyStatus,
    sendMessage,
    copyConversation,
    refreshConversations,
    startNewConversation,
    selectConversation,
    removeConversation,
    getActiveConversationLabel,
    openMini,
    closeMini,
    openFull,
    closeFull,
    openPill,
    expandToFull,
    minimizeToMini,
    closeAll,
    resetChatState,
  }
}
