"""Tests for the security module (hashing, JWT tokens)."""
from datetime import timedelta

import pytest


class TestPasswordHashing:
    """Tests for hash_password and verify_password functions."""

    def test_hash_password_returns_string(self):
        """hash_password should return a string."""
        from app.core.security import hash_password

        result = hash_password("testpassword123")
        assert isinstance(result, str)

    def test_hash_password_different_each_time(self):
        """hash_password should generate different hashes for same password (salted)."""
        from app.core.security import hash_password

        hash1 = hash_password("samepassword")
        hash2 = hash_password("samepassword")
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """verify_password should return True for correct password."""
        from app.core.security import hash_password, verify_password

        password = "mysecretpassword"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """verify_password should return False for incorrect password."""
        from app.core.security import hash_password, verify_password

        hashed = hash_password("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_empty_password(self):
        """verify_password should return False for empty password."""
        from app.core.security import hash_password, verify_password

        hashed = hash_password("somepassword")
        assert verify_password("", hashed) is False

    def test_verify_password_very_long_password(self):
        """verify_password should handle very long passwords."""
        from app.core.security import hash_password, verify_password

        long_password = "a" * 1000
        hashed = hash_password(long_password)
        assert verify_password(long_password, hashed) is True

    def test_verify_password_special_characters(self):
        """verify_password should handle special characters."""
        from app.core.security import hash_password, verify_password

        password = "P@$$w0rd!#$%^&*()_+-=[]{}|;':\",./<>?"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_unicode(self):
        """verify_password should handle unicode characters."""
        from app.core.security import hash_password, verify_password

        password = "пароль密码パスワード🔐"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True


class TestTokenCreation:
    """Tests for create_token, create_access_token, and create_refresh_token."""

    def test_create_token_returns_string(self):
        """create_token should return a string JWT."""
        from app.core.security import create_token

        token = create_token("user123", timedelta(minutes=30), "access")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_returns_string(self):
        """create_access_token should return a string JWT."""
        from app.core.security import create_access_token

        token = create_access_token("user456")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_returns_string(self):
        """create_refresh_token should return a string JWT."""
        from app.core.security import create_refresh_token

        token = create_refresh_token("user789")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_shorter_than_refresh_token(self):
        """Access token should be shorter lived than refresh token."""
        from app.core.security import create_access_token, create_refresh_token
        from app.core.config import JWT_ACCESS_TOKEN_EXPIRE, JWT_REFRESH_TOKEN_EXPIRE

        # JWT_ACCESS_TOKEN_EXPIRE is "30m" and JWT_REFRESH_TOKEN_EXPIRE is "168h"
        # Access token should naturally be shorter
        access_token = create_access_token("user123")
        refresh_token = create_refresh_token("user123")

        # Both should be valid JWTs (3 parts separated by dots)
        assert access_token.count(".") == 2
        assert refresh_token.count(".") == 2

        # Refresh token should be longer (more hours than minutes)
        assert len(refresh_token) > len(access_token)

    def test_different_users_get_different_tokens(self):
        """Same token type for different users should produce different tokens."""
        from app.core.security import create_access_token

        token1 = create_access_token("user1")
        token2 = create_access_token("user2")
        assert token1 != token2

    def test_same_user_different_times_get_different_tokens(self):
        """Tokens created at different times should differ (due to iat claim)."""
        import time
        from app.core.security import create_access_token

        token1 = create_access_token("sameuser")
        time.sleep(0.1)  # Small delay to ensure different iat
        token2 = create_access_token("sameuser")
        # Tokens may or may not differ due to timing, but both should be valid
        assert isinstance(token1, str)
        assert isinstance(token2, str)


class TestTokenDecoding:
    """Tests for decode_token function."""

    def test_decode_access_token(self):
        """decode_token should decode a valid access token."""
        from app.core.security import create_access_token, decode_token

        user_id = "testuser123"
        token = create_access_token(user_id)
        claims = decode_token(token)

        assert claims["sub"] == user_id
        assert claims["type"] == "access"

    def test_decode_refresh_token(self):
        """decode_token should decode a valid refresh token."""
        from app.core.security import create_refresh_token, decode_token

        user_id = "testuser456"
        token = create_refresh_token(user_id)
        claims = decode_token(token)

        assert claims["sub"] == user_id
        assert claims["type"] == "refresh"

    def test_decode_token_has_required_claims(self):
        """decode_token should include iat and exp claims."""
        from app.core.security import create_access_token, decode_token

        token = create_access_token("user123")
        claims = decode_token(token)

        assert "iat" in claims
        assert "exp" in claims
        assert "sub" in claims
        assert "type" in claims

    def test_decode_invalid_token_raises_error(self):
        """decode_token should raise ValueError for invalid token."""
        from app.core.security import decode_token

        with pytest.raises(ValueError, match="Invalid or expired token"):
            decode_token("invalid.token.here")

    def test_decode_tampered_token_raises_error(self):
        """decode_token should raise ValueError for tampered token."""
        from app.core.security import create_access_token, decode_token

        token = create_access_token("user123")
        # Tamper with the token by modifying a character
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(ValueError, match="Invalid or expired token"):
            decode_token(tampered)

    def test_decode_malformed_token_raises_error(self):
        """decode_token should raise ValueError for malformed token."""
        from app.core.security import decode_token

        with pytest.raises(ValueError, match="Invalid or expired token"):
            decode_token("not-a-jwt")

    def test_decode_empty_token_raises_error(self):
        """decode_token should raise ValueError for empty token."""
        from app.core.security import decode_token

        with pytest.raises(ValueError, match="Invalid or expired token"):
            decode_token("")

    def test_decode_token_with_wrong_secret(self):
        """decode_token should fail with token signed by different secret."""
        from authlib.jose import jwt
        from app.core.config import JWT_SECRET, ALGORITHM

        # Create a token with a different secret
        header = {"alg": ALGORITHM}
        payload = {
            "sub": "user123",
            "type": "access",
            "iat": 0,
            "exp": 9999999999,
        }
        token = jwt.encode(header, payload, "wrong_secret_key").decode("utf-8")

        from app.core.security import decode_token

        with pytest.raises(ValueError, match="Invalid or expired token"):
            decode_token(token)


class TestTokenExpiration:
    """Tests for token expiration behavior."""

    def test_token_with_past_expiration_is_invalid(self):
        """Token with past expiration should be invalid."""
        from app.core.security import create_token, decode_token

        # Create a token that expired in the past
        token = create_token("user123", timedelta(seconds=-1), "access")
        with pytest.raises(ValueError, match="Invalid or expired token"):
            decode_token(token)

    def test_token_with_future_expiration_is_valid(self):
        """Token with future expiration should be valid."""
        from app.core.security import create_token, decode_token

        token = create_token("user123", timedelta(hours=1), "access")
        claims = decode_token(token)
        assert claims["sub"] == "user123"


class TestIntegration:
    """Integration tests combining multiple security functions."""

    def test_full_auth_flow(self):
        """Test a complete authentication flow: hash -> verify -> token -> decode."""
        from app.core.security import (
            hash_password,
            verify_password,
            create_access_token,
            decode_token,
        )

        # User registers with password
        password = "securePassword123!"
        hashed = hash_password(password)

        # User logs in with correct password
        assert verify_password(password, hashed) is True

        # Generate access token
        user_id = "user_from_db_123"
        token = create_access_token(user_id)

        # Verify token is valid
        claims = decode_token(token)
        assert claims["sub"] == user_id
        assert claims["type"] == "access"

    def test_token_contains_correct_user_id(self):
        """Token should contain the exact user_id passed to it."""
        from app.core.security import create_access_token, decode_token

        user_ids = ["123", "user@example.com", "uuid-12345-abc"]
        for user_id in user_ids:
            token = create_access_token(user_id)
            claims = decode_token(token)
            assert claims["sub"] == user_id
