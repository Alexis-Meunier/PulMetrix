ARG PYTHON_VERSION=3.12-slim

# ────────── Build stage ──────────
FROM python:${PYTHON_VERSION} AS builder

COPY --from=ghcr.io/astral-sh/uv:0.9.0 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

# Copy lockfiles first for dependency layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --no-install-project --no-editable --no-dev

COPY . .
RUN uv sync --no-editable --no-dev

RUN set -eux; \
    rm -f /app/uv.lock || true; \
    rm -rf /root/.cache/pip /root/.cache/uv /tmp/pip-* || true; \
    find /app/.venv -type d -name "test"      -prune -exec rm -rf {} + || true; \
    find /app/.venv -type d -name "tests"     -prune -exec rm -rf {} + || true; \
    find /app/.venv -type d -name "__pycache__" -prune -exec rm -rf {} + || true; \
    find /app/.venv -type d -name "doc"       -prune -exec rm -rf {} + || true; \
    find /app/.venv -type f -name "*.pyc"     -delete || true; \
    true

# ────────── Runtime stage ──────────
FROM python:${PYTHON_VERSION}

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/. /app/.

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="${PYTHONPATH}:app"

WORKDIR /app

# TODO: Change path to fastapi file
CMD ["fastapi", "run"]
EXPOSE 8000