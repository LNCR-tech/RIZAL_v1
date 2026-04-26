/**
 * useChat — AI Chat Composable
 *
 * Owns all chat state and message logic.
 * Backend integration: replace the simulateAiResponse() function
 * with a real API call (e.g. POST /api/chat/message) when ready.
 *
 * Shared as a singleton (module-level refs) so SideNav mini-chat
 * and the floating AuraChatWindow stay perfectly in sync.
 */

import { ref, nextTick } from 'vue'

// ─── Shared singleton state ───────────────────────────────────────────────────
const isAuraChatUnderDevelopment = ref(true)
const auraChatNoticeTitle = 'Feature under development'
const auraChatNoticeText = 'Talk with Aura is under development. This feature will be available in a future release.'
const messages   = ref([
  {
    id: 1,
    sender: 'ai',
    text: auraChatNoticeText,
  }
])
const inputText  = ref('')
const isTyping   = ref(false)
const isMiniOpen = ref(false)
const isFullOpen = ref(false)

// Holds a ref to the messages scroll container (set by the active chat view)
const scrollEl   = ref(null)

// ─── Helpers ──────────────────────────────────────────────────────────────────
function scrollToBottom() {
  nextTick(() => {
    if (scrollEl.value) {
      scrollEl.value.scrollTop = scrollEl.value.scrollHeight
    }
  })
}

// ─── Backend stub — replace this function with your real API call ─────────────
async function simulateAiResponse(userMessage) {
  /**
   * TODO: Replace with:
   * const { data } = await api.post('/chat/message', { message: userMessage })
   * return data.reply
   */
  await new Promise(resolve => setTimeout(resolve, 1400))

  const normalizedMessage = userMessage.trim().toLowerCase()

  if (/^(hi|hello|hey|good morning|good afternoon|good evening)\b/.test(normalizedMessage)) {
    return "Hello! I'm Aura AI. I'm here to help you navigate your campus tools. I'm still running in demo mode for now, but once the backend is connected I'll be able to answer with live school data."
  }

  if (normalizedMessage.includes('schedule')) {
    return "I can help with schedules. Right now I'm in frontend demo mode, so I can't load live class data yet, but this is where I would guide you through your upcoming classes and time slots."
  }

  if (normalizedMessage.includes('attendance')) {
    return "I can help with attendance. Once the backend is connected, I'll be able to check attendance records, event participation, and status updates for you."
  }

  if (normalizedMessage.includes('event')) {
    return "I can help you track campus events. In the full version, I'll be able to show event details, schedules, and attendance-related information in real time."
  }

  if (normalizedMessage.includes('create a college') || normalizedMessage.includes('college of engineering')) {
    return {
      text: "I've successfully set up the College of Engineering. I have also initialized the primary governance structure and sent an onboarding notification to the assigned Campus Admin.",
      actions: [
        {
          label: "View in Admin Workspace",
          route: "/exposed/admin/schools",
          icon: "ExternalLink"
        }
      ]
    }
  }

  if (normalizedMessage.includes('show me graph') || normalizedMessage.includes('engineering students')) {
    return {
      text: "Here is the enrollment distribution for the College of Engineering across its designated programs:",
      html: `
        <p><strong>College of Engineering Overview</strong></p>
        <div class="mock-graph">
          <div class="mock-graph-bar" style="height: 80%"><span style="color:#0a0a0a; font-weight: 800;">800</span></div>
          <div class="mock-graph-bar" style="height: 45%"><span style="color:#0a0a0a; font-weight: 800;">450</span></div>
          <div class="mock-graph-bar" style="height: 60%"><span style="color:#0a0a0a; font-weight: 800;">600</span></div>
        </div>
        <div class="mock-graph-label">
          <span>BSCE</span>
          <span>BSEE</span>
          <span>BSME</span>
        </div>
      `,
      actions: [
        {
          label: "Download as PDF",
          actionId: "download-pdf",
          icon: "Download"
        },
        {
          label: "Download as CSV",
          actionId: "download-csv",
          icon: "Download"
        }
      ]
    }
  }

  return { text: "I'm here and ready to help. This chat is still using a frontend-only demo response for now, but once the backend is connected I'll be able to give real answers based on your school data." }
}

// ─── Public actions ───────────────────────────────────────────────────────────
async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isTyping.value || isAuraChatUnderDevelopment.value) {
    inputText.value = ''
    return
  }

  messages.value.push({ id: Date.now(), sender: 'user', text })
  inputText.value = ''
  isTyping.value  = true
  scrollToBottom()

  try {
    const reply = await simulateAiResponse(text)
    messages.value.push({ 
      id: Date.now() + 1, 
      sender: 'ai', 
      text: reply.text || (typeof reply === 'string' ? reply : ''),
      html: reply.html || null,
      actions: reply.actions || null
    })
  } catch {
    messages.value.push({
      id: Date.now() + 1,
      sender: 'ai',
      text: 'Something went wrong. Please try again.'
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
    isAuraChatUnderDevelopment,
    auraChatNoticeTitle,
    auraChatNoticeText,
    messages,
    inputText,
    isTyping,
    isMiniOpen,
    isFullOpen,
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
