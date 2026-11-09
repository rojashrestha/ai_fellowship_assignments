FROM python:3.11-slim

WORKDIR /app

# Install basic build tools and curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast, deterministic installs matching uv.lock
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency lockfile
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application files
COPY . .
RUN uv pip install --no-deps -e .

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Expose ports for FastAPI (8000) and Streamlit (8501)
EXPOSE 8000 8501

# Default entrypoint starts the FastAPI backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
