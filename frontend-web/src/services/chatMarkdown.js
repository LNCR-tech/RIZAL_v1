import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { markedHighlight } from 'marked-highlight'
import hljs from 'highlight.js'
import markedKatex from 'marked-katex-extension'

marked.use(
  markedHighlight({
    langPrefix: 'hljs language-',
    highlight(code, lang) {
      const language = hljs.getLanguage(lang) ? lang : 'plaintext'
      return hljs.highlight(code, { language }).value
    },
  }),
  markedKatex({
    throwOnError: false,
  }),
)

marked.setOptions({
  gfm: true,
  breaks: true,
})

let hasLinkHook = false

function ensureLinkHook() {
  if (hasLinkHook || typeof window === 'undefined') return

  DOMPurify.addHook('afterSanitizeAttributes', (node) => {
    if (node?.tagName !== 'A') return

    node.setAttribute('target', '_blank')
    node.setAttribute('rel', 'noopener noreferrer')
  })

  hasLinkHook = true
}

export function renderChatMarkdown(value = '') {
  const source = String(value ?? '')
  if (!source.trim()) return ''

  ensureLinkHook()

  const html = marked.parse(source, { async: false })
  return DOMPurify.sanitize(html, {
    USE_PROFILES: { html: true },
    ALLOWED_URI_REGEXP: /^(?:(?:https?|mailto|tel):|[^a-z]|[a-z+.-]+(?:[^a-z+.-:]|$))/i,
  })
}
