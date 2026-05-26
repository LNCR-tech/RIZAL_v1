# Aura uses centralized Jose

Aura's AI (`assistant/`) does **not** run the model itself — it consumes the
**centralized Jose** service over HTTP (OpenAI-compatible). Centralized Jose is a
**separate project** with its own repository:

- **Repo:** https://github.com/zannn123/centralized-jose
- **Local folder:** the sibling `centralized-jose/` (kept outside this repo so any project can use it)
- **Full docs:** `centralized-jose/docs/integration-and-deployment.md` (in that repo)

## How Aura connects

```
Flutter app ──/assistant/stream──► assistant (:8500) ──/v1/chat/completions──► Jose gateway ──► llama-server (jose.gguf)
```

Aura is just an OpenAI-compatible **client** of the gateway. Aura's personality
("Aura, powered by Jose AI") lives here in `assistant/system_prompt.txt` +
`assistant/assistant_identity.py` and is sent on every request — the gateway adds
no personality.

## Two hops = two configs

The chain is **Jose → assistant (Aura) → Flutter**, so there are **two** API
configs. Each app only knows about the *next* hop — Flutter never talks to Jose
directly, so the Jose key never ships inside the app.

### 1) Jose's API → set in the assistant (`assistant/.env`)

The assistant is a client of the Jose gateway:

```env
AI_PROVIDER=openai
AI_API_BASE=https://<jose-gateway-host>:<port>/v1   # the Jose gateway, + /v1
AI_API_KEY=sk-jose-aura-<your-key>                  # Aura's gateway key (server-side only)
AI_MODEL=jose
AI_MAX_TOKENS=8192
```

No code change is needed — `assistant/lib/llm.py` already speaks the OpenAI API.

### 2) The assistant's API → set in Flutter (`frontend-app/config/cloud.json`)

Flutter is a client of the assistant (not of Jose):

```json
{
  "AURA_API_BASE_URL": "https://<backend-host>",
  "AURA_ASSISTANT_BASE_URL": "https://<assistant-host>:8500"
}
```

Run with `flutter run --dart-define-from-file=config/cloud.json`.
`AURA_ASSISTANT_BASE_URL` is read in `lib/core/config/app_config.dart` and used
by `assistant_service.dart`; the app calls `POST /assistant/stream` on it.

## Deployment notes

- Point `AI_API_BASE` at the **gateway**, never at llama-server directly.
- Keep `AI_API_KEY` secret (it lives in `assistant/.env`, which is git-ignored).
- Handle gateway statuses: `401` (bad key), `429` (rate limited — ask the
  operator to raise Aura's `JOSE_RATE_PER_MIN`), `502` (model/upstream down).
- For purely local dev against your own llama-server (no gateway), see
  `assistant/RUN_LOCAL_JOSE.md` and point `AI_API_BASE` at the local llama-server.
