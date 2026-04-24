"""
System endpoints - health check, readiness, etc.
"""

from fastapi import APIRouter

router = APIRouter(tags=["system"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns basic health status for monitoring.
    """
    return {"status": "healthy", "service": "synthesai-server"}


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.

    Returns readiness status indicating if server can handle requests.
    """
    from learning_assistant.server.context import ServerContext

    if not ServerContext.is_initialized():
        return {
            "status": "not_ready",
            "message": "ServerContext not initialized",
        }

    return {
        "status": "ready",
        "plugins_loaded": len(ServerContext.plugin_manager.plugins) if ServerContext.plugin_manager else 0,
    }