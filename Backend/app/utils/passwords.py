import secrets
import string

from passlib.context import CryptContext

_PASSWORD_ALPHABET = string.ascii_letters + string.digits
_PASSWORD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_secure_password(min_length: int = 10, max_length: int = 16) -> str:
    if min_length < 10:
        raise ValueError("min_length must be at least 10")
    if max_length < min_length:
        raise ValueError("max_length must be greater than or equal to min_length")

    length = secrets.randbelow(max_length - min_length + 1) + min_length

    # Ensure password policy is always satisfied.
    required = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
    ]
    remaining = [secrets.choice(_PASSWORD_ALPHABET) for _ in range(length - len(required))]

    chars = required + remaining
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def hash_password_bcrypt(password: str) -> str:
    return _PASSWORD_CONTEXT.hash(password)
