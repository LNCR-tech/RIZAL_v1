import os
import httpx
from fastapi import Header, HTTPException, status
from typing import Dict, Any, Optional, List
import logging
from .policy import normalize_role

logger = logging.getLogger("uvicorn.error")

# --- Auth Configuration (Verbatim from v1) ---
JWT_SECRETS = list(dict.fromkeys(filter(None, [os.getenv("SECRET_KEY"), os.getenv("JWT_SECRET")])))
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
BACKEND_API_BASE_URL = (os.getenv("BACKEND_API_BASE_URL") or "").strip()
BACKEND_API_TIMEOUT_SECONDS = int(os.getenv("BACKEND_API_TIMEOUT_SECONDS", "30"))

try:
    from jose import jwt, JWTError
except ImportError:
    jwt = None
    JWTError = Exception

ROLE_PRIORITY = ["admin", "campus_admin", "ssg", "sg", "org", "student"]

def _decode_jwt(token: str) -> Dict[str, Any]:
    if not jwt:
        raise HTTPException(status_code=500, detail="python-jose is required to verify JWTs.")
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    if JWT_PUBLIC_KEY:
        try:
            return jwt.decode(token, JWT_PUBLIC_KEY, algorithms=[JWT_ALGORITHM])
        except JWTError:
            pass

    for secret in JWT_SECRETS:
        try:
            return jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        except JWTError:
            pass

    raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_current_identity(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    token = authorization.split(" ", 1)[1].strip()
    return _decode_jwt(token)

def get_token_user_id(identity: Dict[str, Any]) -> str:
    user_id = str(identity.get("user_id") or identity.get("sub") or "")
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing user identity in token")
    return user_id

def get_roles_from_identity(identity: Dict[str, Any], body_role: Optional[str] = None, extra_roles: Optional[List[str]] = None) -> tuple[str, list[str]]:
    raw_roles = identity.get("roles") or identity.get("role") or identity.get("user_role") or []
    if isinstance(raw_roles, str):
        raw_roles = [raw_roles]
    if extra_roles:
        raw_roles = [*raw_roles, *extra_roles]

    normalized_roles: list[str] = []
    seen = set()
    for role in raw_roles:
        normalized = normalize_role(role)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        normalized_roles.append(normalized)

    if not normalized_roles:
        raise HTTPException(status_code=401, detail="Missing user role in token")

    requested_role = normalize_role(body_role or "")
    if requested_role and requested_role not in seen:
        raise HTTPException(status_code=403, detail="user_role mismatch")

    if requested_role:
        primary_role = requested_role
    else:
        primary_role = next((role for role in ROLE_PRIORITY if role in seen), normalized_roles[0])

    sorted_roles = [role for role in ROLE_PRIORITY if role in seen]
    for role in normalized_roles:
        if role not in sorted_roles:
            sorted_roles.append(role)

    return primary_role, sorted_roles

async def request_backend(
    method: str,
    path: str,
    authorization: Optional[str],
    query: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    candidates = [BACKEND_API_BASE_URL, "http://127.0.0.1:8000", "http://localhost:8000"]
    async with httpx.AsyncClient(timeout=BACKEND_API_TIMEOUT_SECONDS) as client:
        for base_url in filter(None, candidates):
            url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
            try:
                resp = await client.request(
                    method, url, headers={"Authorization": authorization} if authorization else {},
                    params=query, json=body
                )
                if resp.status_code < 500:
                    return {"ok": resp.status_code < 400, "status_code": resp.status_code, "data": resp.json() if "application/json" in resp.headers.get("content-type", "") else resp.text}
            except Exception as e:
                logger.warning(f"Backend candidate failed ({url}): {e}")
                continue
    return {"ok": False, "error": "backend unreachable"}

async def resolve_runtime_governance_access(authorization: Optional[str], user_id: str, school_id: Optional[int]) -> Dict[str, Any]:
    if authorization:
        result = await request_backend("GET", "/api/governance/access/me", authorization)
        if result.get("ok"):
            data = result.get("data") or {}
            return {
                "permission_codes": data.get("permission_codes") or [],
                "roles": data.get("roles") or [],
                "school_id": data.get("school_id") or school_id
            }
    return {"permission_codes": [], "roles": [], "school_id": school_id}
