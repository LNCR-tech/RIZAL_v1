import { readdirSync, readFileSync, statSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { join, resolve } from 'node:path'

const repoRoot = resolve(fileURLToPath(new URL('..', import.meta.url)))
const scanRoots = [
  join(repoRoot, 'src'),
  join(repoRoot, 'index.html'),
  join(repoRoot, 'runtime-config.js.template'),
]

const textExtensions = new Set(['.js', '.vue', '.css', '.html'])
const issues = []

function hasRelevantExtension(path) {
  for (const ext of textExtensions) {
    if (path.endsWith(ext)) return true
  }
  return false
}

function scanPath(path) {
  const stat = statSync(path)
  if (stat.isDirectory()) {
    for (const name of readdirSync(path)) {
      scanPath(join(path, name))
    }
    return
  }

  if (!hasRelevantExtension(path)) return
  const content = readFileSync(path, 'utf8')

  if (/^(<<<<<<<|=======|>>>>>>>)/m.test(content)) {
    issues.push(`${path}: unresolved merge marker detected`)
  }
}

for (const rootPath of scanRoots) {
  scanPath(rootPath)
}

if (issues.length > 0) {
  console.error('Frontend lint failed:')
  for (const issue of issues) {
    console.error(`- ${issue}`)
  }
  process.exit(1)
}

console.log('Frontend lint passed: no unresolved merge markers found.')
