# Build from repository root; Linux/amd64, CPython 3.12.
FROM python:3.12-slim-bookworm@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3 AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/adaptive:/app/twin:/app/kernel \
    LANGSMITH_TRACING=false \
    LANGCHAIN_TRACING_V2=false
WORKDIR /app
COPY adaptive/requirements.lock /app/adaptive/requirements.lock
RUN python -m pip install --no-cache-dir --only-binary=:all: --require-hashes -r /app/adaptive/requirements.lock
COPY adaptive/genius_adaptive /app/adaptive/genius_adaptive
COPY adaptive/explorers /app/adaptive/explorers
COPY adaptive/federation /app/adaptive/federation
COPY twin/genius_twin /app/twin/genius_twin
COPY kernel/genius_kernel /app/kernel/genius_kernel
USER 65534:65534
ENTRYPOINT ["python", "-m", "genius_adaptive"]
CMD ["--help"]

# Git is used only by tests to make independent source fixtures. The runner
# executes a prepared mission directory and needs no Git or cloud credentials.
FROM runtime AS tests
USER root
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
COPY adaptive/tests /app/adaptive/tests
COPY adaptive/observers /app/adaptive/observers
USER 65534:65534
ENTRYPOINT ["python", "-m", "unittest", "discover", "-s", "adaptive/tests", "-v"]
CMD []
