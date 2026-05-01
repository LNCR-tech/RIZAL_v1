# Contributing

> Coding standards and patterns to follow when adding features to Aura Frontend v3.

---

## Project Conventions

### File Naming

| Type         | Pattern              | Example                            |
| ------------ | -------------------- | ---------------------------------- |
| Views        | `PascalCase` + `View`| `HomeView.vue`, `SchoolItHomeView.vue` |
| Components   | `PascalCase`         | `TopBar.vue`, `SecurityActionPill.vue` |
| Composables  | `camelCase` + `use`  | `useAuth.js`, `useSchoolItWorkspaceData.js` |
| Services     | `camelCase`          | `backendApi.js`, `localAuth.js`    |
| Config       | `camelCase`          | `theme.js`                         |
| Data files   | `camelCase`          | `schoolItPreview.js`               |

### Component Structure

All components use **`<script setup>`** syntax. Follow this order inside each `.vue` file:

```
<template>    ← HTML structure
<script setup> ← Logic (imports, props, emits, refs, computed, functions)
<style scoped>  ← Scoped styles (only if needed)
```

### Folder Conventions

| Folder                          | Purpose                                          |
| ------------------------------- | ------------------------------------------------ |
| `src/views/auth/`              | Authentication views (login, face reg, password) |
| `src/views/dashboard/`         | Student dashboard and School IT workspace views  |
| `src/views/tools/`             | Developer tools (API Lab)                        |
| `src/components/ui/`           | Generic reusable components (buttons, inputs, chat) |
| `src/components/dashboard/`    | Dashboard-specific components (TopBar, Banner, etc.) |
| `src/components/navigation/`   | SideNav, BottomNav, and navigation item config   |
| `src/components/gather/`       | Gather attendance and discovery components       |
| `src/components/governance/`   | Governance analytics and creation components     |
| `src/components/security/`     | Security-related UI components                   |
| `src/components/attendance/`   | Attendance/face scan components                  |
| `src/components/council/`      | Student council management stage components      |
| `src/composables/`             | Shared state logic (sessions, auth, workspace data) |
| `src/services/`                | Backend API services and utilities               |
| `src/config/`                  | App configuration (theming engine)               |
| `src/data/`                    | Preview/mock data sets                           |
| `src/layouts/`                 | Shared layout shells (AppLayout)                 |

### Import Aliases

Use the `@` alias (mapped to `src/`) for all internal imports:

```js
// ✅ Good
import TopBar from '@/components/dashboard/TopBar.vue'

// ❌ Avoid
import TopBar from '../../components/dashboard/TopBar.vue'
```

---

## Styling Rules

- **Tailwind CSS 4** is the primary styling tool. Use utility classes directly in templates.
- **CSS Variables** (`var(--color-primary)`, etc.) are used for theme-driven values. Apply them via inline `style` attributes.
- **Scoped styles** (`<style scoped>`) only for animations and transitions that Tailwind can't handle.
- **Font**: Manrope — already imported globally. Use via `font-[Manrope]` or the body default.
- **Mobile-first**: Design for mobile first, then enhance for desktop. Use responsive utilities (`md:`, `lg:`).

---

## Adding a New Dashboard View

1. **Create the view** in `src/views/dashboard/`:

```vue
<!-- src/views/dashboard/NewView.vue -->
<template>
  <div class="flex flex-col gap-4 px-4 md:px-10 pb-6">
    <TopBar :user="currentUser" />
    <h1 class="text-[26px] font-extrabold" style="color: var(--color-text-primary);">
      Page Title
    </h1>
    <!-- Your content here -->
  </div>
</template>

<script setup>
import TopBar from '@/components/dashboard/TopBar.vue'
import { useDashboardSession } from '@/composables/useDashboardSession.js'

const { currentUser } = useDashboardSession()
</script>
```

2. **Add the route** in `src/router/index.js`:

```js
// Inside the /dashboard children array:
{
    path: 'new-page',
    name: 'NewPage',
    component: () => import('@/views/dashboard/NewView.vue'),
},
```

3. **Add the nav item** in `src/components/navigation/navigationItems.js`:

```js
{ name: 'New Page', route: '/dashboard/new-page', icon: IconName },
```

The nav item will automatically appear in both `SideNav.vue` and `BottomNav.vue`.

---

## Adding a New Service

1. Place the service in `src/services/`.
2. Use `backendBaseUrl.js` for URL resolution.
3. Use `backendNormalizers.js` patterns for response shaping.
4. Export named functions, not default exports.

```js
// src/services/newService.js
import { getBackendBaseUrl } from './backendBaseUrl.js'

export async function fetchSomething(token) {
    const baseUrl = getBackendBaseUrl()
    const res = await fetch(`${baseUrl}/api/something`, {
        headers: { Authorization: `Bearer ${token}` },
    })
    return res.json()
}
```

---

## Adding a New Reusable Component

1. Place it in `src/components/ui/` if it's generic (buttons, inputs, modals).
2. Place it in `src/components/dashboard/` if it's dashboard-specific.
3. Place it in the appropriate feature folder (`security/`, `council/`, `attendance/`) for feature-specific components.
4. Define `props` with types and defaults. Define `emits` explicitly.
5. Use CSS variables for theme-driven colors, not hardcoded values.

---

## Commit Messages

Use clear, descriptive commit messages:

```
feat: add schedule view with weekly calendar
fix: dark mode text contrast on events card
refactor: extract date formatting into composable
docs: update API integration guide
```

Prefixes: `feat`, `fix`, `refactor`, `docs`, `style`, `chore`.

---

## Things to Watch Out For

- **Always use `--color-text-always-dark`** for text inside white cards — this ensures readability in both light and dark mode.
- **Never hardcode brand colors** — use `var(--color-primary)` so theming works across all schools.
- **Navigation items are centralized** — edit `navigationItems.js` to add/remove nav items. Both `SideNav` and `BottomNav` read from this file.
- **Backend Communication** — Always use `useDashboardSession.js` or services from `src/services/` for data. Do not use direct Axios/fetch calls in views.
- **Use `backendMedia.js`** for building media URLs. Do not hardcode asset paths.
- **Mobile responsiveness** — Test on Android browsers. Use the PWA manifest for install-to-home-screen testing.
