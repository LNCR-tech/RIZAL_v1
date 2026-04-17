import test from 'node:test'
import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
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

test('shared env configuration includes frontend keys', () => {
  const envPath = existsSync(join(repoRoot, '.env.example'))
    ? join(repoRoot, '.env.example')
    : join(repoRoot, '.env')
  const envSource = readFileSync(envPath, 'utf8')
  assert.match(envSource, /^VITE_API_BASE_URL=/m)
  assert.match(envSource, /^AURA_API_BASE_URL=/m)
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

test('login surfaces remember-me controls', () => {
  const loginSource = readFileSync(join(frontendRoot, 'src', 'views', 'auth', 'LoginView.vue'), 'utf8')
  assert.match(loginSource, /Remember me/)
  assert.match(loginSource, /v-model="rememberMe"/)
})

test('privileged face gate route is registered', () => {
  const routerSource = readFileSync(join(frontendRoot, 'src', 'router', 'index.js'), 'utf8')
  assert.match(routerSource, /name:\s*'PrivilegedFaceVerification'/)
  assert.match(routerSource, /allowWithoutFaceEnrollment:\s*true/)
})

test('profile settings expose account configuration save action', () => {
  const profileSource = readFileSync(join(frontendRoot, 'src', 'views', 'dashboard', 'ProfileView.vue'), 'utf8')
  assert.match(profileSource, /Save Configuration/)
  assert.match(profileSource, /saveAppConfiguration/)
})
