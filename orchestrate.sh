#!/bin/bash
set -e

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker/Docker-compose.yml"

ACTION=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --action) ACTION="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

case "$ACTION" in
  start)
    docker compose -f "$COMPOSE_FILE" up -d --build
    echo "Waiting for service (this may take a few minutes on first run)..."
    for i in $(seq 1 150); do
      if curl -sf http://localhost:8000/docs > /dev/null; then
        echo "Service is up."
        exit 0
      fi
      if [ $((i % 15)) -eq 0 ]; then
        echo "  Still waiting... (${i}×2s elapsed)"
      fi
      sleep 2
    done
    echo "Service did not become ready in time."
    docker compose -f "$COMPOSE_FILE" logs app --tail 50
    exit 1
    ;;
  terminate)
    docker compose -f "$COMPOSE_FILE" down
    ;;
  *)
    echo "Usage: ./orchestrate.sh --action [start|terminate]"
    exit 1
    ;;
esac
