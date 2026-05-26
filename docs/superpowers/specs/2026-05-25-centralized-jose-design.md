# Design: Centralized Jose with a thin auth gateway

**Date:** 2026-05-25
**Status:** Approved → implemented as the **separate** `centralized-jose/` project
(sibling of this repo, so any project can reuse it). Aura is wired to consume it
via `assistant/.env`; see `docs/jose/aura-uses-centralized-jose.md`.

## Problem

`jose.gguf` runs locally via llama-server and is wrapped per-app by Aura's
`assistant/` service. We want **one** Jose, usable by **many** projects **over
the network (API only)**, where **each project supplies its own personality**.
No project should need the model file, and no project's identity should be baked
into Jose.

## Decisions (from brainstorming)

1. **Hosting:** already handled — llama-server + assistant are deployed on the
   cloud box (same IP as the backend, separate port). So this design adds the
   layer *in front*, not the hosting.
2. **Personality:** each project owns it. Projects send their own system prompt
   per request; the central service stays persona-agnostic.
3. **Scope:** docs + a thin auth gateway (API keys + rate limiting). No central
   persona registry, no billing, no multi-model routing (YAGNI).

## Key insight

`jose.gguf` is *already* served as an OpenAI-compatible API by llama-server, and
Aura's `assistant/lib/llm.py` is already just a client of it (`AI_API_BASE` +
`AI_MODEL`). "Centralizing" therefore means: (a) make that endpoint reachable
and **safe** to expose, and (b) have each consumer send its own system prompt.

## Architecture

```
projects → Jose Gateway (auth + rate limit, OpenAI-compatible) → llama-server (jose.gguf)
```

- **llama-server**: runs the model; bound to localhost / private network.
- **Jose Gateway** (`jose-gateway/`, FastAPI): single public entry. Validates a
  per-project Bearer key, rate-limits per project, forwards requests verbatim,
  streams SSE through. Injects no persona.
- **Projects**: OpenAI-compatible clients; each sends its own system prompt.

## Components

### Jose Gateway (`centralized-jose/gateway/app.py`, separate project)

- `POST /v1/chat/completions` — non-stream returns upstream JSON; `stream:true`
  forwards the upstream SSE byte stream unchanged.
- `GET /v1/models` — proxied from upstream (auth required).
- `GET /health` — gateway status + an upstream reachability probe (no auth).
- `GET /` — basic info (no auth).

**Auth:** `Authorization: Bearer <key>` checked against `JOSE_API_KEYS`
(JSON `{key: project}`). Missing/invalid → 401. **Fails closed**: no keys
configured → 503 (never runs open).

**Rate limit:** in-memory sliding 60s window, `JOSE_RATE_PER_MIN` per project.
Documented Redis path for multi-instance.

**Safety knobs:** optional `JOSE_MAX_TOKENS_CAP`; configurable upstream URL,
timeout, CORS, port.

### Configuration (env)

`JOSE_UPSTREAM_URL`, `JOSE_API_KEYS`, `JOSE_DEFAULT_MODEL`, `JOSE_RATE_PER_MIN`,
`JOSE_MAX_TOKENS_CAP`, `JOSE_REQUEST_TIMEOUT`, `JOSE_CORS_ORIGINS`, `PORT`.

## Data flow

1. Project POSTs OpenAI-shaped body (with its own system prompt) + Bearer key.
2. Gateway: auth → rate limit → fill default model / cap max_tokens.
3. Gateway forwards to `…/v1/chat/completions` on llama-server.
4. Non-stream: return JSON. Stream: pipe SSE chunks back to the project.

## Security

llama-server has no auth, so it must be private (localhost or firewalled); only
the gateway is public. TLS terminates at the existing reverse proxy. API keys
are deployment secrets; mobile/web clients should call Jose via their own
backend so keys never ship in a binary.

## Error contract

`400` missing `messages` · `401` bad key · `429` rate limited · `502` upstream
unreachable · `503` no keys configured.

## Testing

`jose-gateway/tests/test_gateway.py` covers auth (missing/invalid), rate-limit
trigger, input validation, health, and OpenAI-compat advertising — without a
live upstream (points it at an unreachable address). All 8 pass.

## Out of scope / future

- Central persona registry (named personas selected by id).
- Usage logging/billing dashboards; multi-model routing; Redis-backed limits.

## Consumer deployment

Documented in `centralized-jose/docs/integration-and-deployment.md` §7 and
`docs/jose/aura-uses-centralized-jose.md`: set base URL + key (as a secret) +
model via env, ship your own system prompt, handle 401/429/502, use streaming.
Aura's `assistant/` needs only env changes (`AI_API_BASE` → gateway `/v1`,
`AI_API_KEY` → Aura's key) — no code change. Flutter is unchanged: it still
points `AURA_ASSISTANT_BASE_URL` at the assistant.
