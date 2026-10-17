# Build from the repository root on Linux/amd64.
# Base identity recorded in the accepted Railway build; upgrades require review.
FROM python:3.12-slim-bookworm@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/adaptive:/app/beta:/app/product_local:/app/consumer_views:/app/twin:/app/kernel \
    GENIUS_DATA_DIR=/data/genius \
    GENIUS_ENV=production \
    PORT=8080

WORKDIR /app
COPY beta/requirements.lock /app/beta/requirements.lock
COPY adaptive/requirements.lock /app/adaptive/requirements.lock
RUN python -m pip install --no-cache-dir --only-binary=:all: --require-hashes -r /app/beta/requirements.lock -r /app/adaptive/requirements.lock \
    && groupadd --gid 10001 genius \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin genius \
    && mkdir -p /data/genius \
    && chown 10001:10001 /data /data/genius \
    && chmod 700 /data/genius

COPY beta /app/beta
COPY adaptive/genius_adaptive /app/adaptive/genius_adaptive
COPY adaptive/federation /app/adaptive/federation
COPY product_local/genius_local /app/product_local/genius_local
COPY consumer_views/genius_views /app/consumer_views/genius_views
COPY twin/genius_twin /app/twin/genius_twin
COPY twin/examples /app/twin/examples
COPY twin/cases /app/twin/cases
COPY kernel/genius_kernel /app/kernel/genius_kernel

USER 10001:10001
EXPOSE 8080
STOPSIGNAL SIGTERM
CMD ["python", "/app/beta/deploy/start.py"]
