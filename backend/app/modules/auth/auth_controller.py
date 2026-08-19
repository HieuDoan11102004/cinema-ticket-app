import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.modules.auth.auth_repository import AuthRepository
from app.modules.auth.auth_service import AuthService
from app.modules.auth.dto.login_request import LoginRequest
from app.modules.auth.dto.message_response import MessageResponse
from app.modules.auth.dto.signup_request import SignupRequest
from app.modules.auth.dto.token_response import TokenResponse
from app.modules.auth.dto.user_response import UserResponse
from app.shared.core.config import JWT_ACCESS_TOKEN_EXPIRE, JWT_REFRESH_TOKEN_EXPIRE
from app.shared.core.security import decode_token, is_token_blocked
from app.shared.db.database import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
security_optional = HTTPBearer(auto_error=False)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(AuthRepository(db))


def _get_user_id_from_token(token: str) -> uuid.UUID:
    """Decode token and return user_id if valid."""
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


def get_current_user_id(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_optional)] = None,
) -> uuid.UUID:
    """Extract and validate the user ID from Bearer token or cookie."""
    # Try Bearer token first
    if credentials:
        return _get_user_id_from_token(credentials.credentials)

    # Fall back to cookie
    access_token = request.cookies.get("access_token")
    if access_token:
        return _get_user_id_from_token(access_token)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No authentication token provided",
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


def _set_token_cookies(response: Response, tokens: TokenResponse) -> None:
    """Set access and refresh tokens as HttpOnly cookies."""
    access_max_age = JWT_ACCESS_TOKEN_EXPIRE * 60  # Convert minutes to seconds
    refresh_max_age = JWT_REFRESH_TOKEN_EXPIRE * 60 * 60  # Convert hours to seconds

    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=access_max_age,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=refresh_max_age,
        path="/",
    )


def _clear_token_cookies(response: Response) -> None:
    """Clear access and refresh token cookies."""
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={401: {"model": MessageResponse}},
)
def login(
    login_dto: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    response: Response = None,# type: ignore[arg-type]
) -> TokenResponse:
    """Authenticate with email and password, returning tokens in HttpOnly cookies."""
    try:
        tokens = auth_service.login(login_dto)
        _set_token_cookies(response, tokens)
        return tokens
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
    response: Response,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Refresh access token using refresh token from cookie."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    try:
        tokens = auth_service.refresh_tokens(refresh_token)
        _set_token_cookies(response, tokens)
        return tokens
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
    response: Response,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Revoke the current access token and clear cookies (logout)."""
    access_token = request.cookies.get("access_token")
    if access_token:
        auth_service.revoke_access_token(access_token)

    _clear_token_cookies(response)
    return MessageResponse(detail="Successfully logged out")
