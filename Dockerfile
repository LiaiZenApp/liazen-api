# Development Dockerfile - Optimized for fast rebuilds and debugging
FROM python:3.11-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app \
    LOG_LEVEL=DEBUG \
    LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Install system dependencies, Python packages, and setup directories
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir \
        pytest-watch \
        black \
        flake8 \
        mypy \
        pre-commit

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads profile_images logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Development server with auto-reload and logging
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug", "--access-log"]
