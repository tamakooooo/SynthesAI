# SynthesAI Server Dockerfile
# Python 3.11 slim image with FFmpeg for video processing

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir ".[server,link]"

# Copy application code
COPY src/ src/
COPY config/ config/
COPY templates/ templates/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV SYNTHESAI_CONFIG_DIR=/app/config

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run server
CMD ["uvicorn", "learning_assistant.server.main:app", "--host", "0.0.0.0", "--port", "8000"]