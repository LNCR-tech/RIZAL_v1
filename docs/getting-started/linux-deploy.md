# Deploying to a Linux Server

[<- Back to docs index](../../README.md)

This guide covers running Aura on a Linux machine using the included `deploy.sh` script. It works for both local Linux development and production server deployment — the difference is only in how you configure `.env`.

## Prerequisites

- Ubuntu 22.04+ or Debian 12+ (other distros with `apt` should work)
- A user with `sudo` access
- Ports `80`, `8000`, `8500`, `5050`, `8025` open on the server firewall (production only)

## Local Linux vs Production

| | Local Linux | Production Server |
|---|---|---|
| `SECRET_KEY` | Any string | Long random string (`openssl rand -hex 32`) |
| `DATABASE_URL` | Leave as default (uses Docker container) | External Postgres or leave as default |
| `LOGIN_URL` | `http://localhost` | `https://yourdomain.com` |
| `CORS_ALLOWED_ORIGINS` | `http://localhost` | `https://yourdomain.com` |
| `BACKEND_ORIGIN` | Leave as default | `https://yourdomain.com` or backend URL |
| `FRONTEND_PORT` | Any free port (e.g. `5173`) | `80` or `443` |
| `EMAIL_TRANSPORT` | `disabled` | `mailjet_api` |
| HTTPS | Not needed | Use a reverse proxy (nginx, Caddy) |

For local Linux, the defaults in `.env.example` are fine except for `SECRET_KEY` and the AI credentials. For production, see the full variable list in [Environment Variables](../reference/env.md#production-setup).

## Running the Deploy Script

### Option A — Run directly from GitHub

```bash
curl -fsSL https://raw.githubusercontent.com/LNCR-tech/RIZAL_v1/integrate/pilot-merge/deploy.sh | bash
```

### Option B — Clone first, then run

```bash
git clone https://github.com/LNCR-tech/RIZAL_v1.git -b integrate/pilot-merge
cd RIZAL_v1
chmod +x deploy.sh
./deploy.sh
```

## What the Script Does

1. Installs `git`, `docker`, and the Docker Compose plugin if not already present
2. Clones the repo to `/opt/aura` (or pulls latest if already cloned)
3. Creates `.env` from `.env.example` if it doesn't exist, then prompts for required secrets interactively
4. Runs `docker compose up --build -d`
5. Prints all service URLs using the server's IP address

## Interactive Prompts

When `.env` doesn't exist yet, the script will ask for:

| Prompt | Description |
|---|---|
| `SECRET_KEY` | A long random string — use `openssl rand -hex 32` to generate one |
| `AI_API_KEY` | Your AI provider API key |
| `AI_API_BASE` | Your AI provider base URL (e.g. `https://api.siliconflow.com/v1`) |
| `AI_MODEL` | The model name (e.g. `deepseek-ai/DeepSeek-V3.2`) |
| `FRONTEND_PORT` | Port to expose the frontend on (default `80`) |
| Enable email? | If yes, prompts for `MAILJET_API_KEY` and `MAILJET_API_SECRET` |

If `.env` already exists, the script skips configuration entirely and goes straight to `docker compose up --build -d`.

## Customizing the Deploy Target

The script reads three environment variables you can override before running:

| Variable | Default | Description |
|---|---|---|
| `REPO_URL` | `https://github.com/LNCR-tech/RIZAL_v1.git` | Repo to clone |
| `REPO_BRANCH` | `integrate/pilot-merge` | Branch to deploy |
| `DEPLOY_DIR` | `/opt/aura` | Directory to clone into |

Example with overrides:

```bash
DEPLOY_DIR=/home/ubuntu/aura REPO_BRANCH=main ./deploy.sh
```

## After Deployment

Once the stack is up, services are available at:

| Service | URL |
|---|---|
| Frontend | `http://<server-ip>:<FRONTEND_PORT>` |
| Backend API docs | `http://<server-ip>:8000/docs` |
| Assistant API docs | `http://<server-ip>:8500/docs` |
| pgAdmin | `http://<server-ip>:5050` (login: `admin@example.com` / `admin123`) |
| Mailpit | `http://<server-ip>:8025` |

## Useful Commands

Check running containers:

```bash
docker compose -f /opt/aura/docker-compose.yml ps
```

Follow logs:

```bash
docker compose -f /opt/aura/docker-compose.yml logs -f
```

Restart the stack:

```bash
cd /opt/aura && docker compose up -d
```

Pull latest and redeploy:

```bash
cd /opt/aura && git pull && docker compose up --build -d
```

Stop everything:

```bash
cd /opt/aura && docker compose down
```

## Notes

- The script is idempotent — running it again on an already-deployed server will pull the latest code and restart the stack without touching `.env`.
- Migrations and bootstrap run automatically on every `docker compose up --build` — no manual steps needed.
- If Docker was just installed, you may need to run `newgrp docker` or log out and back in before Docker commands work without `sudo`.
- For HTTPS, put a reverse proxy (nginx, Caddy, Traefik) in front of the frontend container and terminate TLS there.
