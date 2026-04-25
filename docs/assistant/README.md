# Assistant Documentation

[<- Back to docs index](../../README.md)

The supported assistant service in this repository is:

- `assistant-v2/`

Key configuration notes:

- non-secret assistant defaults now live in `assistant-v2/lib/app_settings.py`
- secrets and runtime URLs remain env-driven
- production compose and main docs target `assistant-v2` only

## Prompt Size / Token Budgeting

The assistant sends a system prompt + recent conversation history to the LLM on every message. To keep requests under a
token cap (for example ~25k input tokens), `assistant-v2` supports server-side prompt budgeting:

- Older context is summarized into an internal `meta_summary` message (hidden from conversation APIs/UI).
- Only the most recent messages are sent verbatim, plus the summary when needed.
- MCP tool schemas are cached to avoid repeated tool discovery overhead.

Environment overrides (optional):

- `ASSISTANT_PROMPT_BUDGET_TOKENS` (default `25000`)
- `ASSISTANT_PROMPT_RESERVE_COMPLETION_TOKENS` (default `2000`)
- `ASSISTANT_CONTEXT_KEEP_LAST_MESSAGES` (default `8`)
- `ASSISTANT_CONTEXT_SUMMARY_MAX_CHARS` (default `3500`)

## Existing Docs

- [v1 vs v2 Comparison](../assistant-v2/v1_vs_v2_comparison.md)
