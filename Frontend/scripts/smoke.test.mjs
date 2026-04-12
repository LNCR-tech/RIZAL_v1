import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { join, resolve } from 'node:path'

const frontendRoot = resolve(fileURLToPath(new URL('..', import.meta.url)))
const repoRoot = resolve(frontendRoot, '..')

test('runtime config template exposes required keys', () => {
  const template = readFileSync(join(frontendRoot, 'runtime-config.js.template'), 'utf8')
  assert.match(template, /\$\{AURA_API_BASE_URL\}/)
  assert.match(template, /\$\{AURA_API_TIMEOUT_MS\}/)
  assert.match(template, /\$\{AURA_ASSISTANT_BASE_URL\}/)
})

test('frontend bootstrap mounts app root', () => {
  const mainSource = readFileSync(join(frontendRoot, 'src', 'main.js'), 'utf8')
  assert.match(mainSource, /createApp\(App\)/)
  assert.match(mainSource, /app\.mount\('#app'\)/)
})

test('shared env example includes frontend keys', () => {
  const envExample = readFileSync(join(repoRoot, '.env.example'), 'utf8')
  assert.match(envExample, /^VITE_API_BASE_URL=/m)
  assert.match(envExample, /^AURA_API_BASE_URL=/m)
})

test('student dashboard sanctions routes are wired', () => {
  const routerSource = readFileSync(join(frontendRoot, 'src', 'router', 'index.js'), 'utf8')
  assert.match(routerSource, /name:\s*'DashboardSanctions'/)
  assert.match(routerSource, /name:\s*'PreviewDashboardSanctions'/)
  assert.match(routerSource, /const StudentSanctionsView = dashboardView\('StudentSanctionsView'\)/)
})

test('student navigation includes sanctions destinations', () => {
  const navSource = readFileSync(join(frontendRoot, 'src', 'components', 'navigation', 'navigationItems.js'), 'utf8')
  assert.match(navSource, /route:\s*'\/dashboard\/sanctions'/)
  assert.match(navSource, /route:\s*'\/exposed\/dashboard\/sanctions'/)
})

test('app shell wires sanctions deadline warning redirect', () => {
  const appSource = readFileSync(join(frontendRoot, 'src', 'App.vue'), 'utf8')
  assert.match(appSource, /SanctionsDeadlineWarningModal/)
  assert.match(appSource, /getActiveClearanceDeadline/)
  assert.match(appSource, /name:\s*'DashboardSanctions'/)
})
