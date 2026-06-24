# Build context = backend/ (the uv project root).
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY shared/ ./shared/
COPY server/ ./server/

EXPOSE 8000

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
