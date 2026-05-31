"""
AI创作工坊 - JWT Authentication

Provides token creation, verification, and FastAPI dependency injection
for protected routes.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from config import get_settings
from observability.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_scheme = HTTPBearer()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


class TokenPayload(BaseModel):
    """Decoded JWT payload."""
    sub: str  # user ID
    org_id: str
    role: str = "user"
    exp: Optional[datetime] = None


class UserContext(BaseModel):
    """Authenticated user context injected into route handlers."""
    user_id: str
    org_id: str
    role: str = "user"


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_token(
    user_id: str,
    org_id: str,
    role: str = "user",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        user_id: Unique user identifier
        org_id: Organization identifier
        role: User role (user, admin)
        expires_delta: Custom token expiry

    Returns:
        Encoded JWT string
    """
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": user_id,
        "org_id": org_id,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.app_secret_key, algorithm=ALGORITHM)
    logger.info(f"Token created for user={user_id}, org={org_id}, role={role}")
    return token


def verify_token(token: str) -> TokenPayload:
    """
    Verify and decode a JWT token.

    Args:
        token: Encoded JWT string

    Returns:
        TokenPayload with decoded claims

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.app_secret_key, algorithms=[ALGORITHM])
        return TokenPayload(
            sub=payload["sub"],
            org_id=payload["org_id"],
            role=payload.get("role", "user"),
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc) if "exp" in payload else None,
        )
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> UserContext:
    """
    FastAPI dependency: extract and verify the current user from the Authorization header.

    Usage:
        @router.get("/protected")
        async def protected(user: UserContext = Depends(get_current_user)):
            return {"user": user.user_id}
    """
    token_payload = verify_token(credentials.credentials)
    return UserContext(
        user_id=token_payload.sub,
        org_id=token_payload.org_id,
        role=token_payload.role,
    )


async def require_admin(
    user: UserContext = Depends(get_current_user),
) -> UserContext:
    """FastAPI dependency: require admin role."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
