# Aura Documentation Site

Role-based documentation portal built with Docusaurus.

## Quick start

```bash
npm install
npm start
```

Open `http://localhost:3000`.

## Access model

- `student`: user guides, FAQ, mobile guide, troubleshooting
- `ssg`, `sg`, `org`: user guides plus event-management documentation
- `admin`, `campus_admin`, `school_it`: user guides plus technical documentation
- emails in `DOCUSAURUS_AUTHORIZED_EMAILS`: technical documentation access

## Environment

```env
DOCUSAURUS_AUTH_ENABLED=true
DOCUSAURUS_DEFAULT_ROLE=student
DOCUSAURUS_AUTHORIZED_EMAILS=admin@aura.school,dev@aura.school,it@aura.school
```

Use `DOCUSAURUS_AUTH_ENABLED=false` only for local development.

## Development

- User docs: `docs/user/`
- Technical docs: `docs/technical/`
- Latest implementation notes: `docs/updates/latest-implementation.md`
- UI theme: `src/css/custom.css`
- RBAC helpers: `src/config/roles.js` and `src/config/emailAuth.js`

## Build

```bash
npm run build
npm run serve
```
