"""Use: Provides shared Redis-backed request rate limiting.
Where to use: Use this in middleware or route dependencies for anti-abuse controls.
Role: Core security layer. It keeps rate limiting behavior consistent across routers.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import logging
import threading
import time
from typing import Callable

from fastapi import Depends, HTTPException, Request, status
from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateLimitRule:
    name: str
    limit: int
    window_seconds: int


_redis_client: Redis | None = None
_memory_lock = threading.Lock()
_memory_counters: dict[str, tuple[int, float]] = {}


def reset_rate_limit_state() -> None:
    """Clear in-process limiter state for tests and local diagnostics."""
    global _redis_client
    with _memory_lock:
        _memory_counters.clear()
    _redis_client = None


def _get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=0.2,
            socket_timeout=0.2,
            decode_responses=True,
        )
    return _redis_client


def client_ip_identity(request: Request) -> str:
    """Return a stable client identity for rate limiting without trusting full headers."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        first_hop = forwarded_for.split(",", 1)[0].strip()
        if first_hop:
            return f"ip:{first_hop}"
    if request.client and request.client.host:
        return f"ip:{request.client.host}"
    return "ip:unknown"


def bearer_token_identity(request: Request) -> str | None:
    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    digest = hashlib.sha256(token.strip().encode("utf-8")).hexdigest()
    return f"bearer:{digest}"


def user_identity(user) -> str:
    user_id = getattr(user, "id", None)
    if user_id is not None:
        return f"user:{user_id}"
    email = getattr(user, "email", None)
    if email:
        return f"user-email:{str(email).strip().lower()}"
    return "user:unknown"


def _consume_memory(rule: RateLimitRule, identity: str) -> tuple[bool, int]:
    now = time.monotonic()
    key = f"{rule.name}:{identity}"
    with _memory_lock:
        count, expires_at = _memory_counters.get(key, (0, now + rule.window_seconds))
        if expires_at <= now:
            count = 0
            expires_at = now + rule.window_seconds
        count += 1
        _memory_counters[key] = (count, expires_at)
        retry_after = max(1, int(expires_at - now))
        return count <= rule.limit, retry_after


def _consume_redis(rule: RateLimitRule, identity: str) -> tuple[bool, int]:
    now = int(time.time())
    window_id = now // max(1, rule.window_seconds)
    key_identity = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    key = f"rate-limit:{rule.name}:{window_id}:{key_identity}"
    client = _get_redis_client()
    count = int(client.incr(key))
    if count == 1:
        client.expire(key, rule.window_seconds + 1)
    ttl = int(client.ttl(key))
    retry_after = ttl if ttl > 0 else rule.window_seconds
    return count <= rule.limit, retry_after


def enforce_rate_limit(
    rule: RateLimitRule,
    identity: str,
    *,
    request: Request | None = None,
) -> None:
    settings = get_settings()
    if not settings.rate_limit_enabled:
        return
    if rule.limit <= 0 or rule.window_seconds <= 0:
        return

    try:
        allowed, retry_after = _consume_redis(rule, identity)
    except RedisError as exc:
        if not settings.rate_limit_fail_open:
            logger.warning("Redis rate limiter failed closed for %s: %s", rule.name, exc)
            retry_after = rule.window_seconds
            allowed = False
        else:
            logger.warning("Redis rate limiter unavailable for %s; using memory fallback.", rule.name)
            allowed, retry_after = _consume_memory(rule, identity)

    if allowed:
        return

    client_identity = identity if identity.startswith("user:") else client_ip_identity(request) if request else identity
    logger.warning("Rate limit exceeded for rule=%s identity=%s", rule.name, client_identity)
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "code": "rate_limit_exceeded",
            "message": "Too many requests. Please wait before trying again.",
            "limit": rule.limit,
            "window_seconds": rule.window_seconds,
            "retry_after_seconds": retry_after,
        },
        headers={"Retry-After": str(retry_after)},
    )


def rate_limit_by_ip(rule_factory: Callable[[], RateLimitRule]):
    def dependency(request: Request) -> None:
        enforce_rate_limit(
            rule_factory(),
            client_ip_identity(request),
            request=request,
        )

    return Depends(dependency)


def build_login_rule() -> RateLimitRule:
    settings = get_settings()
    return RateLimitRule(
        name="login",
        limit=settings.rate_limit_login_count,
        window_seconds=settings.rate_limit_login_window_seconds,
    )


def build_forgot_password_rule() -> RateLimitRule:
    settings = get_settings()
    return RateLimitRule(
        name="forgot-password",
        limit=settings.rate_limit_forgot_password_count,
        window_seconds=settings.rate_limit_forgot_password_window_seconds,
    )


def build_face_rule() -> RateLimitRule:
    settings = get_settings()
    return RateLimitRule(
        name="face",
        limit=settings.rate_limit_face_count,
        window_seconds=settings.rate_limit_face_window_seconds,
    )


def build_public_rule() -> RateLimitRule:
    settings = get_settings()
    return RateLimitRule(
        name="public",
        limit=settings.rate_limit_public_count,
        window_seconds=settings.rate_limit_public_window_seconds,
    )


def build_authenticated_mutation_rule() -> RateLimitRule:
    settings = get_settings()
    return RateLimitRule(
        name="authenticated-mutation",
        limit=settings.rate_limit_authenticated_mutation_count,
        window_seconds=settings.rate_limit_authenticated_mutation_window_seconds,
    )
