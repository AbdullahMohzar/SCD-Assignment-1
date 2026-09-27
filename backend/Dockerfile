# ==========================================
# Stage 1: Build stage
# ==========================================
FROM python:3.12.8-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies in isolated wheels/prefix
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ==========================================
# Stage 2: Runtime stage
# ==========================================
FROM python:3.12.8-slim AS runner

# Create non-root system user and group (§3.1)
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -s /bin/bash -m appuser

# Install minimal runtime libraries (libpq for postgres) and curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed Python packages from builder stage
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy application source code and migrations
COPY --chown=appuser:appuser alembic.ini .
COPY --chown=appuser:appuser alembic alembic/
COPY --chown=appuser:appuser seeds seeds/
COPY --chown=appuser:appuser app app/

# Switch to non-root user
USER 10001:10001

EXPOSE 8000

# Docker healthcheck checking liveness probe endpoint (§3.1)
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Exec form CMD (§3.1)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
