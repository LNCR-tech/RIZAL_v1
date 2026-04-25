# Frontend Deployment Notes

<!--nav-->
[← Frontend Architecture](architecture.md) | [🏠 Home](/README.md) | [Assistant Docs →](../assistant/README.md)

---
<!--/nav-->

## Docker Image

- Dev/default compose build: `frontend/Dockerfile`
- Production build (if used): `frontend/Dockerfile.prod`

## Web Server

The container serves the SPA via NGINX using `frontend/nginx.conf.template`.

Health endpoint:

- `GET /healthz`

Reverse proxy prefixes:

- `/__backend__/`
- `/__assistant__/`

