# =========================================================
# Stage 1: Build & Dependencies
# =========================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# =========================================================
# Stage 2: Final Production Runtime
# =========================================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime curl for container healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Copy application source and configuration
COPY app/ ./app/
COPY data/ ./data/
COPY docs/ ./docs/
COPY tests/ ./tests/
COPY README.md .
COPY requirements.txt .

EXPOSE 8000 8501

# Default command: Start FastAPI Backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
