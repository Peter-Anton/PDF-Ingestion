#!/bin/sh
set -e

echo "==> Waiting for Ollama at ${OLLAMA_HOST:-http://ollama:11434}..."
until curl -sf "${OLLAMA_HOST:-http://ollama:11434}/api/version" > /dev/null 2>&1; do
  sleep 2
done
echo "==> Ollama is ready."

echo "==> Pulling embedding model: ${EMBEDDING_MODEL_ID:-all-minilm}..."
curl -s -X POST "${OLLAMA_HOST:-http://ollama:11434}/api/pull" \
  -d "{\"name\": \"${EMBEDDING_MODEL_ID:-all-minilm}\"}" > /dev/null
echo "==> Model pull complete."

echo "==> Running database migrations..."
cd /app/models/db_scheme/pgvector
alembic upgrade head
cd /app

echo "==> Starting application server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
