# Frontend Deployment Notes

[<- Back to frontend index](./README.md)

## Docker Image

- Dev/default compose build: `Frontend/Dockerfile`
- Production build (if used): `Frontend/Dockerfile.prod`

## Web Server

The container serves the SPA via NGINX using `Frontend/nginx.conf.template`.

Health endpoint:

- `GET /healthz`

Reverse proxy prefixes:

- `/__backend__/`
- `/__assistant__/`

