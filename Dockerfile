# Multi-stage Dockerfile for OpenGov-Pension
FROM python:3.12-slim AS base

# Security: Use non-root user
ARG USERNAME=appuser
ARG USER_UID=1001
ARG USER_GID=$USER_UID

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src \
    APP_HOME=/app

WORKDIR /app

# Install system dependencies with security considerations
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        libpq-dev \
        gcc \
        postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/*

# Create non-root user with specific UID/GID for security
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && chown -R $USERNAME:$USERNAME /app

FROM base AS dependencies

# Install Python dependencies in a virtual environment
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install project dependencies
RUN pip install --no-cache-dir .[web]

FROM base AS runtime

# Copy virtual environment from dependencies stage
COPY --from=dependencies /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=$USERNAME:$USERNAME src/ ./src/

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /app/logs && \
    chown -R $USERNAME:$USERNAME /app

# Switch to non-root user
USER $USERNAME

# Expose port
EXPOSE 8000

# Health check with proper error handling
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Add labels for better container management
LABEL org.opencontainers.image.title="OpenGov-Pension" \
      org.opencontainers.image.description="Production-grade pension management API" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.authors="Nik Jois <nikjois@llamasearch.ai>" \
      org.opencontainers.image.source="https://github.com/llamasearchai/OpenPension"

# Use exec form for proper signal handling
CMD ["uvicorn", "opengovpension.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
