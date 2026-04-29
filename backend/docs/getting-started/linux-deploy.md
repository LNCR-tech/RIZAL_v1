# Deploying to AWS Ubuntu (EC2)

<!--nav-->
[Previous](how-to-run.md) | [Next](local-dev.md) | [Home](/README.md)

---
<!--/nav-->

This guide covers deploying Aura on an AWS EC2 Ubuntu instance using the included `deploy.sh` script and `docker-compose.prod.yml`.

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
| 80 | TCP | 0.0.0.0/0 | Frontend |
| 8000 | TCP | 0.0.0.0/0 | Backend API |
| 8500 | TCP | 0.0.0.0/0 | Assistant API |

Ports 5432 (Postgres) and 6379 (Redis) are **not** exposed to the host in the prod compose â€” they are internal only.

---

## What's Different in Production (`docker-compose.prod.yml`)

Compared to the dev `docker-compose.yml`:

- Uses `Dockerfile.prod` for the backend â€” runs as a non-root user, no source bind mounts
- Postgres and Redis have **no host port exposure** â€” only reachable between containers
- Frontend runs on port **80** (not 5174)
- Backend runs on port **8000**, assistant on **8500**
- `mailpit` and `pgadmin` are removed â€” not needed in production
- All secrets come from `.env` via `DB_PASSWORD`, `LOGIN_URL`, `BACKEND_ORIGIN`, etc.
- Backend has a healthcheck â€” frontend waits for it before starting

---

## Running the Deploy Script

### Option A â€” Run directly from GitHub (fresh server)

```bash
curl -fsSL https://raw.githubusercontent.com/LNCR-tech/RIZAL_v1/Pre-Production-v1/deploy.sh | bash
```

### Option B â€” Clone first, then run

```bash
git clone https://github.com/LNCR-tech/RIZAL_v1.git -b Pre-Production-v1
cd RIZAL_v1
chmod +x deploy.sh
./deploy.sh
```

---

## What the Script Does

1. Installs `git`, `docker`, and the Docker Compose plugin if not already present
2. Clones the repo to `/opt/aura` (or pulls latest if already cloned)
3. Creates `.env` from `.env.production.example` if it doesn't exist, then prompts for required values
4. Opens ports 80, 8000, and 8500 in `ufw` if the firewall is active
5. Runs `docker compose -f docker-compose.prod.yml up --build -d`
6. Prints all service URLs using the server's public IP

---

## Interactive Prompts

When `.env` doesn't exist yet, the script will ask for:

| Prompt | Description |
|---|---|
| `SECRET_KEY` | Long random string â€” generate with `openssl rand -hex 32` |
| `DB_PASSWORD` | Postgres password for the containerized database |
| `AI_API_KEY` | Your AI provider API key |
| `AI_API_BASE` | Your AI provider base URL (e.g. `https://api.openai.com/v1`) |
| `AI_MODEL` | The model name (e.g. `gpt-4o`) |
| Frontend public URL | Defaults to `http://<your-public-ip>` |
| Backend public URL | Defaults to `http://<your-public-ip>:8000` |
| Enable email? | If yes, prompts for `MAILJET_API_KEY` and `MAILJET_API_SECRET` |

If `.env` already exists, the script skips configuration and goes straight to `docker compose up --build -d`.

---

## Customizing the Deploy Target

Override these before running the script:

| Variable | Default | Description |
|---|---|---|
| `REPO_URL` | `https://github.com/LNCR-tech/RIZAL_v1.git` | Repo to clone |
| `REPO_BRANCH` | `Pre-Production-v1` | Branch to deploy |
| `DEPLOY_DIR` | `/opt/aura` | Directory to clone into |

Example:

```bash
DEPLOY_DIR=/home/ubuntu/aura REPO_BRANCH=main ./deploy.sh
```

---

## After Deployment

Once the stack is up:

| Service | URL |
|---|---|
| Frontend | `http://<server-ip>` |
| Backend API docs | `http://<server-ip>:8000/docs` |
| Assistant API docs | `http://<server-ip>:8500/docs` |

---

## Useful Commands

All commands assume the stack is at `/opt/aura`.

Follow logs:

```bash
docker compose -f /opt/aura/docker-compose.prod.yml logs -f
```

Check running containers:

```bash
docker compose -f /opt/aura/docker-compose.prod.yml ps
```

Pull latest and redeploy:

```bash
cd /opt/aura && git pull && docker compose -f docker-compose.prod.yml up --build -d
```

Stop everything:

```bash
cd /opt/aura && docker compose -f docker-compose.prod.yml down
```

---

## Notes

- The script is idempotent â€” running it again on an already-deployed server pulls the latest code and restarts the stack without touching `.env`.
- Migrations and bootstrap run automatically on every `up --build` â€” no manual steps needed.
- If Docker was just installed, you may need to run `newgrp docker` or log out and back in before Docker commands work without `sudo`.
- For HTTPS, put a reverse proxy (Caddy or nginx) in front of the frontend on port 443 and terminate TLS there. The simplest option on AWS is to put an **Application Load Balancer** in front with an ACM certificate.
- The dev `docker-compose.yml` still works for local development â€” `docker-compose.prod.yml` is only for server deployments.

