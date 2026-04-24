"""
Link learning endpoint - sync processing for web links.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from learning_assistant.api.schemas import LinkSummaryResult
from learning_assistant.api.exceptions import LLMAPIError
from learning_assistant.server.config import ServerConfig, get_server_config
from learning_assistant.server.middleware import verify_api_key_dependency
from learning_assistant.server.context import ServerContext

router = APIRouter(prefix="/api/v1", tags=["link"])


def get_config() -> ServerConfig:
    """Get server config dependency."""
    return get_server_config()


class LinkRequest(BaseModel):
    """Request model for link processing."""

    url: HttpUrl = Field(description="URL of the web page to process")
    provider: str = Field(default="openai", description="LLM provider")
    model: str | None = Field(default=None, description="LLM model name")
    output_dir: str | None = Field(default=None, description="Output directory")
    generate_quiz: bool = Field(default=True, description="Generate quiz questions")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    detail: str | None = Field(default=None, description="Additional detail")


@router.post("/link", response_model=LinkSummaryResult)
async def process_link(
    request: LinkRequest,
    config: ServerConfig = Depends(get_config),
):
    """
    Process a web link and generate knowledge card.

    Takes a URL, fetches content, and generates:
    - Summary
    - Key points
    - Tags
    - Q&A pairs
    - Quiz questions (optional)

    Typical response time: 15-45 seconds.
    """
    api = ServerContext.get_api()

    try:
        options: dict[str, Any] = {}
        if request.provider:
            options["provider"] = request.provider
        if request.model:
            options["model"] = request.model
        if request.output_dir:
            options["output_dir"] = request.output_dir
        options["generate_quiz"] = request.generate_quiz

        result = await api.process_link(url=str(request.url), **options)
        return result

    except LLMAPIError as e:
        raise HTTPException(
            status_code=e.to_http_status(),
            detail=ErrorResponse(
                error="LLMAPIError",
                message=str(e),
            ).model_dump(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="ValidationError",
                message=str(e),
            ).model_dump(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="InternalError",
                message=str(e),
            ).model_dump(),
        )