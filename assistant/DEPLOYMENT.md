# Aura Assistant — Deployment

This service is the **Aura AI chat** (`POST /assistant/stream`, SSE). It needs four
things: an **LLM endpoint** (local **Jose AI** via llama.cpp, or a cloud LLM), a
**database**, the backend's **`SECRET_KEY`**, and the **backend API URL**.

> Full-stack AWS guide (backend + DB + web + Flutter): see [`../DEPLOYMENT_AWS.md`](../DEPLOYMENT_AWS.md).
> Local dev (no Docker): see [`RUN_LOCAL_JOSE.md`](RUN_LOCAL_JOSE.md).

---

## Environment (`assistant/.env`)
Copy `.env.example` → `.env` and set:

| Var | Meaning | Prod value |
|---|---|---|
| `AI_PROVIDER` | LLM protocol | `openai` (OpenAI-compatible) |
| `AI_API_BASE` | LLM endpoint | `http://127.0.0.1:8091/v1` (self-host) or cloud URL |
| `AI_MODEL` | model id | `jose-ai` (self-host) or the cloud model name |
| `AI_API_KEY` | LLM key | `sk-noop` for llama.cpp; real key for cloud |
| `AI_MAX_TOKENS` | reply cap | `4096`–`8192` |
| `ASSISTANT_DB_URL` | assistant's own DB (conversations) | `postgresql://…` (RDS) |
| `DATABASE_URL` | backend DB (data/chart tools) | `postgresql://…` (same as backend) |
| `BACKEND_API_BASE_URL` | main API | `https://api.youraura.com` |
| `SECRET_KEY` | JWT verify — **must equal the backend's** | from Secrets Manager |
| `JWT_ALGORITHM` | `HS256` | `HS256` |
| `ASSISTANT_ORIGIN` | this service's public URL | `https://api.youraura.com/assistant` |
| `CORS_ALLOWED_ORIGINS` | web origins allowed to call it | your web app origin |

Store secrets in **SSM Parameter Store / Secrets Manager**, never in git
(`.env` is git-ignored).

---

## Option A — with the stack (Docker, recommended)
The root `docker-compose.yml` builds this service from `assistant/Dockerfile`
(port 8500) under the `prod` profile:
```bash
docker compose --profile prod up -d --build      # run from the repo root
docker compose logs -f assistant
```
Put it behind nginx/ALB at `/assistant` over HTTPS (see `../DEPLOYMENT_AWS.md`).

## Option B — standalone on an EC2 (systemd, no Docker)
```bash
cd /opt/aura/assistant
python3 -m venv venv && . venv/bin/activate
pip install -r requirements.txt
# /etc/systemd/system/aura-assistant.service runs:
#   ExecStart=/opt/aura/assistant/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8500
sudo systemctl enable --now aura-assistant
```
Reverse-proxy `127.0.0.1:8500` → `https://…/assistant` with nginx + a TLS cert.
`main.py` auto-loads `.env`; tables are created on first start.

---

## The Jose AI model in production
The assistant only needs an OpenAI-compatible endpoint — pick one:

**a) Self-host Jose AI (`jose.gguf`)** — get the `jose.gguf` file from **Zann** (the
maintainer; it is not in the repo), ship it to the box (~1 GB; e.g. via S3 or scp),
then run llama.cpp as its own service. In the production Compose stack, place the
model at `/opt/aura/jose.gguf`; `docker-compose.prod.yml` starts
the internal `local-llm` service and points the assistant at it automatically.

Standalone command equivalent:
```bash
llama-server -m /opt/aura/jose.gguf \
  --host 127.0.0.1 --port 8091 --jinja --alias jose-ai
```
`--jinja` is required for **charts** (tool-calling). CPU works for 1.5B but is slow
under load — use a **GPU instance** (e.g. `g5.xlarge`, CUDA build) for real traffic.
Set `AI_API_BASE=http://127.0.0.1:8091/v1`, `AI_MODEL=jose-ai`, `AI_API_KEY=sk-noop`.

**b) Cloud LLM** — set `AI_API_BASE`/`AI_MODEL`/`AI_API_KEY` to your provider. Fast,
costs per token; the model must support tool-calling for charts.

---

## Database
- **Prod:** point `ASSISTANT_DB_URL` (conversations) and `DATABASE_URL` (the data the
  tools read) at Postgres/RDS. They can be the same Postgres, different databases.
- **Dev only:** `ASSISTANT_DB_URL=sqlite:///./assistant_local.db` (zero-setup).

## Ports & security
- `8500` assistant — internal; exposed only via the reverse proxy over HTTPS.
- `8091` llama-server — internal/localhost only; never public.
- `SECRET_KEY` identical to the backend (or every request 401s).
- Set `CORS_ALLOWED_ORIGINS` to the real web origin.

## Health & smoke test
- `GET /health` → `200`.
- Ask **"who are you?"** → "Aura, powered by Jose AI".
- Ask for a **chart** → renders (needs `--jinja` + a reachable `DATABASE_URL`).
