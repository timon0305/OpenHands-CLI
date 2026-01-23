"""Tests for OAuth 2.0 Authorization Code Flow with PKCE."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands_cli.auth.authorization_code_flow import (
    AuthorizationCodeFlowClient,
    AuthorizationCodeFlowError,
    AuthorizationCodeTokenResponse,
    CallbackHandler,
    LocalCallbackServer,
    PKCECodes,
)


class TestPKCECodes:
    """Tests for PKCE code generation."""

    def test_code_verifier_length(self):
        """Test that code verifier has correct length (43 chars for 32 bytes)."""
        pkce = PKCECodes()
        # 32 bytes base64url encoded = 43 characters
        assert len(pkce.code_verifier) == 43

    def test_code_verifier_is_url_safe(self):
        """Test that code verifier only contains URL-safe characters."""
        pkce = PKCECodes()
        # URL-safe base64 characters: A-Z, a-z, 0-9, -, _
        import re

        assert re.match(r"^[A-Za-z0-9_-]+$", pkce.code_verifier)

    def test_code_challenge_is_different_from_verifier(self):
        """Test that code challenge is different from code verifier."""
        pkce = PKCECodes()
        assert pkce.code_challenge != pkce.code_verifier

    def test_code_challenge_method_is_s256(self):
        """Test that code challenge method is S256."""
        pkce = PKCECodes()
        assert pkce.code_challenge_method == "S256"

    def test_code_verifier_is_random(self):
        """Test that each instance generates different codes."""
        pkce1 = PKCECodes()
        pkce2 = PKCECodes()
        assert pkce1.code_verifier != pkce2.code_verifier
        assert pkce1.code_challenge != pkce2.code_challenge

    def test_code_challenge_is_deterministic(self):
        """Test that same verifier produces same challenge."""
        verifier = "test_verifier_12345678901234567890123"
        challenge1 = PKCECodes._generate_code_challenge(verifier)
        challenge2 = PKCECodes._generate_code_challenge(verifier)
        assert challenge1 == challenge2


class TestLocalCallbackServer:
    """Tests for the local callback server."""

    def test_find_available_port(self):
        """Test that server can find an available port."""
        server = LocalCallbackServer()
        port = server._find_available_port()
        assert port in server.PORT_RANGE

    def test_start_and_stop(self):
        """Test that server can start and stop."""
        server = LocalCallbackServer()
        event = asyncio.Event()

        callback_url = server.start(event)

        assert callback_url.startswith("http://localhost:")
        assert callback_url.endswith("/callback")
        assert server.server is not None
        assert server.thread is not None

        server.stop()

        assert server.server is None

    def test_callback_url_format(self):
        """Test that callback URL has correct format."""
        server = LocalCallbackServer()
        event = asyncio.Event()

        try:
            callback_url = server.start(event)
            assert "localhost" in callback_url
            assert "/callback" in callback_url
        finally:
            server.stop()


class TestCallbackHandler:
    """Tests for the OAuth callback handler."""

    def test_reset_state(self):
        """Test that handler state can be reset."""
        CallbackHandler.authorization_code = "test_code"
        CallbackHandler.error = "test_error"
        CallbackHandler.error_description = "test_description"
        CallbackHandler.state = "test_state"

        # Reset
        CallbackHandler.authorization_code = None
        CallbackHandler.error = None
        CallbackHandler.error_description = None
        CallbackHandler.state = None

        assert CallbackHandler.authorization_code is None
        assert CallbackHandler.error is None
        assert CallbackHandler.error_description is None
        assert CallbackHandler.state is None


class TestAuthorizationCodeFlowClient:
    """Tests for the Authorization Code Flow client."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return AuthorizationCodeFlowClient(
            server_url="https://test.openhands.ai",
            client_id="test-client",
        )

    def test_build_authorization_url(self, client):
        """Test authorization URL construction."""
        pkce = PKCECodes()
        state = "test_state_123"
        redirect_uri = "http://localhost:14550/callback"

        url = client._build_authorization_url(redirect_uri, pkce, state)

        assert "https://test.openhands.ai/oauth/authorize" in url
        assert "response_type=code" in url
        assert "client_id=test-client" in url
        assert (
            f"redirect_uri={redirect_uri.replace(':', '%3A').replace('/', '%2F')}"
            in url
        )
        assert f"state={state}" in url
        assert f"code_challenge={pkce.code_challenge}" in url
        assert "code_challenge_method=S256" in url

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_success(self, client):
        """Test successful token exchange."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        with patch.object(client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            pkce = PKCECodes()
            result = await client.exchange_code_for_token(
                authorization_code="test_code",
                redirect_uri="http://localhost:14550/callback",
                pkce=pkce,
            )

            assert result.access_token == "test_access_token"
            assert result.token_type == "Bearer"
            assert result.expires_in == 3600

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_error(self, client):
        """Test token exchange error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": "invalid_grant",
            "error_description": "Authorization code expired",
        }

        with patch.object(client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            pkce = PKCECodes()
            with pytest.raises(AuthorizationCodeFlowError) as exc_info:
                await client.exchange_code_for_token(
                    authorization_code="expired_code",
                    redirect_uri="http://localhost:14550/callback",
                    pkce=pkce,
                )

            assert "invalid_grant" in str(exc_info.value)


class TestAuthorizationCodeTokenResponse:
    """Tests for the token response model."""

    def test_minimal_response(self):
        """Test response with only required fields."""
        response = AuthorizationCodeTokenResponse(access_token="test_token")
        assert response.access_token == "test_token"
        assert response.token_type == "Bearer"
        assert response.expires_in is None
        assert response.refresh_token is None

    def test_full_response(self):
        """Test response with all fields."""
        response = AuthorizationCodeTokenResponse(
            access_token="test_token",
            token_type="Bearer",
            expires_in=3600,
            refresh_token="refresh_token",
            scope="openid profile",
        )
        assert response.access_token == "test_token"
        assert response.token_type == "Bearer"
        assert response.expires_in == 3600
        assert response.refresh_token == "refresh_token"
        assert response.scope == "openid profile"
