# Aura — AWS Deployment Guide

How to deploy the full Aura stack to AWS: the **backend API**, the **AI assistant**
(optionally on the local **Jose AI** model), **Postgres**, the **web app**, and the
**Flutter mobile app**.

> The current staging host runs at `18.142.190.113` over **HTTP** (dev only). This
> guide also covers doing it **properly with HTTPS** for production.

---

## 1. Components
| Service | What | Port | Notes |
|---|---|---|---|
| `backend` | FastAPI — main API (auth, events, attendance, governance) | 8001 | issues the JWT |
| `assistant` | FastAPI — Aura AI chat (`/assistant/stream`) | 8500 | calls the LLM |
| `postgres` | App DB + assistant DB | 5432 | RDS in prod |
| LLM | **Jose AI** (`llama-server` + `jose.gguf`) **or** a cloud LLM | 8091 | see §5 |
| `frontend-web` | Vue web app (optional) | — | static hosting / S3+CloudFront |
| Flutter app | Android + iOS client | — | see §8 |

The repo ships a root `docker-compose.yml` with **`dev`** and **`prod`** profiles.
`--profile prod` builds images and runs DB migrations on startup.

---

## 2. Architecture (recommended)
```
        Internet (HTTPS 443)
              │
         [ ALB + ACM cert ]  (or nginx + Let's Encrypt on the EC2)
            /        \
   /api → backend:8001   /assistant → assistant:8500
                              │
                       LLM (one of):
                       a) llama-server:8091 (jose.gguf) on the same/another EC2
                       b) a cloud LLM (e.g. Groq) over HTTPS
                              │
                        RDS Postgres (private subnet)
```

---

## 3. Prerequisites
- An AWS account; an EC2 key pair; a domain (for HTTPS) is strongly recommended.
- Decide the **LLM strategy** (§5): self-host Jose AI (cheap, private, slower) or a
  cloud LLM (fast, costs per token).
- Secrets ready: a strong **`SECRET_KEY`** (shared by backend + assistant), DB
  password, and any cloud-LLM key. Store in **SSM Parameter Store / Secrets
  Manager**, never in git.

---

## 4. Option A — single EC2 + docker compose (simplest, matches staging)
Good for pilots/small deployments.

1. **Launch EC2**: Ubuntu 22.04, `t3.large` (2 vCPU/8 GB) minimum if self-hosting
   Jose AI on the same box (the 1.5B model needs ~1.5 GB free RAM + headroom);
   `t3.medium` is fine if you use a cloud LLM. Attach 30 GB+ gp3.
2. **Security group**: inbound `443` (and `80` for the cert challenge) from
   anywhere; `22` from your IP only. Do **not** expose 8001/8500/8091/5432.
3. **Install** Docker + compose plugin. Clone the repo.
4. **Configure env** (copy each `.env.example` → `.env`):
   - `backend/.env`: `SECRET_KEY`, `DATABASE_URL`, etc.
   - `assistant/.env`: **same** `SECRET_KEY`; `ASSISTANT_DB_URL`, `DATABASE_URL`;
     `AI_API_BASE` / `AI_MODEL` / `AI_API_KEY` per §5.
   - `database/.env`: `POSTGRES_*`.
   All `SECRET_KEY` values must be identical across backend + assistant.
5. **Bring it up**:
   ```bash
   docker compose --profile prod up -d --build   # builds + runs migrations
   docker compose ps
   ```
6. **HTTPS**: put **nginx + Let's Encrypt** (certbot) in front, proxying
   `/api`→8001 and `/assistant`→8500, or terminate TLS at an **ALB** with an **ACM**
   cert. Either way the public app only ever talks HTTPS.

## 5. The Jose AI model in production
The assistant is **model-agnostic** — it just needs an OpenAI-compatible endpoint
in `assistant/.env` (`AI_API_BASE`, `AI_MODEL`, `AI_API_KEY`). Pick one:

**a) Self-host Jose AI (jose.gguf) on AWS**
- Get `jose.gguf` from **Zann** (the maintainer; it is **not** in the repo) and put it
  on the server (~1 GB; e.g. S3 → download on boot, or scp).
- Run llama-server as a service (systemd or its own container), bound to localhost:
  ```bash
  llama-server -m /opt/aura/models/jose.gguf --host 127.0.0.1 --port 8091 --jinja --alias jose-ai
  ```
- Set `AI_API_BASE=http://127.0.0.1:8091/v1` (or `http://<model-host>:8091/v1`),
  `AI_MODEL=jose-ai`, `AI_API_KEY=sk-noop`.
- CPU is fine for 1.5B but slow under load; for real traffic use a **GPU instance**
  (e.g. `g5.xlarge`) and a CUDA llama.cpp build, or a bigger GGUF.

**b) Cloud LLM (fastest path to production)**
- Set `AI_API_BASE` + `AI_MODEL` + `AI_API_KEY` to your provider (the code already
  speaks the OpenAI-compatible protocol; `.env.example` defaults to Groq).
- Keep charts working: the model must support tool-calling.

## 6. Option B — managed (RDS + ECS/Fargate + ALB)
For scale/resilience:
- **RDS Postgres** (Multi-AZ) in private subnets; create the `ai_assistant` +
  app databases.
- Build + push `backend` and `assistant` images to **ECR**; run as **ECS Fargate**
  services behind an **ALB** (path rules `/api/*`→backend, `/assistant/*`→assistant)
  with an **ACM** cert (HTTPS).
- Inject env from **Secrets Manager**. Run migrations as a one-off ECS task.
- LLM: Fargate has no GPU → use a **cloud LLM** (§5b), or run llama-server on a
  separate GPU EC2 and point `AI_API_BASE` at it (private SG).

## 7. Security checklist
- [ ] HTTPS everywhere (ALB+ACM or nginx+certbot). No public HTTP in prod.
- [ ] `SECRET_KEY` identical in backend + assistant; stored in SSM/Secrets Manager.
- [ ] DB + LLM ports private (SG-restricted); only 443 is public.
- [ ] `assistant/.env`, `backend/.env`, `*.gguf` are git-ignored (see `.gitignore`).
- [ ] Rotate any key that ever touched git history.
- [ ] CORS: set `CORS_ALLOWED_ORIGINS` to the real web origin.

---

## 8. Flutter app (Android + iOS)
The app is a thin client — point it at the **prod HTTPS** URLs; nothing about the
model changes on the client.

1. **Configure endpoints** — `frontend-app/config/cloud.json` (git-ignored):
   ```json
   { "AURA_API_BASE_URL": "https://api.youraura.com",
     "AURA_ASSISTANT_BASE_URL": "https://api.youraura.com/assistant" }
   ```
   With HTTPS you can drop the dev cleartext exceptions (Android
   `usesCleartextTraffic`, iOS ATS `NSAllowsArbitraryLoads`).
2. **Android**:
   ```bash
   flutter build appbundle --release --dart-define-from-file=config/cloud.json
   ```
   Sign with an upload key, then upload the `.aab` to **Google Play**. (Direct
   share: `flutter build apk --release` → distribute the APK / Firebase App
   Distribution.)
3. **iOS** (needs macOS or a cloud Mac / Codemagic):
   ```bash
   flutter build ipa --release --dart-define-from-file=config/cloud.json
   ```
   Upload to **App Store Connect** → TestFlight / App Store. Requires an Apple
   Developer account.
4. **Versioning**: bump `pubspec.yaml` `version: <semver>+<build>` each release
   (the build number must increase for the stores).

---

## 9. Post-deploy smoke test
- `GET https://.../api/health` and `GET https://.../assistant/health` → 200.
- Log in from the app → reach the assistant → ask "who are you?" →
  "Aura, powered by Jose AI".
- Ask for a chart → renders (LLM tool-calling + reachable DB).
- Create an event (governance) and check attendance end-to-end.
