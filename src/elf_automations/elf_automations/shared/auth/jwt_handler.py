"""
JWT handling for WebSocket authentication in team chat interface.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

logger = logging.getLogger(__name__)


class JWTHandler:
    """Handle JWT token creation and validation for WebSocket connections."""

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        token_expiry_hours: int = 24,
    ):
        """
        Initialize JWT handler.

        Args:
            secret_key: Secret key for signing tokens. If None, uses JWT_SECRET_KEY env var.
            algorithm: JWT signing algorithm
            token_expiry_hours: Token validity period in hours
        """
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY")
        if not self.secret_key:
            raise ValueError("JWT_SECRET_KEY not provided or found in environment")

        self.algorithm = algorithm
        self.token_expiry_hours = token_expiry_hours

    def create_token(
        self,
        user_id: str,
        team_id: Optional[str] = None,
        session_id: Optional[str] = None,
        roles: Optional[list] = None,
        **extra_claims,
    ) -> str:
        """
        Create a JWT token for WebSocket authentication.

        Args:
            user_id: User identifier
            team_id: Team identifier for chat session
            session_id: Chat session identifier
            roles: User roles/permissions
            **extra_claims: Additional claims to include in token

        Returns:
            Encoded JWT token
        """
        now = datetime.utcnow()
        expiry = now + timedelta(hours=self.token_expiry_hours)

        payload = {
            "user_id": user_id,
            "team_id": team_id,
            "session_id": session_id,
            "roles": roles or ["user"],
            "iat": now,
            "exp": expiry,
            "type": "websocket_auth",
            **extra_claims,
        }

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.debug(f"Created JWT token for user {user_id}")

        return token

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token to verify

        Returns:
            Decoded token payload

        Raises:
            InvalidTokenError: If token is invalid
            ExpiredSignatureError: If token has expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Verify it's a WebSocket auth token
            if payload.get("type") != "websocket_auth":
                raise InvalidTokenError("Invalid token type")

            logger.debug(f"Verified token for user {payload.get('user_id')}")
            return payload

        except ExpiredSignatureError:
            logger.warning("Token has expired")
            raise
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise

    def create_session_token(
        self,
        user_id: str,
        team_id: str,
        session_id: str,
        chat_config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a token specifically for a chat session.

        Args:
            user_id: User identifier
            team_id: Team to chat with
            session_id: Unique session identifier
            chat_config: Chat configuration from team

        Returns:
            Encoded JWT token for the session
        """
        # Extract allowed roles from chat config
        allowed_roles = []
        if chat_config:
            allowed_roles = chat_config.get("allowed_roles", ["user"])

        return self.create_token(
            user_id=user_id,
            team_id=team_id,
            session_id=session_id,
            roles=allowed_roles,
            chat_enabled=True,
        )

    def validate_session_access(
        self,
        token_payload: Dict[str, Any],
        team_id: str,
        session_id: Optional[str] = None,
    ) -> bool:
        """
        Validate that a token grants access to a specific team/session.

        Args:
            token_payload: Decoded JWT payload
            team_id: Team ID to validate access for
            session_id: Optional session ID to validate

        Returns:
            True if access is allowed
        """
        # Check team access
        token_team = token_payload.get("team_id")
        if token_team and token_team != team_id:
            logger.warning(
                f"Team mismatch: token has {token_team}, requested {team_id}"
            )
            return False

        # Check session access if provided
        if session_id:
            token_session = token_payload.get("session_id")
            if token_session and token_session != session_id:
                logger.warning(
                    f"Session mismatch: token has {token_session}, requested {session_id}"
                )
                return False

        # Check if chat is enabled
        if not token_payload.get("chat_enabled", False):
            logger.warning("Token does not have chat enabled")
            return False

        return True

    def extract_bearer_token(self, auth_header: str) -> Optional[str]:
        """
        Extract token from Authorization header.

        Args:
            auth_header: Authorization header value

        Returns:
            Token if found, None otherwise
        """
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]

        return None


class WebSocketAuthMiddleware:
    """Middleware for WebSocket JWT authentication."""

    def __init__(self, jwt_handler: JWTHandler):
        """
        Initialize middleware.

        Args:
            jwt_handler: JWT handler instance
        """
        self.jwt_handler = jwt_handler

    async def __call__(self, websocket, receive, send):
        """
        WebSocket middleware to validate JWT tokens.

        This should be used with FastAPI WebSocket endpoints.
        """
        # Extract token from query params or headers
        token = None

        # Try query parameters first (common for WebSocket)
        if hasattr(websocket, "query_params"):
            token = websocket.query_params.get("token")

        # Try Authorization header if no query param
        if not token and hasattr(websocket, "headers"):
            auth_header = websocket.headers.get("authorization", "")
            token = self.jwt_handler.extract_bearer_token(auth_header)

        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return

        try:
            # Verify token
            payload = self.jwt_handler.verify_token(token)

            # Attach user info to WebSocket for use in endpoint
            websocket.state.user_id = payload.get("user_id")
            websocket.state.team_id = payload.get("team_id")
            websocket.state.session_id = payload.get("session_id")
            websocket.state.roles = payload.get("roles", [])
            websocket.state.jwt_payload = payload

            # Continue to the WebSocket endpoint
            await websocket.app(websocket, receive, send)

        except (InvalidTokenError, ExpiredSignatureError) as e:
            await websocket.close(code=1008, reason=f"Invalid token: {str(e)}")
            return


# Utility functions for FastAPI integration
def get_jwt_handler(secret_key: Optional[str] = None, **kwargs) -> JWTHandler:
    """
    Get a configured JWT handler instance.

    Args:
        secret_key: Optional secret key override
        **kwargs: Additional arguments for JWTHandler

    Returns:
        Configured JWTHandler instance
    """
    return JWTHandler(secret_key=secret_key, **kwargs)


def require_websocket_auth(jwt_handler: Optional[JWTHandler] = None):
    """
    Decorator for FastAPI WebSocket endpoints requiring authentication.

    Usage:
        @app.websocket("/chat")
        @require_websocket_auth()
        async def chat_endpoint(websocket: WebSocket):
            user_id = websocket.state.user_id
            # ... rest of endpoint
    """
    handler = jwt_handler or get_jwt_handler()

    def decorator(func):
        async def wrapper(websocket, *args, **kwargs):
            # Extract and verify token
            token = websocket.query_params.get("token")
            if not token:
                auth_header = websocket.headers.get("authorization", "")
                token = handler.extract_bearer_token(auth_header)

            if not token:
                await websocket.close(code=1008, reason="Missing authentication token")
                return

            try:
                payload = handler.verify_token(token)

                # Attach user info to WebSocket
                websocket.state.user_id = payload.get("user_id")
                websocket.state.team_id = payload.get("team_id")
                websocket.state.session_id = payload.get("session_id")
                websocket.state.roles = payload.get("roles", [])
                websocket.state.jwt_payload = payload

                # Call the actual endpoint
                return await func(websocket, *args, **kwargs)

            except Exception as e:
                await websocket.close(
                    code=1008, reason=f"Authentication failed: {str(e)}"
                )
                return

        return wrapper

    return decorator
