# Deploying to AWS Ubuntu (EC2)

<!--nav-->
[Previous](how-to-run.md) | [Next](local-dev.md) | [Home](/README.md)

---
<!--/nav-->

This guide covers deploying Aura on an AWS EC2 Ubuntu instance using the included `deploy.sh` script and `docker-compose.prod.yml`. The full production CD runbook is maintained in [`docs/devops/PRODUCTION_CD.md`](../../../docs/devops/PRODUCTION_CD.md).

---

## Recommended EC2 Instance

| | Minimum | Recommended |
|---|---|---|
| Instance type | `t3.small` (2 vCPU, 2 GB) | `t3.medium` (2 vCPU, 4 GB) |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| Storage | 20 GB gp3 | 30 GB gp3 |

The face recognition model (InsightFace) and bcrypt hashing are CPU-heavy. A `t3.small` will work but will be slow on first boot when models are downloaded.

---

## AWS Security Group â€” Required Inbound Rules

Before running the deploy script, open these ports in your EC2 Security Group:

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 22 | TCP | Your IP | SSH |
| 80 | TCP | 0.0.0.0/0 | Optional Nginx reverse proxy |
| 443 | TCP | 0.0.0.0/0 | Optional HTTPS reverse proxy |
| 5173 | TCP | 0.0.0.0/0 | Frontend, until Nginx is enabled |
| 8001 | TCP | 0.0.0.0/0 | Backend API, until Nginx is enabled |
| 8500 | TCP | 0.0.0.0/0 | Assistant API |

Ports 5432 (Postgres), 6379 (Redis), 5050 (pgAdmin), and 8025 (Mailpit) are **not** exposed to the host in the prod compose.

---

## What's Different in Production (`docker-compose.prod.yml`)

Compared to the dev `docker-compose.yml`:

- Uses the existing backend Dockerfile as a non-root user with no source bind mounts
- Postgres and Redis have **no host port exposure** â€” only reachable between containers
- Frontend preserves host port **5173**
- Backend preserves host port **8001**, assistant preserves **8500**
- `mailpit`, `pgadmin`, log-viewer, and `seeder/` are removed from production
- All secrets come from `.env.production`
- Backend, assistant, and frontend have health checks
- JSON log rotation is enabled for every production service

---

## Running the Deploy Script

### Option A â€” Run directly from GitHub (fresh server)

```bash
curl -fsSL https://raw.githubusercontent.com/LNCR-tech/RIZAL_v1/main/deploy.sh | bash
```

### Option B â€” Clone first, then run

```bash
git clone https://github.com/LNCR-tech/RIZAL_v1.git -b main
cd RIZAL_v1
chmod +x deploy.sh
./deploy.sh
```

---

## What the Script Does

1. Locks deployment so only one run executes at a time
2. Captures the previous git revision for rollback
3. Pulls the configured branch with `git pull --ff-only`
4. Validates `docker-compose.prod.yml`
5. Creates a Postgres backup when the database is already running
6. Builds images, starts infrastructure, runs migrations/bootstrap, and restarts changed app containers
7. Verifies backend health at `http://18.142.190.113:8001/health`
8. Automatically runs `rollback.sh` if deployment fails

---

## Interactive Prompts

Create `.env.production` from `.env.production.example` and fill in:

| Prompt | Description |
|---|---|
| `SECRET_KEY` | Long random string â€” generate with `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | Postgres password for the containerized database |
| `AI_API_KEY` | Your AI provider API key |
| `AI_API_BASE` | Your AI provider base URL (e.g. `https://api.openai.com/v1`) |
| `AI_MODEL` | The model name (e.g. `gpt-4o`) |
| Frontend public URL | Defaults to `http://18.142.190.113:5173` |
| Backend public URL | Defaults to `http://18.142.190.113:8001` |
| Enable email? | If yes, prompts for `MAILJET_API_KEY` and `MAILJET_API_SECRET` |

The script fails fast if `.env.production` is missing so placeholders are never used accidentally.

---

## Customizing the Deploy Target

Override these before running the script:

| Variable | Default | Description |
|---|---|---|
| `REPO_URL` | `https://github.com/LNCR-tech/RIZAL_v1.git` | Repo to clone |
| `DEPLOY_BRANCH` | `main` | Branch to deploy |
| `DEPLOY_DIR` | `/opt/aura` | Directory to clone into |

Example:

```bash
DEPLOY_DIR=/home/ubuntu/aura DEPLOY_BRANCH=main ./deploy.sh
```

---

## After Deployment

Once the stack is up:

| Service | URL |
|---|---|
| Frontend | `http://<server-ip>:5173` |
| Backend health | `http://<server-ip>:8001/health` |
| Backend API docs | `http://<server-ip>:8001/docs` if docs are enabled |
| Assistant API docs | `http://<server-ip>:8500/docs` |

---

## Useful Commands

All commands assume the stack is at `/opt/aura`.

Follow logs:

```bash
docker compose --env-file /opt/aura/.env.production -f /opt/aura/docker-compose.prod.yml logs -f
```

Check running containers:

```bash
docker compose --env-file /opt/aura/.env.production -f /opt/aura/docker-compose.prod.yml ps
```

Pull latest and redeploy:

```bash
cd /opt/aura && ./deploy.sh
```

Stop everything:

```bash
cd /opt/aura && docker compose --env-file .env.production -f docker-compose.prod.yml down
```

---

## Notes

- The script is idempotent â€” running it again on an already-deployed server pulls the latest code and restarts only containers whose image or configuration changed.
- Migrations and bootstrap run on every deployment before app containers are restarted.
- If Docker was just installed, you may need to run `newgrp docker` or log out and back in before Docker commands work without `sudo`.
- For HTTPS, use `deploy/nginx/aura.conf` with Certbot, or put an **Application Load Balancer** in front with an ACM certificate.
- The dev `docker-compose.yml` still works for local development â€” `docker-compose.prod.yml` is only for server deployments.

