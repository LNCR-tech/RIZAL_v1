"""Use: Defines shared FastAPI/Starlette middleware for request hardening.
Where to use: Register these middleware classes from app.main.
Role: Core web layer. It rejects oversized requests and throttles broad mutation abuse.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.rate_limit import (
    bearer_token_identity,
    build_authenticated_mutation_rule,
    client_ip_identity,
    enforce_rate_limit,
)
from app.core.security import decode_token_to_token_data


class MaxRequestBodySizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        max_size_bytes = max(0, settings.max_request_body_size_mb) * 1024 * 1024
        content_length = request.headers.get("content-length")
        if max_size_bytes and content_length:
            try:
                request_size = int(content_length)
            except ValueError:
                request_size = 0
            if request_size > max_size_bytes:
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": {
                            "code": "request_too_large",
                            "message": f"Request body exceeds {settings.max_request_body_size_mb} MB.",
                            "max_size_bytes": max_size_bytes,
                        }
                    },
                )
        return await call_next(request)


class MutationRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method.upper() not in {"POST", "PUT", "PATCH", "DELETE"}:
            return await call_next(request)

        identity = self._identity_for_request(request)
        try:
            enforce_rate_limit(
                build_authenticated_mutation_rule(),
                identity,
                request=request,
            )
        except Exception as exc:
            status_code = getattr(exc, "status_code", None)
            if status_code == 429:
                headers = getattr(exc, "headers", None) or {}
                return JSONResponse(
                    status_code=429,
                    content={"detail": getattr(exc, "detail", "Too many requests.")},
                    headers=headers,
                )
            raise
        return await call_next(request)

    @staticmethod
    def _identity_for_request(request: Request) -> str:
        authorization = request.headers.get("authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token.strip():
            try:
                token_data = decode_token_to_token_data(token.strip())
            except Exception:
                hashed_token = bearer_token_identity(request)
                return hashed_token or client_ip_identity(request)
            if token_data.email:
                return f"user-email:{token_data.email.strip().lower()}"
        return bearer_token_identity(request) or client_ip_identity(request)
