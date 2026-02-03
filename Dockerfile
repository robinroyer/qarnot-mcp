# Multi-stage Dockerfile for Qarnot MCP Server

# Build stage
FROM python:3.12-slim AS builder

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first for caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY src ./src
COPY main.py ./

# Production stage
FROM python:3.12-slim AS production

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --from=builder /app/src ./src
COPY --from=builder /app/main.py ./

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV QARNOT_BASE_URL=https://api.qarnot.com
ENV QARNOT_API_VERSION=1
ENV LOG_LEVEL=INFO

# Expose port for streamable-http transport
EXPOSE 8000

# Run the server
CMD ["python", "main.py"]
