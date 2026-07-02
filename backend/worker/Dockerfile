# Build context = backend/ (the uv project root).
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-default-groups --group worker

COPY shared/ ./shared/
COPY worker/ ./worker/

CMD ["python", "-m", "worker.agent", "start"]