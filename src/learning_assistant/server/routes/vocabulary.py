"""
Vocabulary extraction endpoint - sync processing for text/URL.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from learning_assistant.api.schemas import VocabularyResult
from learning_assistant.api.exceptions import LLMAPIError
from learning_assistant.server.config import ServerConfig, get_server_config
from learning_assistant.server.middleware import verify_api_key_dependency
from learning_assistant.server.context import ServerContext

router = APIRouter(prefix="/api/v1", tags=["vocabulary"])


def get_config() -> ServerConfig:
    """Get server config dependency."""
    return get_server_config()


class VocabularyRequest(BaseModel):
    """Request model for vocabulary extraction."""

    content: str | None = Field(
        default=None,
        description="Text content to extract vocabulary from",
    )
    url: HttpUrl | None = Field(
        default=None,
        description="URL to fetch content from",
    )
    word_count: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of words to extract (1-50)",
    )
    difficulty: str = Field(
        default="intermediate",
        description="Target difficulty level (beginner/intermediate/advanced)",
    )
    generate_story: bool = Field(
        default=True,
        description="Generate context story using extracted words",
    )

    def validate_input(self) -> None:
        """Validate that either content or url is provided."""
        if not self.content and not self.url:
            raise ValueError("Either content or url must be provided")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    detail: str | None = Field(default=None, description="Additional detail")


@router.post("/vocabulary", response_model=VocabularyResult)
async def extract_vocabulary(
    request: VocabularyRequest,
    config: ServerConfig = Depends(get_config),
):
    """
    Extract vocabulary from text or URL.

    Extracts key vocabulary words and generates:
    - Vocabulary cards with phonetics, definitions, examples
    - Context story (optional)
    - Statistics

    Typical response time: 20-60 seconds.
    """
    # Validate input
    try:
        request.validate_input()
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="ValidationError",
                message=str(e),
            ).model_dump(),
        )

    api = ServerContext.get_api()

    try:
        result = await api.extract_vocabulary(
            content=request.content,
            url=str(request.url) if request.url else None,
            word_count=request.word_count,
            difficulty=request.difficulty,
            generate_story=request.generate_story,
        )
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