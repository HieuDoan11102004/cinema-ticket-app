import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.modules.auth.auth_repository import AuthRepository
from app.modules.auth.auth_service import AuthService
from app.modules.auth.dto.login_request import LoginRequest
from app.modules.auth.dto.message_response import MessageResponse
from app.modules.auth.dto.signup_request import SignupRequest
from app.modules.auth.dto.token_response import TokenResponse
from app.modules.auth.dto.user_response import UserResponse
from app.shared.core.security import decode_token, is_token_blocked, block_token
from app.shared.db.database import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
security = HTTPBearer()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(AuthRepository(db))


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> uuid.UUID:
    """Extract and validate the user ID from the Bearer token."""
    token = credentials.credentials
    try:
        claims = decode_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if claims.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if token has been revoked
    jti = claims.get("jti")
    if jti and is_token_blocked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": MessageResponse}},
)
def signup(
    signup_dto: SignupRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Register a new user account."""
    try:
        return auth_service.signup(signup_dto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={401: {"model": MessageResponse}},
)
def login(
    login_dto: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate with email and password, returning access + refresh tokens."""
    try:
        return auth_service.login(login_dto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={401: {"model": MessageResponse}},
)
def refresh_tokens(
    refresh_token: str,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Issue a new access + refresh token pair from a valid refresh token."""
    try:
        return auth_service.refresh_tokens(refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.get(
    "/me",
    response_model=UserResponse,
    responses={401: {"model": MessageResponse}, 404: {"model": MessageResponse}},
)
def get_current_user(
    user_id: uuid.UUID = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Return the authenticated user's profile."""
    user = auth_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.post(
    "/logout",
    response_model=MessageResponse,
    responses={401: {"model": MessageResponse}},
)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> MessageResponse:
    """Revoke the current access token (logout)."""
    token = credentials.credentials
    try:
        claims = decode_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Add token's JTI to blocklist
    jti = claims.get("jti")
    if jti:
        block_token(jti)

    return MessageResponse(detail="Successfully logged out")

