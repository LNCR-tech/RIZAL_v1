# Theming Guide

> How the Aura frontend adapts its look per school.

---

## How It Works

Each school has a **settings record** on the backend (`GET /school-settings/me`) containing:

```json
{
  "school_id": 1,
  "school_name": "Rizal Technological University",
  "primary_color": "#AAFF00",
  "secondary_color": "#0A0A0A",
  "accent_color": "#88CC00",
  "logo_url": "/path/to/logo.png"
}
```

On app startup (`main.js`):

1. `loadTheme(schoolSettings)` merges the school's values into the default theme.
2. `applyTheme(theme)` writes CSS custom properties to `document.documentElement`.
3. Every component reads these variables (e.g. `var(--color-primary)`).

---

## CSS Variables Reference

| Variable                  | Driven By         | Example Value  |
| ------------------------- | ----------------- | -------------- |
| `--color-primary`         | `primary_color`   | `#AAFF00`      |
| `--color-primary-dark`    | `accent_color`    | `#88CC00`      |
| `--color-bg`              | Light: `#EBEBEB`, Dark: auto-derived | |
| `--color-surface`         | Always `#FFFFFF`  | Card backgrounds |
| `--color-banner-text`     | Auto (YIQ contrast) | `#0A0A0A` or `#FFFFFF` |
| `--color-text-primary`    | Light: `#0A0A0A`, Dark: `#FFFFFF` | |
| `--color-text-always-dark`| Always `#0A0A0A`  | Inside white cards |

---

## Switching Themes in Development

The backend API provides school settings dynamically. In offline/dev mode:

- `mockBackendApi.js` returns mock school settings.
- Settings are loaded via `useDashboardSession.js` on app startup.
- The theme adapts automatically based on the logged-in user's school.

To test different school themes in dev mode, modify the mock user's `school_id` in the mock backend service.

---

## Adding a New School Theme

1. Ensure the backend has a `school_settings` record for the new school with:
   - `primary_color` — brand color (hex)
   - `secondary_color` — secondary brand color
   - `accent_color` — hover/pressed variant color
   - `logo_url` — path to the school logo

2. When a user from that school logs in, the frontend auto-applies the theme.

3. The entire UI — banner, nav highlights, buttons, dark mode — will adapt automatically. No frontend code changes needed.

---

## Mobile Navigation Branding

In `v3.13.0`, mobile navigation received branding enhancements:

- **`MobileBrandedBottomNav.vue`**: Uses the school's primary color (`--color-primary`) as the active indicator and background tint for navigation icons, creating a brand-native feel.
- **`MobileGlassIconNav.vue`**: A premium glassmorphism option that respects the school's primary color for focus and active states while maintaining a modern translucent aesthetic.
- **Preference Storage**: User choices for navigation style are persisted locally via `userPreferences.js`.

---

## Dark Mode Behavior

- Toggled via the moon icon in `TopBar.vue` → calls `toggleDarkMode()`.
- Background becomes the primary color **darkened by 96%** (e.g. `#AAFF00` → `#070a00`).
- Card surfaces (`--color-surface`) stay white.
- Body text (`--color-text-primary`) switches to white.
- The `isDarkMode` ref is exported from `config/theme.js` for any component to read.

---

## Auto-Contrast (YIQ)

The `getContrastYIQ()` function in `theme.js` checks if the school's primary color is light or dark:

- **Light background** (e.g. lime green) → uses **black** text (`#0A0A0A`).
- **Dark background** (e.g. deep blue) → uses **white** text (`#FFFFFF`).

This drives:
- `--color-banner-text` — text on the university banner.
- `activeAuraLogo` — auto-selects `aura_logo_black.png` or `aura_logo_white.png`.

No manual configuration needed. Just set the primary color and contrast handles itself.

---

## Document Branding

The `documentBranding.js` service provides dynamic branding utilities for generated documents (e.g., reports, certificates). It uses the current school theme to apply consistent branding across exported materials.
