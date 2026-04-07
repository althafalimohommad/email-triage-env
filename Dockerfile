# Email Triage Environment — Hugging Face Space Dockerfile
# HF Spaces requires Dockerfile at the repo root.
# Use a fully-qualified slim tag (bookworm) to avoid stale digest errors

FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip first to avoid resolver issues
RUN pip install --no-cache-dir --upgrade pip

# Copy project files
COPY . .

# Install Python dependencies (pinned via pyproject.toml)
RUN pip install --no-cache-dir -e .

# Expose HF Spaces default port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# HF Spaces uses port 7860 by default
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
