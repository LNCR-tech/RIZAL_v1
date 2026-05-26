# Aura (RIZAL) — Flutter Design System (MASTER)

Source of truth for the Flutter app UI. Synthesizes **ui-ux-pro-max** (style, color, typography, UX, Flutter stack) + **emil-design-eng** (motion/polish) + the existing web brand tokens (`frontend-web/src/config/theme.js`). Implementation lives in `lib/core/theme/`.

> Rule of thumb: brand-consistent but **elevated**. Fresh, premium, calm. Lime is a *scalpel*, not a *highlighter* — used for one primary action/indicator per view, never as a fill for large areas.

---

## 1. Brand foundation
- **Identity:** near-black ink + a single electric **lime** accent, generous negative space, soft bento cards, glass nav.
- **Style lineage (ui-ux-pro-max):** *Dark Mode (OLED)* + *Bento Box Grid*. Performance ⚡, accessibility target **WCAG AA (4.5:1)**, AAA where cheap.
- **Modes:** Light (default) and Dark (OLED-leaning). Plus **school-customizable primary** (multi-tenant) that overrides the accent at runtime.

## 2. Color system
Brand + system tokens. Hex are seeds; the runtime computes contrast text via a ported `getContrastYIQ` (see `frontend-web/src/config/theme.js`).

| Token | Light | Dark | Use |
|---|---|---|---|
| `accent` | `#AAFF00` | `#AAFF00` | primary action, active nav, focus accent (sparing) |
| `accentDark` | `#88CC00` | `#9BE600` | pressed/hover of accent, AI surface |
| `onAccent` | `#0A0A0A` | `#0A0A0A` | text/icon on accent |
| `ink` (text-primary) | `#0A0A0A` | `#F4F7EC` | primary text |
| `bg` | `#ECEEE7` | `#070A00` | app background (dark = lime darkened ~96%) |
| `surface` | `#FFFFFF` | `#12150D` | cards / sheets |
| `surfaceAlt` | `#F4F6EF` | `#1A1E12` | nested/inset surfaces, fields |
| `textSecondary` | `#555B50` | `#A6AE9B` | secondary text |
| `textMuted` | `#8A9182` | `#6E7567` | hints, captions |
| `border` | `#E2E5DB` | `#272C1D` | hairlines |
| `navInk` | `#0A0A0A` | `#0A0A0A` | glass bottom-nav base |

**Status (fixed, not branded):** present/compliant `#22C55E` · late `#FB923C` · at-risk `#F59E0B` · absent/non-compliant `#EF4444` · excused `#F97316`. **Governance:** SSG `#6366F1` · SG `#8B5CF6`.

Rules: glass cards in light mode use opacity ≥ 0.8; borders must be visible in both modes; color is never the *only* signal (pair with icon/label).

## 3. Typography
- **Primary:** **Manrope** (300–800) — geometric-modern, on-brand. Loaded via `google_fonts`.
- **Numeric/Mono:** **JetBrains Mono** for tabular data, IDs, timestamps, attendance counts, codes (the "data/precise" cue). Use `fontFeatures: [tabular figures]`.
- **Scale (size/line-height/weight):**

| Role | Size | LH | Weight |
|---|---|---|---|
| display | 32 | 40 | 800 |
| title | 24 | 30 | 700 |
| headline | 20 | 26 | 700 |
| bodyL | 17 | 26 | 500 |
| body | 15 | 22 | 400/500 |
| label | 13 | 16 | 600 |
| caption | 12 | 16 | 500 |

Body never below **15** for dense lists, **16** for primary reading. Line length ≤ ~70 chars.

## 4. Spacing · radii · elevation
- **Spacing scale (dp):** 2, 4, 8, 12, 16, 20, 24, 32, 40, 56.
- **Radii:** field/control `12` · chip/pill `999` · card `24` · sheet `28` · hero `32`.
- **Elevation (soft, never harsh):** card `0 14 32 rgba(0,0,0,.10)` (light) / subtle stroke (dark); raised/pressed reduces blur. Glass nav: blur 18, base `navInk` @ 0.72, top inner light highlight, hairline border `white@0.16`.
- **Bento:** asymmetric tiles (1x1, 2x1, 2x2), gap 16, content fits tile.

## 5. Motion (emil-design-eng)
- **Curves (Cubic):** `easeOutCubic (0.23,1,0.32,1)` for enter/most UI · `easeInOutQuint (0.77,0,0.175,1)` for on-screen move/morph · `drawer (0.32,0.72,0,1)` for sheets · `linear` only for progress/marquee. **Never ease-in for UI.**
- **Durations:** press 120ms · chips/popover 180 · dropdown/tab 220 · modal 260 · sheet/drawer 360. **All UI < 300ms** except sheets.
- **Patterns:**
  - Pressables: `AnimatedScale` to **0.97** on tap-down (120ms ease-out). Add `HapticFeedback.selectionClick()` on primary taps; `mediumImpact` on attendance success.
  - **Never enter from scale 0** — start `0.96 + opacity 0`.
  - **Stagger** list/dashboard entrance **50ms** apart (cap total; never block input).
  - **Asymmetric** enter/exit: exit faster (≈160ms) than enter.
  - Sheets/drag use spring (`bounce ≤ 0.15`); momentum dismissal.
  - **Respect reduced motion:** `MediaQuery.disableAnimations` / `accessibleNavigation` → keep opacity, drop translate/scale.
  - Use `Hero` for card→detail shared-element transitions; **always `dispose()` AnimationControllers**.

## 6. Core components (lib/core/widgets)
- **AuraButton** — filled (accent), tonal, ghost, destructive; 48dp min height; scale-on-press; loading state disables + shows spinner.
- **AuraCard** — bento surface, radius 24, soft shadow, optional press scale + Hero tag.
- **AuraPill / StatusChip** — rounded-full; StatusChip maps status→color+icon (never color alone).
- **AuraTextField** — labeled, 48dp+, clear error text below, focus ring in accent.
- **GlassBottomNav** — frosted, per-role items, active item lime dot/indicator, 48dp targets, 8dp gaps, haptic on switch.
- **StatRing** — fl_chart radial for attendance %, animated sweep (easeOutCubic), mono center label.
- **AppScaffold** — safe areas, scroll-under glass, pull-to-refresh only where meaningful.
- **SectionHeader**, **StaggeredList**, **AuraSkeleton** (shimmer loading), **AuraSheet** (spring bottom sheet), **EmptyState**.
- **Charts:** line/area (trends), bar (comparison), radar (multi-metric), streaming-area (live monitor) — all fl_chart, accent-driven, with accessible labels + data fallback.
- Icons: **Lucide** only (no emoji).

## 7. UX guardrails (ui-ux-pro-max critical rules)
- Touch targets ≥ **48dp**; ≥ **8dp** between adjacent targets.
- Tap (not hover) drives actions; provide pressed/disabled/loading states for every interactive element.
- Loading: **skeletons** for content, spinners for buttons; reserve space to avoid layout jump.
- Errors: clear message near the cause; map FastAPI `{detail}`/422 to friendly copy.
- Haptics for confirmations/important actions; never on every tap.
- Accessibility: semantic labels on icon-only buttons; visible focus; contrast ≥ 4.5:1; color never the only indicator; honor reduced motion + text scaling.

## 8. Flutter implementation notes
- Theme via **`ThemeData`** + a `ThemeExtension<AuraTokens>` (no hardcoded `Color(0x..)` in widgets — read `Theme.of(context).extension<AuraTokens>()`).
- `theme_controller` (Riverpod): toggles dark mode (persisted) and applies **school branding** (primary/secondary/accent + logo) from the decoded token / `/school-settings`.
- Keep widget trees shallow (extract widgets); `const` everywhere possible; `ValueKey` on dynamic list items; `dispose()` controllers.
- Honor `MediaQuery.textScaler`; test at 375 / 768 / 1024 logical widths and large text.

## 9. Per-view checklist (Definition of Polished)
- [ ] Lime used sparingly (≤ 1 primary emphasis per view); status colors correct + iconed.
- [ ] All pressables: 48dp, scale-on-press, loading/disabled states, haptics where apt.
- [ ] Entrance staggered (50ms), never from scale 0; exits faster than enters.
- [ ] Skeletons for async; no blank/frozen states; no layout jump.
- [ ] Light + dark both verified; borders/glass visible in both.
- [ ] Reduced-motion + large-text variants sane; contrast AA; icon-only buttons labeled.
