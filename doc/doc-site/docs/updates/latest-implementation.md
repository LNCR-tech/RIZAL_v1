---
title: Latest Implementation
sidebar_label: Latest implementation
description: Beginner-friendly explanation of the latest Aura doc-site UI, navigation, and RBAC changes.
---

# Latest Implementation

This page explains the latest doc-site work implemented on May 15, 2026. It focuses on what changed, why it changed, and how to test it.

## Short version

The doc-site now behaves more like a focused developer documentation site:

- cleaner top navigation
- grouped sidebar sections
- readable article width
- right-side page outline
- smaller, calmer cards and tables
- RBAC that hides or blocks technical docs for users without access
- a new "Latest Changes" documentation page

## Before vs current

| Area | Before | Current |
| --- | --- | --- |
| Layout | The styling was more like a broad landing page with heavy gradients, large shadows, and many utility styles. | The styling is closer to a docs product: neutral colors, smaller spacing, cleaner cards, and readable article pages. |
| Navigation | Some docs existed but were not in the sidebar, including troubleshooting, notifications, WebSockets, and AI assistant pages. | The sidebar now includes the important user, support, API, assistant, frontend, backend, and deployment pages. |
| Auth status | The login/status control was fixed at the top-right and could overlap navbar content. | The auth status is inserted into the navbar right side, so it stays aligned with the navigation. |
| Technical docs link | The Technical Docs navbar item was hidden with direct DOM style changes. | The site now uses a body class from RBAC state, and CSS hides the link unless the user has technical access. |
| Technical page protection | Technical docs checked authorized emails only. Role-based access was incomplete. | Technical docs allow `admin`, `campus_admin`, `school_it`, or an email listed in `DOCUSAURUS_AUTHORIZED_EMAILS`. |
| Role names | Role handling did not fully normalize backend-style names such as `campus_admin` and `school_it`. | Role names are normalized to doc-site keys such as `campus-admin` and `school-it`. |
| Home page | The home page was long and had broken icon characters in some environments. | The home page is shorter, role-based, and uses plain text so beginners can scan it faster. |

## RBAC behavior

The doc-site has two layers of access control:

1. Navbar visibility: users without technical access do not see the Technical Docs link.
2. Page protection: if a user opens `/technical/...` directly, the page checks access again and shows an access-denied screen when needed.

Technical access is granted when either condition is true:

- the normalized role is `admin`, `campus-admin`, or `school-it`
- the signed-in email is listed in `DOCUSAURUS_AUTHORIZED_EMAILS`

Non-technical roles such as `student`, `ssg`, `sg`, and `org` can still use the public/user documentation.

## UI/UX changes

The updated UI follows the same general direction as Resend-style docs:

- neutral light and dark themes
- compact navbar
- simple grouped sidebar
- readable documentation content width
- subtle borders instead of heavy shadows
- cards with 8px radius or less
- code blocks and tables that are easier to scan
- no decorative gradient blobs or oversized marketing sections

This keeps the doc-site practical for repeated use by students, staff, and developers.

## Files changed

| File | Purpose |
| --- | --- |
| `src/css/custom.css` | Main visual redesign for navbar, sidebar, docs content, cards, tables, code blocks, auth states, and responsiveness. |
| `src/config/roles.js` | Central role list, role normalization, role labels, and technical access helpers. |
| `src/config/emailAuth.js` | Authorized email parsing and technical access check support. |
| `src/context/AuthContext.js` | Uses doc-site auth config and stores normalized roles. |
| `src/theme/Root/index.js` | Adds body classes for authenticated state, role, and technical access. |
| `src/theme/Navbar/index.js` | Places the auth status inside the navbar instead of floating over the page. |
| `src/theme/DocPage/index.js` | Protects technical docs using role and email access checks. |
| `src/components/EmailLogin/*` | Cleaner sign-in screen with clearer access explanation. |
| `src/components/Auth/LoginButton/*` | Compact navbar account control. |
| `src/components/AccessDenied/*` | Clear restricted-page message and recovery links. |
| `sidebars.js` | Adds missing docs to the visible navigation. |
| `docs/index.md` | Rewrites the docs home page into a shorter role-based starting point. |
| `docs/updates/latest-implementation.md` | Adds this beginner-friendly latest-change explanation. |
| `docs/technical/frontend/docusaurus-rbac-architecture.md` | Adds the detailed Docusaurus/RBAC planning guide for docs entry points, auth gates, search, deployment, and SSG comparisons. |

## How to test

Run the doc-site:

```bash
cd doc/doc-site
npm run build
npm start
```

Then open:

```text
http://localhost:3000
```

Test these cases:

| Test | Expected result |
| --- | --- |
| Sign in with an email not listed in `DOCUSAURUS_AUTHORIZED_EMAILS`. | User docs load. Technical Docs link is hidden. Direct `/technical/api/overview` shows access denied. |
| Sign in with an email listed in `DOCUSAURUS_AUTHORIZED_EMAILS`. | User docs and technical docs load. Technical Docs link is visible. |
| Set `DOCUSAURUS_AUTH_ENABLED=false` and `DOCUSAURUS_DEFAULT_ROLE=admin`. | Local development opens as an admin user without manual sign-in. |
| Set `DOCUSAURUS_DEFAULT_ROLE=student` while auth is disabled. | User docs load, but direct technical docs remain blocked. |

## Environment settings

```env
DOCUSAURUS_AUTH_ENABLED=true
DOCUSAURUS_DEFAULT_ROLE=student
DOCUSAURUS_AUTHORIZED_EMAILS=admin@aura.school,dev@aura.school,it@aura.school
```

Use `DOCUSAURUS_AUTH_ENABLED=false` only for local development or internal preview builds.

## What did not change

- No backend routes, schemas, migrations, or models were changed.
- No chat answers or preset question-to-answer mappings were added.
- The doc-site still uses Docusaurus.
- The technical documentation is still protected by the frontend doc-site guard.

## Architecture guide

For the detailed Docusaurus planning guide, open [Docusaurus RBAC Architecture](/technical/frontend/docusaurus-rbac-architecture). It covers docs entry points, sidebar filtering, page gates, auth integration, RBAC search, tool comparison, and a phased roadmap.
