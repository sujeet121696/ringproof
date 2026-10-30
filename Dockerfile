# Ringproof in one container: FastAPI serves the API, the WebSocket and the built dashboard.
# Used for the hosted demo (Render free web service); locally, `npm run local` does the same.

# 1. Build the dashboard
FROM node:22-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# 2. Run the server
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt requirements.lock ./
RUN pip install --no-cache-dir -r requirements.txt -c requirements.lock
COPY app/ app/
COPY samples/ samples/
COPY --from=web /web/dist web/dist
# No root at runtime; secrets come from the host's environment settings, never the image.
RUN useradd --create-home ringproof
USER ringproof
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips '*'"]
