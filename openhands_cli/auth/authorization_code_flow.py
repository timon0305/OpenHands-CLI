"""OAuth 2.0 Authorization Code Flow with PKCE for OpenHands CLI.

This module implements the Authorization Code flow with PKCE (Proof Key for Code
Exchange) as specified by RFC 7636. It uses a local HTTP server to receive the
OAuth callback, which is the preferred method for ACP Registry compatibility.
"""

import asyncio
import base64
import hashlib
import secrets
import socket
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

from pydantic import BaseModel

from openhands_cli.auth.http_client import AuthHttpError, BaseHttpClient
from openhands_cli.auth.utils import _p
from openhands_cli.theme import OPENHANDS_THEME


class AuthorizationCodeFlowError(Exception):
    """Base exception for authorization code flow errors."""

    pass


class AuthorizationCodeTokenResponse(BaseModel):
    """Successful token response from the token endpoint."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    refresh_token: str | None = None
    scope: str | None = None


class PKCECodes:
    """PKCE code verifier and challenge generator."""

    def __init__(self) -> None:
        """Generate PKCE codes (code_verifier and code_challenge)."""
        # Generate a cryptographically random code_verifier (43-128 chars)
        # Using 32 bytes = 43 base64url characters
        self.code_verifier = self._generate_code_verifier()
        self.code_challenge = self._generate_code_challenge(self.code_verifier)
        self.code_challenge_method = "S256"

    @staticmethod
    def _generate_code_verifier() -> str:
        """Generate a cryptographically random code verifier.

        Returns:
            A URL-safe base64-encoded random string (43-128 characters)
        """
        # 32 bytes = 43 base64url characters after encoding
        random_bytes = secrets.token_bytes(32)
        return base64.urlsafe_b64encode(random_bytes).rstrip(b"=").decode("ascii")

    @staticmethod
    def _generate_code_challenge(code_verifier: str) -> str:
        """Generate code challenge from code verifier using S256 method.

        Args:
            code_verifier: The code verifier string

        Returns:
            Base64url-encoded SHA256 hash of the code verifier
        """
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callback."""

    # Class-level attributes to store callback data
    authorization_code: str | None = None
    error: str | None = None
    error_description: str | None = None
    state: str | None = None
    received_event: asyncio.Event | None = None

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress HTTP server logging."""
        pass

    def do_GET(self) -> None:
        """Handle GET request for OAuth callback."""
        parsed_url = urlparse(self.path)

        if parsed_url.path != "/callback":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        # Parse query parameters
        query_params = parse_qs(parsed_url.query)

        # Check for error response
        if "error" in query_params:
            CallbackHandler.error = query_params["error"][0]
            CallbackHandler.error_description = query_params.get(
                "error_description", [""]
            )[0]
            self._send_error_response()
        elif "code" in query_params:
            CallbackHandler.authorization_code = query_params["code"][0]
            CallbackHandler.state = query_params.get("state", [None])[0]
            self._send_success_response()
        else:
            CallbackHandler.error = "invalid_response"
            CallbackHandler.error_description = "No authorization code received"
            self._send_error_response()

        # Signal that we received the callback
        if CallbackHandler.received_event:
            CallbackHandler.received_event.set()

    def _send_success_response(self) -> None:
        """Send success HTML response to browser."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>OpenHands - Authentication Successful</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                                 Roboto, Oxygen, Ubuntu, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }
                .container {
                    text-align: center;
                    padding: 40px;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                }
                h1 { color: #22c55e; margin-bottom: 10px; }
                p { color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✓ Authentication Successful</h1>
                <p>You can close this window and return to the terminal.</p>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

    def _send_error_response(self) -> None:
        """Send error HTML response to browser."""
        self.send_response(400)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        error_msg = CallbackHandler.error_description or CallbackHandler.error
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OpenHands - Authentication Failed</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                                 Roboto, Oxygen, Ubuntu, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .container {{
                    text-align: center;
                    padding: 40px;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                }}
                h1 {{ color: #ef4444; margin-bottom: 10px; }}
                p {{ color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✗ Authentication Failed</h1>
                <p>{error_msg}</p>
                <p>Please close this window and try again.</p>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode())


class LocalCallbackServer:
    """Local HTTP server for receiving OAuth callbacks."""

    DEFAULT_PORT = 14550
    PORT_RANGE = range(14550, 14560)  # Try ports 14550-14559

    def __init__(self) -> None:
        """Initialize the callback server."""
        self.server: HTTPServer | None = None
        self.port: int | None = None
        self.thread: Thread | None = None

    def _find_available_port(self) -> int:
        """Find an available port in the configured range.

        Returns:
            Available port number

        Raises:
            AuthorizationCodeFlowError: If no port is available
        """
        for port in self.PORT_RANGE:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("127.0.0.1", port))
                    return port
            except OSError:
                continue
        raise AuthorizationCodeFlowError(
            f"No available port found in range {self.PORT_RANGE.start}-"
            f"{self.PORT_RANGE.stop - 1}"
        )

    def start(self, received_event: asyncio.Event) -> str:
        """Start the local callback server.

        Args:
            received_event: Event to signal when callback is received

        Returns:
            The callback URL (e.g., http://localhost:14550/callback)

        Raises:
            AuthorizationCodeFlowError: If server cannot be started
        """
        # Reset handler state
        CallbackHandler.authorization_code = None
        CallbackHandler.error = None
        CallbackHandler.error_description = None
        CallbackHandler.state = None
        CallbackHandler.received_event = received_event

        self.port = self._find_available_port()

        try:
            self.server = HTTPServer(("127.0.0.1", self.port), CallbackHandler)
            self.thread = Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            return f"http://localhost:{self.port}/callback"
        except Exception as e:
            raise AuthorizationCodeFlowError(
                f"Failed to start callback server: {e}"
            ) from e

    def stop(self) -> None:
        """Stop the callback server."""
        if self.server:
            self.server.shutdown()
            self.server = None
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None


class AuthorizationCodeFlowClient(BaseHttpClient):
    """OAuth 2.0 Authorization Code Flow client with PKCE."""

    def __init__(
        self,
        server_url: str,
        client_id: str = "openhands-cli",
        authorize_endpoint: str = "/oauth/authorize",
        token_endpoint: str = "/oauth/token",
    ):
        """Initialize the authorization code flow client.

        Args:
            server_url: Base URL of the OpenHands server
            client_id: OAuth client ID
            authorize_endpoint: OAuth authorization endpoint path
            token_endpoint: OAuth token endpoint path
        """
        super().__init__(server_url)
        self.client_id = client_id
        self.authorize_endpoint = authorize_endpoint
        self.token_endpoint = token_endpoint

    def _build_authorization_url(
        self,
        redirect_uri: str,
        pkce: PKCECodes,
        state: str,
        scope: str = "openid profile email",
    ) -> str:
        """Build the OAuth authorization URL.

        Args:
            redirect_uri: Callback URL for the authorization response
            pkce: PKCE codes for the request
            state: Random state parameter for CSRF protection
            scope: OAuth scopes to request

        Returns:
            Full authorization URL
        """
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "code_challenge": pkce.code_challenge,
            "code_challenge_method": pkce.code_challenge_method,
        }
        return f"{self.server_url}{self.authorize_endpoint}?{urlencode(params)}"

    async def exchange_code_for_token(
        self,
        authorization_code: str,
        redirect_uri: str,
        pkce: PKCECodes,
    ) -> AuthorizationCodeTokenResponse:
        """Exchange authorization code for access token.

        Args:
            authorization_code: The authorization code from the callback
            redirect_uri: The redirect URI used in the authorization request
            pkce: PKCE codes used in the authorization request

        Returns:
            Token response containing access_token

        Raises:
            AuthorizationCodeFlowError: If token exchange fails
        """
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": redirect_uri,
            "client_id": self.client_id,
            "code_verifier": pkce.code_verifier,
        }

        try:
            response = await self.post(
                self.token_endpoint,
                form_data=data,
                raise_for_status=False,
            )

            if response.status_code == 200:
                return AuthorizationCodeTokenResponse.model_validate(response.json())

            # Handle error response
            try:
                error_data = response.json()
                error = error_data.get("error", "unknown_error")
                description = error_data.get("error_description", "")
                raise AuthorizationCodeFlowError(
                    f"Token exchange failed: {error} - {description}"
                )
            except AuthorizationCodeFlowError:
                raise
            except Exception:
                raise AuthorizationCodeFlowError(
                    f"Token exchange failed with status {response.status_code}"
                )

        except AuthHttpError as e:
            raise AuthorizationCodeFlowError(
                f"Network error during token exchange: {e}"
            ) from e

    async def authenticate(
        self, timeout: float = 300.0
    ) -> AuthorizationCodeTokenResponse:
        """Complete OAuth 2.0 Authorization Code Flow with PKCE.

        Args:
            timeout: Maximum time to wait for user authorization (seconds)

        Returns:
            Token response containing access_token

        Raises:
            AuthorizationCodeFlowError: If authentication fails
        """
        _p(
            f"[{OPENHANDS_THEME.accent}]Starting OpenHands authentication "
            f"(Authorization Code Flow)...[/{OPENHANDS_THEME.accent}]"
        )

        # Generate PKCE codes and state
        pkce = PKCECodes()
        state = secrets.token_urlsafe(32)

        # Start local callback server
        callback_server = LocalCallbackServer()
        received_event = asyncio.Event()

        try:
            redirect_uri = callback_server.start(received_event)
            _p(
                f"[{OPENHANDS_THEME.secondary}]Callback server started on "
                f"{redirect_uri}[/{OPENHANDS_THEME.secondary}]"
            )

            # Build authorization URL and open browser
            auth_url = self._build_authorization_url(redirect_uri, pkce, state)

            _p(
                f"\n[{OPENHANDS_THEME.warning}]Opening your web browser for "
                f"authentication...[/{OPENHANDS_THEME.warning}]"
            )

            try:
                webbrowser.open(auth_url)
                _p(
                    f"[{OPENHANDS_THEME.success}]✓ Browser "
                    f"opened successfully[/{OPENHANDS_THEME.success}]"
                )
            except Exception as e:
                _p(
                    f"[{OPENHANDS_THEME.warning}]Could not open browser "
                    f"automatically: {e}[/{OPENHANDS_THEME.warning}]"
                )
                _p(
                    f"[{OPENHANDS_THEME.secondary}]Please manually open: "
                    f"[bold]{auth_url}[/bold][/{OPENHANDS_THEME.secondary}]"
                )

            _p(
                f"[{OPENHANDS_THEME.secondary}]Follow the instructions in your "
                f"browser to complete authentication[/{OPENHANDS_THEME.secondary}]"
            )
            _p(
                f"\n[{OPENHANDS_THEME.accent}]Waiting for authentication to "
                f"complete...[/{OPENHANDS_THEME.accent}]"
            )

            # Wait for callback with timeout
            try:
                await asyncio.wait_for(received_event.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                raise AuthorizationCodeFlowError(
                    "Timeout waiting for user authorization. Please try again."
                )

            # Check for errors
            if CallbackHandler.error:
                error_msg = (
                    CallbackHandler.error_description or CallbackHandler.error
                )
                raise AuthorizationCodeFlowError(f"Authorization failed: {error_msg}")

            # Verify state parameter
            if CallbackHandler.state != state:
                raise AuthorizationCodeFlowError(
                    "State mismatch - possible CSRF attack"
                )

            # Get authorization code
            authorization_code = CallbackHandler.authorization_code
            if not authorization_code:
                raise AuthorizationCodeFlowError("No authorization code received")

            # Exchange code for token
            _p(
                f"[{OPENHANDS_THEME.secondary}]Exchanging authorization code "
                f"for token...[/{OPENHANDS_THEME.secondary}]"
            )

            token_response = await self.exchange_code_for_token(
                authorization_code, redirect_uri, pkce
            )

            _p(
                f"[{OPENHANDS_THEME.success}]✓ Authentication "
                f"successful![/{OPENHANDS_THEME.success}]"
            )

            return token_response

        finally:
            callback_server.stop()


async def authenticate_with_authorization_code_flow(
    server_url: str,
    client_id: str = "openhands-cli",
) -> AuthorizationCodeTokenResponse:
    """Convenience function to authenticate using Authorization Code Flow with PKCE.

    Args:
        server_url: OpenHands server URL
        client_id: OAuth client ID

    Returns:
        Token response containing access_token

    Raises:
        AuthorizationCodeFlowError: If authentication fails
    """
    client = AuthorizationCodeFlowClient(server_url, client_id)
    return await client.authenticate()
