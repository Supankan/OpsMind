# Multi-stage Dockerfile for OpsMind API
FROM ghcr.io/astral-sh/uv:0.5.24 AS uv_bin

FROM python:3.13-slim AS builder

WORKDIR /app

# Install uv from the official image
COPY --from=uv_bin /uv /uvx /bin/

# Set uv environment flags
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install dependencies first for layer caching
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project --no-dev

# Copy application source
COPY opsmind/ ./opsmind/
COPY apps/ ./apps/
RUN uv sync --frozen --no-dev

# Final runtime image
FROM python:3.13-slim AS runner

WORKDIR /app

# Create a non-root user
RUN addgroup --system --gid 1001 opsmind && \
    adduser --system --uid 1001 --gid 1001 opsmind

# Copy virtual environment from builder
COPY --from=builder --chown=opsmind:opsmind /app/.venv /app/.venv
COPY --from=builder --chown=opsmind:opsmind /app/opsmind /app/opsmind
COPY --from=builder --chown=opsmind:opsmind /app/apps /app/apps
COPY --chown=opsmind:opsmind README.md /app/README.md

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production

USER opsmind

EXPOSE 8000

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
