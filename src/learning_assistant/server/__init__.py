"""
SynthesAI Server - HTTP API for AI learning assistant.

This module provides FastAPI-based HTTP endpoints for:
- Link learning (sync)
- Vocabulary extraction (sync)
- Video summary (async task queue)
- Query endpoints (skills, history, statistics)
"""

from learning_assistant.server.main import app

__all__ = ["app"]