import { resolveAbsoluteAssistantBaseUrl } from '@/services/assistantBaseUrl.js'

export class AssistantApiError extends Error {
  constructor(message, { status = 0, details = null } = {}) {
    super(message)
    this.name = 'AssistantApiError'
    this.status = status
    this.details = details
  }
}

function buildUrl(baseUrl, path) {
  return new URL(`${resolveAbsoluteAssistantBaseUrl(baseUrl)}${path}`).toString()
}

function getBrowserTimezone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || null
  } catch {
    return null
  }
}

function parseSseBlock(block = '') {
  const lines = String(block).split('\n')
  let event = ''
  let data = ''

  for (const line of lines) {
    if (line.startsWith('event:')) event = line.slice('event:'.length).trim()
    if (line.startsWith('data:')) data = line.slice('data:'.length).trim()
  }

  if (!data) return null

  try {
    return { event: event || 'message', data: JSON.parse(data) }
  } catch {
    return { event: event || 'message', data: { raw: data } }
  }
}

export async function streamAssistantReply({
  baseUrl = '',
  token = '',
  message = '',
  conversationId = null,
  userMeta = null,
  onMessageChunk,
} = {}) {
  const trimmed = String(message || '').trim()
  if (!trimmed) throw new AssistantApiError('Message is required.')
  if (!token) throw new AssistantApiError('Missing access token.', { status: 401 })

  const payload = {
    message: trimmed,
    conversation_id: conversationId || undefined,
    user_name: userMeta?.firstName ? `${userMeta.firstName}${userMeta.lastName ? ` ${userMeta.lastName}` : ''}` : undefined,
    user_school: userMeta?.schoolName || undefined,
    user_school_id: Number.isFinite(Number(userMeta?.schoolId)) ? Number(userMeta.schoolId) : undefined,
    user_timezone: getBrowserTimezone() || undefined,
  }

  const response = await fetch(buildUrl(baseUrl, '/assistant/stream'), {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    let details = null
    try {
      details = await response.json()
    } catch {
      details = await response.text().catch(() => null)
    }

    const messageText = details?.detail || details?.message || response.statusText || 'Assistant request failed.'
    throw new AssistantApiError(String(messageText), { status: response.status, details })
  }

  if (!response.body) {
    throw new AssistantApiError('Assistant stream did not return a response body.')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let latestConversationId = conversationId

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    let splitIndex = buffer.indexOf('\n\n')
    while (splitIndex >= 0) {
      const block = buffer.slice(0, splitIndex)
      buffer = buffer.slice(splitIndex + 2)

      const parsed = parseSseBlock(block)
      if (parsed) {
        if (parsed?.data?.conversation_id) {
          latestConversationId = parsed.data.conversation_id
        }

        if (parsed.event === 'message') {
          const chunk = String(parsed?.data?.content ?? '')
          if (chunk && typeof onMessageChunk === 'function') {
            onMessageChunk(chunk, { conversationId: latestConversationId })
          }
        }

        if (parsed.event === 'done') {
          return {
            conversationId: latestConversationId,
            messageId: parsed?.data?.message_id || null,
            finishReason: parsed?.data?.finish_reason || null,
          }
        }
      }

      splitIndex = buffer.indexOf('\n\n')
    }
  }

  return { conversationId: latestConversationId, messageId: null, finishReason: 'eof' }
}
