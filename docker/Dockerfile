# SynthesAI Server Dockerfile
# Python 3.11 slim image with FFmpeg for video processing

FROM python:3.11-slim

# Install system dependencies
# - ffmpeg: video/audio processing (extract audio from video)
# - curl: health check and API requests
# - ca-certificates: SSL/TLS certificates for HTTPS connections
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && ffmpeg -version

# Set working directory
WORKDIR /app

# Copy and install dependencies
# Includes yutto (B站下载器), yt-dlp, faster-whisper, etc.
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir ".[server,link]" \
    # Verify critical dependencies are installed
    && python -c "import yt_dlp; import yutto; print('Dependencies OK')"

# Copy application code
COPY src/ src/
COPY config/ config/
COPY templates/ templates/

# Create necessary directories
RUN mkdir -p /app/data/downloads /app/data/audio /app/data/cache /app/config/cookies

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