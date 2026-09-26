# Financial Planning Suite v2 — React front end + FastAPI/numpy engine
# Build:  docker build -t financial-planner-v2 -f v2/Dockerfile v2
FROM node:20-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json* ./
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund
COPY web/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY engine/ ./engine/
COPY server/ ./server/
COPY --from=web /web/dist ./web/dist
ENV DATA_DIR=/app/data PYTHONUNBUFFERED=1
RUN mkdir -p /app/data/households
EXPOSE 8502
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD curl -fs http://localhost:8502/api/health || exit 1
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8502", "--workers", "1"]
