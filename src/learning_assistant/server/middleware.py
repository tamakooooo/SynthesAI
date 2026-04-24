"""
API Key authentication middleware for SynthesAI Server.
"""

from fastapi import Request, HTTPException
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware

from loguru import logger

from learning_assistant.server.config import ServerConfig, get_api_key


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API key authentication.

    Validates X-API-Key header against configured API key.
    """

    def __init__(self, app, config: ServerConfig):
        super().__init__(app)
        self.config = config
        self.api_key = get_api_key(config)
        self.whitelist = set(config.auth.whitelist_paths)

    async def dispatch(self, request: Request, call_next):
        # Skip authentication for whitelisted paths
        if request.url.path in self.whitelist:
            return await call_next(request)

        # If auth disabled, skip
        if not self.config.auth.enabled:
            return await call_next(request)

        # If no API key configured, allow (development mode)
        if self.api_key is None:
            logger.warning(
                "No API key configured, allowing request (development mode)"
            )
            return await call_next(request)

        # Check X-API-Key header
        provided_key = request.headers.get("X-API-Key")

        if provided_key is None:
            logger.warning(f"Missing API key for {request.url.path}")
            raise HTTPException(
                status_code=401,
                detail="Missing API key. Provide X-API-Key header.",
            )

        if provided_key != self.api_key:
            logger.warning(f"Invalid API key for {request.url.path}")
            raise HTTPException(
                status_code=401,
                detail="Invalid API key.",
            )

        return await call_next(request)


# FastAPI dependency for API key validation
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key_dependency(
    api_key: str | None,
    config: ServerConfig,
) -> None:
    """
    Dependency function for API key validation.

    Args:
        api_key: API key from header
        config: Server configuration

    Raises:
        HTTPException: If API key is invalid
    """
    if not config.auth.enabled:
        return

    expected_key = get_api_key(config)
    if expected_key is None:
        return  # Development mode

    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide X-API-Key header.",
        )

    if api_key != expected_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key.",
        )