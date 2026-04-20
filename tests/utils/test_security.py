from unittest.mock import patch

import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from utils.security import validate_bearer_token


class TestValidateBearerToken:
    """Test suite for the validate_bearer_token function."""

    @pytest.mark.anyio
    async def test_validate_bearer_token_valid_token(self):
        """Test validation with a valid bearer token."""
        valid_creds = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="test_token"
        )

        with patch("utils.security.BEARER_TOKEN", "test_token"):
            # Should not raise any exception
            await validate_bearer_token(valid_creds)

    @pytest.mark.anyio
    async def test_validate_bearer_token_invalid_token(self):
        """Test validation with an invalid token."""
        invalid_creds = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="wrong_token"
        )

        with patch("utils.security.BEARER_TOKEN", "test_token"):
            with pytest.raises(HTTPException) as exc_info:
                await validate_bearer_token(invalid_creds)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "invalide" in exc_info.value.detail.lower()

    @pytest.mark.anyio
    async def test_validate_bearer_token_whitespace_vs_empty(self):
        """Test difference between empty token and whitespace-only token."""
        whitespace_only = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="   "
        )

        with patch("utils.security.BEARER_TOKEN", "test_token"):
            with pytest.raises(HTTPException) as exc_info:
                await validate_bearer_token(whitespace_only)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_validate_bearer_token_invalid_scheme(self):
        """Test validation with invalid authentication scheme."""
        invalid_scheme_creds = HTTPAuthorizationCredentials(
            scheme="Basic", credentials="test_token"
        )

        with patch("utils.security.BEARER_TOKEN", "test_token"):
            with pytest.raises(HTTPException) as exc_info:
                await validate_bearer_token(invalid_scheme_creds)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "schéma" in exc_info.value.detail.lower()

    @pytest.mark.anyio
    async def test_validate_bearer_token_lowercase_bearer_scheme(self):
        """Test validation with lowercase 'bearer' scheme."""
        lowercase_creds = HTTPAuthorizationCredentials(
            scheme="bearer", credentials="test_token"
        )

        with patch("utils.security.BEARER_TOKEN", "test_token"):
            # Should not raise any exception (scheme is case-insensitive)
            await validate_bearer_token(lowercase_creds)

    @pytest.mark.anyio
    async def test_validate_bearer_token_mixed_case_bearer_scheme(self):
        """Test validation with mixed case 'BeArEr' scheme."""
        mixed_case_creds = HTTPAuthorizationCredentials(
            scheme="BeArEr", credentials="test_token"
        )

        with patch("utils.security.BEARER_TOKEN", "test_token"):
            # Should not raise any exception (scheme is case-insensitive)
            await validate_bearer_token(mixed_case_creds)

    @pytest.mark.anyio
    async def test_validate_bearer_token_empty_token(self):
        """Test validation with an empty token string."""
        empty_token_creds = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=""
        )

        with patch("utils.security.BEARER_TOKEN", "test_token"):
            with pytest.raises(HTTPException) as exc_info:
                await validate_bearer_token(empty_token_creds)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_validate_bearer_token_token_with_spaces(self):
        """Test validation with token containing spaces."""
        space_token_creds = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="test token with spaces"
        )

        with patch("utils.security.BEARER_TOKEN", "test_token"):
            with pytest.raises(HTTPException) as exc_info:
                await validate_bearer_token(space_token_creds)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_validate_bearer_token_token_case_sensitive(self):
        """Test that token validation is case-sensitive."""
        uppercase_token_creds = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="TEST_TOKEN"
        )

        with patch("utils.security.BEARER_TOKEN", "test_token"):
            with pytest.raises(HTTPException) as exc_info:
                await validate_bearer_token(uppercase_token_creds)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_validate_bearer_token_long_token(self):
        """Test validation with a very long token."""
        long_token = "a" * 1000
        long_token_creds = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=long_token
        )

        with patch("utils.security.BEARER_TOKEN", long_token):
            # Should not raise any exception
            await validate_bearer_token(long_token_creds)

    @pytest.mark.anyio
    async def test_validate_bearer_token_special_characters(self):
        """Test validation with token containing special characters."""
        special_token = "test!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        special_creds = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=special_token
        )

        with patch("utils.security.BEARER_TOKEN", special_token):
            # Should not raise any exception
            await validate_bearer_token(special_creds)

    @pytest.mark.anyio
    async def test_validate_bearer_token_unicode_characters(self):
        """Test validation with token containing unicode characters."""
        unicode_token = "test_токен_🔐"
        unicode_creds = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=unicode_token
        )

        with patch("utils.security.BEARER_TOKEN", unicode_token):
            # Should not raise any exception
            await validate_bearer_token(unicode_creds)

    @pytest.mark.anyio
    async def test_validate_bearer_token_only_whitespace(self):
        """Test validation with token containing only whitespace."""
        whitespace_creds = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="   "
        )

        with patch("utils.security.BEARER_TOKEN", "test_token"):
            with pytest.raises(HTTPException) as exc_info:
                await validate_bearer_token(whitespace_creds)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_validate_bearer_token_other_schemes(self):
        """Test validation with other authentication schemes."""
        schemes = ["Basic", "Digest", "OAuth", "Custom", "ApiKey"]

        with patch("utils.security.BEARER_TOKEN", "test_token"):
            for scheme in schemes:
                invalid_scheme_creds = HTTPAuthorizationCredentials(
                    scheme=scheme, credentials="test_token"
                )

                with pytest.raises(HTTPException) as exc_info:
                    await validate_bearer_token(invalid_scheme_creds)

                assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
                assert "schéma" in exc_info.value.detail.lower()

    @pytest.mark.anyio
    async def test_validate_bearer_token_jwt_like_token(self):
        """Test validation with a JWT-like token."""
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        jwt_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=jwt_token)

        with patch("utils.security.BEARER_TOKEN", jwt_token):
            # Should not raise any exception
            await validate_bearer_token(jwt_creds)

    @pytest.mark.anyio
    async def test_validate_bearer_token_uuid_like_token(self):
        """Test validation with a UUID-like token."""
        uuid_token = "550e8400-e29b-41d4-a716-446655440000"
        uuid_creds = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=uuid_token
        )

        with patch("utils.security.BEARER_TOKEN", uuid_token):
            # Should not raise any exception
            await validate_bearer_token(uuid_creds)

    @pytest.mark.anyio
    async def test_validate_bearer_token_http_exception_details(self):
        """Test that HTTPException contains appropriate French error messages."""
        invalid_creds = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="wrong_token"
        )

        with patch("utils.security.BEARER_TOKEN", "test_token"):
            with pytest.raises(HTTPException) as exc_info:
                await validate_bearer_token(invalid_creds)

            # Check that the detail message is in French
            assert "Jeton d'authentification invalide" in exc_info.value.detail

    @pytest.mark.anyio
    async def test_validate_bearer_token_similar_tokens(self):
        """Test that similar but different tokens are rejected."""
        almost_right = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="test_token_similar"
        )

        with patch("utils.security.BEARER_TOKEN", "test_token"):
            with pytest.raises(HTTPException) as exc_info:
                await validate_bearer_token(almost_right)

            # Check that the detail message indicates invalid token
            assert "invalide" in exc_info.value.detail.lower()

    @pytest.mark.anyio
    async def test_validate_bearer_token_scheme_exception_details(self):
        """Test HTTPException message for invalid scheme."""
        invalid_scheme_creds = HTTPAuthorizationCredentials(
            scheme="Basic", credentials="test_token"
        )

        with patch("utils.security.BEARER_TOKEN", "test_token"):
            with pytest.raises(HTTPException) as exc_info:
                await validate_bearer_token(invalid_scheme_creds)

            # Check that the detail message mentions Bearer in French
            assert "Bearer" in exc_info.value.detail
            assert "schéma" in exc_info.value.detail.lower()

    @pytest.mark.anyio
    async def test_validate_bearer_token_returns_none(self):
        """Test that successful validation returns None."""
        valid_creds = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="test_token"
        )

        with patch("utils.security.BEARER_TOKEN", "test_token"):
            result = await validate_bearer_token(valid_creds)
            assert result is None

    @pytest.mark.anyio
    async def test_validate_bearer_token_with_bearer_prefix_in_token(self):
        """Test that 'Bearer' prefix in token itself doesn't cause issues."""
        # This tests that we don't double-parse bearer prefixes
        token_with_bearer = "Bearer test_token"
        creds = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token_with_bearer
        )

        with patch("utils.security.BEARER_TOKEN", token_with_bearer):
            # Should not raise any exception
            await validate_bearer_token(creds)

    @pytest.mark.anyio
    async def test_validate_bearer_token_with_newlines(self):
        """Test validation with token containing newlines."""
        token_with_newlines = "test\ntoken\nvalue"
        creds = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token_with_newlines
        )

        with patch("utils.security.BEARER_TOKEN", "different_token"):
            with pytest.raises(HTTPException) as exc_info:
                await validate_bearer_token(creds)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_validate_bearer_token_is_async(self):
        """Test that validate_bearer_token is an async function."""
        import inspect

        assert inspect.iscoroutinefunction(validate_bearer_token)
