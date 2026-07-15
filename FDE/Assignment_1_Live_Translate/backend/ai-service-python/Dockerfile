# Build context is the assignment root (see docker-compose.yml), so every COPY
# path below is relative to FDE/Assignment_1_Live_Translate/.
#
# Alpine over slim: roughly half the image for the same result. The usual
# objection — musl breaks Python wheels — no longer holds for this dependency
# set. Verified on linux/amd64 (the deploy target): jiter, httptools, pyyaml,
# uvloop, watchfiles, websockets and pydantic_core all resolve to prebuilt
# musllinux_x86_64 wheels, nothing compiles, and fastapi/anthropic/pydantic_core
# import cleanly. Re-check this if a dependency with C extensions is added.
FROM python:3.12-alpine

WORKDIR /app

# Dependencies before source: Docker caches each step and re-runs a step only
# when its inputs changed. Copying requirements.txt on its own means editing
# app.py does not re-install FastAPI.
COPY backend/ai-service-python/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ai-service-python/ .

# Run as a non-root user, with /app left root-owned so the service cannot
# rewrite its own source. Only /data changes hands: it is the mount point for
# the cache volume, and Docker copies the image's ownership onto a named volume
# when it first creates it, so setting it here is what makes the volume
# writable later. The compose file sets LOG_FILE="" so nothing else needs to be.
# adduser here is busybox's, not shadow's: -D skips the password prompt.
RUN adduser -D -u 10001 app \
    && mkdir -p /data \
    && chown -R app:app /data
USER app

# Both defaults in app.py and lib/logger.py are relative to the working
# directory, which is root-owned above. Setting them here is what lets the image
# boot on its own: `docker run`, `fly deploy` and any Coolify config that builds
# the Dockerfile without this compose file would otherwise die during import
# with PermissionError on /app/ai-service.log, and then again on
# /app/translations.db. The compose file now confirms these rather than supplies
# them. Both stay overridable at runtime.
ENV LOG_FILE="" \
    TRANSLATION_DB_PATH=/data/translations.db

EXPOSE 8000

# --host 0.0.0.0 is required. Uvicorn binds 127.0.0.1 by default, which inside
# a container means "this container only" — the gateway would get connection
# refused while the container looks perfectly healthy.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
