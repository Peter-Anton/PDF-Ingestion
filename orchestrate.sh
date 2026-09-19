#!/bin/bash
set -e

ACTION=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --action) ACTION="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

case "$ACTION" in
  start)
    docker compose up -d --build
    echo "Waiting for service..."
    for i in $(seq 1 60); do
      if curl -sf http://localhost:8000/docs > /dev/null; then
        echo "Service is up."
        exit 0
      fi
      sleep 2
    done
    echo "Service did not become ready in time."
    docker compose logs app
    exit 1
    ;;
  terminate)
    docker compose down -v
    ;;
  *)
    echo "Usage: ./orchestrate.sh --action [start|terminate]"
    exit 1
    ;;
esac
