# Email Triage Environment — Hugging Face Space Dockerfile
# HF Spaces requires Dockerfile at the repo root.
# Use Python 3.11-alpine - minimal image most likely to be cached universally

FROM python:3.11-alpine

WORKDIR /app

# Install system dependencies (alpine uses apk instead of apt-get)
RUN apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers && \
    apk add --no-cache --virtual .build-deps build-base

# Upgrade pip first to avoid resolver issues
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements files first for better layer caching
COPY pyproject.toml README.md LICENSE ./
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Clean up build dependencies
RUN apk del .build-deps

# Expose HF Spaces default port
EXPOSE 7860

# Health check (simplified - just check if port is listening)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('localhost', 7860), timeout=5)" || exit 1

# HF Spaces uses port 7860 by default
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
