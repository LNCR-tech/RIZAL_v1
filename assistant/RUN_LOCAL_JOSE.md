# Run Aura's AI locally on jose.gguf — **no Docker**

Goal: the Aura assistant answers from the **local** model `jose.gguf` — identity
**"Aura, powered by Jose AI"** — and your Flutter app talks to it, for testing.
No Docker, no Postgres.

## How it connects
```
Flutter app ──/assistant/stream──► assistant (:8500, uvicorn) ──/v1/chat/completions──► llama-server (:8091) → jose.gguf
```
The app never calls the model directly; it calls the assistant, which calls the
model. So you run **two local processes**: `llama-server` and the assistant.

## Where things are
- Model: `assistant/models/jose.gguf` — **ask Zann for the `jose.gguf` file** (it's
  not in the repo); place it in `assistant/models/`.
- llama.cpp server: `C:\Users\DjMhel\llama\llama-server.exe`
- Assistant config: `assistant/.env` (already set to the local model + SQLite)

---

## Step 1 — Start the model (terminal 1)
```powershell
C:\Users\DjMhel\llama\llama-server.exe -m "C:\Users\DjMhel\Documents\Software\RIZAL_v1-integrate-pilot-merge\assistant\models\jose.gguf" --host 127.0.0.1 --port 8091 --jinja --alias jose-ai -c 8192
```
- `--jinja` = tool-calling on → needed for **charts**. `--alias jose-ai` matches
  `AI_MODEL` in `.env`. Leave this running.
- Verify: open `http://127.0.0.1:8091` (llama.cpp web UI) or
  `curl http://127.0.0.1:8091/v1/models`.

## Step 2 — Fill the one required secret in `assistant/.env`
Everything else is set. You must paste **`SECRET_KEY`** = the *same* secret as the
backend you log into (otherwise the app's login token is rejected → 401):
```env
SECRET_KEY=<same SECRET_KEY as your backend>
```
- `ASSISTANT_DB_URL` is already `sqlite:///./assistant_local.db` (auto-created; no
  Postgres).
- `DATABASE_URL` only matters for **charts with real data** (the data tools query
  it). Plain chat + identity work without it. Point it at a reachable DB to enable
  data-backed charts.

## Step 3 — Run the assistant (terminal 2)
The venv has been recreated for you. `main.py` auto-loads `.env`.
```powershell
cd C:\Users\DjMhel\Documents\Software\RIZAL_v1-integrate-pilot-merge\assistant
.\venv\Scripts\Activate.ps1
uvicorn main:app --host 0.0.0.0 --port 8500
```
First start creates the SQLite tables. Verify: `curl http://127.0.0.1:8500/health`.

## Step 4 — Point the Flutter app at it (temporary)
Edit `frontend-app/config/cloud.json` → `AURA_ASSISTANT_BASE_URL`:
- Running the app on **this PC** (Chrome/desktop): `http://localhost:8500`
- Running on your **Android phone** (same Wi-Fi): `http://<YOUR-PC-LAN-IP>:8500`
  (find it with `ipconfig`; allow TCP 8500 through Windows Firewall).

Leave `AURA_API_BASE_URL` pointing at whichever backend you log in against. Then:
```powershell
cd C:\Users\DjMhel\Documents\Software\RIZAL_v1-integrate-pilot-merge\frontend-app
flutter run --dart-define-from-file=config/cloud.json
```
To revert after testing, just restore the original `AURA_ASSISTANT_BASE_URL`.

## Verify it works
- Ask **"who are you?"** → "I'm Aura, powered by Jose AI…"
- Ask **"chart my attendance this month"** → a chart renders in the bubble (needs a
  reachable `DATABASE_URL`; small model, so retry if the first try comes back as text).

## Notes
- **RAM:** this 1.5B model needs ~1.2 GB; your machine is 8 GB. Close heavy apps for
  headroom. Inference is CPU (~a few seconds per short reply).
- **Charts** require `llama-server --jinja` AND a reachable `DATABASE_URL`.
- This is dev-only (HTTP, SQLite, single user). For production see
  `../DEPLOYMENT_AWS.md`.
