# How to Run Aura

<!--nav-->
[🏠 Home](/README.md) | [Docker →](docker.md)

---
<!--/nav-->

One command is all you need in every scenario. The stack handles database creation, migrations, bootstrap, and all services automatically.

---

## Linux — Local

```bash
docker compose up --build
```

Visit `http://localhost:5173`.

---

## Linux — Production (AWS EC2 / Ubuntu Server)

**First time on a fresh server:**

```bash
curl -fsSL https://raw.githubusercontent.com/LNCR-tech/RIZAL_v1/Pre-Production-v1/start.sh | bash
```

Or if you already cloned the repo:

```bash
chmod +x start.sh && ./start.sh
```

Visit `http://<your-server-ip>`.

**After first setup, use `start.sh` for everything:**

```bash
./start.sh              # start the stack
./start.sh stop         # stop all services
./start.sh restart      # stop then start
./start.sh update       # git pull + rebuild + restart
./start.sh logs         # follow all logs
./start.sh logs backend # follow one service
./start.sh status       # show running containers
./start.sh reset        # wipe everything including database (asks YES)
```

---

## Windows — Local

```powershell
docker compose up --build
```

Visit `http://localhost:5173`.

---

## Windows — Production

Windows can't run `start.sh` directly. SSH into the server and run it there:

```powershell
ssh ubuntu@<your-server-ip>
curl -fsSL https://raw.githubusercontent.com/LNCR-tech/RIZAL_v1/Pre-Production-v1/start.sh | bash
```

Or use Git Bash / WSL on your Windows machine:

```bash
chmod +x start.sh && ./start.sh
```

---

## What Happens Automatically

Every `docker compose up --build` or `./start.sh` runs these in order with no manual steps:

```
db (healthy)
  └── migrate        — runs Alembic migrations, creates all tables
        └── bootstrap  — creates admin account, roles, event types
              └── backend / worker / beat / assistant / frontend
```

---

## Default Credentials After First Boot

| Role | Email | Password |
|---|---|---|
| Platform Admin | `admin@aura.com` | `AdminPass123!` |

---

## Service URLs

| Service | Local | Production |
|---|---|---|
| Frontend | `http://localhost:5173` | `http://<server-ip>` |
| Backend API docs | `http://localhost:8000/docs` | `http://<server-ip>:8000/docs` |
| Assistant API docs | `http://localhost:8500/docs` | `http://<server-ip>:8500/docs` |
| pgAdmin | `http://localhost:5050` | not included in prod |
| Mailpit | `http://localhost:8025` | not included in prod |

pgAdmin login: `admin@example.com` / `admin123` (local only).

---

## AWS Security Group

For production, open these inbound TCP ports in your EC2 Security Group:

| Port | Purpose |
|---|---|
| 22 | SSH |
| 80 | Frontend |
| 8000 | Backend API |
| 8500 | Assistant API |

---

## CI/CD — Automatic Deployment

Pushing to `main`, `master`, `integrate/pilot-merge`, or `Pre-Production-v1` triggers automatic deployment:

1. **CI** — validates compose configs, compiles backend, lints and builds frontend
2. **CD** — if CI passes, SSHs into AWS and deploys the new code

### Setup (one time)

Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions** and add:

| Secret | Value |
|---|---|
| `AWS_SSH_PRIVATE_KEY` | Full contents of your `.pem` key file |
| `AWS_HOST` | Your EC2 public IP (e.g. `54.123.45.67`) |
| `AWS_USER` | SSH username (usually `ubuntu`) |
| `AWS_PROJECT_PATH` | Project path on server (default: `/opt/aura`) |

Then go to **Settings** → **Environments** → **New environment** → name it `production` and save.

### What happens on deploy

```
git push origin main
      ↓
CI: compile + lint + build (GitHub runners)
      ↓ passes
CD: SSH into AWS → git pull → docker compose up --build -d
      ↓
Health check: waits for backend /health to respond
      ↓
Cleanup: removes old Docker images to save disk
```

Data is **never deleted** — Docker volumes (`postgres_data`, `import_storage`, etc.) persist across rebuilds.
