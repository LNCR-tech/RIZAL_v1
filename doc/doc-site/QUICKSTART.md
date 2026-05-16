# Quick Start Guide

This guide explains how to run the Aura Docusaurus documentation site locally.

## Run locally

```bash
cd doc/doc-site
npm install
npm start
```

Open `http://localhost:3000`.

## Local environment

Copy the example environment file if needed:

```bash
cp .env.example .env
```

Useful local values:

```env
DOCUSAURUS_AUTH_ENABLED=false
DOCUSAURUS_DEFAULT_ROLE=admin
DOCUSAURUS_AUTHORIZED_EMAILS=admin@aura.school,dev@aura.school,it@aura.school
```

When `DOCUSAURUS_AUTH_ENABLED=false`, the doc-site creates a local preview user using `DOCUSAURUS_DEFAULT_ROLE`.

## Access levels

| Role | Access |
| --- | --- |
| `student` | User guides, FAQ, mobile guide, troubleshooting |
| `ssg`, `sg`, `org` | User guides plus event-management documentation |
| `admin`, `campus_admin`, `school_it` | User guides plus technical documentation |
| Authorized email | Technical documentation access |

## Project structure

```text
doc/doc-site/
  docs/
    index.md
    updates/
    user/
    technical/
  src/
    components/
    config/
    context/
    css/
    theme/
  static/
  docusaurus.config.js
  sidebars.js
  package.json
```

## Common commands

```bash
npm start
npm run build
npm run serve
npm run clear
```

## Verification

After running `npm run build`, confirm:

- the build completes successfully
- the home page opens
- user docs are available to all signed-in users
- technical docs are visible only to admin, campus admin, school IT, or authorized email users
- direct `/technical/...` access shows an access-denied page when the user lacks permission
