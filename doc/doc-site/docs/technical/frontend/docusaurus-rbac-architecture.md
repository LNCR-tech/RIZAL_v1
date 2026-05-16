---
title: Docusaurus RBAC Architecture
sidebar_label: Docusaurus RBAC architecture
description: Architecture guide for wiring Aura documentation entry points, role-based docs, auth gates, search, and deployment in Docusaurus v3.
---

# Docusaurus RBAC Architecture

This guide explains how Aura should structure a professional Docusaurus v3 documentation site with role-based access control. It is written for the current Aura doc-site implementation and can be reused as a planning guide for future documentation work.

## Current recommendation

Use one Docusaurus v3 instance for Aura docs, deployed either as `docs.aura.school` or behind a `/docs` path, with frontend RBAC for navigation and page-level gating.

For Aura's current state, the best fit is:

| Decision | Recommendation |
| --- | --- |
| Docs framework | Docusaurus v3 |
| Docs location | Keep in the existing doc-site workspace unless deployment needs require a separate repo |
| Entry point | Add a `Docs` link in the main app header |
| Preferred URL | `docs.aura.school` for clean separation, or `/docs` if one domain is required |
| Auth model | Use app-issued JWT/session when available; keep local email-role fallback for doc previews |
| Role model | `student`, `ssg`, `sg`, `org`, `admin`, `campus_admin`, `school_it` |
| Technical docs | Protected by role or authorized email |
| Search | Use role-aware indexing or role-filtered Algolia queries before exposing restricted content |

The current doc-site already implements the key shape: Docusaurus v3, React wrappers, email/role-based technical access, body classes for RBAC state, grouped sidebars, and page gates for `/technical/...`.

## Docs entry point

### How the Docs button is wired

The main application normally treats docs as a separate route target:

```jsx
// Main app navbar example
<a href="https://docs.aura.school">Docs</a>
```

If docs are hosted under the same domain path:

```jsx
// Same-domain path example
<a href="/docs">Docs</a>
```

If the main app is React Router based:

```jsx
// External docs should still use a normal anchor
<a href={import.meta.env.VITE_DOCS_URL}>Docs</a>
```

Use a normal anchor for external docs because the docs app is usually a separate deployment. Use router links only when the docs are inside the same React application.

### Common deployment patterns

| Pattern | Example | Best when | Tradeoff |
| --- | --- | --- | --- |
| Subdomain | `docs.aura.school` | Docs should deploy independently from the main app. | Requires DNS and auth cookie planning across subdomains. |
| Path | `aura.school/docs` | One domain is required for branding or cookie scope. | Reverse proxy/baseUrl setup is more sensitive. |
| Separate deployment | Vercel docs project, Netlify docs site, or VPS container | Docs releases should not block app releases. | Needs shared environment variables and deployment coordination. |
| Monorepo package | `apps/web`, `apps/docs`, `packages/ui` | Web and docs share design tokens/components. | Build pipelines must avoid unnecessary rebuilds. |
| Standalone docs repo | `aura-docs` repo | Docs are managed by a separate team. | Harder to keep code examples synced with app code. |

For Aura, a monorepo-style docs workspace is practical because the docs need to reference backend, frontend, mobile, and assistant behavior. A subdomain deployment keeps it operationally clean.

### Docs home page content

A professional docs home page should not be a marketing landing page. It should help the user choose the right path quickly.

Recommended content:

| Section | Purpose |
| --- | --- |
| Short product context | One paragraph explaining what Aura does. |
| Search entry | Primary way to find docs when search is enabled. |
| Role-based cards | Student, event manager, admin, school IT, developer. |
| Popular workflows | Check in, create event, manage users, deploy, use API. |
| Latest changes | Link to the current implementation notes. |
| Support path | FAQ, troubleshooting, and escalation channel. |

The current Aura home page follows this direction: it provides role paths, current system facts, and a link to the latest implementation page.

### World-class docs layout components

| Component | Why it matters |
| --- | --- |
| Top nav | Global entry points: Guides, Latest Changes, Technical Docs, repository, theme toggle, account status. |
| Left sidebar | Main information architecture with grouped docs. |
| Content area | Focused article width, strong typography, code blocks, tables, admonitions. |
| Right TOC | Shows headings inside the current page. |
| Breadcrumbs | Shows location and helps users recover context. |
| Prev/next links | Supports sequential reading. |
| Search | Finds docs faster than manual navigation. |
| Feedback widget | Captures "Was this helpful?" and stale content reports. |
| Version selector | Useful when APIs or mobile builds have multiple supported versions. |
| Auth/account badge | Makes the current docs access level visible. |

## RBAC docs architecture

### Role tiers

A general RBAC docs system usually has these tiers:

| Tier | Typical role names | Access |
| --- | --- | --- |
| Public | Guest, anonymous | Marketing docs, public setup, FAQ. |
| End user | User, student, member | Product usage guides and own-account workflows. |
| Operator | Manager, event manager, moderator | Operational workflows and team-level actions. |
| Developer | Developer, API user, integration owner | API reference, webhooks, SDKs, auth, examples. |
| Admin | Admin, campus admin, school IT | Configuration, user management, security, deployment. |
| Super admin | Platform admin, owner | Cross-tenant controls, billing, global settings, incident procedures. |

Aura's current roles map like this:

| Aura role | Tier | Content |
| --- | --- | --- |
| `student` | End user | Getting started, attendance, profile, mobile guide, FAQ, troubleshooting. |
| `ssg`, `sg`, `org` | Operator | User guides plus event management and attendance monitoring. |
| `campus_admin` | Admin | User guides, event operations, reports, technical docs. |
| `school_it` | Admin/technical | Technical docs, deployment, auth, troubleshooting. |
| `admin` | Super admin | All docs, platform configuration, technical operations. |

### Content map

Use this map when adding or reorganizing docs:

```text
Public / Guest
  - What is Aura?
  - Support and FAQ
  - Login and account recovery

Student
  - Getting started
  - Face scan check-in
  - Geolocation requirements
  - Attendance history
  - Mobile app
  - Notifications
  - Troubleshooting

Event manager: SSG, SG, ORG
  - Create and publish events
  - Configure event time and geofence
  - Monitor check-ins
  - Manual attendance fallback
  - Notify participants
  - Export attendance reports

Campus admin / School IT
  - Manage users and roles
  - School, department, program, and section setup
  - Security and audit logs
  - Deployment and environment variables
  - Backend services and database
  - API and WebSockets

Platform admin
  - Cross-school management
  - Global security policy
  - Incident response
  - Production release process
```

## Role-based sidebar filtering

Docusaurus sidebars are static at build time, so role-aware sidebars require one of these approaches:

1. Build all sidebar items, then hide restricted links in React/CSS.
2. Split sidebar definitions by role and render a custom sidebar wrapper.
3. Use separate Docusaurus instances or builds per audience.

Aura currently uses approach 1: the Technical Docs nav item has a `dev-only` class and CSS reveals it only when the auth wrapper adds `can-access-technical-docs` to the body.

### Current config pattern

```js title="docusaurus.config.js"
navbar: {
  items: [
    {
      type: 'docSidebar',
      sidebarId: 'userSidebar',
      position: 'left',
      label: 'Guides',
    },
    {
      type: 'docSidebar',
      sidebarId: 'technicalSidebar',
      position: 'left',
      label: 'Technical Docs',
      className: 'dev-only',
    },
  ],
}
```

```css title="src/css/custom.css"
.dev-only {
  display: none !important;
}

body.can-access-technical-docs .dev-only {
  display: inline-flex !important;
}
```

### Stronger custom sidebar pattern

Use this when you need to hide individual sidebar items, not only top-level nav links.

```js title="src/config/docsAccess.js"
export const docAccess = {
  '/user/': ['student', 'ssg', 'sg', 'org', 'admin', 'campus-admin', 'school-it'],
  '/technical/': ['admin', 'campus-admin', 'school-it'],
};

export function canSeeDocPath(role, path) {
  const normalizedRole = role?.replaceAll('_', '-');
  const match = Object.entries(docAccess)
    .filter(([prefix]) => path.startsWith(prefix))
    .sort(([a], [b]) => b.length - a.length)[0];

  if (!match) return true;
  return match[1].includes(normalizedRole);
}
```

```jsx title="src/theme/DocSidebar/Desktop/index.js"
import React from 'react';
import DocSidebarDesktop from '@theme-original/DocSidebar/Desktop';
import { useAuth } from '@site/src/context/AuthContext';
import { canSeeDocPath } from '@site/src/config/docsAccess';

function filterItems(items, role) {
  return items
    .map((item) => {
      if (item.type === 'link' && item.href && !canSeeDocPath(role, item.href)) {
        return null;
      }

      if (item.items) {
        return {
          ...item,
          items: filterItems(item.items, role),
        };
      }

      return item;
    })
    .filter(Boolean);
}

export default function DocSidebarDesktopWrapper(props) {
  const { role } = useAuth();
  return <DocSidebarDesktop {...props} sidebar={filterItems(props.sidebar, role)} />;
}
```

The exact prop shape can change between Docusaurus theme versions. Test this wrapper after every Docusaurus upgrade.

## Page and section gates

### Page-level gate

Aura currently wraps `DocPage` and blocks `/technical/...` routes when the user lacks technical access.

```jsx title="src/theme/DocPage/index.js"
import React from 'react';
import DocPage from '@theme-original/DocPage';
import { useLocation } from '@docusaurus/router';
import { useAuth } from '../../context/AuthContext';
import { useAuthorizedEmails, canAccessTechnicalDocs } from '../../config/emailAuth';
import AccessDenied from '../../components/AccessDenied/AccessDenied';
import EmailLogin from '../../components/EmailLogin/EmailLogin';

export default function DocPageWrapper(props) {
  const location = useLocation();
  const { user, role, loading } = useAuth();
  const authorizedEmails = useAuthorizedEmails();

  if (loading) return <DocPage {...props} />;
  if (!user) return <EmailLogin />;

  if (
    location.pathname.startsWith('/technical') &&
    !canAccessTechnicalDocs(user, role, authorizedEmails)
  ) {
    return <AccessDenied />;
  }

  return <DocPage {...props} />;
}
```

### Frontmatter access metadata

For more precise control, add role metadata to MDX frontmatter:

```mdx title="docs/technical/api/authentication.md"
---
title: Authentication
requiredRoles:
  - admin
  - campus-admin
  - school-it
---
```

Then read metadata in a custom doc item wrapper:

```jsx title="src/theme/DocItem/index.js"
import React from 'react';
import DocItem from '@theme-original/DocItem';
import { useDoc } from '@docusaurus/plugin-content-docs/client';
import { useAuth } from '@site/src/context/AuthContext';
import AccessDenied from '@site/src/components/AccessDenied/AccessDenied';

export default function DocItemWrapper(props) {
  const { metadata } = useDoc();
  const { role } = useAuth();
  const requiredRoles = metadata.frontMatter.requiredRoles || [];

  if (requiredRoles.length && !requiredRoles.includes(role)) {
    return <AccessDenied />;
  }

  return <DocItem {...props} />;
}
```

### Section-level gate

Use a small MDX component when one page has mixed public and restricted sections.

```jsx title="src/components/RoleGate/RoleGate.jsx"
import React from 'react';
import { useAuth } from '@site/src/context/AuthContext';
import { normalizeRole } from '@site/src/config/roles';

export default function RoleGate({ roles, children, fallback = null }) {
  const { role } = useAuth();
  const normalized = normalizeRole(role);

  if (!roles.map(normalizeRole).includes(normalized)) {
    return fallback;
  }

  return <>{children}</>;
}
```

```mdx title="Example MDX usage"
import RoleGate from '@site/src/components/RoleGate/RoleGate';

<RoleGate roles={['admin', 'campus-admin', 'school-it']}>
  This section contains deployment credentials and internal runbook links.
</RoleGate>
```

Avoid putting secrets in gated MDX. Frontend gates protect user experience, not source code or static build artifacts.

## Auth integration

Docusaurus is a static React app after build, so authentication is usually implemented client-side or at the hosting/proxy layer.

### Integration options

| Auth method | How it works | Best for |
| --- | --- | --- |
| JWT from main app | User opens docs, docs reads/receives a token, validates session with backend. | Same company app and docs. |
| HttpOnly session cookie | Reverse proxy or backend checks cookie before serving restricted docs. | Stronger protection for private docs. |
| Auth0, Clerk, Cognito | Hosted identity provider protects docs route or supplies client token. | Teams that already use an IdP. |
| Static basic auth | Host-level password for the whole docs site. | Internal preview environments. |
| Email allowlist fallback | Email determines doc role in local/client state. | Local development or low-risk previews. |

### Recommended Aura flow

1. User clicks `Docs` in the main web app.
2. Main app sends the user to the docs URL.
3. Docs checks for an existing session/JWT.
4. Docs calls a backend endpoint such as `/auth/me` or `/docs/session`.
5. Backend returns the user email and roles.
6. Docusaurus `AuthProvider` stores the normalized role in React state.
7. Navbar, sidebar, search, and page gates use that role.

Example session fetch:

```js title="src/api/docsSession.js"
export async function loadDocsSession() {
  const response = await fetch('/api/docs/session', {
    credentials: 'include',
  });

  if (!response.ok) return null;
  return response.json();
}
```

Example provider behavior:

```jsx title="src/context/AuthContext.js"
useEffect(() => {
  async function load() {
    const session = await loadDocsSession();

    if (session) {
      setUser(session.user);
      setRole(normalizeRole(session.role));
    }

    setLoading(false);
  }

  load();
}, []);
```

## Folder structure

Recommended structure for Aura:

```text
doc/doc-site/
  docs/
    index.md
    updates/
      latest-implementation.md
    user/
      getting-started.md
      mobile-guide.md
      troubleshooting.md
      faq.md
      user-manual/
        overview.md
        attendance.md
        events.md
        notifications.md
        profile.md
    technical/
      api/
        overview.md
        authentication.md
        endpoints.md
        websockets.md
      backend/
        architecture.md
        database.md
        services.md
      frontend/
        architecture.md
        components.md
        state-management.md
        docusaurus-rbac-architecture.md
      assistant/
        overview.md
        mcp-integration.md
      deployment/
        docker.md
        production.md
  src/
    components/
      AccessDenied/
      Auth/
      EmailLogin/
      RoleGate/
    config/
      roles.js
      emailAuth.js
    context/
      AuthContext.js
    theme/
      DocPage/
      Navbar/
      Root/
    css/
      custom.css
  docusaurus.config.js
  sidebars.js
```

## Single instance vs multiple instances

| Option | Advantages | Disadvantages | Aura recommendation |
| --- | --- | --- | --- |
| Single Docusaurus instance | One search UI, one theme, one build, one content tree, easier internal linking. | Restricted content still exists in static build output unless protected at host/proxy level. | Best current choice for Aura. |
| Multiple instances by role | Strong isolation, separate deployments, separate search indexes. | More maintenance, duplicated theme/config, harder cross-linking. | Use only if technical docs must be fully private. |
| Single repo, multiple builds | Shared source but separate public/internal outputs. | Build scripts and sidebars become more complex. | Good future upgrade if RBAC grows. |
| Managed docs platform | Fast authoring and collaboration. | Less control over custom RBAC and app integration. | Consider only if engineering ownership is not desired. |

Important: Docusaurus frontend gating is not enough for highly confidential docs. If content must be private, block it before static files are served or build a separate private docs output.

## RBAC search architecture

Docusaurus has first-class Algolia DocSearch support. RBAC adds a security requirement: users must not discover restricted pages through search results.

### Search options

| Option | How it works | Security level |
| --- | --- | --- |
| Public-only index | Index only public/user docs. Keep technical docs out of public search. | Strong and simple. |
| Separate indexes | `aura_public_docs`, `aura_technical_docs`, selected by role. | Strong if keys are controlled correctly. |
| Facet filters | Add role metadata and apply Algolia `facetFilters` by role. | Good, but requires careful crawler/index config. |
| Secured API keys | Backend generates Algolia keys with enforced filters. | Strongest for role-filtered search. |
| Local search | Build-time local index. | Not recommended for restricted content unless using separate builds. |

### Recommended Aura search path

Phase 1:

- Enable search only for user docs and public pages.
- Do not index `/technical/` until role filtering is ready.

Phase 2:

- Add `docRole` or `visibility` metadata to docs.
- Configure the crawler to capture that metadata.
- Use role-aware Algolia filters.

Example frontmatter:

```mdx
---
title: API Authentication
visibility: technical
allowedRoles:
  - admin
  - campus-admin
  - school-it
---
```

Example Docusaurus Algolia config:

```js title="docusaurus.config.js"
themeConfig: {
  algolia: {
    appId: process.env.DOCUSAURUS_ALGOLIA_APP_ID,
    apiKey: process.env.DOCUSAURUS_ALGOLIA_SEARCH_KEY,
    indexName: 'aura_docs',
    contextualSearch: true,
    searchParameters: {
      facetFilters: ['visibility:public'],
    },
  },
}
```

For authenticated technical users, prefer generating secured search parameters from the backend instead of trusting client-only role state.

## Why Docusaurus

### Comparison table

| Tool | Setup complexity | RBAC/auth support | MDX/React support | Versioning | Search | Performance | Ecosystem | Best fit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Docusaurus v3 | Low to medium | Custom React wrappers, swizzling, proxy auth | Excellent React + MDX fit | Built in for docs | First-class Algolia support | Fast static pages with SPA navigation | Mature docs ecosystem | Full stack teams needing React, MDX, versioning, and custom RBAC. |
| VitePress | Low | Custom Vue/auth work | Vue-first, not React-first | Supported but simpler | Local/Algolia options | Very fast | Strong Vue ecosystem | Vue teams that want simple docs. |
| MkDocs + Material | Low | Usually proxy/host auth, Python plugins | Markdown-first, not React/MDX | Supported through plugins | Strong built-in/plugin search | Very fast static output | Mature Python/docs ecosystem | Python-heavy teams and internal handbooks. |
| Next.js custom docs | High | Excellent because it is a full app framework | Excellent React/MDX with custom setup | Must build or adopt a docs layer | Fully custom | Excellent when tuned | Huge React ecosystem | Teams needing app-grade auth and custom UI over docs convenience. |
| GitBook / Mintlify | Very low | Managed platform controls; custom app RBAC varies by plan/platform | Limited compared with owning a React app | Managed | Managed | Managed | Strong authoring experience | Teams that value speed and editing workflow over source-level control. |
| Starlight | Low | Custom Astro/server/proxy auth | Astro MDX, React islands possible | Supported through content patterns/plugins | Built-in/pagefind options | Excellent static performance | Growing Astro ecosystem | Content-heavy docs where Astro is already used. |

### Recommendation matrix

| Need | Best choice | Reason |
| --- | --- | --- |
| React + MDX components | Docusaurus or Next.js | Docusaurus gives docs defaults; Next.js gives full app control. |
| Fastest setup with professional docs UX | Docusaurus | Sidebar, docs routes, TOC, versioning, i18n, and Algolia are already designed for docs. |
| Strongest private-doc security | Next.js or separate private Docusaurus build behind auth | Server-side enforcement is easier. |
| Best for Aura now | Docusaurus | It matches the current React/MDX doc-site and needs less custom infrastructure. |
| Best if the team moves to Vue | VitePress | Vue-native docs framework. |
| Best if docs are mostly Python/backend handbook | MkDocs Material | Markdown-first and simple. |
| Best if non-developers own docs | GitBook or Mintlify | Managed editing and publishing workflow. |

Docusaurus is the best fit for Aura because the site already uses React, MDX, Docusaurus sidebars, swizzled theme wrappers, and frontend RBAC components. It gives a strong documentation foundation without forcing the team to build navigation, TOC, versioning, or code block behavior from scratch.

## Implementation roadmap

### Phase 1: Docusaurus setup and folder structure

Deliverables:

- Keep `doc/doc-site` as the docs workspace.
- Maintain `docs/user`, `docs/technical`, and `docs/updates`.
- Confirm `routeBasePath: '/'` for subdomain deployment or change to `/docs` for path deployment.
- Keep `.gitignore` excluding `node_modules`, `build`, `.docusaurus`, and local env files.

Validation:

```bash
cd doc/doc-site
npm run build
```

### Phase 2: Role-based sidebar config

Deliverables:

- Keep separate `userSidebar` and `technicalSidebar`.
- Keep `Technical Docs` navbar item marked with `className: 'dev-only'`.
- Use auth-derived body classes to reveal technical nav only for technical users.
- If item-level hiding becomes necessary, swizzle `DocSidebar` and filter by role.

Validation:

- Student/unlisted email cannot see Technical Docs nav.
- Admin/listed email can see Technical Docs nav.

### Phase 3: Auth integration and page gating

Deliverables:

- Replace email-only demo auth with the real Aura session endpoint when backend support is ready.
- Keep role normalization in one file.
- Keep page-level gate for `/technical/...`.
- Add frontmatter-based `requiredRoles` only when individual page rules differ from the route prefix.

Validation:

- Direct `/technical/api/overview` is blocked for users without access.
- Refreshing a protected page keeps the correct auth state.
- Logout clears local role and token state.

### Phase 4: Search with RBAC

Deliverables:

- Start with public/user docs search only.
- Add `visibility` metadata before indexing technical docs.
- Configure Algolia facets for `visibility` and allowed roles.
- For stronger enforcement, issue secured Algolia keys from the backend.

Validation:

- Student search never returns technical docs.
- Technical users can search technical docs.
- Direct URL access remains protected even if a result URL is copied.

### Phase 5: Deployment strategy

Deliverables:

- Choose `docs.aura.school` for separate docs deployment, or `/docs` if the docs must share a domain.
- For Vercel/Netlify: set Docusaurus build command to `npm run build` and output to `build`.
- For VPS: serve static build through Nginx or the provided Docker/Nginx setup.
- Configure environment variables in the deployment platform.

Recommended production settings:

```env
DOCUSAURUS_AUTH_ENABLED=true
DOCUSAURUS_DEFAULT_ROLE=student
DOCUSAURUS_AUTHORIZED_EMAILS=admin@aura.school,dev@aura.school,it@aura.school
DOCUSAURUS_SITE_URL=https://docs.aura.school
```

## Docusaurus RBAC gotchas

- Static files are still generated for gated docs. Do not rely on client-only gates for secrets.
- Sidebars are build-time data. Dynamic role filtering requires custom theme wrappers.
- Search can leak titles and snippets if restricted pages are indexed without filters.
- `routeBasePath` must match deployment. `/` is good for a docs subdomain; `/docs` is needed for same-domain path deployment.
- Docusaurus swizzled components can break during upgrades if internal theme props change.
- Auth state must be SSR-safe because Docusaurus builds pages in Node and runs React in the browser.
- Do not hardcode one-off role checks across many files. Keep roles and access helpers centralized.
- Do not put production secrets in MDX, frontmatter, or static assets.
- After changing sidebar IDs or doc IDs, check old links and redirects.

## Prompt template for future doc-site work

Use this prompt when asking for future documentation improvements:

```text
Act as a Senior Full Stack Developer and Docusaurus Documentation Architect.
Work only inside doc/doc-site unless a main-app integration is explicitly required.
Keep the existing Aura roles and RBAC behavior:
student, ssg, sg, org, admin, campus_admin, school_it.

Goal:
[describe the doc-site feature or content change]

Requirements:
- Do not change backend or main frontend files unless required.
- Keep technical docs protected by role/email access.
- Update sidebars if new pages are added.
- Add beginner-readable implementation notes when behavior changes.
- Run npm run build from doc/doc-site before finishing.

Output:
- List changed docs/pages/components.
- Explain how to test RBAC and navigation.
```

## References

- [Docusaurus documentation](https://docusaurus.io/docs)
- [Docusaurus search documentation](https://docusaurus.io/docs/search)
- [VitePress documentation](https://vitepress.dev/guide/what-is-vitepress)
- [Material for MkDocs documentation](https://squidfunk.github.io/mkdocs-material/)
- [Next.js documentation](https://nextjs.org/docs)
- [GitBook documentation](https://gitbook.com/docs/)
- [Mintlify documentation](https://www.mintlify.com/docs)
- [Starlight documentation](https://starlight.astro.build/)
- [Algolia user-restricted access guide](https://www.algolia.com/doc/guides/security/api-keys/how-to/user-restricted-access-to-data)
