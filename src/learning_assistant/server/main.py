"""
SynthesAI Server - FastAPI main application.

HTTP API for AI-powered learning assistant:
- Link learning (sync)
- Vocabulary extraction (sync)
- Video summary (async task queue)
- Query endpoints (skills, history, statistics)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from learning_assistant.server.config import ServerConfig, load_server_config
from learning_assistant.server.context import ServerContext
from learning_assistant.server.middleware import APIKeyMiddleware
from learning_assistant.server.task_manager import TaskManager
from learning_assistant.server.routes import system, query, link, vocabulary, video, llm, auth
from learning_assistant.api.exceptions import LearningAssistantError


# Global config (loaded at startup)
_server_config: ServerConfig | None = None


def get_server_config() -> ServerConfig:
    """Get server configuration."""
    global _server_config
    if _server_config is None:
        _server_config = load_server_config()
    return _server_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    config = get_server_config()

    # Startup
    logger.info("Starting SynthesAI Server...")
    ServerContext.initialize()

    # Create task manager
    task_manager = TaskManager(config.task_queue)
    app.state.task_manager = task_manager

    # Start worker
    await task_manager.start_worker()

    logger.info(f"Server ready on {config.host}:{config.port}")

    yield

    # Shutdown
    logger.info("Shutting down SynthesAI Server...")
    await task_manager.stop_worker()
    logger.info("Server shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="SynthesAI Server",
    description="HTTP API for AI-powered learning assistant",
    version="0.2.0",
    lifespan=lifespan,
)

# Add middleware
config = get_server_config()
if config.auth.enabled:
    app.add_middleware(APIKeyMiddleware, config=config)


# Register routes
app.include_router(system.router)
app.include_router(query.router)
app.include_router(link.router)
app.include_router(vocabulary.router)
app.include_router(video.router)
app.include_router(llm.router)
app.include_router(auth.router)


# Exception handlers
@app.exception_handler(LearningAssistantError)
async def learning_assistant_exception_handler(
    request: Request,
    exc: LearningAssistantError,
):
    """Handle LearningAssistantError exceptions."""
    return JSONResponse(
        status_code=exc.to_http_status(),
        content={
            "error": exc.__class__.__name__,
            "message": str(exc),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalError",
            "message": str(exc),
        },
    )


# Main entry point for uvicorn
if __name__ == "__main__":
    import uvicorn

    config = get_server_config()
    uvicorn.run(
        "learning_assistant.server.main:app",
        host=config.host,
        port=config.port,
        reload=True,
    )