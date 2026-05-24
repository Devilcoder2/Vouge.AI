"""
Authentication API — POST /v1/auth/*

Endpoints:
  POST /v1/auth/signup   — Create new account
  POST /v1/auth/login    — Authenticate user
  POST /v1/auth/refresh  — Rotate refresh token
  POST /v1/auth/logout   — Revoke session
"""
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import uuid4

from app.auth.security import (
    create_access_token,
    create_refresh_token,
    get_token_hash,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.auth.dependencies import get_current_active_user
from app.config import settings
from app.database.models import RefreshToken, User, UserSession
from app.database.session import get_db
from app.schemas.auth import (
    AuthSuccessResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    SignupRequest,
    TokenPayload,
    UserResponse,
)

logger = logging.getLogger("fashion-ai-service")
router = APIRouter(prefix="/v1/auth", tags=["Authentication"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_token_response(user: User) -> dict:
    """Creates a fresh access + refresh token pair for a user."""
    access_token = create_access_token(str(user.id), user.email)
    raw_refresh, refresh_hash = create_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return {
        "access_token": access_token,
        "raw_refresh": raw_refresh,
        "refresh_hash": refresh_hash,
        "expires_at": expires_at,
    }


async def _persist_refresh_token(
    db: AsyncSession,
    user_id,
    refresh_hash: str,
    expires_at: datetime,
    request: Request = None,
) -> RefreshToken:
    """Saves a new refresh token record to the database."""
    device_name = None
    ip_address = None
    if request:
        user_agent = request.headers.get("User-Agent", "")
        device_name = user_agent[:200] if user_agent else None
        ip_address = request.client.host if request.client else None

    token_row = RefreshToken(
        id=uuid4(),
        user_id=user_id,
        token_hash=refresh_hash,
        device_name=device_name,
        ip_address=ip_address,
        expires_at=expires_at,
        revoked=False,
    )
    db.add(token_row)
    return token_row


async def _upsert_session(db: AsyncSession, user_id, request: Request = None) -> None:
    """Creates or refreshes the user session record."""
    device_info = None
    if request:
        device_info = request.headers.get("User-Agent", "")[:500]

    session_row = UserSession(
        id=uuid4(),
        user_id=user_id,
        device_info=device_info,
    )
    db.add(session_row)


def _token_payload_response(tokens: dict) -> TokenPayload:
    return TokenPayload(
        access_token=tokens["access_token"],
        refresh_token=tokens["raw_refresh"],
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ── POST /v1/auth/signup ──────────────────────────────────────────────────────

@router.post("/signup", response_model=AuthSuccessResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Creates a new Vouge.AI user account.

    - Validates email uniqueness and username uniqueness
    - Enforces password strength rules
    - Returns a JWT access token and refresh token on success
    """
    # Password strength check (raises ValueError → 422 via Pydantic, but we check here for custom 400)
    try:
        validate_password_strength(payload.password)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    # Check email uniqueness
    email_result = await db.execute(select(User).where(User.email == payload.email.lower()))
    if email_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{payload.email}' already exists.",
        )

    # Check username uniqueness
    username_result = await db.execute(select(User).where(User.username == payload.username.lower()))
    if username_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{payload.username}' is already taken.",
        )

    # Create user
    user = User(
        id=uuid4(),
        email=payload.email.lower(),
        username=payload.username.lower(),
        hashed_password=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        gender=payload.gender,
        style_personas=[],
        avoided_colors=[],
    )
    db.add(user)
    await db.flush()  # Get user.id before commit

    # Generate tokens
    tokens = _build_token_response(user)
    await _persist_refresh_token(db, user.id, tokens["refresh_hash"], tokens["expires_at"], request)
    await _upsert_session(db, user.id, request)
    await db.commit()
    await db.refresh(user)

    logger.info(f"New user registered: {user.email} (ID: {user.id})")

    return AuthSuccessResponse(
        success=True,
        data={
            "user": UserResponse.model_validate(user).model_dump(),
            **_token_payload_response(tokens).model_dump(),
        },
    )


# ── POST /v1/auth/login ───────────────────────────────────────────────────────

@router.post("/login", response_model=AuthSuccessResponse, status_code=status.HTTP_200_OK)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticates a user by email and password.

    - Returns a JWT access token and a new refresh token
    - Creates a session record for the device
    """
    _invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
    )

    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise _invalid

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated.")

    # Issue fresh token pair
    tokens = _build_token_response(user)
    await _persist_refresh_token(db, user.id, tokens["refresh_hash"], tokens["expires_at"], request)
    await _upsert_session(db, user.id, request)
    await db.commit()
    await db.refresh(user)

    logger.info(f"User logged in: {user.email} (ID: {user.id})")

    return AuthSuccessResponse(
        success=True,
        data={
            "user": UserResponse.model_validate(user).model_dump(),
            **_token_payload_response(tokens).model_dump(),
        },
    )


# ── POST /v1/auth/refresh ─────────────────────────────────────────────────────

@router.post("/refresh", response_model=AuthSuccessResponse, status_code=status.HTTP_200_OK)
async def refresh_tokens(
    payload: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Rotates a refresh token.

    - Validates the incoming refresh token (not revoked, not expired)
    - Revokes the old refresh token immediately (rotation prevents reuse)
    - Issues a new access token + new refresh token pair
    """
    token_hash = get_token_hash(payload.refresh_token)

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    token_row = result.scalar_one_or_none()

    _invalid_refresh = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token.",
    )

    if not token_row:
        raise _invalid_refresh
    if token_row.revoked:
        # Token reuse detected — revoke all tokens for this user as a security measure
        await db.execute(
            select(RefreshToken).where(RefreshToken.user_id == token_row.user_id)
        )
        logger.warning(f"Refresh token reuse detected for user_id={token_row.user_id}. Revoking all tokens.")
        raise _invalid_refresh
    if token_row.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise _invalid_refresh

    # Revoke old token
    token_row.revoked = True

    # Fetch user
    user_result = await db.execute(select(User).where(User.id == token_row.user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise _invalid_refresh

    # Issue new token pair
    tokens = _build_token_response(user)
    await _persist_refresh_token(db, user.id, tokens["refresh_hash"], tokens["expires_at"], request)
    await db.commit()
    await db.refresh(user)

    logger.info(f"Token refreshed for user: {user.email} (ID: {user.id})")

    return AuthSuccessResponse(
        success=True,
        data={
            "user": UserResponse.model_validate(user).model_dump(),
            **_token_payload_response(tokens).model_dump(),
        },
    )


# ── POST /v1/auth/logout ──────────────────────────────────────────────────────

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    payload: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Logs out the authenticated user by revoking their refresh token.

    Requires a valid Bearer JWT in the Authorization header.
    """
    token_hash = get_token_hash(payload.refresh_token)

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == current_user.id,
        )
    )
    token_row = result.scalar_one_or_none()

    if token_row and not token_row.revoked:
        token_row.revoked = True
        await db.commit()

    logger.info(f"User logged out: {current_user.email} (ID: {current_user.id})")

    return {"success": True, "message": "Successfully logged out."}
