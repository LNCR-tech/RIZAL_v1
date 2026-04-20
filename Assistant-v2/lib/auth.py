import os
from typing import Any, Dict, List, Optional
from fastapi import Header, HTTPException, status
from policy import normalize_role

try:
    from jose import JWTError, jwt
except ImportError:
    jwt = None
    JWTError = Exception

# Configuration (mirrored from v1)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY")
JWT_SECRETS = list(
    dict.fromkeys(
        secret for secret in (os.getenv("SECRET_KEY"), os.getenv("JWT_SECRET")) if secret
    )
)

ROLE_PRIORITY = ["admin", "campus_admin", "ssg", "sg", "org", "student"]

def decode_jwt(token: str) -> Dict[str, Any]:
    if not jwt:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="python-jose is required to verify JWTs.",
        )
    
    if JWT_PUBLIC_KEY:
        try:
            return jwt.decode(token, JWT_PUBLIC_KEY, algorithms=[JWT_ALGORITHM])
        except JWTError:
            pass

    for secret in JWT_SECRETS:
        try:
            return jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        except JWTError:
            continue

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def get_current_identity(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")
    token = authorization.split(" ", 1)[1].strip()
    return decode_jwt(token)

def get_roles_from_identity(identity: Dict[str, Any]) -> List[str]:
    raw_roles = identity.get("roles") or identity.get("role") or identity.get("user_role") or []
    if isinstance(raw_roles, str):
        raw_roles = [raw_roles]
    
    normalized = []
    seen = set()
    for role in raw_roles:
        norm = normalize_role(role)
        if norm and norm not in seen:
            seen.add(norm)
            normalized.append(norm)
    return normalized

def get_primary_role(roles: List[str]) -> str:
    for role in ROLE_PRIORITY:
        if role in roles:
            return role
    return roles[0] if roles else "student"
