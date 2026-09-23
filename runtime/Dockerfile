# Cognitia Standalone Runtime Container
# Local-first, unprivileged, non-root, read-only root compatible with durable file persistence

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src:/app \
    COGNITIA_HOST=0.0.0.0 \
    COGNITIA_PORT=8000

WORKDIR /app

# Create unprivileged service user and persistence directory
RUN addgroup --system --gid 10001 cognitia && \
    adduser --system --uid 10001 --gid 10001 --no-create-home cognitia && \
    mkdir -p /var/lib/cognitia && \
    chown -R cognitia:cognitia /var/lib/cognitia

# Copy source code and runtime configuration
COPY src/ /app/src/
COPY runtime/ /app/runtime/
COPY pyproject.toml /app/

# Set strict permissions
RUN chown -R cognitia:cognitia /app

# Switch to non-root user
USER cognitia

# Expose service port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
  CMD python /app/runtime/scripts/health_check.py http://127.0.0.1:8000/v1/health || exit 1

ENTRYPOINT ["python", "/app/runtime/scripts/start_runtime.py"]
