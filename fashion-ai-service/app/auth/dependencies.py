"""FastAPI auth dependencies — extracts and validates JWT from incoming requests."""
import logging
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.auth.security import decode_access_token
from app.database.models import User
from app.database.session import get_db

logger = logging.getLogger("fashion-ai-service")

# Bearer token extractor — reads Authorization: Bearer <token> header
bearer_scheme = HTTPBearer(auto_error=False)

_401 = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated. Provide a valid Bearer token.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency that:
    1. Extracts the Bearer JWT from the Authorization header
    2. Decodes and validates its signature + expiry
    3. Fetches the corresponding User from PostgreSQL
    4. Raises HTTP 401 on any failure
    """
    if not credentials:
        raise _401

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired. Use /v1/auth/refresh to get a new one.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise _401

    user_id: str = payload.get("sub")
    if not user_id:
        raise _401

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise _401

    return user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """
    Extends get_current_user by additionally checking the user's active status.
    Raises HTTP 403 if the account has been deactivated.
    """
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )
    return user
