# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder

WORKDIR /src
COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --no-cache-dir build && \
    python -m build --wheel --outdir /dist

# ---- runtime ----
FROM python:3.12-slim

LABEL org.opencontainers.image.title="agent-lint"
LABEL org.opencontainers.image.description="Lint agent workflow YAML for anti-patterns"
LABEL org.opencontainers.image.source="https://github.com/AreteDriver/agent-lint"

COPY --from=builder /dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm -rf /tmp/*.whl

ENTRYPOINT ["agent-lint"]
CMD ["--help"]
