FROM python:3.11-slim
RUN pip install --no-cache-dir fastapi uvicorn httpx pynacl \
 && useradd -u 10001 -m app \
 && mkdir -p /data && chown 10001:10001 /data
ARG SERVICE
WORKDIR /app
COPY ${SERVICE}/ /app/
USER 10001
