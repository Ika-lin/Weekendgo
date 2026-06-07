FROM node:20-bookworm-slim AS web-builder

WORKDIR /app/web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_DEBUG=false \
    PORT=5000

WORKDIR /app

COPY backend/ ./backend/
COPY --from=web-builder /app/web/dist ./web/dist

RUN pip install --no-cache-dir -r backend/requirements.txt

EXPOSE 5000

CMD ["sh", "-c", "gunicorn --chdir backend 'app:create_app()' --bind 0.0.0.0:${PORT:-5000} --workers 1 --threads 4 --timeout 120"]
