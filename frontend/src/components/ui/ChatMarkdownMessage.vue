<template>
  <div class="chat-markdown-message" ref="containerRef" v-html="html" />
</template>

<script setup>
import { computed, ref, onMounted, onUpdated, nextTick } from 'vue'
import { renderChatMarkdown } from '@/services/chatMarkdown.js'

const props = defineProps({
  text: {
    type: String,
    default: '',
  },
})

const containerRef = ref(null)
const html = computed(() => renderChatMarkdown(props.text))

/**
 * ChatGPT-style "Copy" button and header injection for code blocks.
 */
async function processCodeBlocks() {
  await nextTick()
  if (!containerRef.value) return

  const pres = containerRef.value.querySelectorAll('pre')
  pres.forEach((pre) => {
    // Avoid double injection
    if (pre.parentElement.classList.contains('code-block-wrapper')) return

    const wrapper = document.createElement('div')
    wrapper.className = 'code-block-wrapper'

    const header = document.createElement('div')
    header.className = 'code-block-header'

    // Try to find language from <code> class
    const code = pre.querySelector('code')
    let lang = 'code'
    if (code) {
      const langClass = Array.from(code.classList).find((c) => c.startsWith('language-'))
      if (langClass) {
        lang = langClass.replace('language-', '')
      }
    }

    const langLabel = document.createElement('span')
    langLabel.className = 'code-block-lang'
    langLabel.textContent = lang

    const copyBtn = document.createElement('button')
    copyBtn.className = 'code-block-copy'
    copyBtn.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
      <span>Copy code</span>
    `

    copyBtn.addEventListener('click', () => {
      const textToCopy = code ? code.innerText : pre.innerText
      navigator.clipboard.writeText(textToCopy).then(() => {
        copyBtn.innerHTML = `
          <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="green" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
          <span style="color: #4ade80">Copied!</span>
        `
        setTimeout(() => {
          copyBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
            <span>Copy code</span>
          `
        }, 2000)
      })
    })

    header.appendChild(langLabel)
    header.appendChild(copyBtn)

    // Rearrange DOM
    pre.parentNode.insertBefore(wrapper, pre)
    wrapper.appendChild(header)
    wrapper.appendChild(pre)
  })
}

onMounted(processCodeBlocks)
onUpdated(processCodeBlocks)
</script>

<style scoped>
.chat-markdown-message {
  white-space: normal;
  color: inherit;
  font-family: inherit;
  line-height: 1.6;
}

/* Base resets for markdown elements */
.chat-markdown-message :deep(p),
.chat-markdown-message :deep(ul),
.chat-markdown-message :deep(ol),
.chat-markdown-message :deep(blockquote),
.chat-markdown-message :deep(table),
.chat-markdown-message :deep(.code-block-wrapper) {
  margin: 0;
}

.chat-markdown-message :deep(p + p),
.chat-markdown-message :deep(p + ul),
.chat-markdown-message :deep(p + ol),
.chat-markdown-message :deep(p + blockquote),
.chat-markdown-message :deep(p + table),
.chat-markdown-message :deep(p + .code-block-wrapper),
.chat-markdown-message :deep(ul + p),
.chat-markdown-message :deep(ol + p),
.chat-markdown-message :deep(table + p),
.chat-markdown-message :deep(.code-block-wrapper + p),
.chat-markdown-message :deep(blockquote + p) {
  margin-top: 0.85em;
}

/* Lists */
.chat-markdown-message :deep(ul),
.chat-markdown-message :deep(ol) {
  padding-left: 1.5em;
}

.chat-markdown-message :deep(li + li) {
  margin-top: 0.35em;
}

/* Typography */
.chat-markdown-message :deep(strong) {
  font-weight: 700;
  color: inherit;
}

.chat-markdown-message :deep(a) {
  color: #3b82f6;
  text-decoration: underline;
  text-underline-offset: 3px;
  transition: opacity 0.2s;
}

.chat-markdown-message :deep(a:hover) {
  opacity: 0.8;
}

/* Code Blocks & Injected Header */
.chat-markdown-message :deep(.code-block-wrapper) {
  background: #0d1117;
  border-radius: 8px;
  overflow: hidden;
  margin: 1em 0;
  border: 1px solid rgba(255, 255, 255, 0.1);
  max-width: 100%;
}

.chat-markdown-message :deep(.code-block-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #161b22;
  padding: 8px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  font-family: 'Inter', sans-serif;
}

.chat-markdown-message :deep(.code-block-lang) {
  font-size: 11px;
  text-transform: lowercase;
  color: #8b949e;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.chat-markdown-message :deep(.code-block-copy) {
  display: flex;
  align-items: center;
  gap: 5px;
  background: transparent;
  border: none;
  color: #8b949e;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s, color 0.2s;
}

.chat-markdown-message :deep(.code-block-copy:hover) {
  background: rgba(255, 255, 255, 0.05);
  color: #c9d1d9;
}

.chat-markdown-message :deep(pre) {
  margin: 0;
  padding: 16px;
  overflow-x: auto;
  white-space: pre; /* Ensure no wrapping */
  word-wrap: normal;
}

.chat-markdown-message :deep(code) {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.9em;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.06);
  padding: 0.2em 0.4em;
}

.chat-markdown-message :deep(pre code) {
  background: transparent;
  padding: 0;
  border-radius: 0;
  color: #e6edf3;
  line-height: 1.5;
  white-space: pre;
}

/* Tables */
.chat-markdown-message :deep(table) {
  display: block; /* Required for horizontal overflow on the table itself */
  width: 100%;
  max-width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  margin: 1em 0;
}

.chat-markdown-message :deep(th),
.chat-markdown-message :deep(td) {
  min-width: 100px; /* Encourages scrolling for many columns */
  white-space: nowrap; /* Prevents wrapping within cells to force horizontal scroll */
}

.chat-markdown-message :deep(th) {
  background: rgba(0, 0, 0, 0.04);
  font-weight: 700;
  text-align: left;
  padding: 10px 12px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.chat-markdown-message :deep(td) {
  padding: 8px 12px;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.chat-markdown-message :deep(tr:nth-child(even)) {
  background: rgba(0, 0, 0, 0.015);
}

/* Blockquotes */
.chat-markdown-message :deep(blockquote) {
  border-left: 4px solid #3b82f6;
  background: rgba(59, 130, 246, 0.05);
  padding: 0.8em 1.2em;
  color: rgba(0, 0, 0, 0.75);
  border-radius: 2px 8px 8px 2px;
}

/* KaTeX Math Tweaks */
.chat-markdown-message :deep(.katex-display) {
  margin: 1em 0;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 0.5em 0;
}
</style>
