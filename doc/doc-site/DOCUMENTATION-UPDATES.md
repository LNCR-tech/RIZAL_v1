# Documentation Updates

Updated on May 15, 2026.

## Latest doc-site implementation

The doc-site was updated to make the frontend easier to read and to make the existing RBAC behavior clearer.

## What changed

| Area | Update |
| --- | --- |
| UI style | Reworked the theme into a cleaner documentation layout inspired by Resend docs. |
| Navigation | Added missing pages to sidebars: troubleshooting, notifications, WebSockets, AI assistant, and latest implementation notes. |
| Home page | Replaced the long landing-style page with a shorter role-based docs entry page. |
| RBAC | Technical docs now allow `admin`, `campus_admin`, `school_it`, or emails listed in `DOCUSAURUS_AUTHORIZED_EMAILS`. |
| Navbar | Moved the account/status control into the navbar so it does not overlap links or content. |
| Change log | Added `docs/updates/latest-implementation.md` and `DOC-SITE-CHANGES.md`. |

## How to test

```bash
cd doc/doc-site
npm run build
npm start
```

Open `http://localhost:3000`.

Expected results:

- unlisted email: user docs only
- listed email: user docs and technical docs
- direct `/technical/...` access without permission: access denied
- `DOCUSAURUS_AUTH_ENABLED=false` with `DOCUSAURUS_DEFAULT_ROLE=admin`: local admin preview

## More detail

Read `docs/updates/latest-implementation.md` for the beginner-friendly before/current comparison.
