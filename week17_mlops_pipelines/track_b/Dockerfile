FROM python:3.11-slim

WORKDIR /app

# Install basic build tools and curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast, deterministic installs matching uv.lock
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency lockfile and install dependencies without the root project
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application files
COPY . .

# Install the project itself
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Expose ports for FastAPI (8000) and Streamlit (8501)
EXPOSE 8000 8501

# Shell form ensures $PORT is evaluated at runtime by Render
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
