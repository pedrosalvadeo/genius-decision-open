# Build from the repository root. No inbound port; all communication uses HTTPS.
FROM python:3.12-slim-bookworm@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3
ENV PYTHONPATH=/app/adaptive:/app/twin:/app/kernel PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY beta/requirements.lock /app/beta/requirements.lock
RUN python -m pip install --no-cache-dir --only-binary=:all: --require-hashes -r beta/requirements.lock \
    && groupadd --gid 10001 genius && useradd --uid 10001 --gid 10001 --no-create-home genius \
    && mkdir /state && chown 10001:10001 /state && chmod 700 /state
COPY adaptive/federation /app/adaptive/federation
COPY twin/genius_twin /app/twin/genius_twin
COPY kernel/genius_kernel /app/kernel/genius_kernel
USER 10001:10001
VOLUME ["/state"]
ENTRYPOINT ["python","-m","federation.internet","--state","/state"]
CMD ["--help"]
