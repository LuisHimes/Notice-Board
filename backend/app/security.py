import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

password_hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)


@dataclass(frozen=True)
class AuthSettings:
    secret_key: str = field(repr=False)
    issuer: str = "notice-board-api"
    audience: str = "notice-board-client"
    token_minutes: int = 15

    def __post_init__(self):
        if len(self.secret_key.encode()) < 32:
            raise ValueError("JWT_SECRET_KEY must contain at least 32 bytes")
        if not 1 <= self.token_minutes <= 60:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be between 1 and 60")
        if not self.issuer or not self.audience:
            raise ValueError("Token issuer and audience must not be empty")

    @classmethod
    def from_env(cls):
        return cls(
            secret_key=os.getenv("JWT_SECRET_KEY", ""),
            issuer=os.getenv("JWT_ISSUER", "notice-board-api"),
            audience=os.getenv("JWT_AUDIENCE", "notice-board-client"),
            token_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")),
        )


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def create_access_token(user_id: int, token_version: int, settings: AuthSettings) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user_id),
            "ver": token_version,
            "iss": settings.issuer,
            "aud": settings.audience,
            "iat": now,
            "nbf": now,
            "exp": now + timedelta(minutes=settings.token_minutes),
        },
        settings.secret_key,
        algorithm="HS256",
    )


def decode_access_token(token: str, settings: AuthSettings) -> tuple[int, int]:
    claims = jwt.decode(
        token,
        settings.secret_key,
        algorithms=["HS256"],
        issuer=settings.issuer,
        audience=settings.audience,
        options={"require": ["sub", "ver", "iss", "aud", "iat", "nbf", "exp"]},
    )
    subject = claims["sub"]
    version = claims["ver"]
    if not isinstance(subject, str) or not subject.isdecimal() or int(subject) <= 0:
        raise jwt.InvalidTokenError("Invalid subject")
    if type(version) is not int or version < 0:
        raise jwt.InvalidTokenError("Invalid token version")
    return int(subject), version