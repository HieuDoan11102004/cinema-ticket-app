import uuid

from app.models.user import User
from app.modules.auth.auth_repository import AuthRepository
from app.modules.auth.dto.login_request import LoginRequest
from app.modules.auth.dto.signup_request import SignupRequest
from app.modules.auth.dto.token_response import TokenResponse
from app.modules.auth.dto.user_response import UserResponse
from app.shared.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)


class AuthService:
    def __init__(self, auth_repository: AuthRepository):
        self._auth_repo = auth_repository

    def signup(self, signup_dto: SignupRequest) -> UserResponse:
        """Create a new user account."""
        # Check if email already exists
        if self._auth_repo.exists_by_email(signup_dto.email):
            raise ValueError("Email already registered")

        # Hash password
        password_hash = hash_password(signup_dto.password)

        # Create user model
        user = User(
            first_name=signup_dto.first_name,
            last_name=signup_dto.last_name,
            email=signup_dto.email,
            password_hash=password_hash,  # type: ignore[assignment]
            address=signup_dto.address or None,
            phone_number=signup_dto.phone_number,
            birth_date=signup_dto.birth_date,
        )

        # Save to database
        created_user = self._auth_repo.create(user)

        # Return user response
        return UserResponse.model_validate(created_user)

    def login(self, login_dto: LoginRequest) -> TokenResponse:
        """Authenticate user and return tokens."""
        # Find user by email
        user = self._auth_repo.get_by_email(login_dto.email)
        if user is None:
            raise ValueError("Invalid email or password")

        # Verify password
        if not verify_password(login_dto.password, user.password_hash):  # type: ignore[arg-type]
            raise ValueError("Invalid email or password")

        # Generate tokens
        user_id_str = str(user.id)
        access_token = create_access_token(user_id_str)
        refresh_token = create_refresh_token(user_id_str)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token."""
        from app.shared.core.security import decode_token

        # Decode and validate refresh token
        claims = decode_token(refresh_token)

        # Verify token type
        if claims.get("type") != "refresh":
            raise ValueError("Invalid token type")

        # Get user ID from token
        user_id = claims.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload")

        # Verify user exists
        user = self._auth_repo.get_by_id(uuid.UUID(user_id))
        if user is None:
            raise ValueError("User not found")

        # Generate new tokens
        access_token = create_access_token(user_id)
        new_refresh_token = create_refresh_token(user_id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
        )

    def get_user_by_id(self, user_id: uuid.UUID) -> UserResponse | None:
        """Get user by ID."""
        user = self._auth_repo.get_by_id(user_id)
        if user is None:
            return None
        return UserResponse.model_validate(user)
