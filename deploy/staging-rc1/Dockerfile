# KC-016 — Cobra Core Protocol V1 staging image
# Core package contents are pinned to certified RC1:
#   v0.9.0-rc1 / ec400d83a9cc8105557bda2105f177cc619638b2
#
# Build context: repository root (cobra-core), preferably checked out at that SHA.
# Staging edge (deploy/staging-rc1) is the only additive runtime surface.

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.title="cobra-core-staging-rc1"
LABEL org.opencontainers.image.version="v0.9.0-rc1"
LABEL org.opencontainers.image.revision="ec400d83a9cc8105557bda2105f177cc619638b2"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    COBRA_CORE_REVISION=ec400d83a9cc8105557bda2105f177cc619638b2 \
    COBRA_CORE_GIT_SHA=ec400d83a9cc8105557bda2105f177cc619638b2 \
    COBRA_PROTOCOL_VERSION=1 \
    COBRA_COMPATIBILITY_VERSION=1 \
    COBRA_INFERENCE_MODE=mock \
    COBRA_CORE_ENABLED=true \
    COBRA_CORE_METRICS_ENABLED=true \
    COBRA_CORE_MAX_CONCURRENT=2 \
    COBRA_CORE_REQUIRE_ORG_HEADER=true \
    COBRA_CORE_INTERNAL_PORT=18080 \
    PORT=8080

WORKDIR /app

# Install certified Core library from this build context (must be RC1 tree).
COPY pyproject.toml README.md ./
COPY src ./src
COPY scripts ./scripts
RUN pip install --no-cache-dir .

# Staging edge only (not part of Protocol V1 certified sources).
COPY deploy/staging-rc1/staging_edge.py /app/staging_edge.py

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request; s=os.environ['COBRA_CORE_AUTH_SECRET']; \
r=urllib.request.Request('http://127.0.0.1:'+os.environ.get('PORT','8080')+'/health', headers={'Authorization':'Bearer '+s}); \
urllib.request.urlopen(r, timeout=4)"

CMD ["python", "/app/staging_edge.py"]
