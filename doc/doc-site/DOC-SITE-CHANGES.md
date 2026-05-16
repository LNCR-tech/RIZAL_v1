# Doc-Site Changes

Implemented on May 15, 2026.

## What changed

- Reworked the doc-site frontend into a cleaner documentation layout inspired by Resend docs.
- Added a compact docs home page focused on role-based paths.
- Added `docs/updates/latest-implementation.md` for the before/current implementation explanation.
- Fixed RBAC helpers so technical docs support `admin`, `campus_admin`, `school_it`, and authorized technical emails.
- Moved the signed-in user control into the navbar so it does not overlap content.
- Updated sidebars so missing pages such as troubleshooting, notifications, WebSockets, and AI assistant docs are reachable.
- Added a protected Docusaurus/RBAC architecture guide under technical frontend docs.

## How to test

```bash
cd doc/doc-site
npm run build
npm start
```

Open `http://localhost:3000`.

Expected RBAC results:

- student or unlisted email: user docs only
- `ssg`, `sg`, or `org`: user and event docs only
- `admin`, `campus_admin`, `school_it`, or listed email: user and technical docs

Full details are in `docs/updates/latest-implementation.md`.

The full Docusaurus architecture guide is in `docs/technical/frontend/docusaurus-rbac-architecture.md`.
