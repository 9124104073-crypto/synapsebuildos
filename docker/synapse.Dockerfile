# Synapse BuildOS — one image, one origin: the FastAPI service serves the API
# and the two pages (web/), so the browser never makes a cross-origin call.
#
#   docker build -f docker/synapse.Dockerfile -t synapse .
#   docker run -p 8000:8000 -e SYNAPSE_JWT_SECRET=... -e ANTHROPIC_API_KEY=... synapse
#
# With no DATABASE_URL it runs on SQLite inside the container, which is fine
# for a demo and wrong for anything shared: point SYNAPSE_DATABASE_URL at
# Postgres and the same image is a real deployment.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SYNAPSE_STATIC_DIR=/srv/web

WORKDIR /srv

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY api/app ./app
COPY web ./web

# Not root, and not writable by the app: the only thing that needs to be
# writable is the SQLite file, which lives in /data.
RUN useradd --system --uid 10001 synapse && mkdir -p /data && chown synapse /data
USER synapse
ENV SYNAPSE_DATABASE_URL=sqlite:////data/synapse.db

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
