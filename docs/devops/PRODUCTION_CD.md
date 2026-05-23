# Production Continuous Deployment

This repository is a monorepo with `backend`, `frontend-web`, `frontend-apk`,
`assistant`, a root Docker Compose stack, and existing GitHub Actions workflows.
The production path keeps the current service ports: backend `8001`, frontend
`5173`, assistant `8500`, pgAdmin `5050` for dev only, and Mailpit `8025` only
when explicitly added for local testing.

## Existing Pipeline Analysis

- `.github/workflows/ci.yml` runs on `main`, `develop`, `feature/*`, and
  `integrate/pilot-merge`. It performs dependency audit, backend lint/tests,
  frontend lint/typecheck/unit tests, Playwright E2E, and Docker Compose build
  validation.
- `.github/workflows/production-cd.yml`, `staging-cd.yml`, and `hotfix-cd.yml`
  were disabled stubs. Production CD is now enabled only for `main`.
- The branch docs describe `main` as release-ready, an integration branch for
  active work, and `hotfix/*` for urgent fixes.
- The root `docker-compose.yml` has `dev` and `prod` profiles with Postgres,
  Redis, migrate/bootstrap jobs, backend, worker, beat, assistant, frontend,
  and dev-only pgAdmin/log-viewer. The production compose added here excludes
  pgAdmin, log-viewer, Mailpit, and `seeder/`.
- Runtime configuration comes from service `.env` files in development. The
  production stack centralizes server-side values in `.env.production`.

## Architecture

GitHub Actions runs tests and backend production image builds first. After
those gates pass, the workflow opens an SSH session to the Ubuntu VPS, runs
`deploy.sh`, pulls `main`, validates Compose, backs up Postgres, rebuilds the
backend image, runs migrations/bootstrap jobs, restarts `backend`, `worker`,
and `beat`, and verifies `http://18.142.190.113:8001/health`.

Docker Compose health checks gate service startup. Rollback is automatic when
deployment fails after the previous revision is captured. Because the backend is
directly published on host port `8001`, true blue-green cutover is not possible
without adding a load balancer or reverse proxy target switch; this setup
minimizes downtime and rolls back on failed health checks.

## Files

- `.github/workflows/production-cd.yml`: main-branch production CD with test,
  build, SSH deploy, and final public health verification.
- `docker-compose.prod.yml`: production Compose stack using the existing
  `rizal_v1` project and `db` database service, with internal Postgres and
  Redis, health checks, restart policies, log rotation, app services, and no
  dev-only exposed database/admin ports.
- `.env.production.example`: server-side example for required production
  variables. Copy it to `.env.production` on the VPS and never commit the real
  file.
- `deploy.sh`: idempotent VPS deployment script with locking, backup, build,
  migration, restart, health check, and automatic rollback.
- `rollback.sh`: revision rollback script for application containers.
- `deploy/nginx/aura.conf`: optional Nginx reverse proxy for HTTP/HTTPS.

## Required GitHub Secrets

- `SERVER_HOST`: `18.142.190.113` or the production DNS name.
- `SERVER_PORT`: SSH port for the production host, usually `22`.
- `SERVER_USER`: SSH user, usually `ubuntu`.
- `SERVER_SSH_KEY`: private key with access to the VPS deploy user.
- `SERVER_APP_DIR`: deployment directory, for example `/opt/aura`.

The deploy job validates the host, user, app directory, and SSH key before
opening the SSH session so missing secrets fail with an explicit message instead
of an ambiguous deploy error. `SERVER_PORT` defaults to `22` when omitted.

Do not store application secrets in GitHub Actions unless you also change the
workflow to render `.env.production` on the server. The recommended model is to
create `.env.production` once on the VPS with restricted permissions.

Existing VPS env files that use `DB_USER`, `DB_PASSWORD`, `DB_NAME`,
`ADMIN_EMAIL`, and `ADMIN_PASSWORD` remain supported. The deploy scripts derive
the current `POSTGRES_*`, `DATABASE_URL`, and bootstrap admin settings from
those legacy names when the current names are not present.

## VPS Setup

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg git ufw
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker ubuntu
```

Log out and back in after adding the user to the `docker` group.

```bash
sudo mkdir -p /opt/aura
sudo chown ubuntu:ubuntu /opt/aura
git clone -b main https://github.com/LNCR-tech/RIZAL_v1.git /opt/aura
cd /opt/aura
cp .env.production.example .env.production
chmod 600 .env.production
openssl rand -hex 32
```

Edit `.env.production` and replace all placeholders.

## SSH Key Setup

```bash
ssh-keygen -t ed25519 -C "github-actions-aura-production" -f aura-prod-deploy
ssh-copy-id -i aura-prod-deploy.pub ubuntu@18.142.190.113
```

Put the contents of `aura-prod-deploy` into `SERVER_SSH_KEY`. Keep the
public key in `/home/ubuntu/.ssh/authorized_keys` on the VPS.

## Firewall

Direct-port deployment:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 5173/tcp
sudo ufw allow 8001/tcp
sudo ufw allow 8500/tcp
sudo ufw enable
```

With Nginx and HTTPS, prefer exposing only `22`, `80`, and `443`, then remove
public access to `5173`, `8001`, and `8500` after the frontend and API are
validated through the proxy.

## Nginx and SSL

```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx
sudo cp /opt/aura/deploy/nginx/aura.conf /etc/nginx/sites-available/aura.conf
sudo ln -s /etc/nginx/sites-available/aura.conf /etc/nginx/sites-enabled/aura.conf
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d aura.example.com
```

After HTTPS is enabled, update `.env.production` URLs and CORS origins to the
domain, then redeploy.

## Operations

Manual backend-only deployment:

```bash
cd /opt/aura
DEPLOY_BRANCH=main DEPLOY_SCOPE=backend DB_SERVICE=db HEALTHCHECK_URL=http://18.142.190.113:8001/health ./deploy.sh
```

Full deployment, including frontend and assistant rebuild/restart, is available
only when intentionally requested:

```bash
cd /opt/aura
DEPLOY_BRANCH=main DEPLOY_SCOPE=full DB_SERVICE=db HEALTHCHECK_URL=http://18.142.190.113:8001/health ./deploy.sh
```

Manual rollback:

```bash
cd /opt/aura
./rollback.sh
```

Logs:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml ps
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f --tail=200 backend
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f --tail=200 frontend assistant worker beat
```

Backups are written to `/opt/aura/backups` before each deployment when Postgres
is already running. Copy those files to object storage or another host daily.

## Security Checklist

- Replace every placeholder in `.env.production`.
- Keep `.env.production` at mode `600`.
- Use a strong `SECRET_KEY`, database password, admin password, and AI key.
- Set `API_DOCS_ENABLED=false` for public production.
- Use `RATE_LIMIT_ENABLED=true` and `RATE_LIMIT_FAIL_OPEN=false`.
- Restrict SSH to trusted IPs where possible.
- Do not expose Postgres, Redis, pgAdmin, Mailpit, or Docker socket publicly.
- Enable HTTPS before real users enter credentials.
- Rotate the deploy SSH key and application credentials on staff changes.
- Monitor disk usage for Docker images, volumes, and backups.

## Troubleshooting

- `compose config` fails: check `.env.production` for missing values or invalid
  quotes.
- Database health fails before migrations: inspect
  `docker compose --env-file .env.production -f docker-compose.prod.yml logs db`
  and confirm `POSTGRES_USER`, `POSTGRES_PASSWORD`, and the existing data
  volume.
- Backend health fails: inspect `docker compose ... logs backend migrate
  bootstrap` and confirm `DATABASE_URL`, `SECRET_KEY`, CORS, and migrations.
- Frontend loads but API calls fail: confirm `BACKEND_ORIGIN=http://backend:8000`
  and `AURA_API_BASE_URL=/__backend__/`.
- SSH deploy fails: verify `VPS_HOST`, `VPS_USER`, `VPS_SSH_PRIVATE_KEY`, the
  server authorized key, and `known_hosts`.
- Rollback fails after migrations: restore the latest backup manually, then run
  `./rollback.sh <known-good-sha>`.
