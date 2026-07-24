# KC-001 reproducible research image (no model weights baked in).
FROM pytorch/pytorch:2.7.0-cuda12.8-cudnn9-runtime

WORKDIR /workspace/kc001
COPY pyproject.toml README.md ./
COPY src ./src
COPY tests ./tests
COPY scripts ./scripts
RUN pip install --no-cache-dir -e ".[dev]"

ENV COBRA_KC001_ROOT=/workspace/kc001
ENV HF_HOME=/workspace/.cache/huggingface
ENV TRANSFORMERS_CACHE=/workspace/.cache/huggingface
ENV COBRA_EXPERIMENT_DIR=/workspace/kc001/artifacts/experiments

CMD ["pytest", "-q"]
