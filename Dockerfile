FROM ghcr.io/astral-sh/uv:debian-slim

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_INSTALL_DIR=/opt/python \
    PYTHONUNBUFFERED=1 \
    SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0

WORKDIR /app
COPY . .

# pyproject pins requires-python to exactly 3.14.10, so let uv fetch that build.
RUN uv python install 3.14.10 \
    && uv sync --frozen --no-dev --python 3.14.10

ENV PATH="/app/.venv/bin:${PATH}" \
    HOST=0.0.0.0 \
    FCC_OPEN_BROWSER=false \
    MESSAGING_PLATFORM=none \
    VOICE_NOTE_ENABLED=false

CMD ["python", "scripts/render_start.py"]
