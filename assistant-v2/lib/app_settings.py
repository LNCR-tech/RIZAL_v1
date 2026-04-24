"""Assistant non-secret runtime defaults."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AssistantAppSettings:
    context_max_messages: int = 20
    ai_provider: str = "openai"
    ai_model: str = "deepseek-ai/DeepSeek-V3.2"
    ai_max_tokens: int = 16384
    ai_api_version: str = "2023-06-01"
    ai_request_timeout_seconds: int = 60
    backend_api_timeout_seconds: int = 30
    report_request_timeout_seconds: int = 60
    import_request_timeout_seconds: int = 120
    default_cors_allowed_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )


APP_SETTINGS = AssistantAppSettings()


def get_backend_api_base_url() -> str:
    return (os.getenv("BACKEND_API_BASE_URL") or "").strip()


def get_cors_allowed_origins() -> list[str]:
    raw_value = os.getenv("CORS_ALLOWED_ORIGINS")
    if raw_value:
        origins = [item.strip() for item in raw_value.split(",") if item.strip()]
        if origins:
            return origins
    return list(APP_SETTINGS.default_cors_allowed_origins)
