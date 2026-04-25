"""
Server routes for SynthesAI HTTP API.
"""

from learning_assistant.server.routes import (
    auth,
    configuration,
    link,
    llm,
    query,
    system,
    video,
    vocabulary,
)

__all__ = ["link", "vocabulary", "video", "query", "system", "llm", "auth", "configuration"]
