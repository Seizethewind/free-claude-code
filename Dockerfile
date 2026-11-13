FROM ghcr.io/astral-sh/uv:debian-slim

# The slim base has no CA bundle; needed for HTTPS to providers and the self-ping.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_INSTALL_DIR=/opt/python \
    PYTHONUNBUFFERED=1 \
    SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

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
