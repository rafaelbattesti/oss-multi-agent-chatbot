# Build context is the repo root (the uv workspace).
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
COPY packages ./packages
RUN uv sync --frozen --no-dev --package mcp-arxiv
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "mcp_arxiv.server"]
