# ============================================================
# Dockerfile — Titan AIO Multi-Stage Build
# ============================================================
# Stage 1 (vps)  : Lightweight deps only, for 859MB VPS deploy
# Stage 2 (dev)  : Full deps incl. ML, for local dev / Kaggle
#
# Build targets:
#   docker build --target vps -t titan-vps .
#   docker build --target dev -t titan-dev .
#
# Run:
#   docker run --env-file .env -p 8080:8080 titan-vps
#   docker run --env-file .env -p 8080:8080 titan-dev
# ============================================================

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Shared system deps (no GPU libs — GPU work runs on Kaggle)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# Stage 1: VPS — lightweight only (~859MB RAM constraint)
# ============================================================
# Excludes: torch, diffusers, transformers, accelerate,
#           opencv-python, sentencepiece, protobuf, chromadb
# ============================================================
FROM base AS vps

# Layer 1: Install production deps (changes less often → better cache)
RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.30.0" \
    "pydantic>=2.9.0" \
    "pydantic-settings>=2.5.0" \
    "sqlalchemy[asyncio]>=2.0.35" \
    "asyncpg>=0.30.0" \
    "aiosqlite>=0.20.0" \
    "redis>=5.2.0" \
    "langgraph>=0.2.21" \
    "httpx>=0.27.0" \
    "boto3>=1.35.0" \
    "fastmcp>=0.4.0" \
    "python-dotenv>=1.0.0" \
    "beautifulsoup4>=4.12.0" \
    "lxml>=5.3.0" \
    "google-genai>=2.0.0"

# Layer 2: Install titan-aio package (no heavy deps)
COPY pyproject.toml /app/
RUN pip install --no-cache-dir --no-deps . 2>/dev/null || true

# Layer 3: Copy application code
COPY titan/ /app/titan/
COPY MCP/ /app/MCP/
COPY Services/ /app/Services/
COPY Database/ /app/Database/
COPY Workers/ /app/Workers/

EXPOSE 8080

# FastAPI entrypoint (override with MCP stdio if needed)
CMD ["python", "-m", "titan.main"]

# ============================================================
# Stage 2: Dev — full deps including ML packages
# ============================================================
# Adds: torch, diffusers, transformers, accelerate,
#       opencv-python, sentencepiece, protobuf, chromadb
# Plus: pytest, mypy, ruff (dev tools)
# ============================================================
FROM base AS dev

# Layer 1: Install ALL deps (heavy ML packages)
RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.30.0" \
    "pydantic>=2.9.0" \
    "pydantic-settings>=2.5.0" \
    "sqlalchemy[asyncio]>=2.0.35" \
    "asyncpg>=0.30.0" \
    "aiosqlite>=0.20.0" \
    "redis>=5.2.0" \
    "chromadb>=0.5.5" \
    "langgraph>=0.2.21" \
    "httpx>=0.27.0" \
    "boto3>=1.35.0" \
    "fastmcp>=0.4.0" \
    "python-dotenv>=1.0.0" \
    "beautifulsoup4>=4.12.0" \
    "lxml>=5.3.0" \
    "google-genai>=2.0.0" \
    "diffusers>=0.30.0" \
    "torch>=2.0.0" \
    "transformers>=4.40.0" \
    "accelerate>=0.30.0" \
    "opencv-python>=4.9.0" \
    "sentencepiece>=0.2.0" \
    "protobuf>=5.0.0"

# Layer 2: Dev/test tools
RUN pip install --no-cache-dir \
    "pytest>=8.3.0" \
    "pytest-asyncio>=0.24.0" \
    "pytest-cov>=5.0.0" \
    "mypy>=1.11.0" \
    "ruff>=0.6.0"

# Layer 3: Install titan-aio package
COPY pyproject.toml /app/
RUN pip install --no-cache-dir --no-deps . 2>/dev/null || true

# Layer 4: Copy full project source
COPY . /app/

EXPOSE 8080

# Default: start dev server (tests via: docker run titan-dev pytest Tests/ -v)
CMD ["python", "-m", "titan.main"]
